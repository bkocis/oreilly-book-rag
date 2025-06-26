"""
Script to populate the database with sample achievements for the quiz system.
Run this script after database setup to add initial achievements.
"""

from sqlalchemy.orm import Session
from app.models.quiz_models import Achievement
from app.utils.database import get_db, SessionLocal


def create_sample_achievements():
    """Create sample achievements for the quiz system."""
    db = SessionLocal()
    
    try:
        # Check if achievements already exist
        existing_count = db.query(Achievement).count()
        if existing_count > 0:
            print(f"Found {existing_count} existing achievements. Skipping creation.")
            return
        
        achievements = [
            # Quiz Count Achievements
            Achievement(
                name="First Steps",
                description="Complete your first quiz",
                category="milestone",
                requirement_type="quiz_count",
                requirement_value=1,
                points=10,
                badge_color="bronze"
            ),
            Achievement(
                name="Getting Started",
                description="Complete 5 quizzes",
                category="milestone",
                requirement_type="quiz_count",
                requirement_value=5,
                points=25,
                badge_color="bronze"
            ),
            Achievement(
                name="Quiz Explorer",
                description="Complete 25 quizzes",
                category="milestone",
                requirement_type="quiz_count",
                requirement_value=25,
                points=100,
                badge_color="silver"
            ),
            Achievement(
                name="Quiz Master",
                description="Complete 100 quizzes",
                category="milestone",
                requirement_type="quiz_count",
                requirement_value=100,
                points=500,
                badge_color="gold"
            ),
            Achievement(
                name="Quiz Legend",
                description="Complete 500 quizzes",
                category="milestone",
                requirement_type="quiz_count",
                requirement_value=500,
                points=2000,
                badge_color="platinum"
            ),
            
            # Streak Achievements
            Achievement(
                name="On a Roll",
                description="Maintain a 3-day streak",
                category="streak",
                requirement_type="streak_days",
                requirement_value=3,
                points=20,
                badge_color="bronze"
            ),
            Achievement(
                name="Consistent Learner",
                description="Maintain a 7-day streak",
                category="streak",
                requirement_type="streak_days",
                requirement_value=7,
                points=50,
                badge_color="silver"
            ),
            Achievement(
                name="Dedicated Student",
                description="Maintain a 30-day streak",
                category="streak",
                requirement_type="streak_days",
                requirement_value=30,
                points=200,
                badge_color="gold"
            ),
            Achievement(
                name="Unstoppable",
                description="Maintain a 100-day streak",
                category="streak",
                requirement_type="streak_days",
                requirement_value=100,
                points=1000,
                badge_color="platinum"
            ),
            
            # Accuracy Achievements
            Achievement(
                name="Sharp Shooter",
                description="Achieve 80% overall accuracy",
                category="mastery",
                requirement_type="accuracy",
                requirement_value=80,
                points=75,
                badge_color="bronze"
            ),
            Achievement(
                name="Precision Expert",
                description="Achieve 90% overall accuracy",
                category="mastery",
                requirement_type="accuracy",
                requirement_value=90,
                points=150,
                badge_color="silver"
            ),
            Achievement(
                name="Perfect Aim",
                description="Achieve 95% overall accuracy",
                category="mastery",
                requirement_type="accuracy",
                requirement_value=95,
                points=300,
                badge_color="gold"
            ),
            Achievement(
                name="Flawless",
                description="Achieve 98% overall accuracy",
                category="mastery",
                requirement_type="accuracy",
                requirement_value=98,
                points=500,
                badge_color="platinum"
            ),
            
            # Social Achievements
            Achievement(
                name="Social Butterfly",
                description="Follow 5 other learners",
                category="social",
                requirement_type="social_follows",
                requirement_value=5,
                points=30,
                badge_color="bronze"
            ),
            Achievement(
                name="Community Builder",
                description="Get 10 followers",
                category="social",
                requirement_type="social_followers",
                requirement_value=10,
                points=50,
                badge_color="silver"
            ),
            Achievement(
                name="Influencer",
                description="Get 50 followers",
                category="social",
                requirement_type="social_followers",
                requirement_value=50,
                points=200,
                badge_color="gold"
            ),
            
            # Special Category Achievements
            Achievement(
                name="Night Owl",
                description="Complete 10 quizzes after 10 PM",
                category="special",
                requirement_type="time_based",
                requirement_value=10,
                points=40,
                badge_color="bronze"
            ),
            Achievement(
                name="Early Bird",
                description="Complete 10 quizzes before 8 AM",
                category="special",
                requirement_type="time_based",
                requirement_value=10,
                points=40,
                badge_color="bronze"
            ),
            Achievement(
                name="Speed Demon",
                description="Complete a quiz in under 2 minutes",
                category="special",
                requirement_type="speed_completion",
                requirement_value=120,  # seconds
                points=60,
                badge_color="silver"
            ),
            Achievement(
                name="Marathon Runner",
                description="Spend over 5 hours total learning",
                category="special",
                requirement_type="time_spent",
                requirement_value=18000,  # 5 hours in seconds
                points=100,
                badge_color="gold"
            )
        ]
        
        # Add all achievements to the database
        for achievement in achievements:
            db.add(achievement)
        
        db.commit()
        print(f"Successfully created {len(achievements)} sample achievements!")
        
        # Print summary
        print("\nAchievements by category:")
        for category in ["milestone", "streak", "mastery", "social", "special"]:
            count = len([a for a in achievements if a.category == category])
            print(f"  {category.title()}: {count} achievements")
            
    except Exception as e:
        print(f"Error creating achievements: {str(e)}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    create_sample_achievements() 