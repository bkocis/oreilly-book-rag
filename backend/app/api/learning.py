"""
Learning API endpoints for the O'Reilly RAG Quiz system.

This module provides endpoints for:
- Topic management and listing
- Difficulty level management
- Study session management
- Learning recommendations
- Progress tracking
- Mastery assessment
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, Query, Path
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from ..models.quiz_models import Quiz, QuizSession, UserProgress
from ..services.learning_analytics import (
    LearningAnalyticsService,
    LearningMetrics,
    SpacedRepetitionItem,
    LearningRecommendation,
    LearningInsightType
)
from ..services.indexing_service import get_indexing_service
from ..utils.database import get_db
from config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


# Request Models
class StudySessionRequest(BaseModel):
    """Request model for creating a study session."""
    user_id: str = Field(..., description="User identifier")
    topic: str = Field(..., description="Topic to study")
    difficulty_level: str = Field(..., description="Difficulty level")
    duration_minutes: int = Field(30, description="Planned session duration in minutes")
    session_type: str = Field("practice", description="Type of study session")
    goals: List[str] = Field(default_factory=list, description="Learning goals for the session")


class ProgressTrackingRequest(BaseModel):
    """Request model for tracking progress."""
    user_id: str = Field(..., description="User identifier")
    topic: str = Field(..., description="Topic")
    performance_score: float = Field(..., description="Performance score (0-100)")
    time_spent_minutes: int = Field(..., description="Time spent in minutes")
    questions_answered: int = Field(..., description="Number of questions answered")
    correct_answers: int = Field(..., description="Number of correct answers")


# Response Models
class TopicResponse(BaseModel):
    """Response model for topic data."""
    name: str
    description: Optional[str]
    difficulty_levels: List[str]
    total_content_pieces: int
    average_completion_time: Optional[int]
    user_progress: Optional[float]
    is_available: bool


class DifficultyLevelResponse(BaseModel):
    """Response model for difficulty level data."""
    name: str
    description: str
    prerequisites: List[str]
    estimated_time_hours: float
    skill_level: str
    is_available: bool


class StudySessionResponse(BaseModel):
    """Response model for study session data."""
    id: str
    user_id: str
    topic: str
    difficulty_level: str
    session_type: str
    status: str
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_minutes: int
    planned_duration: int
    goals: List[str]
    progress: Dict[str, Any]
    recommendations: List[str]


class LearningRecommendationResponse(BaseModel):
    """Response model for learning recommendations."""
    type: str
    topic: str
    difficulty: str
    priority: int
    reason: str
    estimated_time_minutes: int
    confidence_score: float
    action_url: Optional[str]


class ProgressTrackingResponse(BaseModel):
    """Response model for progress tracking data."""
    user_id: str
    topic: str
    current_level: str
    mastery_progress: float
    total_time_spent: int
    sessions_completed: int
    knowledge_gaps: List[str]
    strengths: List[str]
    next_recommendations: List[LearningRecommendationResponse]
    spaced_repetition_items: List[Dict[str, Any]]


class MasteryAssessmentResponse(BaseModel):
    """Response model for mastery assessment."""
    user_id: str
    topic: str
    mastery_level: str
    mastery_score: float
    assessment_date: datetime
    skills_mastered: List[str]
    skills_in_progress: List[str]
    skills_to_learn: List[str]
    next_milestone: Optional[str]
    estimated_time_to_mastery: Optional[int]


# Dependency injection
def get_learning_analytics(db: Session = Depends(get_db)) -> LearningAnalyticsService:
    """Get learning analytics service instance."""
    return LearningAnalyticsService(db_session=db)


# Topic Management Endpoints

@router.get("/topics", response_model=List[TopicResponse])
async def get_topics(
    user_id: Optional[str] = Query(None, description="User ID for personalized data"),
    include_progress: bool = Query(False, description="Include user progress data"),
    db: Session = Depends(get_db)
):
    """
    Get all available learning topics.
    
    Returns a list of available topics with metadata including:
    - Topic name and description
    - Available difficulty levels
    - Content statistics
    - User progress (if user_id provided)
    """
    try:
        logger.info(f"Fetching topics for user: {user_id}")
        
        # Get indexing service to fetch available topics
        indexing_service = get_indexing_service()
        
        # Get unique topics from indexed documents
        # This would need to be implemented in the indexing service
        # For now, we'll return a hardcoded list based on common O'Reilly topics
        topics_data = [
            {
                "name": "Python Programming",
                "description": "Learn Python programming fundamentals and advanced concepts",
                "difficulty_levels": ["beginner", "intermediate", "advanced"],
                "total_content_pieces": 150,
                "average_completion_time": 180,
                "is_available": True
            },
            {
                "name": "Machine Learning",
                "description": "Understand machine learning algorithms and applications",
                "difficulty_levels": ["intermediate", "advanced"],
                "total_content_pieces": 200,
                "average_completion_time": 240,
                "is_available": True
            },
            {
                "name": "Data Science",
                "description": "Data analysis, visualization, and statistical methods",
                "difficulty_levels": ["beginner", "intermediate", "advanced"],
                "total_content_pieces": 180,
                "average_completion_time": 220,
                "is_available": True
            },
            {
                "name": "Web Development",
                "description": "Frontend and backend web development technologies",
                "difficulty_levels": ["beginner", "intermediate", "advanced"],
                "total_content_pieces": 120,
                "average_completion_time": 160,
                "is_available": True
            },
            {
                "name": "DevOps",
                "description": "Development operations, CI/CD, and infrastructure",
                "difficulty_levels": ["intermediate", "advanced"],
                "total_content_pieces": 90,
                "average_completion_time": 140,
                "is_available": True
            },
            {
                "name": "Cloud Computing",
                "description": "Cloud platforms, services, and architecture",
                "difficulty_levels": ["beginner", "intermediate", "advanced"],
                "total_content_pieces": 110,
                "average_completion_time": 170,
                "is_available": True
            }
        ]
        
        # Add user progress if requested
        if user_id and include_progress:
            for topic_data in topics_data:
                progress = db.query(UserProgress).filter(
                    UserProgress.user_id == user_id,
                    UserProgress.topic == topic_data["name"]
                ).first()
                
                if progress:
                    topic_data["user_progress"] = progress.mastery_score
                else:
                    topic_data["user_progress"] = 0.0
        
        # Convert to response format
        topics = []
        for topic_data in topics_data:
            topics.append(TopicResponse(
                name=topic_data["name"],
                description=topic_data["description"],
                difficulty_levels=topic_data["difficulty_levels"],
                total_content_pieces=topic_data["total_content_pieces"],
                average_completion_time=topic_data["average_completion_time"],
                user_progress=topic_data.get("user_progress"),
                is_available=topic_data["is_available"]
            ))
        
        logger.info(f"Retrieved {len(topics)} topics")
        return topics
        
    except Exception as e:
        logger.error(f"Failed to fetch topics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/difficulty-levels", response_model=List[DifficultyLevelResponse])
async def get_difficulty_levels():
    """
    Get all available difficulty levels with descriptions and requirements.
    
    Returns detailed information about each difficulty level including:
    - Prerequisites
    - Estimated completion time
    - Skill level descriptions
    """
    try:
        logger.info("Fetching difficulty levels")
        
        difficulty_levels = [
            {
                "name": "beginner",
                "description": "For those new to the topic with little to no prior experience",
                "prerequisites": [],
                "estimated_time_hours": 20.0,
                "skill_level": "Novice",
                "is_available": True
            },
            {
                "name": "intermediate",
                "description": "For those with basic understanding looking to deepen their knowledge",
                "prerequisites": ["beginner"],
                "estimated_time_hours": 40.0,
                "skill_level": "Competent",
                "is_available": True
            },
            {
                "name": "advanced",
                "description": "For experienced practitioners seeking expert-level mastery",
                "prerequisites": ["beginner", "intermediate"],
                "estimated_time_hours": 60.0,
                "skill_level": "Expert",
                "is_available": True
            }
        ]
        
        response = []
        for level in difficulty_levels:
            response.append(DifficultyLevelResponse(
                name=level["name"],
                description=level["description"],
                prerequisites=level["prerequisites"],
                estimated_time_hours=level["estimated_time_hours"],
                skill_level=level["skill_level"],
                is_available=level["is_available"]
            ))
        
        logger.info(f"Retrieved {len(response)} difficulty levels")
        return response
        
    except Exception as e:
        logger.error(f"Failed to fetch difficulty levels: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Study Session Management

@router.post("/study-sessions", response_model=StudySessionResponse)
async def create_study_session(
    request: StudySessionRequest,
    db: Session = Depends(get_db),
    learning_analytics: LearningAnalyticsService = Depends(get_learning_analytics)
):
    """
    Create a new study session for a user.
    
    This endpoint creates a personalized study session based on:
    - User's current progress
    - Selected topic and difficulty
    - Learning goals
    - Available time
    """
    try:
        logger.info(f"Creating study session for user {request.user_id}")
        
        # Get user's current progress for recommendations
        user_progress = db.query(UserProgress).filter(
            UserProgress.user_id == request.user_id,
            UserProgress.topic == request.topic
        ).first()
        
        # Generate study session recommendations
        recommendations = await learning_analytics.generate_learning_recommendations(
            user_id=request.user_id,
            max_recommendations=3
        )
        
        # Create study session data
        session_data = {
            "id": f"study_session_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{request.user_id}",
            "user_id": request.user_id,
            "topic": request.topic,
            "difficulty_level": request.difficulty_level,
            "session_type": request.session_type,
            "status": "created",
            "created_at": datetime.utcnow(),
            "started_at": None,
            "completed_at": None,
            "duration_minutes": 0,
            "planned_duration": request.duration_minutes,
            "goals": request.goals,
            "progress": {
                "current_mastery": user_progress.mastery_score if user_progress else 0.0,
                "target_improvement": 5.0,  # 5% improvement target
                "recommended_focus_areas": user_progress.knowledge_gaps if user_progress else []
            },
            "recommendations": [rec.reason for rec in recommendations[:3]]
        }
        
        response = StudySessionResponse(**session_data)
        
        logger.info(f"Study session created: {response.id}")
        return response
        
    except Exception as e:
        logger.error(f"Failed to create study session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Learning Recommendations

@router.get("/recommendations/{user_id}", response_model=List[LearningRecommendationResponse])
async def get_learning_recommendations(
    user_id: str = Path(..., description="User identifier"),
    max_recommendations: int = Query(5, description="Maximum number of recommendations"),
    learning_analytics: LearningAnalyticsService = Depends(get_learning_analytics)
):
    """
    Get personalized learning recommendations for a user.
    
    Generates recommendations based on:
    - Current progress and performance
    - Knowledge gaps
    - Learning patterns
    - Spaced repetition schedule
    """
    try:
        logger.info(f"Generating learning recommendations for user {user_id}")
        
        recommendations = await learning_analytics.generate_learning_recommendations(
            user_id=user_id,
            max_recommendations=max_recommendations
        )
        
        response = []
        for rec in recommendations:
            response.append(LearningRecommendationResponse(
                type=rec.type,
                topic=rec.topic,
                difficulty=rec.difficulty,
                priority=rec.priority,
                reason=rec.reason,
                estimated_time_minutes=rec.estimated_time_minutes,
                confidence_score=rec.confidence_score,
                action_url=f"/api/v1/quizzes/generate?topic={rec.topic}&difficulty={rec.difficulty}"
            ))
        
        logger.info(f"Generated {len(response)} recommendations")
        return response
        
    except Exception as e:
        logger.error(f"Failed to generate recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Progress Tracking

@router.post("/progress/track", response_model=ProgressTrackingResponse)
async def track_progress(
    request: ProgressTrackingRequest,
    db: Session = Depends(get_db),
    learning_analytics: LearningAnalyticsService = Depends(get_learning_analytics)
):
    """
    Track and update user learning progress.
    
    Updates progress metrics and provides insights including:
    - Current mastery level
    - Knowledge gaps and strengths
    - Spaced repetition schedule
    - Next learning recommendations
    """
    try:
        logger.info(f"Tracking progress for user {request.user_id}")
        
        # Update spaced repetition based on performance
        await learning_analytics.update_spaced_repetition(
            user_id=request.user_id,
            topic=request.topic,
            performance_score=request.performance_score
        )
        
        # Get updated metrics
        # Create a mock session for tracking
        session_id = f"progress_session_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        metrics = await learning_analytics.track_user_performance(
            user_id=request.user_id,
            session_id=session_id
        )
        
        # Get recommendations
        recommendations = await learning_analytics.generate_learning_recommendations(
            user_id=request.user_id,
            max_recommendations=3
        )
        
        # Get spaced repetition items
        sr_items = await learning_analytics.get_spaced_repetition_items(
            user_id=request.user_id
        )
        
        # Convert to response format
        response = ProgressTrackingResponse(
            user_id=request.user_id,
            topic=request.topic,
            current_level="intermediate",  # This would be calculated based on metrics
            mastery_progress=metrics.mastery_progress,
            total_time_spent=int(metrics.time_spent_minutes),
            sessions_completed=metrics.total_sessions,
            knowledge_gaps=metrics.knowledge_gaps,
            strengths=metrics.strengths,
            next_recommendations=[
                LearningRecommendationResponse(
                    type=rec.type,
                    topic=rec.topic,
                    difficulty=rec.difficulty,
                    priority=rec.priority,
                    reason=rec.reason,
                    estimated_time_minutes=rec.estimated_time_minutes,
                    confidence_score=rec.confidence_score,
                    action_url=f"/api/v1/quizzes/generate?topic={rec.topic}"
                ) for rec in recommendations
            ],
            spaced_repetition_items=[
                {
                    "topic": item.topic,
                    "difficulty": item.difficulty,
                    "next_review": item.next_review.isoformat(),
                    "success_rate": item.success_rate
                } for item in sr_items
            ]
        )
        
        logger.info(f"Progress tracked successfully for user {request.user_id}")
        return response
        
    except Exception as e:
        logger.error(f"Failed to track progress: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/progress/{user_id}", response_model=List[ProgressTrackingResponse])
async def get_user_progress(
    user_id: str = Path(..., description="User identifier"),
    topic: Optional[str] = Query(None, description="Filter by topic"),
    db: Session = Depends(get_db),
    learning_analytics: LearningAnalyticsService = Depends(get_learning_analytics)
):
    """
    Get comprehensive progress data for a user.
    
    Returns detailed progress information including:
    - Progress across all topics (or filtered by topic)
    - Mastery levels and scores
    - Learning streaks and achievements
    - Recommendations for improvement
    """
    try:
        logger.info(f"Fetching progress for user {user_id}")
        
        # Get user progress records
        query = db.query(UserProgress).filter(UserProgress.user_id == user_id)
        if topic:
            query = query.filter(UserProgress.topic == topic)
        
        progress_records = query.all()
        
        if not progress_records:
            # Return empty progress if no records found
            return []
        
        responses = []
        for progress in progress_records:
            # Get recommendations for this topic
            recommendations = await learning_analytics.generate_learning_recommendations(
                user_id=user_id,
                max_recommendations=3
            )
            
            # Filter recommendations for this topic
            topic_recommendations = [
                rec for rec in recommendations 
                if rec.topic.lower() == progress.topic.lower()
            ]
            
            # Get spaced repetition items
            sr_items = await learning_analytics.get_spaced_repetition_items(user_id)
            topic_sr_items = [
                item for item in sr_items 
                if item.topic.lower() == progress.topic.lower()
            ]
            
            response = ProgressTrackingResponse(
                user_id=user_id,
                topic=progress.topic,
                current_level=progress.mastery_level,
                mastery_progress=progress.mastery_score,
                total_time_spent=0,  # This would need to be calculated from sessions
                sessions_completed=progress.total_quizzes_taken,
                knowledge_gaps=progress.knowledge_gaps,
                strengths=progress.strengths,
                next_recommendations=[
                    LearningRecommendationResponse(
                        type=rec.type,
                        topic=rec.topic,
                        difficulty=rec.difficulty,
                        priority=rec.priority,
                        reason=rec.reason,
                        estimated_time_minutes=rec.estimated_time_minutes,
                        confidence_score=rec.confidence_score,
                        action_url=f"/api/v1/quizzes/generate?topic={rec.topic}"
                    ) for rec in topic_recommendations
                ],
                spaced_repetition_items=[
                    {
                        "topic": item.topic,
                        "difficulty": item.difficulty,
                        "next_review": item.next_review.isoformat(),
                        "success_rate": item.success_rate
                    } for item in topic_sr_items
                ]
            )
            responses.append(response)
        
        logger.info(f"Retrieved progress for {len(responses)} topics")
        return responses
        
    except Exception as e:
        logger.error(f"Failed to fetch user progress: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Mastery Assessment

@router.get("/mastery/{user_id}/{topic}", response_model=MasteryAssessmentResponse)
async def assess_mastery(
    user_id: str = Path(..., description="User identifier"),
    topic: str = Path(..., description="Topic to assess"),
    db: Session = Depends(get_db),
    learning_analytics: LearningAnalyticsService = Depends(get_learning_analytics)
):
    """
    Assess user's mastery level for a specific topic.
    
    Provides comprehensive mastery assessment including:
    - Current mastery level and score
    - Skills mastered, in progress, and to learn
    - Next milestones and estimated time to mastery
    - Detailed progress breakdown
    """
    try:
        logger.info(f"Assessing mastery for user {user_id} in topic {topic}")
        
        # Get user progress
        progress = db.query(UserProgress).filter(
            UserProgress.user_id == user_id,
            UserProgress.topic == topic
        ).first()
        
        if not progress:
            raise HTTPException(
                status_code=404,
                detail=f"No progress found for user {user_id} in topic {topic}"
            )
        
        # Get detailed mastery tracking
        mastery_data = await learning_analytics.track_mastery_progress(user_id)
        topic_mastery = mastery_data.get(topic, {})
        
        # Determine skills status based on mastery score
        mastery_score = progress.mastery_score
        
        # Mock skill categories - in production, these would be derived from content analysis
        all_skills = [
            "Basic Concepts", "Fundamental Principles", "Practical Application",
            "Advanced Techniques", "Best Practices", "Troubleshooting",
            "Integration", "Optimization", "Expert Knowledge"
        ]
        
        skills_mastered = []
        skills_in_progress = []
        skills_to_learn = []
        
        for i, skill in enumerate(all_skills):
            skill_threshold = (i + 1) * 10  # 10%, 20%, 30%, etc.
            if mastery_score >= skill_threshold + 10:
                skills_mastered.append(skill)
            elif mastery_score >= skill_threshold - 10:
                skills_in_progress.append(skill)
            else:
                skills_to_learn.append(skill)
        
        # Determine next milestone
        next_milestone = None
        if mastery_score < 25:
            next_milestone = "Beginner Mastery (25%)"
        elif mastery_score < 50:
            next_milestone = "Intermediate Mastery (50%)"
        elif mastery_score < 75:
            next_milestone = "Advanced Mastery (75%)"
        elif mastery_score < 90:
            next_milestone = "Expert Mastery (90%)"
        else:
            next_milestone = "Complete Mastery (100%)"
        
        # Estimate time to mastery (rough calculation)
        estimated_time = None
        if mastery_score < 90:
            remaining_points = 90 - mastery_score
            # Assume 1 point per hour of study (rough estimate)
            estimated_time = int(remaining_points * 1.5)  # 1.5 hours per point
        
        response = MasteryAssessmentResponse(
            user_id=user_id,
            topic=topic,
            mastery_level=progress.mastery_level,
            mastery_score=mastery_score,
            assessment_date=progress.last_updated,
            skills_mastered=skills_mastered,
            skills_in_progress=skills_in_progress,
            skills_to_learn=skills_to_learn,
            next_milestone=next_milestone,
            estimated_time_to_mastery=estimated_time
        )
        
        logger.info(f"Mastery assessment completed for user {user_id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to assess mastery: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/mastery/{user_id}", response_model=List[MasteryAssessmentResponse])
async def assess_all_mastery(
    user_id: str = Path(..., description="User identifier"),
    db: Session = Depends(get_db),
    learning_analytics: LearningAnalyticsService = Depends(get_learning_analytics)
):
    """
    Assess user's mastery across all topics they've studied.
    
    Returns mastery assessments for all topics the user has progress in,
    providing an overview of their learning journey and achievements.
    """
    try:
        logger.info(f"Assessing all mastery for user {user_id}")
        
        # Get all user progress records
        progress_records = db.query(UserProgress).filter(
            UserProgress.user_id == user_id
        ).all()
        
        if not progress_records:
            return []
        
        responses = []
        for progress in progress_records:
            # Reuse the single topic assessment logic
            try:
                mastery_response = await assess_mastery(
                    user_id=user_id,
                    topic=progress.topic,
                    db=db,
                    learning_analytics=learning_analytics
                )
                responses.append(mastery_response)
            except Exception as e:
                logger.warning(f"Failed to assess mastery for topic {progress.topic}: {str(e)}")
                continue
        
        logger.info(f"Assessed mastery for {len(responses)} topics")
        return responses
        
    except Exception as e:
        logger.error(f"Failed to assess all mastery: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 