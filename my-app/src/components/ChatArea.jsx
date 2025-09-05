import React from 'react'
import { useState } from 'react';
import { useChat } from "../providers/ChatContext";

const ChatArea = () => {
    const [query, setQuery] = useState("");
    const { sendQuery } = useChat();

    const handleSubmit = (e) => {
      e.preventDefault();
      sendQuery(query);
    };
  return (
    <div className='w-[90%] flex flex-col justify-center items-center bg-black text-white '>
        <div className='flex w-full h-full justify-around items-center'>
            <textarea value={query} className='w-[85%] h-[90%] p-2 overflow-y-scroll rounded-lg text-black' name="query" id="" placeholder='Enter your question here..' onChange={e => setQuery(e.target.value)}></textarea>
            <button className='flex w-[10%] h-[70%] bg-white text-black justify-center items-center rounded-lg' onClick={(e) => handleSubmit(e)}>
              Submit
            </button>
        </div>
        <div>
            
        </div>
    </div>
  )
}

export default ChatArea
