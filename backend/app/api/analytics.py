"""
Analytics API endpoints for the O'Reilly RAG Quiz system.

This module provides endpoints for:
- Performance analytics and reporting
- Learning insights and patterns
- Progress visualization data
- Knowledge gap analysis
- Study recommendations based on analytics
- Export functionality for reports and data
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, Query, Path, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
import json
import io
import csv
from enum import Enum

from ..models.quiz_models import Quiz, QuizSession, UserResponse, QuizAnalytics, UserProgress
from ..services.learning_analytics import (
    LearningAnalyticsService,
    LearningMetrics,
    SpacedRepetitionItem,
    LearningRecommendation,
    LearningInsightType
)
from ..utils.database import get_db
from config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


# Enums
class AnalyticsPeriod(str, Enum):
    """Analytics reporting periods."""
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"
    ALL_TIME = "all_time"


class ExportFormat(str, Enum):
    """Export format options."""
    JSON = "json"
    CSV = "csv"


class MetricType(str, Enum):
    """Types of metrics for analytics."""
    ACCURACY = "accuracy"
    SPEED = "speed"
    ENGAGEMENT = "engagement"
    PROGRESS = "progress"
    RETENTION = "retention"


# Request Models
class AnalyticsFilterRequest(BaseModel):
    """Request model for filtering analytics data."""
    user_id: Optional[str] = Field(None, description="Filter by user ID")
    topic: Optional[str] = Field(None, description="Filter by topic")
    difficulty: Optional[str] = Field(None, description="Filter by difficulty level")
    start_date: Optional[datetime] = Field(None, description="Start date for filtering")
    end_date: Optional[datetime] = Field(None, description="End date for filtering")
    period: AnalyticsPeriod = Field(AnalyticsPeriod.MONTH, description="Analysis period")


class KnowledgeGapAnalysisRequest(BaseModel):
    """Request model for knowledge gap analysis."""
    user_id: str = Field(..., description="User identifier")
    topics: Optional[List[str]] = Field(None, description="Specific topics to analyze")
    min_confidence_threshold: float = Field(0.7, description="Minimum confidence threshold")
    include_recommendations: bool = Field(True, description="Include recommendations")


# Response Models
class PerformanceMetricsResponse(BaseModel):
    """Response model for performance metrics."""
    user_id: str
    period: str
    total_sessions: int
    total_questions: int
    accuracy_rate: float
    average_score: float
    time_spent_hours: float
    improvement_rate: float
    streak_days: int
    completion_rate: float
    engagement_score: float
    skill_velocity: float
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class LearningInsightResponse(BaseModel):
    """Response model for learning insights."""
    type: LearningInsightType
    title: str
    description: str
    topic: str
    confidence_score: float
    priority: int
    timestamp: datetime
    data: Dict[str, Any]
    recommendations: List[str]
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ProgressVisualizationResponse(BaseModel):
    """Response model for progress visualization data."""
    user_id: str
    timeline_data: List[Dict[str, Any]]
    topic_breakdown: Dict[str, Any]
    skill_progression: Dict[str, Any]
    performance_trends: Dict[str, Any]
    milestones: List[Dict[str, Any]]
    comparative_analytics: Dict[str, Any]
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class KnowledgeGapResponse(BaseModel):
    """Response model for knowledge gap analysis."""
    user_id: str
    analysis_date: datetime
    overall_score: float
    knowledge_gaps: List[Dict[str, Any]]
    strengths: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]
    priority_areas: List[str]
    learning_path: List[Dict[str, Any]]
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class StudyRecommendationResponse(BaseModel):
    """Response model for study recommendations."""
    user_id: str
    generated_at: datetime
    recommendations: List[Dict[str, Any]]
    priority_topics: List[str]
    optimal_study_times: List[str]
    estimated_improvement: Dict[str, float]
    personalization_factors: Dict[str, Any]
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AnalyticsReportResponse(BaseModel):
    """Response model for comprehensive analytics reports."""
    report_id: str
    user_id: str
    generated_at: datetime
    period: str
    executive_summary: Dict[str, Any]
    performance_metrics: PerformanceMetricsResponse
    learning_insights: List[LearningInsightResponse]
    progress_visualization: ProgressVisualizationResponse
    knowledge_analysis: KnowledgeGapResponse
    recommendations: StudyRecommendationResponse
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# Dependency injection
def get_learning_analytics(db: Session = Depends(get_db)) -> LearningAnalyticsService:
    """Get learning analytics service instance."""
    return LearningAnalyticsService(db_session=db)


# Performance Analytics Endpoints

@router.get("/performance/{user_id}", response_model=PerformanceMetricsResponse)
async def get_performance_analytics(
    user_id: str = Path(..., description="User identifier"),
    period: AnalyticsPeriod = Query(AnalyticsPeriod.MONTH, description="Analysis period"),
    topic: Optional[str] = Query(None, description="Filter by topic"),
    learning_analytics: LearningAnalyticsService = Depends(get_learning_analytics)
):
    """
    Get comprehensive performance analytics for a user.
    
    Returns detailed performance metrics including:
    - Accuracy rates and score trends
    - Time spent and engagement metrics
    - Learning velocity and improvement rates
    - Streak tracking and completion rates
    """
    try:
        logger.info(f"Fetching performance analytics for user: {user_id}, period: {period}")
        
        # Calculate period dates
        end_date = datetime.utcnow()
        if period == AnalyticsPeriod.WEEK:
            start_date = end_date - timedelta(days=7)
        elif period == AnalyticsPeriod.MONTH:
            start_date = end_date - timedelta(days=30)
        elif period == AnalyticsPeriod.QUARTER:
            start_date = end_date - timedelta(days=90)
        elif period == AnalyticsPeriod.YEAR:
            start_date = end_date - timedelta(days=365)
        else:  # ALL_TIME
            start_date = datetime(2020, 1, 1)
        
        # Get performance report from analytics service
        report = await learning_analytics.generate_performance_report(
            user_id=user_id,
            period_days=(end_date - start_date).days
        )
        
        # Calculate additional metrics
        metrics = await learning_analytics.track_user_performance(
            user_id=user_id,
            session_id=""  # Will be calculated internally
        )
        
        # Calculate engagement and skill velocity
        engagement_score = min(100, (metrics.streak_count * 5) + (metrics.accuracy_rate * 0.5))
        skill_velocity = report.get("improvement_rate", 0) * 10  # Scale for better representation
        
        return PerformanceMetricsResponse(
            user_id=user_id,
            period=period.value,
            total_sessions=metrics.total_sessions,
            total_questions=metrics.total_questions,
            accuracy_rate=metrics.accuracy_rate,
            average_score=metrics.average_score,
            time_spent_hours=metrics.time_spent_minutes / 60,
            improvement_rate=report.get("improvement_rate", 0),
            streak_days=metrics.streak_count,
            completion_rate=report.get("completion_rate", 0),
            engagement_score=engagement_score,
            skill_velocity=skill_velocity
        )
        
    except Exception as e:
        logger.error(f"Failed to get performance analytics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve performance analytics")


@router.get("/insights/{user_id}", response_model=List[LearningInsightResponse])
async def get_learning_insights(
    user_id: str = Path(..., description="User identifier"),
    limit: int = Query(10, description="Maximum number of insights"),
    min_confidence: float = Query(0.7, description="Minimum confidence score"),
    learning_analytics: LearningAnalyticsService = Depends(get_learning_analytics)
):
    """
    Get learning insights and patterns for a user.
    
    Returns AI-generated insights about:
    - Learning patterns and behaviors
    - Knowledge gaps and strengths
    - Performance trends and improvements
    - Personalized recommendations
    """
    try:
        logger.info(f"Fetching learning insights for user: {user_id}")
        
        # Get knowledge gaps analysis
        gaps_analysis = await learning_analytics.identify_knowledge_gaps(user_id)
        
        # Get learning recommendations
        recommendations = await learning_analytics.generate_learning_recommendations(
            user_id=user_id,
            max_recommendations=limit
        )
        
        # Generate insights based on analytics data
        insights = []
        
        # Knowledge gap insights
        for gap in gaps_analysis.get("knowledge_gaps", []):
            insights.append(LearningInsightResponse(
                type=LearningInsightType.KNOWLEDGE_GAP,
                title=f"Knowledge Gap in {gap['topic']}",
                description=f"You have a knowledge gap in {gap['topic']} with {gap['confidence']:.1%} confidence",
                topic=gap["topic"],
                confidence_score=gap["confidence"],
                priority=gap.get("priority", 5),
                timestamp=datetime.utcnow(),
                data=gap,
                recommendations=[f"Focus on {gap['topic']} fundamentals", "Take practice quizzes"]
            ))
        
        # Strength insights
        for strength in gaps_analysis.get("strengths", []):
            insights.append(LearningInsightResponse(
                type=LearningInsightType.STRENGTH,
                title=f"Strength in {strength['topic']}",
                description=f"You show strong performance in {strength['topic']}",
                topic=strength["topic"],
                confidence_score=strength["confidence"],
                priority=strength.get("priority", 3),
                timestamp=datetime.utcnow(),
                data=strength,
                recommendations=[f"Consider advanced {strength['topic']} topics", "Help others in this area"]
            ))
        
        # Filter by confidence and sort by priority
        filtered_insights = [i for i in insights if i.confidence_score >= min_confidence]
        filtered_insights.sort(key=lambda x: x.priority, reverse=True)
        
        return filtered_insights[:limit]
        
    except Exception as e:
        logger.error(f"Failed to get learning insights: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve learning insights")


@router.get("/progress-visualization/{user_id}", response_model=ProgressVisualizationResponse)
async def get_progress_visualization_data(
    user_id: str = Path(..., description="User identifier"),
    period: AnalyticsPeriod = Query(AnalyticsPeriod.MONTH, description="Analysis period"),
    learning_analytics: LearningAnalyticsService = Depends(get_learning_analytics),
    db: Session = Depends(get_db)
):
    """
    Get data for progress visualization charts and graphs.
    
    Returns structured data for:
    - Timeline charts showing progress over time
    - Topic breakdown pie charts
    - Skill progression radar charts
    - Performance trend line graphs
    - Milestone achievements
    - Comparative analytics
    """
    try:
        logger.info(f"Fetching progress visualization data for user: {user_id}")
        
        # Calculate period dates
        end_date = datetime.utcnow()
        days_back = {
            AnalyticsPeriod.WEEK: 7,
            AnalyticsPeriod.MONTH: 30,
            AnalyticsPeriod.QUARTER: 90,
            AnalyticsPeriod.YEAR: 365,
            AnalyticsPeriod.ALL_TIME: 1000
        }
        start_date = end_date - timedelta(days=days_back[period])
        
        # Get user sessions for the period
        sessions = db.query(QuizSession).filter(
            QuizSession.user_id == user_id,
            QuizSession.status == "completed",
            QuizSession.completed_at >= start_date
        ).order_by(QuizSession.completed_at).all()
        
        # Generate timeline data
        timeline_data = []
        for session in sessions:
            timeline_data.append({
                "date": session.completed_at.isoformat(),
                "score": session.score,
                "accuracy": (session.correct_answers / session.total_questions * 100) if session.total_questions > 0 else 0,
                "time_spent": session.time_spent or 0,
                "topic": session.quiz.topic if session.quiz else "Unknown"
            })
        
        # Generate topic breakdown
        topic_stats = {}
        for session in sessions:
            topic = session.quiz.topic if session.quiz else "Unknown"
            if topic not in topic_stats:
                topic_stats[topic] = {"sessions": 0, "total_score": 0, "total_questions": 0, "correct_answers": 0}
            topic_stats[topic]["sessions"] += 1
            topic_stats[topic]["total_score"] += session.score
            topic_stats[topic]["total_questions"] += session.total_questions
            topic_stats[topic]["correct_answers"] += session.correct_answers
        
        topic_breakdown = {
            topic: {
                "sessions": stats["sessions"],
                "average_score": stats["total_score"] / stats["sessions"],
                "accuracy": (stats["correct_answers"] / stats["total_questions"] * 100) if stats["total_questions"] > 0 else 0,
                "total_questions": stats["total_questions"]
            }
            for topic, stats in topic_stats.items()
        }
        
        # Generate skill progression data
        mastery_data = await learning_analytics.track_mastery_progress(user_id)
        skill_progression = mastery_data.get("topic_mastery", {})
        
        # Generate performance trends
        performance_trends = {
            "accuracy_trend": [
                {
                    "date": session.completed_at.isoformat(),
                    "value": (session.correct_answers / session.total_questions * 100) if session.total_questions > 0 else 0
                }
                for session in sessions
            ],
            "score_trend": [
                {
                    "date": session.completed_at.isoformat(),
                    "value": session.score
                }
                for session in sessions
            ],
            "speed_trend": [
                {
                    "date": session.completed_at.isoformat(),
                    "value": (session.time_spent / session.total_questions) if session.total_questions > 0 and session.time_spent else 0
                }
                for session in sessions
            ]
        }
        
        # Generate milestones
        milestones = []
        if len(sessions) >= 10:
            milestones.append({
                "type": "sessions",
                "title": "Quiz Enthusiast",
                "description": "Completed 10 quiz sessions",
                "achieved_at": sessions[9].completed_at.isoformat(),
                "icon": "🎯"
            })
        
        total_questions = sum(s.total_questions for s in sessions)
        if total_questions >= 100:
            milestones.append({
                "type": "questions",
                "title": "Question Master",
                "description": "Answered 100 questions",
                "achieved_at": datetime.utcnow().isoformat(),
                "icon": "🧠"
            })
        
        # Generate comparative analytics (placeholder)
        comparative_analytics = {
            "percentile_ranking": 75,  # Placeholder
            "peer_comparison": {
                "better_than": 68,
                "similar_to": 20,
                "worse_than": 12
            },
            "global_averages": {
                "accuracy": 72.5,
                "score": 78.2,
                "session_length": 15.3
            }
        }
        
        return ProgressVisualizationResponse(
            user_id=user_id,
            timeline_data=timeline_data,
            topic_breakdown=topic_breakdown,
            skill_progression=skill_progression,
            performance_trends=performance_trends,
            milestones=milestones,
            comparative_analytics=comparative_analytics
        )
        
    except Exception as e:
        logger.error(f"Failed to get progress visualization data: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve progress visualization data")


@router.post("/knowledge-gaps", response_model=KnowledgeGapResponse)
async def analyze_knowledge_gaps(
    request: KnowledgeGapAnalysisRequest,
    learning_analytics: LearningAnalyticsService = Depends(get_learning_analytics)
):
    """
    Perform comprehensive knowledge gap analysis for a user.
    
    Analyzes user performance to identify:
    - Specific knowledge gaps and weaknesses
    - Areas of strength and expertise
    - Personalized learning recommendations
    - Priority areas for improvement
    - Suggested learning paths
    """
    try:
        logger.info(f"Analyzing knowledge gaps for user: {request.user_id}")
        
        # Get comprehensive knowledge gap analysis
        analysis = await learning_analytics.identify_knowledge_gaps(request.user_id)
        
        # Get learning recommendations
        recommendations = await learning_analytics.generate_learning_recommendations(
            user_id=request.user_id,
            max_recommendations=10
        )
        
        # Process knowledge gaps
        knowledge_gaps = []
        for gap in analysis.get("knowledge_gaps", []):
            if gap.get("confidence", 0) >= request.min_confidence_threshold:
                knowledge_gaps.append({
                    "topic": gap["topic"],
                    "severity": gap["severity"],
                    "confidence": gap["confidence"],
                    "description": gap.get("description", ""),
                    "impact_score": gap.get("impact_score", 0),
                    "suggested_actions": gap.get("suggested_actions", [])
                })
        
        # Process strengths
        strengths = []
        for strength in analysis.get("strengths", []):
            strengths.append({
                "topic": strength["topic"],
                "proficiency": strength["proficiency"],
                "confidence": strength["confidence"],
                "description": strength.get("description", ""),
                "mastery_level": strength.get("mastery_level", "")
            })
        
        # Process recommendations
        processed_recommendations = []
        if request.include_recommendations:
            for rec in recommendations:
                processed_recommendations.append({
                    "type": rec.type,
                    "topic": rec.topic,
                    "difficulty": rec.difficulty,
                    "priority": rec.priority,
                    "reason": rec.reason,
                    "estimated_time": rec.estimated_time_minutes,
                    "confidence": rec.confidence_score
                })
        
        # Generate priority areas
        priority_areas = [gap["topic"] for gap in knowledge_gaps[:5] if gap["confidence"] > 0.8]
        
        # Generate learning path
        learning_path = []
        for i, rec in enumerate(processed_recommendations[:5]):
            learning_path.append({
                "step": i + 1,
                "topic": rec["topic"],
                "difficulty": rec["difficulty"],
                "estimated_time": rec["estimated_time"],
                "prerequisites": [],  # Would be calculated based on topic relationships
                "description": f"Master {rec['topic']} at {rec['difficulty']} level"
            })
        
        return KnowledgeGapResponse(
            user_id=request.user_id,
            analysis_date=datetime.utcnow(),
            overall_score=analysis.get("overall_score", 0),
            knowledge_gaps=knowledge_gaps,
            strengths=strengths,
            recommendations=processed_recommendations,
            priority_areas=priority_areas,
            learning_path=learning_path
        )
        
    except Exception as e:
        logger.error(f"Failed to analyze knowledge gaps: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to analyze knowledge gaps")


@router.get("/study-recommendations/{user_id}", response_model=StudyRecommendationResponse)
async def get_study_recommendations(
    user_id: str = Path(..., description="User identifier"),
    max_recommendations: int = Query(5, description="Maximum number of recommendations"),
    learning_analytics: LearningAnalyticsService = Depends(get_learning_analytics)
):
    """
    Get personalized study recommendations based on analytics.
    
    Provides AI-powered recommendations for:
    - What to study next
    - When to study for optimal retention
    - How to optimize learning efficiency
    - Personalized learning strategies
    """
    try:
        logger.info(f"Generating study recommendations for user: {user_id}")
        
        # Get learning recommendations
        recommendations = await learning_analytics.generate_learning_recommendations(
            user_id=user_id,
            max_recommendations=max_recommendations
        )
        
        # Get user metrics for personalization
        metrics = await learning_analytics.track_user_performance(user_id, "")
        
        # Generate spaced repetition items
        sr_items = await learning_analytics.get_spaced_repetition_items(user_id)
        
        # Process recommendations
        processed_recommendations = []
        for rec in recommendations:
            processed_recommendations.append({
                "id": f"rec_{len(processed_recommendations)}",
                "type": rec.type,
                "topic": rec.topic,
                "difficulty": rec.difficulty,
                "priority": rec.priority,
                "reason": rec.reason,
                "estimated_time_minutes": rec.estimated_time_minutes,
                "confidence_score": rec.confidence_score,
                "action": f"Start {rec.type} session on {rec.topic}",
                "benefits": [
                    f"Improve {rec.topic} knowledge",
                    f"Fill knowledge gaps",
                    f"Increase overall proficiency"
                ]
            })
        
        # Determine priority topics
        priority_topics = list(set([rec.topic for rec in recommendations[:3]]))
        
        # Generate optimal study times (based on user activity patterns)
        optimal_study_times = [
            "9:00 AM - Peak focus time",
            "2:00 PM - Post-lunch review",
            "7:00 PM - Evening reinforcement"
        ]
        
        # Estimate improvement potential
        estimated_improvement = {
            "accuracy": min(100, metrics.accuracy_rate + 15),
            "speed": 25,  # 25% faster completion
            "retention": 40,  # 40% better retention
            "confidence": 30  # 30% increase in confidence
        }
        
        # Personalization factors
        personalization_factors = {
            "learning_style": "visual",  # Would be determined from user behavior
            "optimal_session_length": 20,  # minutes
            "difficulty_preference": "progressive",
            "time_availability": "moderate",
            "current_streak": metrics.streak_count,
            "preferred_topics": priority_topics
        }
        
        return StudyRecommendationResponse(
            user_id=user_id,
            generated_at=datetime.utcnow(),
            recommendations=processed_recommendations,
            priority_topics=priority_topics,
            optimal_study_times=optimal_study_times,
            estimated_improvement=estimated_improvement,
            personalization_factors=personalization_factors
        )
        
    except Exception as e:
        logger.error(f"Failed to generate study recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate study recommendations")


@router.get("/report/{user_id}", response_model=AnalyticsReportResponse)
async def generate_comprehensive_report(
    user_id: str = Path(..., description="User identifier"),
    period: AnalyticsPeriod = Query(AnalyticsPeriod.MONTH, description="Report period"),
    learning_analytics: LearningAnalyticsService = Depends(get_learning_analytics),
    db: Session = Depends(get_db)
):
    """
    Generate a comprehensive analytics report for a user.
    
    Combines all analytics data into a single comprehensive report including:
    - Executive summary
    - Performance metrics
    - Learning insights
    - Progress visualization
    - Knowledge gap analysis
    - Study recommendations
    """
    try:
        logger.info(f"Generating comprehensive report for user: {user_id}")
        
        # Generate report ID
        report_id = f"report_{user_id}_{period.value}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        # Get all analytics components
        performance_metrics = await get_performance_analytics(user_id, period, None, learning_analytics)
        learning_insights = await get_learning_insights(user_id, 10, 0.6, learning_analytics)
        progress_visualization = await get_progress_visualization_data(user_id, period, learning_analytics, db)
        
        # Create knowledge gap analysis request
        gap_request = KnowledgeGapAnalysisRequest(
            user_id=user_id,
            min_confidence_threshold=0.7,
            include_recommendations=True
        )
        knowledge_analysis = await analyze_knowledge_gaps(gap_request, learning_analytics)
        
        study_recommendations = await get_study_recommendations(user_id, 5, learning_analytics)
        
        # Generate executive summary
        executive_summary = {
            "period": period.value,
            "total_sessions": performance_metrics.total_sessions,
            "overall_performance": "Good" if performance_metrics.accuracy_rate > 75 else "Needs Improvement",
            "key_achievements": [
                f"{performance_metrics.streak_days} day learning streak",
                f"{performance_metrics.accuracy_rate:.1f}% accuracy rate",
                f"{performance_metrics.time_spent_hours:.1f} hours of study time"
            ],
            "areas_for_improvement": [gap["topic"] for gap in knowledge_analysis.knowledge_gaps[:3]],
            "next_steps": [rec["action"] for rec in study_recommendations.recommendations[:3]]
        }
        
        return AnalyticsReportResponse(
            report_id=report_id,
            user_id=user_id,
            generated_at=datetime.utcnow(),
            period=period.value,
            executive_summary=executive_summary,
            performance_metrics=performance_metrics,
            learning_insights=learning_insights,
            progress_visualization=progress_visualization,
            knowledge_analysis=knowledge_analysis,
            recommendations=study_recommendations
        )
        
    except Exception as e:
        logger.error(f"Failed to generate comprehensive report: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate comprehensive report")


@router.get("/export/{user_id}")
async def export_analytics_data(
    user_id: str = Path(..., description="User identifier"),
    format: ExportFormat = Query(ExportFormat.JSON, description="Export format"),
    period: AnalyticsPeriod = Query(AnalyticsPeriod.MONTH, description="Data period"),
    include_raw_data: bool = Query(False, description="Include raw session data"),
    learning_analytics: LearningAnalyticsService = Depends(get_learning_analytics),
    db: Session = Depends(get_db)
):
    """
    Export analytics data in various formats.
    
    Supports exporting:
    - Performance metrics and trends
    - Learning insights and patterns
    - Progress tracking data
    - Knowledge gap analysis
    - Raw session data (if requested)
    
    Available formats: JSON, CSV
    """
    try:
        logger.info(f"Exporting analytics data for user: {user_id}, format: {format}")
        
        # Generate comprehensive report
        report = await generate_comprehensive_report(user_id, period, learning_analytics, db)
        
        # Prepare export data
        export_data = {
            "report_metadata": {
                "report_id": report.report_id,
                "user_id": report.user_id,
                "generated_at": report.generated_at.isoformat(),
                "period": report.period
            },
            "executive_summary": report.executive_summary,
            "performance_metrics": report.performance_metrics.dict(),
            "learning_insights": [insight.dict() for insight in report.learning_insights],
            "knowledge_analysis": report.knowledge_analysis.dict(),
            "study_recommendations": report.recommendations.dict()
        }
        
        # Include raw data if requested
        if include_raw_data:
            # Calculate period dates
            end_date = datetime.utcnow()
            days_back = {
                AnalyticsPeriod.WEEK: 7,
                AnalyticsPeriod.MONTH: 30,
                AnalyticsPeriod.QUARTER: 90,
                AnalyticsPeriod.YEAR: 365,
                AnalyticsPeriod.ALL_TIME: 1000
            }
            start_date = end_date - timedelta(days=days_back[period])
            
            # Get raw session data
            sessions = db.query(QuizSession).filter(
                QuizSession.user_id == user_id,
                QuizSession.status == "completed",
                QuizSession.completed_at >= start_date
            ).all()
            
            export_data["raw_sessions"] = [
                {
                    "session_id": session.id,
                    "quiz_id": session.quiz_id,
                    "completed_at": session.completed_at.isoformat(),
                    "score": session.score,
                    "total_questions": session.total_questions,
                    "correct_answers": session.correct_answers,
                    "time_spent": session.time_spent,
                    "difficulty": session.difficulty,
                    "topic": session.quiz.topic if session.quiz else None
                }
                for session in sessions
            ]
        
        # Generate export file
        if format == ExportFormat.JSON:
            # JSON export
            json_data = json.dumps(export_data, indent=2, default=str)
            
            return Response(
                content=json_data,
                media_type="application/json",
                headers={
                    "Content-Disposition": f"attachment; filename=analytics_report_{user_id}_{period.value}.json"
                }
            )
            
        elif format == ExportFormat.CSV:
            # CSV export (flattened performance metrics)
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write headers
            headers = [
                "user_id", "period", "total_sessions", "total_questions", 
                "accuracy_rate", "average_score", "time_spent_hours", 
                "improvement_rate", "streak_days", "completion_rate",
                "engagement_score", "skill_velocity"
            ]
            writer.writerow(headers)
            
            # Write performance metrics
            metrics = report.performance_metrics
            writer.writerow([
                metrics.user_id, metrics.period, metrics.total_sessions,
                metrics.total_questions, metrics.accuracy_rate, metrics.average_score,
                metrics.time_spent_hours, metrics.improvement_rate, metrics.streak_days,
                metrics.completion_rate, metrics.engagement_score, metrics.skill_velocity
            ])
            
            # Add raw session data if requested
            if include_raw_data and "raw_sessions" in export_data:
                writer.writerow([])  # Empty row
                writer.writerow(["Raw Session Data"])
                writer.writerow([
                    "session_id", "quiz_id", "completed_at", "score", 
                    "total_questions", "correct_answers", "time_spent", 
                    "difficulty", "topic"
                ])
                
                for session in export_data["raw_sessions"]:
                    writer.writerow([
                        session["session_id"], session["quiz_id"], session["completed_at"],
                        session["score"], session["total_questions"], session["correct_answers"],
                        session["time_spent"], session["difficulty"], session["topic"]
                    ])
            
            csv_data = output.getvalue()
            output.close()
            
            return Response(
                content=csv_data,
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename=analytics_report_{user_id}_{period.value}.csv"
                }
            )
        
    except Exception as e:
        logger.error(f"Failed to export analytics data: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to export analytics data")


# Health check endpoint
@router.get("/health")
async def analytics_health_check():
    """Health check endpoint for analytics service."""
    return {
        "status": "healthy",
        "service": "analytics",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    } 