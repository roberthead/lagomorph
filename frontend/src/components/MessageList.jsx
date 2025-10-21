import { useEffect, useRef } from 'react'
import MessageBubble from './MessageBubble'

function MessageList({ messages }) {
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  return (
    <div className="h-full overflow-y-auto px-4 py-6">
      <div className="max-w-4xl mx-auto space-y-4">
        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}
        <div ref={messagesEndRef} />
      </div>
    </div>
  )
}

export default MessageList
