import Navbar from "./components/navbar"
import InputArea from "./components/InputArea"
import ChatArea from "./components/ChatArea"
import Citation from "./components/Citation"
import ReplyArea from "./components/ReplyArea"
import { ChatProvider } from "./providers/ChatContext"

function App() {
  return (
    <>
      <ChatProvider>  
      <div className="w-screen h-[90vh] p-1">
        <div> 
            <Navbar/>
        </div>
        <div className="flex w-full h-full">
          <div className="flex flex-col w-[40%] h-full bg-gray-500 border-gray-400 border-4">
              <div className="flex bg-black h-[60%]">
                  <InputArea/>
              </div>
              <div className="flex bg-black h-[40%] box-border justify-center items-center">
                  <Citation/>
              </div>
          </div>
          <div className="flex flex-col w-[60%] bg-black text-white border-gray-400 border-4">
              <div className="flex w-full h-[15%] justify-center py-3">
                  <ChatArea/>
              </div>
              <div className="flex w-full h-[80%] justify-center items-center">
                  <ReplyArea/>
              </div>
          </div>
        </div>
      </div>
      </ChatProvider>
    </>
  )
}

export default App
