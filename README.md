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

### Frontend

- **Run dev server**: `npm run dev`
- **Build for production**: `npm run build`
- **Preview production build**: `npm run preview`

## API Endpoints

- `GET /` - Root endpoint
- `GET /api/welcome` - Welcome message
- `GET /docs` - Interactive API documentation (Swagger UI)
- `GET /redoc` - Alternative API documentation (ReDoc)

## Environment Variables

### Backend (.env)

- `DATABASE_URL` - PostgreSQL connection string
- `SECRET_KEY` - Secret key for signing tokens
- `ENVIRONMENT` - Application environment (development/production)

## License

MIT
