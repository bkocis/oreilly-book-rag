"""
User Management API endpoints for the O'Reilly RAG Quiz system.

This module provides endpoints for:
- User registration and authentication
- User profile management
- Learning preferences
- Study history tracking
- Achievement system
- Social features (following, leaderboards)
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, Query, Path, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from pydantic import BaseModel, Field, EmailStr
from passlib.context import CryptContext
from jose import JWTError, jwt

from ..models.quiz_models import (
    User, UserPreferences, StudySession, Achievement, UserAchievement, 
    UserFollowing, UserStats, UserProgress
)
from ..utils.database import get_db
from config import settings

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Settings
SECRET_KEY = settings.secret_key if hasattr(settings, 'secret_key') else "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


# Utility functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get the current authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user


# Request/Response Models
class UserRegistrationRequest(BaseModel):
    """Request model for user registration."""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    display_name: Optional[str] = None


class UserLoginRequest(BaseModel):
    """Request model for user login."""
    username: str
    password: str


class UserProfileUpdateRequest(BaseModel):
    """Request model for updating user profile."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    display_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None


class UserPreferencesRequest(BaseModel):
    """Request model for updating user preferences."""
    preferred_topics: Optional[List[str]] = None
    difficulty_preference: Optional[str] = None
    question_types_preference: Optional[List[str]] = None
    daily_goal: Optional[int] = None
    session_length: Optional[int] = None
    email_notifications: Optional[bool] = None
    push_notifications: Optional[bool] = None
    reminder_frequency: Optional[str] = None
    theme: Optional[str] = None
    language: Optional[str] = None
    timezone: Optional[str] = None
    profile_visibility: Optional[str] = None
    share_progress: Optional[bool] = None


class StudySessionRequest(BaseModel):
    """Request model for creating study sessions."""
    session_type: Optional[str] = "quiz"
    topics_covered: Optional[List[str]] = None
    questions_answered: Optional[int] = 0
    correct_answers: Optional[int] = 0
    time_spent: Optional[int] = 0
    extra_data: Optional[Dict[str, Any]] = None


# Response Models
class UserResponse(BaseModel):
    """Response model for user data."""
    id: str
    username: str
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    display_name: Optional[str]
    bio: Optional[str]
    avatar_url: Optional[str]
    is_active: bool
    is_verified: bool
    email_verified: bool
    created_at: datetime
    last_login: Optional[datetime]

    class Config:
        from_attributes = True


class UserPreferencesResponse(BaseModel):
    """Response model for user preferences."""
    id: str
    user_id: str
    preferred_topics: List[str]
    difficulty_preference: str
    question_types_preference: List[str]
    daily_goal: int
    session_length: int
    email_notifications: bool
    push_notifications: bool
    reminder_frequency: str
    theme: str
    language: str
    timezone: str
    profile_visibility: str
    share_progress: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class StudySessionResponse(BaseModel):
    """Response model for study sessions."""
    id: str
    user_id: str
    session_type: str
    topics_covered: List[str]
    questions_answered: int
    correct_answers: int
    time_spent: int
    accuracy: float
    improvement: float
    started_at: datetime
    ended_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class AchievementResponse(BaseModel):
    """Response model for achievements."""
    id: str
    name: str
    description: str
    category: str
    icon_url: Optional[str]
    requirement_type: str
    requirement_value: int
    points: int
    badge_color: str
    is_active: bool

    class Config:
        from_attributes = True


class UserAchievementResponse(BaseModel):
    """Response model for user achievements."""
    id: str
    user_id: str
    achievement: AchievementResponse
    progress: float
    is_completed: bool
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserStatsResponse(BaseModel):
    """Response model for user statistics."""
    id: str
    user_id: str
    total_quizzes_taken: int
    total_questions_answered: int
    total_correct_answers: int
    total_time_spent: int
    overall_accuracy: float
    current_streak: int
    longest_streak: int
    total_points: int
    topic_stats: Dict[str, Any]
    difficulty_stats: Dict[str, Any]
    last_updated: datetime
    last_activity: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Response model for authentication tokens."""
    access_token: str
    token_type: str
    expires_in: int
    user: UserResponse


# Authentication Endpoints

@router.post("/register", response_model=TokenResponse)
async def register_user(
    user_request: UserRegistrationRequest,
    db: Session = Depends(get_db)
):
    """Register a new user account."""
    try:
        # Check if username or email already exists
        existing_user = db.query(User).filter(
            or_(User.username == user_request.username, 
                User.email == user_request.email)
        ).first()
        
        if existing_user:
            if existing_user.username == user_request.username:
                raise HTTPException(
                    status_code=400,
                    detail="Username already registered"
                )
            else:
                raise HTTPException(
                    status_code=400,
                    detail="Email already registered"
                )
        
        # Create new user
        hashed_password = get_password_hash(user_request.password)
        user = User(
            username=user_request.username,
            email=user_request.email,
            hashed_password=hashed_password,
            first_name=user_request.first_name,
            last_name=user_request.last_name,
            display_name=user_request.display_name or user_request.username
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Create default preferences
        preferences = UserPreferences(user_id=user.id)
        db.add(preferences)
        
        # Create user stats
        stats = UserStats(user_id=user.id)
        db.add(stats)
        
        db.commit()
        
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.id}, expires_delta=access_token_expires
        )
        
        logger.info(f"New user registered: {user.username}")
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserResponse.from_orm(user)
        )
        
    except Exception as e:
        logger.error(f"User registration failed: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/login", response_model=TokenResponse)
async def login_user(
    user_request: UserLoginRequest,
    db: Session = Depends(get_db)
):
    """Authenticate a user and return access token."""
    try:
        # Find user by username or email
        user = db.query(User).filter(
            or_(User.username == user_request.username,
                User.email == user_request.username)
        ).first()
        
        if not user or not verify_password(user_request.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is disabled"
            )
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.commit()
        
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.id}, expires_delta=access_token_expires
        )
        
        logger.info(f"User logged in: {user.username}")
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserResponse.from_orm(user)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User login failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# User Profile Endpoints

@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """Get current user's profile."""
    return UserResponse.from_orm(current_user)


@router.put("/me", response_model=UserResponse)
async def update_user_profile(
    profile_update: UserProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user's profile."""
    try:
        # Update profile fields
        for field, value in profile_update.dict(exclude_unset=True).items():
            setattr(current_user, field, value)
        
        current_user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(current_user)
        
        logger.info(f"User profile updated: {current_user.username}")
        return UserResponse.from_orm(current_user)
        
    except Exception as e:
        logger.error(f"Profile update failed: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{user_id}", response_model=UserResponse)
async def get_user_profile(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a user's profile by ID."""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check privacy settings
        preferences = db.query(UserPreferences).filter(
            UserPreferences.user_id == user_id
        ).first()
        
        if preferences and preferences.profile_visibility == "private":
            if current_user.id != user_id:
                raise HTTPException(status_code=403, detail="Profile is private")
        
        return UserResponse.from_orm(user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user profile failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# User Preferences Endpoints

@router.get("/me/preferences", response_model=UserPreferencesResponse)
async def get_user_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's preferences."""
    try:
        preferences = db.query(UserPreferences).filter(
            UserPreferences.user_id == current_user.id
        ).first()
        
        if not preferences:
            # Create default preferences if they don't exist
            preferences = UserPreferences(user_id=current_user.id)
            db.add(preferences)
            db.commit()
            db.refresh(preferences)
        
        return UserPreferencesResponse.from_orm(preferences)
        
    except Exception as e:
        logger.error(f"Get preferences failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/me/preferences", response_model=UserPreferencesResponse)
async def update_user_preferences(
    preferences_update: UserPreferencesRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user's preferences."""
    try:
        preferences = db.query(UserPreferences).filter(
            UserPreferences.user_id == current_user.id
        ).first()
        
        if not preferences:
            preferences = UserPreferences(user_id=current_user.id)
            db.add(preferences)
        
        # Update preference fields
        for field, value in preferences_update.dict(exclude_unset=True).items():
            setattr(preferences, field, value)
        
        preferences.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(preferences)
        
        logger.info(f"User preferences updated: {current_user.username}")
        return UserPreferencesResponse.from_orm(preferences)
        
    except Exception as e:
        logger.error(f"Update preferences failed: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# Study History Endpoints

@router.get("/me/study-sessions", response_model=List[StudySessionResponse])
async def get_study_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session_type: Optional[str] = Query(None)
):
    """Get current user's study sessions."""
    try:
        query = db.query(StudySession).filter(
            StudySession.user_id == current_user.id
        )
        
        if session_type:
            query = query.filter(StudySession.session_type == session_type)
        
        sessions = query.order_by(StudySession.created_at.desc()).offset(offset).limit(limit).all()
        
        return [StudySessionResponse.from_orm(session) for session in sessions]
        
    except Exception as e:
        logger.error(f"Get study sessions failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/me/study-sessions", response_model=StudySessionResponse)
async def create_study_session(
    session_request: StudySessionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new study session."""
    try:
        # Calculate accuracy
        accuracy = 0.0
        if session_request.questions_answered and session_request.questions_answered > 0:
            accuracy = (session_request.correct_answers / session_request.questions_answered) * 100
        
        session = StudySession(
            user_id=current_user.id,
            session_type=session_request.session_type,
            topics_covered=session_request.topics_covered or [],
            questions_answered=session_request.questions_answered,
            correct_answers=session_request.correct_answers,
            time_spent=session_request.time_spent,
            accuracy=accuracy,
            ended_at=datetime.utcnow(),
            extra_data=session_request.extra_data or {}
        )
        
        db.add(session)
        db.commit()
        db.refresh(session)
        
        # Update user statistics
        await update_user_statistics(current_user.id, session, db)
        
        logger.info(f"Study session created for user: {current_user.username}")
        return StudySessionResponse.from_orm(session)
        
    except Exception as e:
        logger.error(f"Create study session failed: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# Achievement Endpoints

@router.get("/achievements", response_model=List[AchievementResponse])
async def get_all_achievements(
    db: Session = Depends(get_db),
    category: Optional[str] = Query(None)
):
    """Get all available achievements."""
    try:
        query = db.query(Achievement).filter(Achievement.is_active == True)
        
        if category:
            query = query.filter(Achievement.category == category)
        
        achievements = query.order_by(Achievement.points.asc()).all()
        
        return [AchievementResponse.from_orm(achievement) for achievement in achievements]
        
    except Exception as e:
        logger.error(f"Get achievements failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/me/achievements", response_model=List[UserAchievementResponse])
async def get_user_achievements(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    completed_only: bool = Query(False)
):
    """Get current user's achievements."""
    try:
        query = db.query(UserAchievement).filter(
            UserAchievement.user_id == current_user.id
        ).join(Achievement)
        
        if completed_only:
            query = query.filter(UserAchievement.is_completed == True)
        
        user_achievements = query.order_by(UserAchievement.updated_at.desc()).all()
        
        result = []
        for ua in user_achievements:
            achievement_data = AchievementResponse.from_orm(ua.achievement)
            result.append(UserAchievementResponse(
                id=ua.id,
                user_id=ua.user_id,
                achievement=achievement_data,
                progress=ua.progress,
                is_completed=ua.is_completed,
                completed_at=ua.completed_at,
                created_at=ua.created_at,
                updated_at=ua.updated_at
            ))
        
        return result
        
    except Exception as e:
        logger.error(f"Get user achievements failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Statistics Endpoints

@router.get("/me/stats", response_model=UserStatsResponse)
async def get_user_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's statistics."""
    try:
        stats = db.query(UserStats).filter(
            UserStats.user_id == current_user.id
        ).first()
        
        if not stats:
            # Create default stats if they don't exist
            stats = UserStats(user_id=current_user.id)
            db.add(stats)
            db.commit()
            db.refresh(stats)
        
        return UserStatsResponse.from_orm(stats)
        
    except Exception as e:
        logger.error(f"Get user statistics failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Social Features Endpoints

@router.post("/follow/{user_id}")
async def follow_user(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Follow another user."""
    try:
        if current_user.id == user_id:
            raise HTTPException(status_code=400, detail="Cannot follow yourself")
        
        # Check if user exists
        target_user = db.query(User).filter(User.id == user_id).first()
        if not target_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if already following
        existing_follow = db.query(UserFollowing).filter(
            and_(
                UserFollowing.follower_id == current_user.id,
                UserFollowing.following_id == user_id
            )
        ).first()
        
        if existing_follow:
            if existing_follow.is_active:
                raise HTTPException(status_code=400, detail="Already following this user")
            else:
                existing_follow.is_active = True
                existing_follow.created_at = datetime.utcnow()
        else:
            follow = UserFollowing(
                follower_id=current_user.id,
                following_id=user_id
            )
            db.add(follow)
        
        db.commit()
        
        logger.info(f"User {current_user.username} followed {target_user.username}")
        return {"message": f"Successfully followed {target_user.display_name or target_user.username}"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Follow user failed: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/unfollow/{user_id}")
async def unfollow_user(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Unfollow another user."""
    try:
        follow = db.query(UserFollowing).filter(
            and_(
                UserFollowing.follower_id == current_user.id,
                UserFollowing.following_id == user_id,
                UserFollowing.is_active == True
            )
        ).first()
        
        if not follow:
            raise HTTPException(status_code=404, detail="Not following this user")
        
        follow.is_active = False
        db.commit()
        
        target_user = db.query(User).filter(User.id == user_id).first()
        logger.info(f"User {current_user.username} unfollowed {target_user.username if target_user else user_id}")
        
        return {"message": "Successfully unfollowed user"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unfollow user failed: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/me/following", response_model=List[UserResponse])
async def get_following(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """Get users that current user is following."""
    try:
        following_users = db.query(User).join(
            UserFollowing, UserFollowing.following_id == User.id
        ).filter(
            and_(
                UserFollowing.follower_id == current_user.id,
                UserFollowing.is_active == True
            )
        ).offset(offset).limit(limit).all()
        
        return [UserResponse.from_orm(user) for user in following_users]
        
    except Exception as e:
        logger.error(f"Get following failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/me/followers", response_model=List[UserResponse])
async def get_followers(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """Get users that are following current user."""
    try:
        followers = db.query(User).join(
            UserFollowing, UserFollowing.follower_id == User.id
        ).filter(
            and_(
                UserFollowing.following_id == current_user.id,
                UserFollowing.is_active == True
            )
        ).offset(offset).limit(limit).all()
        
        return [UserResponse.from_orm(user) for user in followers]
        
    except Exception as e:
        logger.error(f"Get followers failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/leaderboard", response_model=List[Dict[str, Any]])
async def get_leaderboard(
    db: Session = Depends(get_db),
    limit: int = Query(10, ge=1, le=100),
    timeframe: str = Query("all_time", regex="^(all_time|monthly|weekly)$")
):
    """Get leaderboard of top users."""
    try:
        # Get top users by total points
        top_users = db.query(
            User.username,
            User.display_name,
            User.avatar_url,
            UserStats.total_points,
            UserStats.overall_accuracy,
            UserStats.current_streak,
            UserStats.total_quizzes_taken
        ).join(UserStats).filter(
            User.is_active == True
        ).order_by(
            UserStats.total_points.desc()
        ).limit(limit).all()
        
        leaderboard = []
        for i, user in enumerate(top_users, 1):
            leaderboard.append({
                "rank": i,
                "username": user.username,
                "display_name": user.display_name,
                "avatar_url": user.avatar_url,
                "total_points": user.total_points,
                "accuracy": user.overall_accuracy,
                "streak": user.current_streak,
                "quizzes_taken": user.total_quizzes_taken
            })
        
        return leaderboard
        
    except Exception as e:
        logger.error(f"Get leaderboard failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Helper Functions

async def update_user_statistics(user_id: str, session: StudySession, db: Session):
    """Update user statistics after a study session."""
    try:
        stats = db.query(UserStats).filter(UserStats.user_id == user_id).first()
        if not stats:
            stats = UserStats(user_id=user_id)
            db.add(stats)
        
        # Update basic stats
        stats.total_quizzes_taken += 1
        stats.total_questions_answered += session.questions_answered
        stats.total_correct_answers += session.correct_answers
        stats.total_time_spent += session.time_spent
        
        # Calculate overall accuracy
        if stats.total_questions_answered > 0:
            stats.overall_accuracy = (stats.total_correct_answers / stats.total_questions_answered) * 100
        
        # Update streak (simplified logic)
        if session.accuracy >= 70:  # Passing threshold
            stats.current_streak += 1
            if stats.current_streak > stats.longest_streak:
                stats.longest_streak = stats.current_streak
        else:
            stats.current_streak = 0
        
        # Update topic stats
        if not stats.topic_stats:
            stats.topic_stats = {}
        
        for topic in session.topics_covered:
            if topic not in stats.topic_stats:
                stats.topic_stats[topic] = {
                    "questions_answered": 0,
                    "correct_answers": 0,
                    "accuracy": 0.0
                }
            
            topic_stats = stats.topic_stats[topic]
            topic_stats["questions_answered"] += session.questions_answered
            topic_stats["correct_answers"] += session.correct_answers
            
            if topic_stats["questions_answered"] > 0:
                topic_stats["accuracy"] = (topic_stats["correct_answers"] / topic_stats["questions_answered"]) * 100
        
        stats.last_updated = datetime.utcnow()
        stats.last_activity = datetime.utcnow()
        
        db.commit()
        
        # Check for new achievements
        await check_achievements(user_id, stats, db)
        
    except Exception as e:
        logger.error(f"Update user statistics failed: {str(e)}")
        db.rollback()


async def check_achievements(user_id: str, stats: UserStats, db: Session):
    """Check and award achievements based on user statistics."""
    try:
        # Get all active achievements
        achievements = db.query(Achievement).filter(Achievement.is_active == True).all()
        
        for achievement in achievements:
            # Check if user already has this achievement
            user_achievement = db.query(UserAchievement).filter(
                and_(
                    UserAchievement.user_id == user_id,
                    UserAchievement.achievement_id == achievement.id
                )
            ).first()
            
            if not user_achievement:
                user_achievement = UserAchievement(
                    user_id=user_id,
                    achievement_id=achievement.id
                )
                db.add(user_achievement)
            
            # Calculate progress based on achievement type
            progress = 0.0
            completed = False
            
            if achievement.requirement_type == "quiz_count":
                progress = min((stats.total_quizzes_taken / achievement.requirement_value) * 100, 100)
                completed = stats.total_quizzes_taken >= achievement.requirement_value
            
            elif achievement.requirement_type == "streak_days":
                progress = min((stats.current_streak / achievement.requirement_value) * 100, 100)
                completed = stats.current_streak >= achievement.requirement_value
            
            elif achievement.requirement_type == "accuracy":
                progress = min((stats.overall_accuracy / achievement.requirement_value) * 100, 100)
                completed = stats.overall_accuracy >= achievement.requirement_value
            
            # Update achievement progress
            user_achievement.progress = progress
            
            if completed and not user_achievement.is_completed:
                user_achievement.is_completed = True
                user_achievement.completed_at = datetime.utcnow()
                stats.total_points += achievement.points
                
                logger.info(f"Achievement earned: {achievement.name} by user {user_id}")
        
        db.commit()
        
    except Exception as e:
        logger.error(f"Check achievements failed: {str(e)}")
        db.rollback() 