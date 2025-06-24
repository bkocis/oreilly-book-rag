"""
Learning Analytics Service

This service provides comprehensive learning analytics including:
- User performance and progress tracking
- Spaced repetition algorithms
- Learning path recommendations
- Knowledge gap identification
- Mastery tracking
- Performance reports
"""

import asyncio
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func, asc
from pydantic import BaseModel, Field
import structlog
from dataclasses import dataclass
import numpy as np
from collections import defaultdict

from ..models.quiz_models import Quiz, QuizSession, UserResponse, QuizAnalytics, UserProgress
from ..utils.database import get_db

logger = structlog.get_logger(__name__)


class LearningInsightType(str, Enum):
    """Types of learning insights."""
    KNOWLEDGE_GAP = "knowledge_gap"
    STRENGTH = "strength"
    IMPROVEMENT = "improvement"
    REGRESSION = "regression"
    MASTERY_ACHIEVED = "mastery_achieved"


class SpacedRepetitionLevel(str, Enum):
    """Spaced repetition interval levels."""
    LEVEL_1 = "level_1"  # 1 day
    LEVEL_2 = "level_2"  # 3 days
    LEVEL_3 = "level_3"  # 7 days
    LEVEL_4 = "level_4"  # 14 days
    LEVEL_5 = "level_5"  # 30 days
    MASTERED = "mastered"  # 90+ days


@dataclass
class LearningMetrics:
    """Data class for learning metrics."""
    total_sessions: int
    total_questions: int
    correct_answers: int
    accuracy_rate: float
    average_score: float
    time_spent_minutes: float
    streak_count: int
    mastery_progress: float
    knowledge_gaps: List[str]
    strengths: List[str]


@dataclass
class SpacedRepetitionItem:
    """Data class for spaced repetition items."""
    topic: str
    difficulty: str
    last_reviewed: datetime
    next_review: datetime
    repetition_level: SpacedRepetitionLevel
    success_rate: float
    review_count: int


@dataclass
class LearningRecommendation:
    """Data class for learning recommendations."""
    type: str
    topic: str
    difficulty: str
    priority: int
    reason: str
    estimated_time_minutes: int
    confidence_score: float


class LearningAnalyticsService:
    """Service for comprehensive learning analytics and recommendations."""
    
    def __init__(self, db_session: Session):
        """Initialize the learning analytics service."""
        self.db = db_session
        
        # Spaced repetition intervals (in days)
        self.sr_intervals = {
            SpacedRepetitionLevel.LEVEL_1: 1,
            SpacedRepetitionLevel.LEVEL_2: 3,
            SpacedRepetitionLevel.LEVEL_3: 7,
            SpacedRepetitionLevel.LEVEL_4: 14,
            SpacedRepetitionLevel.LEVEL_5: 30,
            SpacedRepetitionLevel.MASTERED: 90
        }
        
        logger.info("Learning analytics service initialized")
    
    # USER PERFORMANCE TRACKING
    
    async def track_user_performance(self, user_id: str, session_id: str) -> LearningMetrics:
        """
        Track and analyze user performance across all sessions.
        
        Args:
            user_id: User identifier
            session_id: Latest session identifier
            
        Returns:
            Comprehensive learning metrics
        """
        try:
            logger.info("Tracking user performance", user_id=user_id)
            
            # Get all user sessions
            sessions = self.db.query(QuizSession).filter(
                QuizSession.user_id == user_id,
                QuizSession.status == "completed"
            ).order_by(desc(QuizSession.completed_at)).all()
            
            if not sessions:
                return LearningMetrics(
                    total_sessions=0, total_questions=0, correct_answers=0,
                    accuracy_rate=0.0, average_score=0.0, time_spent_minutes=0.0,
                    streak_count=0, mastery_progress=0.0, knowledge_gaps=[], strengths=[]
                )
            
            # Calculate basic metrics
            total_sessions = len(sessions)
            total_questions = sum(s.total_questions for s in sessions)
            correct_answers = sum(s.correct_answers for s in sessions)
            accuracy_rate = (correct_answers / total_questions * 100) if total_questions > 0 else 0
            average_score = sum(s.score for s in sessions) / total_sessions
            time_spent_minutes = sum(s.time_spent or 0 for s in sessions) / 60
            
            # Calculate streak
            streak_count = await self._calculate_learning_streak(user_id)
            
            # Calculate mastery progress
            mastery_progress = await self._calculate_overall_mastery_progress(user_id)
            
            # Identify knowledge gaps and strengths
            knowledge_gaps, strengths = await self._identify_knowledge_gaps_and_strengths(user_id)
            
            metrics = LearningMetrics(
                total_sessions=total_sessions,
                total_questions=total_questions,
                correct_answers=correct_answers,
                accuracy_rate=accuracy_rate,
                average_score=average_score,
                time_spent_minutes=time_spent_minutes,
                streak_count=streak_count,
                mastery_progress=mastery_progress,
                knowledge_gaps=knowledge_gaps,
                strengths=strengths
            )
            
            # Update user progress records
            await self._update_comprehensive_user_progress(user_id, metrics)
            
            logger.info("User performance tracked successfully", user_id=user_id)
            return metrics
            
        except Exception as e:
            logger.error("Failed to track user performance", error=str(e), user_id=user_id)
            raise
    
    async def _calculate_learning_streak(self, user_id: str) -> int:
        """Calculate current learning streak in days."""
        try:
            # Get sessions from last 30 days ordered by date
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            sessions = self.db.query(QuizSession).filter(
                QuizSession.user_id == user_id,
                QuizSession.status == "completed",
                QuizSession.completed_at >= thirty_days_ago
            ).order_by(desc(QuizSession.completed_at)).all()
            
            if not sessions:
                return 0
            
            # Group sessions by date
            session_dates = set()
            for session in sessions:
                session_dates.add(session.completed_at.date())
            
            # Calculate consecutive days
            current_date = datetime.utcnow().date()
            streak = 0
            
            while current_date in session_dates:
                streak += 1
                current_date -= timedelta(days=1)
            
            return streak
            
        except Exception as e:
            logger.error("Failed to calculate learning streak", error=str(e))
            return 0
    
    # SPACED REPETITION ALGORITHMS
    
    async def get_spaced_repetition_items(self, user_id: str) -> List[SpacedRepetitionItem]:
        """
        Get items due for spaced repetition review.
        
        Args:
            user_id: User identifier
            
        Returns:
            List of items due for review
        """
        try:
            logger.info("Getting spaced repetition items", user_id=user_id)
            
            # Get user progress for all topics
            progress_records = self.db.query(UserProgress).filter(
                UserProgress.user_id == user_id
            ).all()
            
            sr_items = []
            current_time = datetime.utcnow()
            
            for progress in progress_records:
                # Check if review is due
                if progress.next_review_date and progress.next_review_date <= current_time:
                    # Calculate success rate
                    success_rate = (progress.correct_answers / progress.total_questions_answered 
                                  if progress.total_questions_answered > 0 else 0)
                    
                    # Determine repetition level
                    rep_level = self._get_repetition_level(progress.spaced_repetition_interval)
                    
                    sr_item = SpacedRepetitionItem(
                        topic=progress.topic,
                        difficulty=progress.suggested_difficulty,
                        last_reviewed=progress.last_updated,
                        next_review=progress.next_review_date,
                        repetition_level=rep_level,
                        success_rate=success_rate,
                        review_count=progress.total_quizzes_taken
                    )
                    sr_items.append(sr_item)
            
            # Sort by priority (overdue items first, then by success rate)
            sr_items.sort(key=lambda x: (x.next_review, -x.success_rate))
            
            logger.info("Spaced repetition items retrieved", count=len(sr_items))
            return sr_items
            
        except Exception as e:
            logger.error("Failed to get spaced repetition items", error=str(e))
            return []
    
    async def update_spaced_repetition(
        self, 
        user_id: str, 
        topic: str, 
        performance_score: float
    ) -> SpacedRepetitionItem:
        """
        Update spaced repetition schedule based on performance.
        
        Args:
            user_id: User identifier
            topic: Topic that was reviewed
            performance_score: Performance score (0-100)
            
        Returns:
            Updated spaced repetition item
        """
        try:
            # Get user progress for topic
            progress = self.db.query(UserProgress).filter(
                UserProgress.user_id == user_id,
                UserProgress.topic == topic
            ).first()
            
            if not progress:
                logger.warning("No progress record found for spaced repetition update")
                return None
            
            # Calculate new interval based on performance
            current_interval = progress.spaced_repetition_interval
            
            if performance_score >= 80:
                # Good performance - increase interval
                new_interval = min(current_interval * 2, 90)
            elif performance_score >= 60:
                # Moderate performance - maintain interval
                new_interval = current_interval
            else:
                # Poor performance - decrease interval
                new_interval = max(current_interval // 2, 1)
            
            # Update progress record
            progress.spaced_repetition_interval = new_interval
            progress.next_review_date = datetime.utcnow() + timedelta(days=new_interval)
            progress.last_updated = datetime.utcnow()
            
            self.db.commit()
            
            # Create return object
            rep_level = self._get_repetition_level(new_interval)
            success_rate = (progress.correct_answers / progress.total_questions_answered 
                          if progress.total_questions_answered > 0 else 0)
            
            sr_item = SpacedRepetitionItem(
                topic=topic,
                difficulty=progress.suggested_difficulty,
                last_reviewed=datetime.utcnow(),
                next_review=progress.next_review_date,
                repetition_level=rep_level,
                success_rate=success_rate,
                review_count=progress.total_quizzes_taken
            )
            
            logger.info("Spaced repetition updated", topic=topic, new_interval=new_interval)
            return sr_item
            
        except Exception as e:
            logger.error("Failed to update spaced repetition", error=str(e))
            self.db.rollback()
            raise
    
    def _get_repetition_level(self, interval_days: int) -> SpacedRepetitionLevel:
        """Get repetition level based on interval."""
        if interval_days <= 1:
            return SpacedRepetitionLevel.LEVEL_1
        elif interval_days <= 3:
            return SpacedRepetitionLevel.LEVEL_2
        elif interval_days <= 7:
            return SpacedRepetitionLevel.LEVEL_3
        elif interval_days <= 14:
            return SpacedRepetitionLevel.LEVEL_4
        elif interval_days <= 30:
            return SpacedRepetitionLevel.LEVEL_5
        else:
            return SpacedRepetitionLevel.MASTERED
    
    # LEARNING PATH RECOMMENDATIONS
    
    async def generate_learning_recommendations(
        self, 
        user_id: str, 
        max_recommendations: int = 5
    ) -> List[LearningRecommendation]:
        """
        Generate personalized learning path recommendations.
        
        Args:
            user_id: User identifier
            max_recommendations: Maximum number of recommendations
            
        Returns:
            List of learning recommendations
        """
        try:
            logger.info("Generating learning recommendations", user_id=user_id)
            
            recommendations = []
            
            # Get user progress and performance data
            progress_records = self.db.query(UserProgress).filter(
                UserProgress.user_id == user_id
            ).all()
            
            if not progress_records:
                # New user - recommend beginner topics
                return await self._get_beginner_recommendations()
            
            # Analyze performance patterns
            for progress in progress_records:
                # Check for knowledge gaps
                if progress.average_score < 70:
                    recommendations.append(LearningRecommendation(
                        type="knowledge_gap",
                        topic=progress.topic,
                        difficulty=progress.suggested_difficulty,
                        priority=1,
                        reason=f"Low performance (${progress.average_score:.1f}%) - needs reinforcement",
                        estimated_time_minutes=20,
                        confidence_score=0.9
                    ))
                
                # Check for spaced repetition
                if (progress.next_review_date and 
                    progress.next_review_date <= datetime.utcnow()):
                    recommendations.append(LearningRecommendation(
                        type="spaced_repetition",
                        topic=progress.topic,
                        difficulty=progress.suggested_difficulty,
                        priority=2,
                        reason="Due for spaced repetition review",
                        estimated_time_minutes=15,
                        confidence_score=0.8
                    ))
                
                # Check for progression opportunities
                if (progress.mastery_score >= 80 and 
                    progress.suggested_difficulty != "advanced"):
                    next_difficulty = self._get_next_difficulty(progress.suggested_difficulty)
                    if next_difficulty:
                        recommendations.append(LearningRecommendation(
                            type="progression",
                            topic=progress.topic,
                            difficulty=next_difficulty,
                            priority=3,
                            reason=f"Ready for ${next_difficulty} level",
                            estimated_time_minutes=25,
                            confidence_score=0.7
                        ))
            
            # Add new topic recommendations
            new_topics = await self._get_new_topic_recommendations(user_id)
            recommendations.extend(new_topics)
            
            # Sort by priority and confidence
            recommendations.sort(key=lambda x: (x.priority, -x.confidence_score))
            
            logger.info("Learning recommendations generated", count=len(recommendations))
            return recommendations[:max_recommendations]
            
        except Exception as e:
            logger.error("Failed to generate learning recommendations", error=str(e))
            return []
    
    # KNOWLEDGE GAP IDENTIFICATION
    
    async def identify_knowledge_gaps(self, user_id: str) -> Dict[str, Any]:
        """
        Identify specific knowledge gaps and learning needs.
        
        Args:
            user_id: User identifier
            
        Returns:
            Detailed knowledge gap analysis
        """
        try:
            logger.info("Identifying knowledge gaps", user_id=user_id)
            
            # Get user responses for detailed analysis
            responses = self.db.query(UserResponse).join(QuizSession).filter(
                QuizSession.user_id == user_id,
                QuizSession.status == "completed"
            ).all()
            
            if not responses:
                return {"gaps": [], "recommendations": [], "confidence": 0.0}
            
            # Analyze by topic and difficulty
            topic_performance = defaultdict(lambda: {"total": 0, "correct": 0, "questions": []})
            
            for response in responses:
                topic = response.topic
                topic_performance[topic]["total"] += 1
                if response.is_correct:
                    topic_performance[topic]["correct"] += 1
                else:
                    topic_performance[topic]["questions"].append({
                        "question": response.question_text,
                        "difficulty": response.difficulty,
                        "type": response.question_type
                    })
            
            # Identify gaps (performance < 70%)
            gaps = []
            for topic, data in topic_performance.items():
                accuracy = (data["correct"] / data["total"]) * 100
                if accuracy < 70:
                    gaps.append({
                        "topic": topic,
                        "accuracy": accuracy,
                        "total_questions": data["total"],
                        "weak_areas": data["questions"][:5],  # Top 5 missed questions
                        "severity": "high" if accuracy < 50 else "medium"
                    })
            
            # Generate targeted recommendations
            recommendations = []
            for gap in gaps:
                recommendations.append({
                    "action": "focused_practice",
                    "topic": gap["topic"],
                    "target_accuracy": 80,
                    "estimated_sessions": max(1, int((80 - gap["accuracy"]) / 10))
                })
            
            confidence = min(1.0, len(responses) / 50)  # Higher confidence with more data
            
            result = {
                "gaps": gaps,
                "recommendations": recommendations,
                "total_responses": len(responses),
                "confidence": confidence,
                "analysis_date": datetime.utcnow().isoformat()
            }
            
            logger.info("Knowledge gaps identified", gaps_count=len(gaps))
            return result
            
        except Exception as e:
            logger.error("Failed to identify knowledge gaps", error=str(e))
            return {"gaps": [], "recommendations": [], "confidence": 0.0}
    
    # MASTERY TRACKING
    
    async def track_mastery_progress(self, user_id: str) -> Dict[str, Any]:
        """
        Track mastery progress across all topics.
        
        Args:
            user_id: User identifier
            
        Returns:
            Comprehensive mastery tracking data
        """
        try:
            logger.info("Tracking mastery progress", user_id=user_id)
            
            progress_records = self.db.query(UserProgress).filter(
                UserProgress.user_id == user_id
            ).all()
            
            if not progress_records:
                return {"mastery_levels": {}, "overall_progress": 0.0, "achievements": []}
            
            mastery_levels = {}
            total_mastery_score = 0
            achievements = []
            
            for progress in progress_records:
                # Update mastery calculations
                mastery_score = await self._calculate_detailed_mastery_score(progress)
                mastery_level = self._determine_mastery_level(mastery_score)
                
                mastery_levels[progress.topic] = {
                    "level": mastery_level,
                    "score": mastery_score,
                    "accuracy": progress.average_score,
                    "sessions": progress.total_quizzes_taken,
                    "last_updated": progress.last_updated.isoformat()
                }
                
                total_mastery_score += mastery_score
                
                # Check for achievements
                if mastery_level == "expert" and "expert_" + progress.topic not in [a["id"] for a in achievements]:
                    achievements.append({
                        "id": "expert_" + progress.topic,
                        "title": f"Expert in ${progress.topic}",
                        "description": f"Achieved expert level mastery in ${progress.topic}",
                        "earned_at": datetime.utcnow().isoformat()
                    })
            
            overall_progress = total_mastery_score / len(progress_records) if progress_records else 0
            
            result = {
                "mastery_levels": mastery_levels,
                "overall_progress": overall_progress,
                "achievements": achievements,
                "total_topics": len(progress_records),
                "expert_topics": len([m for m in mastery_levels.values() if m["level"] == "expert"]),
                "analysis_date": datetime.utcnow().isoformat()
            }
            
            logger.info("Mastery progress tracked", overall_progress=overall_progress)
            return result
            
        except Exception as e:
            logger.error("Failed to track mastery progress", error=str(e))
            return {"mastery_levels": {}, "overall_progress": 0.0, "achievements": []}
    
    # PERFORMANCE REPORTS
    
    async def generate_performance_report(
        self, 
        user_id: str, 
        period_days: int = 30
    ) -> Dict[str, Any]:
        """
        Generate comprehensive performance report.
        
        Args:
            user_id: User identifier
            period_days: Analysis period in days
            
        Returns:
            Detailed performance report
        """
        try:
            logger.info("Generating performance report", user_id=user_id, period=period_days)
            
            start_date = datetime.utcnow() - timedelta(days=period_days)
            
            # Get sessions in period
            sessions = self.db.query(QuizSession).filter(
                QuizSession.user_id == user_id,
                QuizSession.status == "completed",
                QuizSession.completed_at >= start_date
            ).order_by(QuizSession.completed_at).all()
            
            if not sessions:
                return {"message": "No activity in selected period", "period_days": period_days}
            
            # Calculate comprehensive metrics
            total_sessions = len(sessions)
            total_time_minutes = sum(s.time_spent or 0 for s in sessions) / 60
            total_questions = sum(s.total_questions for s in sessions)
            total_correct = sum(s.correct_answers for s in sessions)
            
            # Performance trends
            daily_performance = {}
            for session in sessions:
                day = session.completed_at.date().isoformat()
                if day not in daily_performance:
                    daily_performance[day] = {"sessions": 0, "accuracy": 0, "scores": []}
                daily_performance[day]["sessions"] += 1
                daily_performance[day]["scores"].append(session.score)
            
            # Calculate daily averages
            for day_data in daily_performance.values():
                day_data["accuracy"] = sum(day_data["scores"]) / len(day_data["scores"])
            
            # Topic performance
            topic_performance = defaultdict(lambda: {"sessions": 0, "total_questions": 0, "correct": 0})
            for session in sessions:
                quiz = self.db.query(Quiz).filter(Quiz.id == session.quiz_id).first()
                if quiz:
                    topic = quiz.topic
                    topic_performance[topic]["sessions"] += 1
                    topic_performance[topic]["total_questions"] += session.total_questions
                    topic_performance[topic]["correct"] += session.correct_answers
            
            # Learning insights
            insights = await self._generate_performance_insights(sessions)
            
            report = {
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": datetime.utcnow().isoformat(),
                    "days": period_days
                },
                "summary": {
                    "total_sessions": total_sessions,
                    "total_questions": total_questions,
                    "overall_accuracy": (total_correct / total_questions * 100) if total_questions > 0 else 0,
                    "average_score": sum(s.score for s in sessions) / total_sessions,
                    "total_time_minutes": total_time_minutes,
                    "average_time_per_session": total_time_minutes / total_sessions if total_sessions > 0 else 0
                },
                "trends": {
                    "daily_performance": daily_performance,
                    "improvement_rate": await self._calculate_improvement_rate(sessions)
                },
                "topic_breakdown": dict(topic_performance),
                "insights": insights,
                "generated_at": datetime.utcnow().isoformat()
            }
            
            logger.info("Performance report generated successfully")
            return report
            
        except Exception as e:
            logger.error("Failed to generate performance report", error=str(e))
            return {"error": "Failed to generate report"}
    
    # HELPER METHODS
    
    async def _calculate_overall_mastery_progress(self, user_id: str) -> float:
        """Calculate overall mastery progress across all topics."""
        progress_records = self.db.query(UserProgress).filter(
            UserProgress.user_id == user_id
        ).all()
        
        if not progress_records:
            return 0.0
        
        total_mastery = sum(record.mastery_score for record in progress_records)
        return total_mastery / len(progress_records)
    
    async def _identify_knowledge_gaps_and_strengths(self, user_id: str) -> Tuple[List[str], List[str]]:
        """Identify knowledge gaps and strengths."""
        progress_records = self.db.query(UserProgress).filter(
            UserProgress.user_id == user_id
        ).all()
        
        gaps = []
        strengths = []
        
        for record in progress_records:
            if record.average_score < 70:
                gaps.append(record.topic)
            elif record.average_score >= 85:
                strengths.append(record.topic)
        
        return gaps, strengths
    
    async def _update_comprehensive_user_progress(self, user_id: str, metrics: LearningMetrics):
        """Update comprehensive user progress based on metrics."""
        # This would update various user progress records
        # Implementation depends on specific requirements
        pass
    
    def _determine_mastery_level(self, mastery_score: float) -> str:
        """Determine mastery level based on score."""
        if mastery_score >= 90:
            return "expert"
        elif mastery_score >= 75:
            return "proficient"
        elif mastery_score >= 50:
            return "learning"
        else:
            return "novice"
    
    async def _calculate_detailed_mastery_score(self, progress: UserProgress) -> float:
        """Calculate detailed mastery score considering multiple factors."""
        # Base score from accuracy
        accuracy_score = progress.average_score
        
        # Consistency bonus (more sessions = more consistent)
        consistency_bonus = min(10, progress.total_quizzes_taken * 0.5)
        
        # Recency bonus (recent activity is good)
        days_since_last = (datetime.utcnow() - progress.last_updated).days
        recency_bonus = max(0, 10 - days_since_last * 0.5)
        
        total_score = accuracy_score + consistency_bonus + recency_bonus
        return min(100, total_score)
    
    async def _generate_performance_insights(self, sessions: List[QuizSession]) -> List[Dict[str, Any]]:
        """Generate performance insights from sessions."""
        insights = []
        
        if len(sessions) >= 2:
            # Compare first half vs second half
            mid_point = len(sessions) // 2
            first_half_avg = sum(s.score for s in sessions[:mid_point]) / mid_point
            second_half_avg = sum(s.score for s in sessions[mid_point:]) / (len(sessions) - mid_point)
            
            if second_half_avg > first_half_avg + 5:
                insights.append({
                    "type": "improvement",
                    "message": f"Performance improved by {second_half_avg - first_half_avg:.1f}% over time",
                    "confidence": 0.8
                })
            elif first_half_avg > second_half_avg + 5:
                insights.append({
                    "type": "regression",
                    "message": f"Performance declined by {first_half_avg - second_half_avg:.1f}% recently",
                    "confidence": 0.8
                })
        
        return insights
    
    async def _calculate_improvement_rate(self, sessions: List[QuizSession]) -> float:
        """Calculate improvement rate over sessions."""
        if len(sessions) < 2:
            return 0.0
        
        # Simple linear regression on scores
        scores = [s.score for s in sessions]
        x = list(range(len(scores)))
        
        # Calculate slope
        n = len(scores)
        sum_x = sum(x)
        sum_y = sum(scores)
        sum_xy = sum(x[i] * scores[i] for i in range(n))
        sum_x2 = sum(xi * xi for xi in x)
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        return slope
    
    async def _get_beginner_recommendations(self) -> List[LearningRecommendation]:
        """Get recommendations for new users."""
        # This would return beginner-friendly topics
        return [
            LearningRecommendation(
                type="beginner",
                topic="fundamentals",
                difficulty="beginner",
                priority=1,
                reason="Great starting point for new learners",
                estimated_time_minutes=15,
                confidence_score=1.0
            )
        ]
    
    def _get_next_difficulty(self, current_difficulty: str) -> Optional[str]:
        """Get next difficulty level."""
        difficulty_progression = {
            "beginner": "intermediate",
            "intermediate": "advanced",
            "advanced": None
        }
        return difficulty_progression.get(current_difficulty)
    
    async def _get_new_topic_recommendations(self, user_id: str) -> List[LearningRecommendation]:
        """Get recommendations for new topics to explore."""
        # This would analyze user's current topics and suggest related ones
        return []


def get_learning_analytics(db_session: Session) -> LearningAnalyticsService:
    """Factory function to create learning analytics service."""
    return LearningAnalyticsService(db_session) 