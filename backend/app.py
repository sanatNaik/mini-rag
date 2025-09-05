import os
import requests
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
from fastapi import FastAPI, Request, HTTPException
import time
import openai
from openai import OpenAI
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()

# Allow requests from your frontend origin
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # you can use ["*"] to allow all
    allow_credentials=True,
    allow_methods=["*"],    # allow GET, POST, etc.
    allow_headers=["*"],    # allow all headers
)


load_dotenv()
PC_TOKEN = os.getenv("PINECONE_TOKEN")
PD_HF_TOKEN = os.getenv("PD_HF_TOKEN")
HF_EMBED_MODEL = "sentence-transformers/all-mpnet-base-v2"
JINA_RERANK_MODEL = "jinaai/jina-reranker-v2-base-multilingual"
JINA_API_KEY = os.getenv("JINA_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENAI_PD_OR")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_EMBED_MODEL = "text-embedding-3-small"

client = OpenAI(api_key=OPENAI_API_KEY)

index_name = "predusk-mini-rag"

pc = Pinecone(api_key=PC_TOKEN)

existing_indexes = [idx["name"] for idx in pc.list_indexes()]
print("Existing Indexes:", existing_indexes)

if index_name not in existing_indexes:
    pc.create_index(index_name, 
                    dimension=1536, 
                    metric="cosine",
                   spec=ServerlessSpec(cloud="aws", region="us-east-1")
                   )
else:
    print("Index already exists")
index = pc.Index(index_name)

def get_embeddings(text):

    print("inside get embeddings function")
    
    if not text or not text.strip():
        raise ValueError("Text is required for embeddings")
    
    try:
        print("yo")
        response = client.embeddings.create(
            input=text,
            model="text-embedding-3-small"
        )
        print("Embedding response:", response)
        print("reached response")
        
        # if not isinstance(response, dict):
        #     raise HTTPException(status_code=500, detail=f"Unexpected response type: {type(response)}")

        # data_list = response.get("data")
        # if not data_list or not isinstance(data_list, list):
        #     raise HTTPException(status_code=500, detail="No embeddings returned from API")
        embedding = response.data[0].embedding
        print("embedding generated successfully")
        return embedding
    
    except requests.exceptions.RequestException as req_err:
        print("RequestException in embeddings:", str(req_err))
        raise HTTPException(status_code=500, detail=f"Request error: {str(req_err)}")
    
    except Exception as e:
        print("Error in get_embeddings:", str(e))
        raise HTTPException(status_code=500, detail=f"Error generating embeddings: {str(e)}")


@app.post("/embed-upload")
async def embed_upload(request: Request):
    print("inside embed upload function")
    try:
        data = await request.json()
        text = data.get("text")
        source = data.get("source", "unknown")           # New field
        section_title = data.get("section_title", "NA")  # New field
        position = data.get("position", 1)               # New field

        if not text:
            raise HTTPException(status_code=400, detail="Text is required")

        start = time.time()
        print("working fine before embedding")
        embedding = get_embeddings(text)  # HuggingFace embedding call
        print("Embedding type:", type(embedding))
        print("Embedding length:", len(embedding))
        print("Embedding sample:", embedding[:5])
        vec_id = f"{source}-{position}-{int(time.time())}"  # Unique ID using metadata
        print("working fine till now")
        # Store embedding with metadata in Pinecone
        print(index)
        index.upsert([
            (
                vec_id,
                embedding,
                {
                    "text": text,
                    "source": source,
                    "section_title": section_title,
                    "position": position
                }
            )
        ])
        print("Upserted into pinecone")
        elapsed = round(time.time() - start, 2)
        return {
            "message": "Stored in Pinecone",
            "id": vec_id,
            "metadata": {
                "source": source,
                "section_title": section_title,
                "position": position
            },
            "time_taken": elapsed
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query")
async def query_rag(request: Request):
    print("inside query recieved function")
    try:
        data = await request.json()
        query_text = data.get("query")
        print("recieved query")
        print(query_text)
        if not query_text:
            raise HTTPException(status_code=400, detail="Query text is required")

        start = time.time()
        print("i am here")
        query_embedding = get_embeddings(query_text)
        print("got embeddings")
        results = index.query(
            vector=query_embedding,
            top_k=5,
            include_metadata=True
        )
        print("Pinecone raw results:", results)
        reranked_matches = rerank_with_jina(query_text, results["matches"], top_n=3)
        print("getting")
        final_answer = generate_answer_openrouter(query_text, reranked_matches)

        citations = [m["metadata"].get("text", "") for m in results["matches"]]
        print(citations)
        sources = [m["metadata"].get("source", "unknown") for m in reranked_matches]

        elapsed = round(time.time() - start, 2)

        return {
            "answer": final_answer,
            "citations": citations,
            "sources": sources,
            "time_taken": elapsed
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/delete_all/")
def delete_all_vectors():
    print("inside delete all vectors function")
    try:
        index.delete(deleteAll=True) 
        return {"status": "success", "message": "All vectors deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def chunk_text_with_metadata(text, source, section_title, chunk_size=500, overlap=50):
    print("inside chunking function function")
    chunks = []
    start = 0
    chunk_id = 1
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk_text = text[start:end]
        metadata = {
            "source": source,
            "section_title": section_title,
            "position": chunk_id
        }
        chunks.append((chunk_text, metadata))
        start += chunk_size - overlap
        chunk_id += 1
    return chunks


def rerank_with_jina(query, matches, top_n=3, api_key=None, model="jina-reranker-v2-base-multilingual"):
    try:
        if not matches:
            return []

        print("inside reranking function")

        # Extract only text, ignore metadata
        docs_for_jina = []
        for m in matches:
            text = m.get("metadata", {}).get("text")
            if text is None:
                continue
            # Convert non-string text to string
            text_str = str(text)  # <-- convert to string
            docs_for_jina.append(text_str)
            doc_to_match[text_str] = m

        if not docs_for_jina:
            return matches[:top_n]

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key or JINA_API_KEY}"
        }

        payload = {
            "model": model,
            "query": str(query),
            "documents": docs_for_jina,
            "top_n": top_n
        }

        url = "https://api.jina.ai/v1/rerank"
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()

        results = response.json().get("results", [])


        # Return matches in the reranked order, ignore metadata
        ranked_matches = []
        for r in results:
            doc_text = r.get("document")
            if doc_text is not None:
                doc_text = str(doc_text)  # ensure string
            if doc_text in doc_to_match:
                ranked_matches.append(doc_to_match[doc_text])

        return ranked_matches[:top_n]

    except Exception as e:
        print("Reranker Exception:", str(e))
        return matches[:top_n]  # fallback
    

openrouter_client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key=OPENROUTER_API_KEY,
)


def generate_answer_openrouter(query, reranked_chunks):
    print("inside open router calling function")

    # Prepare context
    if not reranked_chunks:
        context_text = "No relevant context found to answer the question."
    else:
        context_text = "\n\n".join(
            f"[Source: {c['metadata'].get('source', 'unknown')}] {c['metadata'].get('text','')}"
            for c in reranked_chunks
        )

    # Build prompt
    prompt = f"""
You are a helpful RAG-supported AI assistant that is meant to use the given context and answer the user query.
Use the following context to answer the question accurately.

Context:
{context_text}

Question: {query}

Answer:
"""
    print(prompt)
    try:
        # Call the model
        response = openrouter_client.chat.completions.create(
            model="openai/gpt-oss-20b:free",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a helpful RAG-supported AI assistant. Make sure your answer is strictly "
                        "based on the provided context. Mention citations like [1], [2], etc. Do not invent information. "
                        "If you cannot answer the question based on the context, say so directly."
                    )
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )

        # Safely extract the text
        if not response.choices or len(response.choices) == 0:
            return "No response from model"

        # OpenAI-style
        answer = response.choices[0].message.content
        print("recieved answer")
        return answer.strip()

    except Exception as e:
        print("Error in OpenRouter call:", str(e))
        return f"Error generating answer: {str(e)}"