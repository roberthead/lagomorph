import { useState, useEffect } from 'react'
import Navigation from '../components/Navigation'

function ValidationsPage() {
  const [stats, setStats] = useState(null)
  const [responses, setResponses] = useState([])
  const [validations, setValidations] = useState({})
  const [isLoading, setIsLoading] = useState(true)
  const [selectedResponse, setSelectedResponse] = useState(null)

  useEffect(() => {
    fetchStats()
    fetchResponses()
  }, [])

  const fetchStats = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/validations/stats')
      if (response.ok) {
        const data = await response.json()
        setStats(data)
      }
    } catch (error) {
      console.error('Error fetching validation stats:', error)
    }
  }

  const fetchResponses = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/scraping/responses')
      if (response.ok) {
        const data = await response.json()
        setResponses(data.responses || [])
      }
    } catch (error) {
      console.error('Error fetching responses:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const validateResponse = async (responseId) => {
    try {
      const response = await fetch('http://localhost:8000/api/validations/validate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          response_id: responseId,
          validator_name: 'AddressCompletenessValidator'
        })
      })

      if (response.ok) {
        const validation = await response.json()
        setValidations(prev => ({
          ...prev,
          [responseId]: validation
        }))
        // Refresh stats
        fetchStats()
      }
    } catch (error) {
      console.error('Error validating response:', error)
    }
  }

  const fetchValidationForResponse = async (responseId) => {
    try {
      const response = await fetch(`http://localhost:8000/api/validations/response/${responseId}`)
      if (response.ok) {
        const data = await response.json()
        if (data.length > 0) {
          setValidations(prev => ({
            ...prev,
            [responseId]: data[0]  // Get most recent validation
          }))
        }
      }
    } catch (error) {
      console.error('Error fetching validation:', error)
    }
  }

  const getScoreColor = (score) => {
    if (score >= 0.9) return 'text-green-600 bg-green-50'
    if (score >= 0.7) return 'text-blue-600 bg-blue-50'
    if (score >= 0.5) return 'text-yellow-600 bg-yellow-50'
    return 'text-red-600 bg-red-50'
  }

  const getScoreLabel = (score) => {
    if (score >= 0.9) return 'Excellent'
    if (score >= 0.7) return 'Good'
    if (score >= 0.5) return 'Acceptable'
    return 'Poor'
  }

  const showValidationDetails = async (responseId) => {
    setSelectedResponse(responseId)
    await fetchValidationForResponse(responseId)
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-50">
        <div className="text-gray-500">Loading validations...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <Navigation />

      {/* Page Header */}
      <div className="border-b border-gray-200 px-6 py-4 bg-white">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-lg font-medium text-gray-900">Validation Results</h2>
          <p className="text-sm text-gray-500">Address quality scoring</p>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Stats Cards */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <div className="bg-white rounded-lg shadow p-6">
              <div className="text-sm text-gray-500">Total Validations</div>
              <div className="text-3xl font-semibold mt-2">{stats.total_validations}</div>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <div className="text-sm text-gray-500">Average Score</div>
              <div className="text-3xl font-semibold mt-2">
                {(stats.average_score * 100).toFixed(0)}%
              </div>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <div className="text-sm text-gray-500">Distribution</div>
              <div className="mt-2 space-y-1">
                <div className="flex justify-between text-sm">
                  <span className="text-green-600">Excellent:</span>
                  <span className="font-medium">{stats.distribution.excellent}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-blue-600">Good:</span>
                  <span className="font-medium">{stats.distribution.good}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-yellow-600">Acceptable:</span>
                  <span className="font-medium">{stats.distribution.acceptable}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-red-600">Poor:</span>
                  <span className="font-medium">{stats.distribution.poor}</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Responses List */}
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-medium text-gray-900">Responses</h2>
          </div>

          <div className="divide-y divide-gray-200">
            {responses.map((response) => {
              const validation = validations[response.id]

              return (
                <div key={response.id} className="px-6 py-4 hover:bg-gray-50">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="text-sm font-medium text-gray-900">
                        {response.request_body}
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        {new Date(response.created_at).toLocaleString()}
                      </div>
                    </div>

                    <div className="flex items-center gap-3">
                      {validation ? (
                        <>
                          <div className={`px-3 py-1 rounded-full text-sm font-medium ${getScoreColor(validation.score)}`}>
                            {getScoreLabel(validation.score)} ({(validation.score * 100).toFixed(0)}%)
                          </div>
                          <button
                            onClick={() => showValidationDetails(response.id)}
                            className="text-sm text-blue-600 hover:text-blue-700"
                          >
                            Details
                          </button>
                        </>
                      ) : (
                        <button
                          onClick={() => validateResponse(response.id)}
                          className="px-4 py-2 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700"
                        >
                          Validate
                        </button>
                      )}
                    </div>
                  </div>

                  {/* Validation Details */}
                  {selectedResponse === response.id && validation && (
                    <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                      <h3 className="text-sm font-medium text-gray-900 mb-3">Validation Details</h3>

                      <div className="space-y-2 mb-4">
                        {Object.entries(validation.criteria_scores).map(([criterion, score]) => (
                          <div key={criterion} className="flex items-center justify-between">
                            <span className="text-sm text-gray-700 capitalize">
                              {criterion.replace(/_/g, ' ')}
                            </span>
                            <div className="flex items-center gap-2">
                              <div className="w-32 h-2 bg-gray-200 rounded-full">
                                <div
                                  className="h-2 bg-blue-600 rounded-full"
                                  style={{ width: `${score * 100}%` }}
                                />
                              </div>
                              <span className="text-sm font-medium text-gray-900 w-12 text-right">
                                {(score * 100).toFixed(0)}%
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>

                      <div className="text-sm text-gray-700 bg-white p-3 rounded border border-gray-200">
                        <strong>Feedback:</strong> {validation.feedback}
                      </div>

                      <div className="mt-2 text-xs text-gray-500">
                        Validated: {new Date(validation.validated_at).toLocaleString()} •
                        Version: {validation.validator_version}
                      </div>
                    </div>
                  )}
                </div>
              )
            })}

            {responses.length === 0 && (
              <div className="px-6 py-8 text-center text-gray-500">
                No responses to validate yet. Try chatting and scraping some websites first!
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default ValidationsPage
