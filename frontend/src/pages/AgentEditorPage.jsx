import { useState, useEffect, useRef } from 'react'
import { useParams } from 'react-router-dom'
import MessageList from '../components/MessageList'
import ChatInput from '../components/ChatInput'
import Navigation from '../components/Navigation'

function AgentEditorPage() {
  const { name } = useParams()
  const [prompt, setPrompt] = useState(null)
  const [systemPrompt, setSystemPrompt] = useState('')
  const [description, setDescription] = useState('')
  const [isActive, setIsActive] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [saveMessage, setSaveMessage] = useState('')
  const [isLoading, setIsLoading] = useState(true)

  // Chat state
  const [messages, setMessages] = useState([
    {
      id: '1',
      sender: 'agent',
      text: 'Test the agent with this chat interface. Your edits will affect responses in real-time.',
      timestamp: new Date().toISOString(),
      type: 'message'
    }
  ])
  const [isChatLoading, setIsChatLoading] = useState(false)

  // Load agent prompt on mount
  useEffect(() => {
    fetchPrompt()
  }, [name])

  const fetchPrompt = async () => {
    try {
      setIsLoading(true)
      const response = await fetch(`http://localhost:8000/api/agents/prompts/${name}`)

      if (!response.ok) {
        throw new Error('Failed to fetch agent prompt')
      }

      const data = await response.json()
      setPrompt(data)
      setSystemPrompt(data.system_prompt)
      setDescription(data.description || '')
      setIsActive(data.is_active)
    } catch (error) {
      console.error('Error fetching prompt:', error)
      setSaveMessage('Error loading agent prompt')
    } finally {
      setIsLoading(false)
    }
  }

  const handleSave = async () => {
    try {
      setIsSaving(true)
      setSaveMessage('')

      const response = await fetch(`http://localhost:8000/api/agents/prompts/${name}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          system_prompt: systemPrompt,
          description: description,
          is_active: isActive
        })
      })

      if (!response.ok) {
        throw new Error('Failed to update prompt')
      }

      const data = await response.json()
      setPrompt(data)
      setSaveMessage('✓ Saved successfully!')

      // Clear message after 3 seconds
      setTimeout(() => setSaveMessage(''), 3000)
    } catch (error) {
      console.error('Error saving prompt:', error)
      setSaveMessage('✗ Error saving changes')
    } finally {
      setIsSaving(false)
    }
  }

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
    setIsChatLoading(true)

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
      // Prepare conversation history
      const conversationHistory = messages.slice(-10).map(msg => ({
        sender: msg.sender,
        text: msg.text,
        timestamp: msg.timestamp
      }))

      // Stream chat response
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
        buffer = lines.pop()

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = JSON.parse(line.substring(6))

            setMessages(prev => {
              const newMessages = [...prev]
              const agentMsgIndex = newMessages.findIndex(m => m.id === agentMessageId)

              if (agentMsgIndex !== -1) {
                if (data.type === 'message' || data.type === 'progress') {
                  newMessages[agentMsgIndex] = {
                    ...newMessages[agentMsgIndex],
                    text: data.message,
                    type: data.type
                  }
                } else if (data.type === 'complete') {
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
      setIsChatLoading(false)
    }
  }

  const formatAgentName = (name) => {
    return name
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ')
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-50">
        <div className="text-gray-500">Loading agent...</div>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Navigation */}
      <Navigation />

      {/* Page Header */}
      <div className="border-b border-gray-200 px-6 py-3 bg-white">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div>
            <h2 className="text-lg font-medium text-gray-900">
              {formatAgentName(name)}
            </h2>
            <p className="text-sm text-gray-500">Agent Editor</p>
          </div>
          {saveMessage && (
            <div className={`text-sm ${saveMessage.includes('✓') ? 'text-green-600' : 'text-red-600'}`}>
              {saveMessage}
            </div>
          )}
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Panel - Editor Form */}
        <div className="w-1/2 border-r border-gray-200 bg-white overflow-y-auto">
          <div className="p-6 max-w-2xl">
            <div className="space-y-6">
              {/* Description */}
              <div>
                <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-2">
                  Description
                </label>
                <input
                  type="text"
                  id="description"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Brief description of what this agent does"
                />
              </div>

              {/* System Prompt */}
              <div>
                <label htmlFor="systemPrompt" className="block text-sm font-medium text-gray-700 mb-2">
                  System Prompt
                </label>
                <textarea
                  id="systemPrompt"
                  value={systemPrompt}
                  onChange={(e) => setSystemPrompt(e.target.value)}
                  rows={20}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md font-mono text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Enter the system prompt for this agent..."
                />
                <div className="mt-1 text-xs text-gray-500">
                  {systemPrompt.length} characters
                </div>
              </div>

              {/* Active Toggle */}
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="isActive"
                  checked={isActive}
                  onChange={(e) => setIsActive(e.target.checked)}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <label htmlFor="isActive" className="ml-2 text-sm text-gray-700">
                  Active
                </label>
              </div>

              {/* Save Button */}
              <div>
                <button
                  onClick={handleSave}
                  disabled={isSaving}
                  className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
                >
                  {isSaving ? 'Saving...' : 'Save Changes'}
                </button>
              </div>

              {/* Metadata */}
              {prompt && (
                <div className="pt-4 border-t border-gray-200 text-xs text-gray-500 space-y-1">
                  <div>Created: {new Date(prompt.created_at).toLocaleString()}</div>
                  <div>Updated: {new Date(prompt.updated_at).toLocaleString()}</div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Right Panel - Chat Testing */}
        <div className="w-1/2 flex flex-col bg-white">
          {/* Chat Header */}
          <div className="border-b border-gray-200 px-6 py-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-medium text-gray-900">Test Chat</h2>
                <p className="text-sm text-gray-500">Test your agent changes in real-time</p>
              </div>
              {saveMessage && saveMessage.includes('✓') && (
                <div className="text-xs text-green-600 bg-green-50 px-3 py-1 rounded-full">
                  Using latest prompt
                </div>
              )}
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-hidden bg-gray-50">
            <MessageList messages={messages} />
          </div>

          {/* Input */}
          <div className="border-t border-gray-200 bg-white">
            <ChatInput onSendMessage={handleSendMessage} isLoading={isChatLoading} />
          </div>
        </div>
      </div>
    </div>
  )
}

export default AgentEditorPage
