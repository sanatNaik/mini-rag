import React from 'react'
import { useChat } from "../providers/ChatContext";

const Citation = () => {
  const {answer, citations, sources, loading, error, sendQuery } = useChat();
  return (
    <div className='flex flex-col items-center bg-white rounded-lg box-border w-[90%] h-[80%] p-2 overflow-y-scroll'>
        <div className='font-semibold'>Citations</div><br/>
       {citations}
    </div>
  )
}

export default Citation
