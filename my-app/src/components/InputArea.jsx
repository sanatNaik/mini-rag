import React from 'react'
import { useState } from 'react'

const InputArea = () => {
  const [text, setText] = useState('');
  const [status, setStatus] = useState('');
  const [loading, setLoading] = useState(false);

  const handleReset = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch("https://mini-rag-1-f05u.onrender.com/delete_all/", {
        method: 'DELETE', // correct method
      });

      if (!res.ok) throw new Error(`Error: ${res.status}`);

      const data = await res.json();
      setStatus(data.message); // "All vectors deleted successfully"
      setText(''); // clear input
    } catch (err) {
      setStatus(`Failed to delete vectors: ${err.message}`);
    }
  };
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!text.trim()) return;

    setLoading(true);
    setStatus('');

    try {
      const res = await fetch("https://mini-rag-1-f05u.onrender.com/embed-upload'", {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: text,
          source: 'user',          
          section_title: 'Input',  // optional metadata
          position: 1              // optional metadata
        })
      });

      if (!res.ok) throw new Error(`Error: ${res.status}`);

      const data = await res.json();
      setStatus(`Text uploaded successfully! Vector ID: ${data.id}`);
      setText(''); // optional: clear input
    } catch (err) {
      setStatus(`Failed to upload: ${err.message}`);
    }

    setLoading(false);
  };

  
  return (
    <div className='flex flex-col items-center justify-between w-full h-full p-6 border-gray-400 border-b-4'>
        <textarea type="text" value={text} className='flex p-5 w-full h-[80%] rounded-md overflow-scroll' placeholder='Enter your text here..' onChange={e => setText(e.target.value)}/>
        <div className='flex items-center justify-around w-full h-[15%]'>
            <button className='w-[30%] h-full rounded-lg bg-white text-black font-semibold' onClick={e => handleSubmit(e)}>
                Submit
            </button>
            <button className='w-[30%] h-full rounded-lg bg-white text-black font-semibold' onClick={e => handleReset(e)}>
                Reset
            </button>
        </div>
        
    </div>
  )
}

export default InputArea
