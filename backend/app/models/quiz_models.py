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
    metadata = Column(JSON, default=dict)
    
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
    metadata = Column(JSON, default=dict)
    
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
    metadata = Column(JSON, default=dict) 