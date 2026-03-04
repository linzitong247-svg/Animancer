"""
Generate API Routes

Provides endpoints for animation generation:
- POST /api/generate - Start generation with image and prompt
- POST /api/generate/answer - Continue generation after clarification
"""

import json
import logging
import uuid
from pathlib import Path
from typing import Dict, Any

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel, Field

from app.config import UPLOADS_DIR
from app.agents.ma import start_generation, continue_generation, get_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["generate"])


class AnswerItem(BaseModel):
    """Single answer item for a question."""
    question_id: str = Field(..., description="Question ID")
    selected: str = Field(..., description="Selected option value")
    custom_input: str | None = Field(None, description="Custom input if 'other' was selected")


class GenerateAnswerRequest(BaseModel):
    """Request model for answering clarification questions."""
    session_id: str = Field(..., description="Session ID from initial generation")
    answers: list[AnswerItem] = Field(..., description="User's answers to questions")


class QuestionOption(BaseModel):
    """Question option model."""
    id: str = Field(..., description="Question ID")
    question: str = Field(..., description="Question text")
    options: list[str] = Field(..., description="Available options")


class GenerateResponse(BaseModel):
    """Response model for generate endpoints."""
    status: str = Field(..., description="Status: questioning, processing, completed, failed, error")
    session_id: str | None = Field(None, description="Session ID for tracking")
    questions: list[QuestionOption] | None = Field(None, description="Clarification questions if info needed")
    question_round: int | None = Field(None, description="Current question round (0-indexed)")
    max_question_rounds: int | None = Field(None, description="Maximum question rounds allowed")
    video_url: str | None = Field(None, description="URL to generated video if completed")
    video_path: str | None = Field(None, description="Local path to generated video if completed")
    qc_result: Dict[str, Any] | None = Field(None, description="Quality check result")
    generated_prompt: str | None = Field(None, description="Generated prompt for animation")
    retry_count: int | None = Field(None, description="Number of retries attempted")
    error: str | None = Field(None, description="Error message if failed")
    message: str | None = Field(None, description="Additional information")


@router.post("/generate", response_model=GenerateResponse)
async def generate_animation(
    file: UploadFile = File(..., description="Reference image for animation generation"),
    prompt: str = Form(..., description="User's animation description")
) -> GenerateResponse:
    """
    Start animation generation with an image and prompt.

    Process:
    1. Validates and saves uploaded image to data/uploads/
    2. Checks if information is sufficient
    3. If sufficient: starts generation pipeline (SA_A -> SA_G -> SA_QC)
    4. If insufficient: returns clarification questions

    Args:
        file: Uploaded image file (supports PNG, JPG, JPEG, WEBP)
        prompt: User's description of desired animation

    Returns:
        GenerateResponse with status and relevant data:
        - status="questioning": questions array provided, need user input
        - status="processing": generation in progress
        - status="completed": video_path and qc_result provided
        - status="failed": error information provided
        - status="error": unexpected error occurred

    Raises:
        HTTPException: 400 if file invalid, 500 if server error
    """
    # Validate file type
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Please upload an image file."
        )

    # Generate session ID
    session_id = str(uuid.uuid4())

    try:
        # Create unique filename for uploaded image
        filename = file.filename or "upload.png"
        file_extension = Path(filename).suffix or ".png"
        safe_filename = f"{session_id}_{filename}"
        upload_path = UPLOADS_DIR / safe_filename

        # Ensure uploads directory exists
        UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

        # Save uploaded file
        with upload_path.open("wb") as buffer:
            content = await file.read()
            buffer.write(content)

        logger.info(f"Saved uploaded image: {upload_path}")

        # Start generation process
        result = await start_generation(
            session_id=session_id,
            image_path=str(upload_path),
            prompt=prompt
        )

        # Add session_id to result
        result["session_id"] = session_id

        return GenerateResponse(**result)

    except FileNotFoundError as e:
        logger.error(f"File not found error: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected error in generate_animation: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start generation: {str(e)}"
        )


@router.post("/answer", response_model=GenerateResponse)
async def answer_clarification(request: GenerateAnswerRequest) -> GenerateResponse:
    """
    Continue animation generation after answering clarification questions.

    This endpoint is called when the user provides answers to clarification
    questions from a previous need_more_info response.

    Args:
        request: Contains session_id and user's answers (list of AnswerItem)

    Returns:
        GenerateResponse with status and relevant data:
        - status="completed": video_path and qc_result provided
        - status="failed": error information provided
        - status="error": unexpected error occurred

    Raises:
        HTTPException: 400 if session_id invalid, 500 if server error
    """
    try:
        # Validate session exists
        session = get_session(request.session_id)
        if session is None:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid session_id: {request.session_id}"
            )

        # Convert answers to JSON string for continue_generation
        answer_json = json.dumps([ans.model_dump() for ans in request.answers])

        # Continue generation with answer
        result = await continue_generation(
            session_id=request.session_id,
            answer=answer_json
        )

        # Ensure session_id is in result
        result["session_id"] = request.session_id

        return GenerateResponse(**result)

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected error in answer_clarification: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to continue generation: {str(e)}"
        )


@router.get("/status/{session_id}", response_model=Dict[str, Any])
async def get_session_status(session_id: str) -> Dict[str, Any]:
    """
    Get the current status of a generation session.

    Returns a subset of session state suitable for frontend polling.

    Args:
        session_id: Session ID to query

    Returns:
        Dict with status, generation_stage, video_url, error, retry_count

    Raises:
        HTTPException: 404 if session not found
    """
    session = get_session(session_id)
    if session is None:
        raise HTTPException(
            status_code=404,
            detail=f"Session not found: {session_id}"
        )
    return {
        "status": session.get("status", session.get("state", "generating")),
        "generation_stage": session.get("generation_stage"),
        "video_url": session.get("video_url"),
        "error": session.get("error"),
        "retry_count": session.get("retry_count", 0),
    }
