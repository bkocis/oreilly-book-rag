"""
Quiz Management Service

This service handles quiz creation, session management, progress tracking,
adaptive difficulty adjustment, analytics, and sharing functionality.
"""

import asyncio
import json
import logging
import secrets
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from pydantic import BaseModel, Field

import structlog

from ..models.quiz_models import Quiz, QuizSession, UserResponse, QuizAnalytics, UserProgress
from ..services.quiz_generator import QuizGenerationService, QuizGenerationRequest, QuizQuestion, DifficultyLevel, QuestionType
from ..utils.database import get_db

logger = structlog.get_logger(__name__)


class QuizStatus(str, Enum):
    """Enum for quiz session status."""
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class MasteryLevel(str, Enum):
    """Enum for user mastery levels."""
    NOVICE = "novice"
    LEARNING = "learning"
    PROFICIENT = "proficient"
    EXPERT = "expert"


class QuizCreateRequest(BaseModel):
    """Request model for creating a new quiz."""
    title: str
    description: Optional[str] = None
    topic: str
    difficulty_level: DifficultyLevel
    question_types: List[QuestionType] = Field(default=[QuestionType.MULTIPLE_CHOICE])
    total_questions: int = Field(default=10, ge=1, le=50)
    time_limit: Optional[int] = None  # Minutes
    passing_score: float = Field(default=70.0, ge=0, le=100)
    is_public: bool = False
    created_by: Optional[str] = None
    settings: Dict[str, Any] = Field(default_factory=dict)


class QuizSessionCreateRequest(BaseModel):
    """Request model for starting a quiz session."""
    quiz_id: str
    user_id: Optional[str] = None
    settings: Dict[str, Any] = Field(default_factory=dict)


class QuizAnswerRequest(BaseModel):
    """Request model for submitting an answer."""
    session_id: str
    question_id: str
    user_answer: Any  # Can be string, list, etc.
    time_taken: Optional[int] = None  # Seconds


class QuizManagerService:
    """Service for managing quizzes, sessions, and user progress."""
    
    def __init__(
        self,
        quiz_generator: QuizGenerationService,
        db_session: Session
    ):
        """Initialize the quiz manager service."""
        self.quiz_generator = quiz_generator
        self.db = db_session
        
        logger.info("Quiz manager service initialized")
    
    # QUIZ CREATION AND CUSTOMIZATION
    
    async def create_quiz(self, request: QuizCreateRequest) -> Quiz:
        """
        Create a new customizable quiz.
        
        Args:
            request: Quiz creation parameters
            
        Returns:
            Created quiz object
        """
        try:
            logger.info(
                "Creating new quiz",
                title=request.title,
                topic=request.topic,
                difficulty=request.difficulty_level,
                questions=request.total_questions
            )
            
            # Create quiz in database
            quiz = Quiz(
                title=request.title,
                description=request.description,
                topic=request.topic,
                difficulty_level=request.difficulty_level.value,
                question_types=[qt.value for qt in request.question_types],
                total_questions=request.total_questions,
                time_limit=request.time_limit,
                passing_score=request.passing_score,
                is_public=request.is_public,
                created_by=request.created_by,
                settings=request.settings
            )
            
            self.db.add(quiz)
            self.db.commit()
            self.db.refresh(quiz)
            
            # Initialize analytics
            await self._initialize_quiz_analytics(quiz.id)
            
            logger.info("Quiz created successfully", quiz_id=quiz.id)
            return quiz
            
        except Exception as e:
            logger.error("Failed to create quiz", error=str(e))
            self.db.rollback()
            raise
    
    async def get_quiz(self, quiz_id: str) -> Optional[Quiz]:
        """Get quiz by ID."""
        return self.db.query(Quiz).filter(Quiz.id == quiz_id).first()
    
    async def list_quizzes(
        self,
        topic: Optional[str] = None,
        difficulty: Optional[DifficultyLevel] = None,
        is_public: Optional[bool] = None,
        created_by: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[Quiz]:
        """List quizzes with optional filters."""
        query = self.db.query(Quiz)
        
        if topic:
            query = query.filter(Quiz.topic == topic)
        if difficulty:
            query = query.filter(Quiz.difficulty_level == difficulty.value)
        if is_public is not None:
            query = query.filter(Quiz.is_public == is_public)
        if created_by:
            query = query.filter(Quiz.created_by == created_by)
        
        query = query.filter(Quiz.is_active == True)
        query = query.order_by(desc(Quiz.created_at))
        query = query.offset(offset).limit(limit)
        
        return query.all()
    
    # QUIZ SESSION MANAGEMENT
    
    async def start_quiz_session(self, request: QuizSessionCreateRequest) -> QuizSession:
        """
        Start a new quiz session.
        
        Args:
            request: Session creation parameters
            
        Returns:
            Created quiz session
        """
        try:
            logger.info(
                "Starting quiz session",
                quiz_id=request.quiz_id,
                user_id=request.user_id
            )
            
            # Get quiz
            quiz = await self.get_quiz(request.quiz_id)
            if not quiz:
                raise ValueError("Quiz not found")
            
            if not quiz.is_active:
                raise ValueError("Quiz is not active")
            
            # Generate questions for this session
            quiz_request = QuizGenerationRequest(
                topic=quiz.topic,
                question_types=[QuestionType(qt) for qt in quiz.question_types],
                difficulty_level=DifficultyLevel(quiz.difficulty_level),
                num_questions=quiz.total_questions
            )
            
            questions = await self.quiz_generator.generate_quiz(quiz_request)
            questions_data = [q.dict() for q in questions]
            
            # Create session
            session = QuizSession(
                quiz_id=request.quiz_id,
                user_id=request.user_id,
                session_token=secrets.token_urlsafe(32),
                total_questions=len(questions),
                questions_data=questions_data,
                metadata=request.settings
            )
            
            self.db.add(session)
            self.db.commit()
            self.db.refresh(session)
            
            logger.info("Quiz session started", session_id=session.id)
            return session
            
        except Exception as e:
            logger.error("Failed to start quiz session", error=str(e))
            self.db.rollback()
            raise
    
    async def get_quiz_session(self, session_id: str) -> Optional[QuizSession]:
        """Get quiz session by ID."""
        return self.db.query(QuizSession).filter(QuizSession.id == session_id).first()
    
    async def submit_answer(self, request: QuizAnswerRequest) -> Dict[str, Any]:
        """
        Submit an answer for a question in a quiz session.
        
        Args:
            request: Answer submission request
            
        Returns:
            Result of answer submission
        """
        try:
            logger.info(
                "Submitting answer",
                session_id=request.session_id,
                question_id=request.question_id
            )
            
            # Get session
            session = await self.get_quiz_session(request.session_id)
            if not session:
                raise ValueError("Quiz session not found")
            
            if session.status != QuizStatus.IN_PROGRESS.value:
                raise ValueError("Quiz session is not in progress")
            
            # Find question in session data
            question_data = None
            for q in session.questions_data:
                if q['id'] == request.question_id:
                    question_data = q
                    break
            
            if not question_data:
                raise ValueError("Question not found in session")
            
            # Check if already answered
            existing_response = self.db.query(UserResponse).filter(
                and_(
                    UserResponse.session_id == request.session_id,
                    UserResponse.question_id == request.question_id
                )
            ).first()
            
            if existing_response:
                raise ValueError("Question already answered")
            
            # Evaluate answer
            is_correct = await self._evaluate_answer(
                question_data,
                request.user_answer
            )
            
            # Create user response
            response = UserResponse(
                session_id=request.session_id,
                question_id=request.question_id,
                question_type=question_data['question_type'],
                question_text=question_data['question_text'],
                correct_answer=question_data['correct_answer'],
                topic=question_data['topic'],
                difficulty=question_data['difficulty'],
                user_answer=request.user_answer,
                is_correct=is_correct,
                time_taken=request.time_taken
            )
            
            self.db.add(response)
            
            # Update session progress
            session.answered_questions += 1
            if is_correct:
                session.correct_answers += 1
            session.current_question += 1
            
            # Check if quiz is completed
            if session.answered_questions >= session.total_questions:
                await self._complete_quiz_session(session)
            
            self.db.commit()
            
            result = {
                "is_correct": is_correct,
                "correct_answer": question_data['correct_answer'],
                "explanation": question_data.get('explanation', ''),
                "progress": {
                    "answered": session.answered_questions,
                    "total": session.total_questions,
                    "current_score": (session.correct_answers / session.answered_questions) * 100 if session.answered_questions > 0 else 0
                },
                "session_completed": session.status == QuizStatus.COMPLETED.value
            }
            
            logger.info(
                "Answer submitted",
                session_id=request.session_id,
                is_correct=is_correct,
                progress=f"{session.answered_questions}/{session.total_questions}"
            )
            
            return result
            
        except Exception as e:
            logger.error("Failed to submit answer", error=str(e))
            self.db.rollback()
            raise
    
    async def _complete_quiz_session(self, session: QuizSession):
        """Complete a quiz session and calculate final results."""
        session.status = QuizStatus.COMPLETED.value
        session.completed_at = datetime.utcnow()
        session.score = (session.correct_answers / session.total_questions) * 100
        
        # Get quiz to check passing score
        quiz = await self.get_quiz(session.quiz_id)
        if quiz:
            session.passed = session.score >= quiz.passing_score
        
        # Update user progress if user_id is available
        if session.user_id:
            await self._update_user_progress(session)
        
        # Update quiz analytics
        await self._update_quiz_analytics(session)
    
    # PROGRESS TRACKING
    
    async def _update_user_progress(self, session: QuizSession):
        """Update user progress based on completed session."""
        if not session.user_id:
            return
        
        quiz = await self.get_quiz(session.quiz_id)
        if not quiz:
            return
        
        # Get or create user progress record
        progress = self.db.query(UserProgress).filter(
            and_(
                UserProgress.user_id == session.user_id,
                UserProgress.topic == quiz.topic
            )
        ).first()
        
        if not progress:
            progress = UserProgress(
                user_id=session.user_id,
                topic=quiz.topic,
                first_attempt=session.started_at
            )
            self.db.add(progress)
        
        # Update progress metrics
        progress.total_quizzes_taken += 1
        progress.total_questions_answered += session.total_questions
        progress.correct_answers += session.correct_answers
        progress.average_score = (progress.correct_answers / progress.total_questions_answered) * 100
        
        # Update mastery level
        progress.mastery_level = await self._calculate_mastery_level(progress)
        progress.mastery_score = await self._calculate_mastery_score(progress)
        
        # Update adaptive difficulty suggestion
        progress.suggested_difficulty = await self._suggest_next_difficulty(progress, session)
        
        # Update spaced repetition
        await self._update_spaced_repetition(progress, session)
    
    async def get_user_progress(self, user_id: str, topic: Optional[str] = None) -> List[UserProgress]:
        """Get user progress for all topics or specific topic."""
        query = self.db.query(UserProgress).filter(UserProgress.user_id == user_id)
        
        if topic:
            query = query.filter(UserProgress.topic == topic)
        
        return query.all()
    
    # ADAPTIVE DIFFICULTY
    
    async def _suggest_next_difficulty(self, progress: UserProgress, latest_session: QuizSession) -> str:
        """Suggest next difficulty level based on user performance."""
        quiz = await self.get_quiz(latest_session.quiz_id)
        current_difficulty = DifficultyLevel(quiz.difficulty_level)
        score = latest_session.score
        
        # Simple adaptive logic
        if score >= 85:
            # User is performing well, suggest harder difficulty
            if current_difficulty == DifficultyLevel.BEGINNER:
                return DifficultyLevel.INTERMEDIATE.value
            elif current_difficulty == DifficultyLevel.INTERMEDIATE:
                return DifficultyLevel.ADVANCED.value
            else:
                return DifficultyLevel.ADVANCED.value
        elif score <= 60:
            # User is struggling, suggest easier difficulty
            if current_difficulty == DifficultyLevel.ADVANCED:
                return DifficultyLevel.INTERMEDIATE.value
            elif current_difficulty == DifficultyLevel.INTERMEDIATE:
                return DifficultyLevel.BEGINNER.value
            else:
                return DifficultyLevel.BEGINNER.value
        else:
            # User is doing okay, maintain current difficulty
            return current_difficulty.value
    
    async def _calculate_mastery_level(self, progress: UserProgress) -> str:
        """Calculate user mastery level for a topic."""
        if progress.average_score >= 90 and progress.total_quizzes_taken >= 5:
            return MasteryLevel.EXPERT.value
        elif progress.average_score >= 80 and progress.total_quizzes_taken >= 3:
            return MasteryLevel.PROFICIENT.value
        elif progress.average_score >= 60 and progress.total_quizzes_taken >= 2:
            return MasteryLevel.LEARNING.value
        else:
            return MasteryLevel.NOVICE.value
    
    async def _calculate_mastery_score(self, progress: UserProgress) -> float:
        """Calculate a comprehensive mastery score (0-100)."""
        # Weighted combination of average score, consistency, and experience
        base_score = progress.average_score
        
        # Experience bonus (more quizzes taken = higher mastery)
        experience_bonus = min(progress.total_quizzes_taken * 2, 20)
        
        # Consistency factor (based on recent performance)
        # This would require more complex tracking of recent sessions
        consistency_factor = 1.0  # Simplified for now
        
        mastery_score = min((base_score + experience_bonus) * consistency_factor, 100)
        return mastery_score
    
    async def _update_spaced_repetition(self, progress: UserProgress, session: QuizSession):
        """Update spaced repetition schedule based on performance."""
        if session.score >= 80:
            # Good performance, increase interval
            progress.spaced_repetition_interval = min(progress.spaced_repetition_interval * 2, 30)
        else:
            # Poor performance, reset to shorter interval
            progress.spaced_repetition_interval = max(progress.spaced_repetition_interval // 2, 1)
        
        # Set next review date
        progress.next_review_date = datetime.utcnow() + timedelta(days=progress.spaced_repetition_interval)
    
    # QUIZ ANALYTICS AND INSIGHTS
    
    async def _initialize_quiz_analytics(self, quiz_id: str):
        """Initialize analytics record for a new quiz."""
        analytics = QuizAnalytics(quiz_id=quiz_id)
        self.db.add(analytics)
        self.db.commit()
    
    async def _update_quiz_analytics(self, session: QuizSession):
        """Update quiz analytics after session completion."""
        analytics = self.db.query(QuizAnalytics).filter(
            QuizAnalytics.quiz_id == session.quiz_id
        ).first()
        
        if not analytics:
            await self._initialize_quiz_analytics(session.quiz_id)
            analytics = self.db.query(QuizAnalytics).filter(
                QuizAnalytics.quiz_id == session.quiz_id
            ).first()
        
        # Update basic metrics
        analytics.total_attempts += 1
        if session.status == QuizStatus.COMPLETED.value:
            analytics.total_completions += 1
        
        # Update completion rate
        analytics.completion_rate = (analytics.total_completions / analytics.total_attempts) * 100
        
        # Update average score (only for completed sessions)
        if session.status == QuizStatus.COMPLETED.value:
            # Get all completed sessions for this quiz
            completed_sessions = self.db.query(QuizSession).filter(
                and_(
                    QuizSession.quiz_id == session.quiz_id,
                    QuizSession.status == QuizStatus.COMPLETED.value
                )
            ).all()
            
            total_score = sum(s.score for s in completed_sessions)
            analytics.average_score = total_score / len(completed_sessions)
        
        analytics.last_updated = datetime.utcnow()
    
    async def get_quiz_analytics(self, quiz_id: str) -> Optional[QuizAnalytics]:
        """Get analytics for a specific quiz."""
        return self.db.query(QuizAnalytics).filter(
            QuizAnalytics.quiz_id == quiz_id
        ).first()
    
    # QUIZ SHARING FUNCTIONALITY
    
    async def share_quiz(self, quiz_id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Generate sharing information for a quiz."""
        quiz = await self.get_quiz(quiz_id)
        if not quiz:
            raise ValueError("Quiz not found")
        
        # Check permissions
        if not quiz.is_public and quiz.created_by != user_id:
            raise ValueError("Quiz is not public and you don't have permission to share it")
        
        # Generate sharing data
        sharing_data = {
            "quiz_id": quiz.id,
            "title": quiz.title,
            "description": quiz.description,
            "topic": quiz.topic,
            "difficulty": quiz.difficulty_level,
            "total_questions": quiz.total_questions,
            "time_limit": quiz.time_limit,
            "share_url": f"/quiz/{quiz.id}",  # This would be the frontend URL
            "public": quiz.is_public,
            "created_at": quiz.created_at.isoformat()
        }
        
        return sharing_data
    
    # UTILITY METHODS
    
    async def _evaluate_answer(self, question_data: Dict[str, Any], user_answer: Any) -> bool:
        """Evaluate if a user's answer is correct."""
        correct_answer = question_data['correct_answer']
        question_type = question_data['question_type']
        
        if question_type == QuestionType.MULTIPLE_CHOICE.value:
            return str(user_answer).strip().lower() == str(correct_answer).strip().lower()
        
        elif question_type == QuestionType.TRUE_FALSE.value:
            return bool(user_answer) == bool(correct_answer)
        
        elif question_type == QuestionType.FILL_IN_BLANK.value:
            # More flexible matching for fill-in-the-blank
            user_answer_clean = str(user_answer).strip().lower()
            correct_answer_clean = str(correct_answer).strip().lower()
            return user_answer_clean == correct_answer_clean
        
        elif question_type == QuestionType.SHORT_ANSWER.value:
            # For short answers, we could implement more sophisticated matching
            # For now, simple string comparison
            user_answer_clean = str(user_answer).strip().lower()
            correct_answer_clean = str(correct_answer).strip().lower()
            return user_answer_clean in correct_answer_clean or correct_answer_clean in user_answer_clean
        
        return False


def get_quiz_manager(
    quiz_generator: QuizGenerationService,
    db_session: Session
) -> QuizManagerService:
    """Factory function to create QuizManagerService instance."""
    return QuizManagerService(quiz_generator, db_session) 