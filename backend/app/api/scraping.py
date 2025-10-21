"""API endpoints for web scraping functionality."""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.orm import Session
import logging
import json

from app.schemas.scraping import ScrapeRequest, ScrapeResponse
from app.schemas.chat import ChatRequest
from app.services.scraping_agent import create_agent
from app.services.chat_agent import create_chat_agent
from app.db.base import get_db
from app.models.response import Response

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/scrape", response_model=ScrapeResponse)
async def scrape_website(request: ScrapeRequest) -> ScrapeResponse:
    """
    Scrape a website and extract company information using Claude AI.

    Args:
        request: Scraping request containing URL and parameters

    Returns:
        ScrapeResponse with extracted company information

    Raises:
        HTTPException: If scraping fails
    """
    try:
        logger.info(f"Starting scrape request for URL: {request.url}")

        # Create agent
        agent = create_agent()

        # Perform scraping
        result = agent.scrape_and_extract(
            start_url=request.url,
            max_depth=request.max_depth,
            max_pages=request.max_pages
        )

        logger.info(f"Scraping completed. Found {result['companies_found']} companies")

        return ScrapeResponse(**result)

    except ValueError as e:
        logger.error(f"Configuration error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Configuration error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error during scraping: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Scraping failed: {str(e)}"
        )


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest, db: Session = Depends(get_db)):
    """
    Chat interface with streaming responses using Server-Sent Events.

    Args:
        request: Chat request with message and conversation history
        db: Database session

    Returns:
        StreamingResponse with SSE events
    """
    async def event_generator():
        response_events = []
        try:
            # Create chat agent
            agent = create_chat_agent()

            # Parse user intent
            intent = agent.parse_intent(
                request.message,
                [msg.dict() for msg in request.conversation_history]
            )

            # Send initial response
            initial_event = {'type': 'message', 'message': intent['response']}
            response_events.append(initial_event)
            yield f"data: {json.dumps(initial_event)}\n\n"

            # If action is scrape, stream the scraping process
            if intent.get('action') == 'scrape':
                url = intent.get('url')
                max_depth = intent.get('max_depth', 2)
                max_pages = intent.get('max_pages', 20)

                # Stream scraping progress
                async for event in agent.stream_scraping(url, max_depth, max_pages):
                    response_events.append(event)
                    yield f"data: {json.dumps(event)}\n\n"

            # Save interaction to database
            try:
                db_response = Response(
                    request_body=request.message,
                    response_body=json.dumps(response_events)
                )
                db.add(db_response)
                db.commit()
                logger.info(f"Saved interaction to database with ID: {db_response.id}")
            except Exception as db_error:
                logger.error(f"Failed to save interaction to database: {str(db_error)}")
                db.rollback()

        except Exception as e:
            logger.error(f"Error in chat stream: {str(e)}")
            error_event = {'type': 'error', 'message': f'Error: {str(e)}'}
            response_events.append(error_event)
            yield f"data: {json.dumps(error_event)}\n\n"

            # Try to save error interaction
            try:
                db_response = Response(
                    request_body=request.message,
                    response_body=json.dumps(response_events)
                )
                db.add(db_response)
                db.commit()
            except Exception as db_error:
                logger.error(f"Failed to save error interaction to database: {str(db_error)}")
                db.rollback()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@router.get("/responses")
async def get_responses(db: Session = Depends(get_db)):
    """
    Get all saved response records from the database.

    Returns:
        List of response records with id, request_body, response_body, and created_at
    """
    try:
        responses = db.query(Response).order_by(Response.created_at.desc()).all()
        return {
            "responses": [
                {
                    "id": r.id,
                    "request_body": r.request_body,
                    "response_body": r.response_body,
                    "created_at": r.created_at.isoformat()
                }
                for r in responses
            ]
        }
    except Exception as e:
        logger.error(f"Error fetching responses: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch responses: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """Health check endpoint for the scraping service."""
    return {"status": "healthy", "service": "web-scraping"}
