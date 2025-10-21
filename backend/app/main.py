from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import routes

app = FastAPI(title="Lagomorph API", version="0.1.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes.router, prefix="/api")


@app.get("/")
async def root():
    return {"message": "Welcome to Lagomorph API"}
