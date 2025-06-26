"""
Database models for quiz management and tracking.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Optional, Dict, Any
import uuid

from ..utils.database import Base


class Quiz(Base):
    """Model for storing quiz metadata and configuration."""
    __tablename__ = "quizzes"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False)
    description = Column(Text)
    topic = Column(String, nullable=False)
    difficulty_level = Column(String, nullable=False)  # beginner, intermediate, advanced
    question_types = Column(JSON)  # List of question types
    total_questions = Column(Integer, nullable=False)
    time_limit = Column(Integer)  # In minutes, optional
    passing_score = Column(Float, default=70.0)  # Percentage
    is_active = Column(Boolean, default=True)
    is_public = Column(Boolean, default=False)
    created_by = Column(String)  # User ID who created the quiz
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Configuration settings
    settings = Column(JSON, default=dict)  # Additional quiz settings
    
    # Relationships
    sessions = relationship("QuizSession", back_populates="quiz", cascade="all, delete-orphan")
    analytics = relationship("QuizAnalytics", back_populates="quiz", cascade="all, delete-orphan")


class QuizSession(Base):
    """Model for tracking individual quiz taking sessions."""
    __tablename__ = "quiz_sessions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    quiz_id = Column(String, ForeignKey("quizzes.id"), nullable=False)
    user_id = Column(String, nullable=True)  # Optional user tracking
    session_token = Column(String, unique=True, nullable=False)
    
    # Session status
    status = Column(String, default="in_progress")  # in_progress, completed, abandoned
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    time_spent = Column(Integer)  # Total time in seconds
    
    # Results
    total_questions = Column(Integer, nullable=False)
    answered_questions = Column(Integer, default=0)
    correct_answers = Column(Integer, default=0)
    score = Column(Float, default=0.0)  # Percentage
    passed = Column(Boolean, default=False)
    
    # Progress tracking
    current_question = Column(Integer, default=0)
    questions_data = Column(JSON)  # Generated questions for this session
    
    # Additional data
    extra_data = Column(JSON, default=dict)
    
    # Relationships
    quiz = relationship("Quiz", back_populates="sessions")
    responses = relationship("UserResponse", back_populates="session", cascade="all, delete-orphan")


class UserResponse(Base):
    """Model for storing individual question responses."""
    __tablename__ = "user_responses"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("quiz_sessions.id"), nullable=False)
    question_id = Column(String, nullable=False)  # From QuizQuestion.id
    
    # Question data (denormalized for analytics)
    question_type = Column(String, nullable=False)
    question_text = Column(Text, nullable=False)
    correct_answer = Column(JSON, nullable=False)
    topic = Column(String, nullable=False)
    difficulty = Column(String, nullable=False)
    
    # User response
    user_answer = Column(JSON)  # Can be string, list, etc.
    is_correct = Column(Boolean, nullable=False)
    time_taken = Column(Integer)  # Time in seconds
    attempted_at = Column(DateTime, default=datetime.utcnow)
    
    # Additional data
    extra_data = Column(JSON, default=dict)
    
    # Relationships
    session = relationship("QuizSession", back_populates="responses")


class QuizAnalytics(Base):
    """Model for storing quiz analytics and insights."""
    __tablename__ = "quiz_analytics"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    quiz_id = Column(String, ForeignKey("quizzes.id"), nullable=False)
    
    # Analytics data
    total_attempts = Column(Integer, default=0)
    total_completions = Column(Integer, default=0)
    average_score = Column(Float, default=0.0)
    average_time = Column(Float, default=0.0)  # In seconds
    completion_rate = Column(Float, default=0.0)  # Percentage
    
    # Question-level analytics
    question_stats = Column(JSON, default=dict)  # Statistics per question
    topic_performance = Column(JSON, default=dict)  # Performance by topic
    difficulty_distribution = Column(JSON, default=dict)  # Performance by difficulty
    
    # Time-based analytics
    last_updated = Column(DateTime, default=datetime.utcnow)
    analytics_period = Column(String, default="all_time")  # all_time, monthly, weekly
    
    # Relationships
    quiz = relationship("Quiz", back_populates="analytics")


class UserProgress(Base):
    """Model for tracking user learning progress across topics."""
    __tablename__ = "user_progress"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False)
    topic = Column(String, nullable=False)
    
    # Progress metrics
    total_quizzes_taken = Column(Integer, default=0)
    total_questions_answered = Column(Integer, default=0)
    correct_answers = Column(Integer, default=0)
    average_score = Column(Float, default=0.0)
    
    # Mastery tracking
    mastery_level = Column(String, default="novice")  # novice, learning, proficient, expert
    mastery_score = Column(Float, default=0.0)  # 0-100
    knowledge_gaps = Column(JSON, default=list)  # List of weak areas
    strengths = Column(JSON, default=list)  # List of strong areas
    
    # Adaptive learning
    suggested_difficulty = Column(String, default="beginner")
    next_review_date = Column(DateTime)
    spaced_repetition_interval = Column(Integer, default=1)  # Days
    
    # Timestamps
    first_attempt = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Additional data
    extra_data = Column(JSON, default=dict)


# New User Management Models

class User(Base):
    """Model for user accounts and basic information."""
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    
    # Profile information
    first_name = Column(String)
    last_name = Column(String)
    display_name = Column(String)
    bio = Column(Text)
    avatar_url = Column(String)
    
    # Account status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    email_verified = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime)
    
    # Relationships
    preferences = relationship("UserPreferences", back_populates="user", uselist=False, cascade="all, delete-orphan")
    achievements = relationship("UserAchievement", back_populates="user", cascade="all, delete-orphan")
    study_sessions = relationship("StudySession", back_populates="user", cascade="all, delete-orphan")


class UserPreferences(Base):
    """Model for user learning preferences and settings."""
    __tablename__ = "user_preferences"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    # Learning preferences
    preferred_topics = Column(JSON, default=list)  # List of preferred topics
    difficulty_preference = Column(String, default="adaptive")  # beginner, intermediate, advanced, adaptive
    question_types_preference = Column(JSON, default=list)  # Preferred question types
    daily_goal = Column(Integer, default=5)  # Questions per day
    session_length = Column(Integer, default=20)  # Minutes per session
    
    # Notification preferences
    email_notifications = Column(Boolean, default=True)
    push_notifications = Column(Boolean, default=True)
    reminder_frequency = Column(String, default="daily")  # daily, weekly, none
    
    # UI preferences
    theme = Column(String, default="light")  # light, dark, auto
    language = Column(String, default="en")
    timezone = Column(String, default="UTC")
    
    # Privacy settings
    profile_visibility = Column(String, default="public")  # public, friends, private
    share_progress = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="preferences")


class StudySession(Base):
    """Model for tracking individual study sessions."""
    __tablename__ = "study_sessions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    # Session data
    session_type = Column(String, default="quiz")  # quiz, review, practice
    topics_covered = Column(JSON, default=list)
    questions_answered = Column(Integer, default=0)
    correct_answers = Column(Integer, default=0)
    time_spent = Column(Integer, default=0)  # Seconds
    
    # Performance metrics
    accuracy = Column(Float, default=0.0)  # Percentage
    improvement = Column(Float, default=0.0)  # Compared to previous sessions
    
    # Timestamps
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Additional data
    extra_data = Column(JSON, default=dict)
    
    # Relationships
    user = relationship("User", back_populates="study_sessions")


class Achievement(Base):
    """Model for defining available achievements."""
    __tablename__ = "achievements"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String, nullable=False)  # streak, mastery, social, milestone
    icon_url = Column(String)
    
    # Requirements
    requirement_type = Column(String, nullable=False)  # quiz_count, streak_days, accuracy, mastery_topics
    requirement_value = Column(Integer, nullable=False)
    requirement_conditions = Column(JSON, default=dict)  # Additional conditions
    
    # Reward
    points = Column(Integer, default=0)
    badge_color = Column(String, default="bronze")  # bronze, silver, gold, platinum
    
    # Status
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user_achievements = relationship("UserAchievement", back_populates="achievement", cascade="all, delete-orphan")


class UserAchievement(Base):
    """Model for tracking user achievements and progress."""
    __tablename__ = "user_achievements"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    achievement_id = Column(String, ForeignKey("achievements.id"), nullable=False)
    
    # Progress tracking
    progress = Column(Float, default=0.0)  # Percentage progress toward achievement
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime)
    
    # Metadata
    extra_data = Column(JSON, default=dict)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="achievements")
    achievement = relationship("Achievement", back_populates="user_achievements")


class UserFollowing(Base):
    """Model for social following relationships."""
    __tablename__ = "user_following"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    follower_id = Column(String, ForeignKey("users.id"), nullable=False)
    following_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    # Status
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships - Note: These would create circular references, so we'll handle them in queries
    # follower = relationship("User", foreign_keys=[follower_id])
    # following = relationship("User", foreign_keys=[following_id])


class UserStats(Base):
    """Model for caching user statistics and performance metrics."""
    __tablename__ = "user_stats"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    # Overall statistics
    total_quizzes_taken = Column(Integer, default=0)
    total_questions_answered = Column(Integer, default=0)
    total_correct_answers = Column(Integer, default=0)
    total_time_spent = Column(Integer, default=0)  # Seconds
    
    # Performance metrics
    overall_accuracy = Column(Float, default=0.0)
    current_streak = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)
    total_points = Column(Integer, default=0)
    
    # Topic-based statistics
    topic_stats = Column(JSON, default=dict)  # Performance by topic
    difficulty_stats = Column(JSON, default=dict)  # Performance by difficulty
    
    # Time-based statistics
    daily_stats = Column(JSON, default=dict)  # Daily activity
    weekly_stats = Column(JSON, default=dict)  # Weekly activity
    monthly_stats = Column(JSON, default=dict)  # Monthly activity
    
    # Timestamps
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow) 