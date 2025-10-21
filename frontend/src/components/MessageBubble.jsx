import CompanyTable from './CompanyTable'

function MessageBubble({ message }) {
  const isUser = message.sender === 'user'
  const isError = message.type === 'error'
  const isProgress = message.type === 'progress'
  const hasResults = message.type === 'complete' && message.data?.companies

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-6`}>
      <div className={`max-w-2xl ${isUser ? 'w-auto' : 'w-full'}`}>
        {/* Message bubble */}
        <div
          className={`rounded-lg px-4 py-3 ${
            isUser
              ? 'bg-blue-600 text-white'
              : isError
              ? 'bg-red-50 text-red-900 border border-red-200'
              : 'bg-white text-gray-900 border border-gray-200'
          }`}
        >
          {/* Message text */}
          <div className="whitespace-pre-wrap text-[15px] leading-relaxed">
            {isProgress && !hasResults && (
              <span className="inline-flex items-center gap-2">
                <svg className="animate-spin h-4 w-4 text-gray-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <span className="text-gray-700">{message.text}</span>
              </span>
            )}
            {!isProgress && message.text}
          </div>

          {/* Results table */}
          {hasResults && (
            <div className="mt-4">
              <CompanyTable companies={message.data.companies} />
            </div>
          )}
        </div>

        {/* Timestamp */}
        {!isUser && (
          <div className="text-xs text-gray-400 mt-1.5 ml-3">
            {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </div>
        )}
      </div>
    </div>
  )
}

export default MessageBubble
