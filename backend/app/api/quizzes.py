"""
Quiz API endpoints for the O'Reilly RAG Quiz system.

This module provides endpoints for:
- Quiz generation
- Quiz retrieval
- Quiz submission
- User progress tracking
- Quiz customization
- Quiz sharing and export
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Query, Path
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from ..models.quiz_models import Quiz, QuizSession, UserResponse, UserProgress
from ..services.quiz_generator import (
    QuizGenerationService, 
    QuizGenerationRequest, 
    QuizQuestion, 
    DifficultyLevel, 
    QuestionType
)
from ..services.quiz_manager import (
    QuizManagerService,
    QuizCreateRequest,
    QuizSessionCreateRequest,
    QuizAnswerRequest,
    QuizStatus
)
from ..utils.database import get_db
from config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


# Response Models
class QuizResponse(BaseModel):
    """Response model for quiz data."""
    id: str
    title: str
    description: Optional[str]
    topic: str
    difficulty_level: str
    question_types: List[str]
    total_questions: int
    time_limit: Optional[int]
    passing_score: float
    is_public: bool
    created_by: Optional[str]
    created_at: datetime
    updated_at: datetime
    settings: Dict[str, Any]

    class Config:
        from_attributes = True


class QuizSessionResponse(BaseModel):
    """Response model for quiz session data."""
    id: str
    quiz_id: str
    user_id: Optional[str]
    session_token: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime]
    time_spent: Optional[int]
    total_questions: int
    answered_questions: int
    correct_answers: int
    score: float
    passed: bool
    current_question: int

    class Config:
        from_attributes = True


class QuizQuestionResponse(BaseModel):
    """Response model for quiz question data."""
    id: str
    question_type: str
    question_text: str
    options: Optional[List[str]]
    difficulty: str
    topic: str
    metadata: Dict[str, Any]


class QuizSubmissionResponse(BaseModel):
    """Response model for quiz submission results."""
    session_id: str
    question_id: str
    is_correct: bool
    correct_answer: Any
    explanation: str
    time_taken: Optional[int]
    session_status: str
    current_question: int
    total_questions: int
    score: float


class UserProgressResponse(BaseModel):
    """Response model for user progress data."""
    id: str
    user_id: str
    topic: str
    total_quizzes_taken: int
    total_questions_answered: int
    correct_answers: int
    average_score: float
    mastery_level: str
    mastery_score: float
    knowledge_gaps: List[str]
    strengths: List[str]
    suggested_difficulty: str
    next_review_date: Optional[datetime]
    last_updated: datetime

    class Config:
        from_attributes = True


# Dependency injection
def get_quiz_generator(db: Session = Depends(get_db)) -> QuizGenerationService:
    """Get quiz generation service instance."""
    from ..services.indexing_service import get_indexing_service
    indexing_service = get_indexing_service()
    return QuizGenerationService(
        openai_api_key=settings.openai_api_key,
        indexing_service=indexing_service
    )


def get_quiz_manager(
    db: Session = Depends(get_db),
    quiz_generator: QuizGenerationService = Depends(get_quiz_generator)
) -> QuizManagerService:
    """Get quiz manager service instance."""
    return QuizManagerService(quiz_generator=quiz_generator, db_session=db)


# Quiz Generation Endpoints

@router.post("/generate", response_model=List[QuizQuestionResponse])
async def generate_quiz(
    request: QuizGenerationRequest,
    quiz_generator: QuizGenerationService = Depends(get_quiz_generator)
):
    """
    Generate a quiz based on the provided parameters.
    
    This endpoint generates quiz questions from indexed documents based on:
    - Topic (optional)
    - Question types (multiple choice, true/false, etc.)
    - Difficulty level
    - Number of questions
    - Content filters
    """
    try:
        logger.info(f"Generating quiz for topic: {request.topic}")
        
        questions = await quiz_generator.generate_quiz(request)
        
        if not questions:
            raise HTTPException(
                status_code=404,
                detail="No suitable content found for generating quiz questions"
            )
        
        # Convert to response format
        response_questions = []
        for question in questions:
            response_questions.append(QuizQuestionResponse(
                id=question.id,
                question_type=question.question_type.value,
                question_text=question.question_text,
                options=question.options,
                difficulty=question.difficulty.value,
                topic=question.topic,
                metadata=question.metadata
            ))
        
        logger.info(f"Generated {len(response_questions)} questions")
        return response_questions
        
    except Exception as e:
        logger.error(f"Quiz generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Quiz Management Endpoints

@router.post("/", response_model=QuizResponse)
async def create_quiz(
    request: QuizCreateRequest,
    quiz_manager: QuizManagerService = Depends(get_quiz_manager)
):
    """
    Create a new quiz with customizable settings.
    
    This endpoint allows creating persistent quizzes that can be:
    - Shared with other users
    - Customized with specific settings
    - Used for multiple sessions
    """
    try:
        logger.info(f"Creating quiz: {request.title}")
        
        quiz = await quiz_manager.create_quiz(request)
        
        return QuizResponse(
            id=quiz.id,
            title=quiz.title,
            description=quiz.description,
            topic=quiz.topic,
            difficulty_level=quiz.difficulty_level,
            question_types=quiz.question_types,
            total_questions=quiz.total_questions,
            time_limit=quiz.time_limit,
            passing_score=quiz.passing_score,
            is_public=quiz.is_public,
            created_by=quiz.created_by,
            created_at=quiz.created_at,
            updated_at=quiz.updated_at,
            settings=quiz.settings
        )
        
    except Exception as e:
        logger.error(f"Quiz creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{quiz_id}", response_model=QuizResponse)
async def get_quiz(
    quiz_id: str,
    quiz_manager: QuizManagerService = Depends(get_quiz_manager)
):
    """
    Get a specific quiz by ID.
    
    Returns quiz metadata and configuration without the actual questions.
    Use the session endpoints to get questions for taking the quiz.
    """
    try:
        quiz = await quiz_manager.get_quiz(quiz_id)
        
        if not quiz:
            raise HTTPException(status_code=404, detail="Quiz not found")
        
        return QuizResponse(
            id=quiz.id,
            title=quiz.title,
            description=quiz.description,
            topic=quiz.topic,
            difficulty_level=quiz.difficulty_level,
            question_types=quiz.question_types,
            total_questions=quiz.total_questions,
            time_limit=quiz.time_limit,
            passing_score=quiz.passing_score,
            is_public=quiz.is_public,
            created_by=quiz.created_by,
            created_at=quiz.created_at,
            updated_at=quiz.updated_at,
            settings=quiz.settings
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get quiz {quiz_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{quiz_id}/submit", response_model=QuizSubmissionResponse)
async def submit_answer(
    quiz_id: str,
    answer_request: QuizAnswerRequest,
    quiz_manager: QuizManagerService = Depends(get_quiz_manager)
):
    """
    Submit an answer for a quiz question.
    
    Evaluates the answer, updates session progress, and returns
    feedback including whether the answer was correct and the explanation.
    """
    try:
        result = await quiz_manager.submit_answer(answer_request)
        
        return QuizSubmissionResponse(
            session_id=result["session_id"],
            question_id=result["question_id"],
            is_correct=result["is_correct"],
            correct_answer=result["correct_answer"],
            explanation=result["explanation"],
            time_taken=result.get("time_taken"),
            session_status=result["session_status"],
            current_question=result["current_question"],
            total_questions=result["total_questions"],
            score=result["score"]
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to submit answer for quiz {quiz_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user-progress/{user_id}", response_model=List[UserProgressResponse])
async def get_user_progress(
    user_id: str,
    topic: Optional[str] = Query(None, description="Filter by topic"),
    quiz_manager: QuizManagerService = Depends(get_quiz_manager)
):
    """
    Get user progress across topics.
    
    Returns learning analytics, mastery levels, and recommendations
    for the specified user. Can be filtered by topic.
    """
    try:
        progress_records = await quiz_manager.get_user_progress(user_id, topic)
        
        response_progress = []
        for progress in progress_records:
            response_progress.append(UserProgressResponse(
                id=progress.id,
                user_id=progress.user_id,
                topic=progress.topic,
                total_quizzes_taken=progress.total_quizzes_taken,
                total_questions_answered=progress.total_questions_answered,
                correct_answers=progress.correct_answers,
                average_score=progress.average_score,
                mastery_level=progress.mastery_level,
                mastery_score=progress.mastery_score,
                knowledge_gaps=progress.knowledge_gaps,
                strengths=progress.strengths,
                suggested_difficulty=progress.suggested_difficulty,
                next_review_date=progress.next_review_date,
                last_updated=progress.last_updated
            ))
        
        return response_progress
        
    except Exception as e:
        logger.error(f"Failed to get user progress for {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Quiz Session Endpoints

@router.post("/sessions", response_model=QuizSessionResponse)
async def start_quiz_session(
    request: QuizSessionCreateRequest,
    quiz_manager: QuizManagerService = Depends(get_quiz_manager)
):
    """
    Start a new quiz session.
    
    Creates a new session for taking a quiz, generating questions
    and tracking progress. Returns session details and a session token
    for subsequent interactions.
    """
    try:
        logger.info(f"Starting quiz session for quiz: {request.quiz_id}")
        
        session = await quiz_manager.start_quiz_session(request)
        
        return QuizSessionResponse(
            id=session.id,
            quiz_id=session.quiz_id,
            user_id=session.user_id,
            session_token=session.session_token,
            status=session.status,
            started_at=session.started_at,
            completed_at=session.completed_at,
            time_spent=session.time_spent,
            total_questions=session.total_questions,
            answered_questions=session.answered_questions,
            correct_answers=session.correct_answers,
            score=session.score,
            passed=session.passed,
            current_question=session.current_question
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to start quiz session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Quiz Sharing and Export Endpoints

@router.post("/{quiz_id}/share")
async def share_quiz(
    quiz_id: str,
    user_id: Optional[str] = Query(None, description="User ID (optional)"),
    quiz_manager: QuizManagerService = Depends(get_quiz_manager)
):
    """
    Generate a shareable link for a quiz.
    
    Creates a public sharing token that allows others to access
    and take the quiz without authentication.
    """
    try:
        share_data = await quiz_manager.share_quiz(quiz_id, user_id)
        
        if not share_data:
            raise HTTPException(status_code=404, detail="Quiz not found")
        
        return share_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to share quiz {quiz_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{quiz_id}/export")
async def export_quiz(
    quiz_id: str,
    format: str = Query("json", description="Export format (json, csv, pdf)"),
    quiz_manager: QuizManagerService = Depends(get_quiz_manager)
):
    """
    Export quiz data in various formats.
    
    Supports exporting quiz questions and analytics in JSON, CSV, or PDF format.
    """
    try:
        quiz = await quiz_manager.get_quiz(quiz_id)
        
        if not quiz:
            raise HTTPException(status_code=404, detail="Quiz not found")
        
        # For now, return basic quiz data
        # TODO: Implement proper export functionality with formatting
        export_data = {
            "quiz": {
                "id": quiz.id,
                "title": quiz.title,
                "description": quiz.description,
                "topic": quiz.topic,
                "difficulty_level": quiz.difficulty_level,
                "total_questions": quiz.total_questions,
                "created_at": quiz.created_at.isoformat(),
            },
            "format": format,
            "exported_at": datetime.utcnow().isoformat()
        }
        
        return export_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export quiz {quiz_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 