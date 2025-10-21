import { useState } from 'react'
import ExportButton from './ExportButton'

function CompanyTable({ companies }) {
  const [sortConfig, setSortConfig] = useState({ key: null, direction: 'asc' })

  const sortedCompanies = [...companies].sort((a, b) => {
    if (!sortConfig.key) return 0

    const aValue = a[sortConfig.key] || ''
    const bValue = b[sortConfig.key] || ''

    if (aValue < bValue) {
      return sortConfig.direction === 'asc' ? -1 : 1
    }
    if (aValue > bValue) {
      return sortConfig.direction === 'asc' ? 1 : -1
    }
    return 0
  })

  const handleSort = (key) => {
    let direction = 'asc'
    if (sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc'
    }
    setSortConfig({ key, direction })
  }

  const SortIcon = ({ columnKey }) => {
    if (sortConfig.key !== columnKey) {
      return <span className="text-gray-300">⇅</span>
    }
    return <span className="text-blue-600">{sortConfig.direction === 'asc' ? '↑' : '↓'}</span>
  }

  if (!companies || companies.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500 text-sm">
        No companies found
      </div>
    )
  }

  return (
    <div className="space-y-3">
      <div className="flex justify-between items-center">
        <div className="text-sm text-gray-600">
          <span className="font-medium text-gray-900">{companies.length}</span> {companies.length === 1 ? 'company' : 'companies'} found
        </div>
        <ExportButton companies={companies} />
      </div>

      <div className="overflow-hidden rounded-lg border border-gray-200">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th
                  className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort('company_name')}
                >
                  <div className="flex items-center gap-2">
                    Company Name
                    <SortIcon columnKey="company_name" />
                  </div>
                </th>
                <th
                  className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort('address')}
                >
                  <div className="flex items-center gap-2">
                    Address
                    <SortIcon columnKey="address" />
                  </div>
                </th>
                <th
                  className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort('source_url')}
                >
                  <div className="flex items-center gap-2">
                    Source
                    <SortIcon columnKey="source_url" />
                  </div>
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {sortedCompanies.map((company, idx) => (
                <tr key={idx} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-sm font-medium text-gray-900">
                    {company.company_name}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600">
                    {company.address}
                  </td>
                  <td className="px-4 py-3 text-sm">
                    <a
                      href={company.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:text-blue-700 hover:underline inline-flex items-center gap-1"
                    >
                      {new URL(company.source_url).pathname || '/'}
                      <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                      </svg>
                    </a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

export default CompanyTable
