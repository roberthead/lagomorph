from fastapi import APIRouter
from app.api import scraping, agents

router = APIRouter()


@router.get("/welcome")
async def welcome():
    return {"message": "Welcome to Lagomorph"}


# Include scraping routes
router.include_router(scraping.router, prefix="/scraping", tags=["scraping"])

# Include agent management routes
router.include_router(agents.router, prefix="/agents", tags=["agents"])
