// ChatContext.js
import React, { createContext, useContext, useState } from "react";

const ChatContext = createContext();

export const useChat = () => useContext(ChatContext);

export const ChatProvider = ({ children }) => {
  const [answer, setAnswer] = useState(null);       // LLM output
  const [citations, setCitations] = useState([]);   // Citation IDs
  const [sources, setSources] = useState([]);       // Source names
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const sendQuery = async (query) => {
    setLoading(true);
    setError("");
    setAnswer(null);
    setCitations([]);
    setSources([]);

    try {
      const res = await fetch("https://mini-rag-1-f05u.onrender.com/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query }),
      });

      if (!res.ok) {
        const errorText = await res.text();
        throw new Error(`Error ${res.status}: ${errorText}`);
      }

      const data = await res.json();

      if (data.answer) setAnswer(data.answer);
      if (data.citations) setCitations(data.citations);
      if (data.sources) setSources(data.sources);

      if (!data.answer) {
        setError(data.detail || "Unexpected response from server");
      }

    } catch (err) {
      setError(err.message || "Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  return (
    <ChatContext.Provider
      value={{ answer, citations, sources, loading, error, sendQuery }}
    >
      {children}
    </ChatContext.Provider>
  );
};