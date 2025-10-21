import { Link, useLocation } from 'react-router-dom'

function Navigation() {
  const location = useLocation()

  const isActive = (path) => {
    if (path === '/') {
      return location.pathname === '/'
    }
    return location.pathname.startsWith(path)
  }

  const linkClass = (path) => {
    const baseClass = "text-sm px-3 py-2 rounded-md transition-colors"
    return isActive(path)
      ? `${baseClass} bg-blue-100 text-blue-700 font-medium`
      : `${baseClass} text-gray-600 hover:text-gray-900 hover:bg-gray-100`
  }

  return (
    <div className="border-b border-gray-200 px-6 py-3 bg-white">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        {/* Logo/Brand */}
        <Link to="/" className="flex items-center gap-3">
          <div className="text-2xl">🐰</div>
          <div>
            <h1 className="text-xl font-medium text-gray-900">Lagomorph</h1>
            <p className="text-xs text-gray-500">Web Scraping Assistant</p>
          </div>
        </Link>

        {/* Navigation Links */}
        <nav className="flex items-center gap-2">
          <Link to="/" className={linkClass('/')}>
            Chat
          </Link>
          <Link to="/validations" className={linkClass('/validations')}>
            Validations
          </Link>
          <Link to="/responses" className={linkClass('/responses')}>
            History
          </Link>
          <Link to="/agent/chat_agent" className={linkClass('/agent')}>
            Agent Editor
          </Link>
        </nav>
      </div>
    </div>
  )
}

export default Navigation
