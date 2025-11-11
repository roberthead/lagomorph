# Lagomorph

A modern full-stack web application built with FastAPI, React, PostgreSQL, and TailwindCSS.

## Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - SQL toolkit and ORM
- **Alembic** - Database migration tool
- **Pydantic** - Data validation using Python type annotations
- **PostgreSQL** - Relational database

### Frontend
- **React** - UI library
- **Vite** - Build tool and dev server
- **TailwindCSS** - Utility-first CSS framework
- **TanStack Query** - Data fetching and caching
- **TanStack Router** - Type-safe routing

## Project Structure

```
lagomorph/
├── backend/
│   ├── alembic/              # Database migrations
│   ├── app/
│   │   ├── api/              # API routes
│   │   ├── core/             # Core configuration
│   │   ├── db/               # Database setup
│   │   ├── models/           # SQLAlchemy models
│   │   ├── schemas/          # Pydantic schemas
│   │   └── main.py           # FastAPI application
│   ├── .env.example          # Environment variables template
│   ├── alembic.ini           # Alembic configuration
│   └── requirements.txt      # Python dependencies
└── frontend/
    ├── src/
    │   ├── App.jsx           # Main React component
    │   └── main.jsx          # Application entry point
    ├── package.json          # Node dependencies
    └── vite.config.js        # Vite configuration
```

## Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 14+

## Setup Instructions

### Database Setup

1. Install PostgreSQL if you haven't already
2. Create a database:
   ```bash
   createdb lagomorph
   ```

3. Create a database user (optional):
   ```bash
   psql lagomorph
   CREATE USER lagomorph WITH PASSWORD 'lagomorph';
   GRANT ALL PRIVILEGES ON DATABASE lagomorph TO lagomorph;
   ```

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file based on `.env.example`:
   ```bash
   cp .env.example .env
   ```

5. Update the `.env` file with your database credentials:
   ```
   DATABASE_URL=postgresql://lagomorph:lagomorph@localhost:5432/lagomorph
   SECRET_KEY=your-secret-key-here
   ENVIRONMENT=development
   ```

6. Run database migrations:
   ```bash
   alembic upgrade head
   ```

7. Start the backend server:
   ```bash
   uvicorn app.main:app --reload
   ```

   The API will be available at `http://localhost:8000`
   API documentation at `http://localhost:8000/docs`

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

   The application will be available at `http://localhost:5173`

## Development

### Backend

- **Run server**: `uvicorn app.main:app --reload`
- **Create migration**: `alembic revision --autogenerate -m "description"`
- **Apply migrations**: `alembic upgrade head`
- **Rollback migration**: `alembic downgrade -1`
- **Run tests**: `pytest` (see Testing section below)
- **Run tests with coverage**: `pytest --cov=app --cov-report=html`

### Frontend

- **Run dev server**: `npm run dev`
- **Build for production**: `npm run build`
- **Preview production build**: `npm run preview`

## API Endpoints

- `GET /` - Root endpoint
- `GET /api/welcome` - Welcome message
- `GET /docs` - Interactive API documentation (Swagger UI)
- `GET /redoc` - Alternative API documentation (ReDoc)

## Testing

### Backend Testing

The backend has comprehensive test coverage (87%+) using pytest. Tests are organized into:

- **Unit tests** (`tests/unit/`) - Test individual components in isolation
  - `test_models.py` - Database model tests
  - `test_validators.py` - Validation framework tests
  - `test_agents.py` - Agent orchestration tests (ChatAgent, ScrapingAgent)

- **Integration tests** (`tests/integration/`) - Test API endpoints and component interactions
  - `test_api.py` - API endpoint tests

#### Running Tests

1. Make sure you're in the backend directory with the virtual environment activated:
   ```bash
   cd backend
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Run all tests:
   ```bash
   pytest
   ```

3. Run tests with coverage report:
   ```bash
   pytest --cov=app --cov-report=html
   ```

   This generates an HTML coverage report in `htmlcov/index.html`

4. Run tests with verbose output:
   ```bash
   pytest -v
   ```

5. Run specific test file:
   ```bash
   pytest tests/unit/test_models.py
   ```

6. Run specific test:
   ```bash
   pytest tests/unit/test_models.py::TestResponseModel::test_create_response
   ```

#### Test Coverage

Current test coverage: **87%**

Coverage breakdown by component:
- **Models**: 100% - Database models and relationships
- **Validators**: 91-93% - Validation framework (BaseValidator, AddressCompletenessValidator)
- **Agents**: 97-99% - Agent orchestration (ChatAgent, ScrapingAgent)
- **API Endpoints**: 57-74% - REST API endpoints
- **Services**: 85%+ - Web scraping and other services

#### Test Configuration

Tests are configured in `pytest.ini`:
- Automatic test discovery
- Coverage measurement with 80% minimum threshold
- HTML, terminal, and XML coverage reports
- Exclusions for migrations, venv, and test files

## Environment Variables

### Backend (.env)

- `DATABASE_URL` - PostgreSQL connection string
- `SECRET_KEY` - Secret key for signing tokens
- `ENVIRONMENT` - Application environment (development/production)
- `ANTHROPIC_API_KEY` - API key for Claude AI integration

## License

MIT
