import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

export interface Topic {
  id: string;
  name: string;
  description: string;
  difficulty_levels: string[];
  question_count: number;
  completion_rate?: number;
}

export interface StudyRecommendation {
  topic: string;
  difficulty: string;
  reason: string;
  priority: 'high' | 'medium' | 'low';
  estimated_time: number; // in minutes
}

export interface LearningProgress {
  topics_studied: number;
  total_topics: number;
  average_score: number;
  study_time: number; // in hours
  quizzes_completed: number;
  streak_days: number;
  level: string;
  achievements: Achievement[];
}

export interface Achievement {
  id: string;
  name: string;
  description: string;
  icon: string;
  unlocked: boolean;
  unlocked_at?: string;
}

export interface QuizCustomization {
  topic?: string;
  difficulty?: 'easy' | 'medium' | 'hard';
  num_questions?: number;
  question_types?: string[];
  time_limit?: number;
}

export class LearningService {
  private api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
      'Content-Type': 'application/json',
    },
  });

  // Get available topics
  async getTopics(): Promise<Topic[]> {
    const response = await this.api.get('/topics');
    return response.data;
  }

  // Get difficulty levels
  async getDifficultyLevels(): Promise<string[]> {
    const response = await this.api.get('/difficulty-levels');
    return response.data;
  }

  // Get learning progress for current user
  async getLearningProgress(): Promise<LearningProgress> {
    const response = await this.api.get('/learning/progress');
    return response.data;
  }

  // Get study recommendations
  async getStudyRecommendations(): Promise<StudyRecommendation[]> {
    const response = await this.api.get('/learning/recommendations');
    return response.data;
  }

  // Create a study session
  async createStudySession(customization: QuizCustomization): Promise<{ session_id: string }> {
    const response = await this.api.post('/study-sessions', customization);
    return response.data;
  }

  // Get user achievements
  async getAchievements(): Promise<Achievement[]> {
    const response = await this.api.get('/learning/achievements');
    return response.data;
  }

  // Get learning analytics
  async getLearningAnalytics(): Promise<any> {
    const response = await this.api.get('/analytics/learning');
    return response.data;
  }
}

export const learningService = new LearningService(); 