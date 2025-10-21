import { BrowserRouter, Routes, Route } from 'react-router-dom'
import ChatPage from './pages/ChatPage'
import ResponsesPage from './pages/ResponsesPage'
import AgentEditorPage from './pages/AgentEditorPage'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<ChatPage />} />
        <Route path="/responses" element={<ResponsesPage />} />
        <Route path="/agent/:name" element={<AgentEditorPage />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
