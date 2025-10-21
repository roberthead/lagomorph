import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'

function ResponsesPage() {
  const [responses, setResponses] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchResponses()
  }, [])

  const fetchResponses = async () => {
    try {
      setLoading(true)
      const response = await fetch('http://localhost:8000/api/scraping/responses')
      if (!response.ok) {
        throw new Error('Failed to fetch responses')
      }
      const data = await response.json()
      setResponses(data.responses)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const formatDate = (isoString) => {
    const date = new Date(isoString)
    return date.toLocaleString()
  }

  const parseResponseBody = (responseBody) => {
    try {
      const parsed = JSON.parse(responseBody)
      return parsed
    } catch {
      return responseBody
    }
  }

  const getResponseSummary = (responseBody) => {
    const events = parseResponseBody(responseBody)
    if (Array.isArray(events)) {
      const lastEvent = events[events.length - 1]
      if (lastEvent?.type === 'complete') {
        return `Found ${lastEvent.data?.companies?.length || 0} companies`
      }
      return `${events.length} events`
    }
    return 'Response data'
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading responses...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="text-center">
          <p className="text-red-600 mb-4">Error: {error}</p>
          <button
            onClick={fetchResponses}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-6xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link
                to="/"
                className="text-blue-600 hover:text-blue-700 flex items-center gap-1"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
                Back to Chat
              </Link>
              <div>
                <h1 className="text-xl font-medium text-gray-900">Response History</h1>
                <p className="text-sm text-gray-500">{responses.length} saved interactions</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-6xl mx-auto px-6 py-8">
        {responses.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-500 mb-4">No responses saved yet</p>
            <Link
              to="/"
              className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Start Chatting
            </Link>
          </div>
        ) : (
          <div className="space-y-4">
            {responses.map((response) => (
              <div
                key={response.id}
                className="bg-white border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow"
              >
                <div className="flex justify-between items-start mb-4">
                  <div className="flex-1">
                    <h3 className="text-sm font-medium text-gray-900 mb-1">
                      Request
                    </h3>
                    <p className="text-[15px] text-gray-700">
                      {response.request_body}
                    </p>
                  </div>
                  <div className="text-xs text-gray-500 ml-4 whitespace-nowrap">
                    {formatDate(response.created_at)}
                  </div>
                </div>

                <div>
                  <h3 className="text-sm font-medium text-gray-900 mb-1">
                    Response
                  </h3>
                  <p className="text-sm text-gray-600">
                    {getResponseSummary(response.response_body)}
                  </p>
                </div>

                <details className="mt-4">
                  <summary className="text-sm text-blue-600 hover:text-blue-700 cursor-pointer">
                    View full response
                  </summary>
                  <div className="mt-2 p-4 bg-gray-50 rounded border border-gray-200 overflow-x-auto">
                    <pre className="text-xs text-gray-700 whitespace-pre-wrap">
                      {JSON.stringify(parseResponseBody(response.response_body), null, 2)}
                    </pre>
                  </div>
                </details>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default ResponsesPage
