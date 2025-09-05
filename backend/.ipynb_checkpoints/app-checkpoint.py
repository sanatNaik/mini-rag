import os
import requests
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
from fastapi import FastAPI, Request, HTTPException
import time
import openai

load_dotenv()
PC_TOKEN = os.getenv("PINECONE_TOKEN")
PD_HF_TOKEN = os.getenv("PD_HF_TOKEN")
HF_EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
JINA_RERANK_MODEL = "jinaai/jina-reranker-v2-base-multilingual"
OPENROUTER_API_KEY = os.getenv("OPENAI_PD_OR")

def get_embeddings(text):
    headers = {"Authorization": f"Bearer {PD_HF_TOKEN}"}
    payload = {"inputs": text}
    response = requests.post(f"https://api-inference.huggingface.co/pipeline/feature-extraction/{HF_EMBED_MODEL}", 
                             headers=headers, json=payload)
    return response.json()

index_name = "predusk-mini-rag"

pc = Pinecone(api_key=PC_TOKEN)

existing_indexes = [idx["name"] for idx in pc.list_indexes()]
print("Existing Indexes:", existing_indexes)

if index_name not in existing_indexes:
    pc.create_index(index_name, 
                    dimension=384, 
                    metric="cosine",
                   spec=ServerlessSpec(cloud="aws", region="us-east-1")
                   )
else:
    print("Index already exists")
index = pc.Index(index_name)

def get_embeddings(text):
    """Call Hugging Face API for embeddings"""
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    payload = {"inputs": text}
    resp = requests.post(
        f"https://api-inference.huggingface.co/pipeline/feature-extraction/{HF_EMBED_MODEL}",
        headers=headers,
        json=payload
    )
    return resp.json()


app = FastAPI()

@app.post("/embed-upload")
async def embed_upload(request: Request):
    try:
        data = await request.json()
        text = data.get("text")
        source = data.get("source", "unknown")           # New field
        section_title = data.get("section_title", "NA")  # New field
        position = data.get("position", 1)               # New field

        if not text:
            raise HTTPException(status_code=400, detail="Text is required")

        start = time.time()
        embedding = get_embeddings(text)  # HuggingFace embedding call
        vec_id = f"{source}-{position}-{int(time.time())}"  # Unique ID using metadata

        # Store embedding with metadata in Pinecone
        index.upsert([
            (
                vec_id,
                embedding[0],
                {
                    "text": text,
                    "source": source,
                    "section_title": section_title,
                    "position": position
                }
            )
        ])

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
    try:
        data = await request.json()
        query_text = data.get("query")

        if not query_text:
            raise HTTPException(status_code=400, detail="Query text is required")

        start = time.time()

        query_embedding = get_embeddings(query_text)

        results = index.query(
            vector=query_embedding[0],
            top_k=5,
            include_metadata=True
        )

        reranked_matches = rerank_with_jina(query_text, results["matches"], top_n=3)

        final_answer = generate_answer_openrouter(query_text, reranked_matches)

        citations = [m["id"] for m in reranked_matches]
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
    try:
        index.delete(deleteAll=True) 
        return {"status": "success", "message": "All vectors deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def chunk_text_with_metadata(text, source, section_title, chunk_size=500, overlap=50):
    
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

def rerank_with_jina(query, matches, top_n=3):
    docs_for_jina = [m["metadata"]["text"] for m in matches] 

    headers = {"Authorization": f"Bearer {PD_HF_TOKEN}"}
    payload = {
        "query": query,
        "documents": docs_for_jina
    }

    url = f"https://api-inference.huggingface.co/models/{JINA_RERANK_MODEL}"
    response = requests.post(url, headers=headers, json=payload)

    if response.status_code != 200:
        print("Reranker Error:", response.text)
        return matches  # fallback: return original order

    scores = response.json() 

    ranked_matches = sorted(
        zip(matches, scores),
        key=lambda x: x[1],
        reverse=True
    )

    return [match for match, _ in ranked_matches[:top_n]]


openai.api_key = OPENROUTER_API_KEY
openai.api_base = "https://openrouter.ai/api/v1"

def generate_answer_openrouter(query, reranked_chunks):
    """Generate final answer using gpt-oss-20b:free on OpenRouter"""
    context_text = "\n\n".join(
        f"[Source: {c['metadata'].get('source', 'unknown')}] {c['metadata'].get('text','')}"
        for c in reranked_chunks
    )
    
    prompt = f"""
You are a helpful RAG suppported AI assistant that is meant to use the given context and answer the user query. 
Use the following context to answer the question accurately.

Context:
{context_text}

Question: {query}

Answer:
"""

    try:
        response = openai.ChatCompletion.create(
            model="openai/gpt-oss-20b:free",
            messages=[
                {"role": "system", "content": """You are a helpful RAG suppported AI assistant that is meant to use the given context and answer the user query. Make sure your answer is strictly based on the 
context that is provided to you. Mention the citation you have used for answering the question eg.[1],[2],etc . Do not produce information of your own. If you cannot answer the question based on the context provided to you please say so directly."""},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
        return response["choices"][0]["message"]["content"].strip()

    except Exception as e:
        return f"Error generating answer: {str(e)}"