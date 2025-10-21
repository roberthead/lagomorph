import { useState, useRef, useEffect } from 'react'
import MessageList from '../components/MessageList'
import ChatInput from '../components/ChatInput'
import Navigation from '../components/Navigation'

function ChatPage() {
  const [messages, setMessages] = useState([
    {
      id: '1',
      sender: 'agent',
      text: 'Hello! I can help you scrape websites to find company names and addresses. Just tell me which website to scrape!',
      timestamp: new Date().toISOString(),
      type: 'message'
    }
  ])
  const [isLoading, setIsLoading] = useState(false)
  const eventSourceRef = useRef(null)

  const handleSendMessage = async (messageText) => {
    // Add user message
    const userMessage = {
      id: Date.now().toString(),
      sender: 'user',
      text: messageText,
      timestamp: new Date().toISOString(),
      type: 'message'
    }

    setMessages(prev => [...prev, userMessage])
    setIsLoading(true)

    // Create placeholder for agent response
    const agentMessageId = (Date.now() + 1).toString()
    const agentMessage = {
      id: agentMessageId,
      sender: 'agent',
      text: '',
      timestamp: new Date().toISOString(),
      type: 'progress',
      data: null
    }

    setMessages(prev => [...prev, agentMessage])

    try {
      // Close any existing connection
      if (eventSourceRef.current) {
        eventSourceRef.current.close()
      }

      // Prepare conversation history (last 10 messages for context)
      const conversationHistory = messages.slice(-10).map(msg => ({
        sender: msg.sender,
        text: msg.text,
        timestamp: msg.timestamp
      }))

      // Make POST request to start SSE stream
      const response = await fetch('http://localhost:8000/api/scraping/chat/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: messageText,
          conversation_history: conversationHistory
        })
      })

      const reader = response.body.getReader()
      const decoder = new TextDecoder()

      let buffer = ''

      while (true) {
        const { value, done } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() // Keep incomplete line in buffer

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = JSON.parse(line.substring(6))

            setMessages(prev => {
              const newMessages = [...prev]
              const agentMsgIndex = newMessages.findIndex(m => m.id === agentMessageId)

              if (agentMsgIndex !== -1) {
                if (data.type === 'message' || data.type === 'progress') {
                  // Update the text of the agent message
                  newMessages[agentMsgIndex] = {
                    ...newMessages[agentMsgIndex],
                    text: data.message,
                    type: data.type
                  }
                } else if (data.type === 'complete') {
                  // Final result with data
                  newMessages[agentMsgIndex] = {
                    ...newMessages[agentMsgIndex],
                    text: data.message,
                    type: 'complete',
                    data: data.data
                  }
                } else if (data.type === 'error') {
                  newMessages[agentMsgIndex] = {
                    ...newMessages[agentMsgIndex],
                    text: data.message,
                    type: 'error'
                  }
                }
              }

              return newMessages
            })
          }
        }
      }
    } catch (error) {
      console.error('Error:', error)
      setMessages(prev => {
        const newMessages = [...prev]
        const agentMsgIndex = newMessages.findIndex(m => m.id === agentMessageId)
        if (agentMsgIndex !== -1) {
          newMessages[agentMsgIndex] = {
            ...newMessages[agentMsgIndex],
            text: `Error: ${error.message}`,
            type: 'error'
          }
        }
        return newMessages
      })
    } finally {
      setIsLoading(false)
    }
  }

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close()
      }
    }
  }, [])

  return (
    <div className="flex flex-col h-screen bg-white">
      {/* Navigation */}
      <Navigation />

      {/* Messages */}
      <div className="flex-1 overflow-hidden bg-gray-50">
        <MessageList messages={messages} />
      </div>

      {/* Input */}
      <div className="border-t border-gray-200 bg-white">
        <ChatInput onSendMessage={handleSendMessage} isLoading={isLoading} />
      </div>
    </div>
  )
}

export default ChatPage
