import axios from 'axios';
import type { Quiz, QuizSession, QuizResult } from '../types/quiz';

const API_BASE_URL = 'http://localhost:8000/api/v1';

export class QuizService {
  private api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
      'Content-Type': 'application/json',
    },
  });

  // Generate a new quiz
  async generateQuiz(params: {
    topic?: string;
    difficulty?: 'easy' | 'medium' | 'hard';
    num_questions?: number;
    question_types?: string[];
  }): Promise<Quiz> {
    const response = await this.api.post('/quizzes/generate', params);
    return response.data;
  }

  // Get a specific quiz by ID
  async getQuiz(quizId: string): Promise<Quiz> {
    const response = await this.api.get(`/quizzes/${quizId}`);
    return response.data;
  }

  // Start a new quiz session
  async startQuizSession(quizId: string): Promise<QuizSession> {
    const response = await this.api.post(`/quizzes/sessions`, { quiz_id: quizId });
    return response.data;
  }

  // Submit an answer for a question
  async submitAnswer(sessionId: string, questionId: string, answer: string | number): Promise<void> {
    await this.api.post(`/quizzes/${sessionId}/submit`, {
      question_id: questionId,
      answer: answer,
    });
  }

  // Complete a quiz session and get results
  async completeQuiz(sessionId: string): Promise<QuizResult> {
    const response = await this.api.post(`/quizzes/${sessionId}/complete`);
    return response.data;
  }

  // Get quiz session details
  async getQuizSession(sessionId: string): Promise<QuizSession> {
    const response = await this.api.get(`/quizzes/sessions/${sessionId}`);
    return response.data;
  }

  // Get available topics
  async getTopics(): Promise<string[]> {
    const response = await this.api.get('/learning/topics');
    return response.data;
  }

  // Get user's quiz progress
  async getUserProgress(userId: string): Promise<any> {
    const response = await this.api.get(`/quizzes/user-progress/${userId}`);
    return response.data;
  }
}

export const quizService = new QuizService(); 