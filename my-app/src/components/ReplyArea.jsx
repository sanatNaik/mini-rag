import React from 'react'
import { useChat } from "../providers/ChatContext";

const ReplyArea = () => {
    const {answer, citations, sources, loading, error, sendQuery } = useChat();
    return (
        <div className='flex flex-col items-center w-[90%] h-[90%] p-4 bg-white text-black rounded-lg overflow-y-scroll'>
            <div className='font-semibold text-2xl'>Response</div>
            {answer}
        </div>
    )
}

export default ReplyArea
