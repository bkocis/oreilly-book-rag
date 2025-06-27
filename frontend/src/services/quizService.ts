import axios from 'axios';
import type { Quiz, QuizSession, QuizResult } from '../types/quiz';

const API_BASE_URL = 'http://localhost:8000';

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
    const response = await this.api.post(`/quizzes/${quizId}/start`);
    return response.data;
  }

  // Submit an answer for a question
  async submitAnswer(sessionId: string, questionId: string, answer: string | number): Promise<void> {
    await this.api.post(`/quiz-sessions/${sessionId}/answer`, {
      question_id: questionId,
      answer: answer,
    });
  }

  // Complete a quiz session and get results
  async completeQuiz(sessionId: string): Promise<QuizResult> {
    const response = await this.api.post(`/quiz-sessions/${sessionId}/complete`);
    return response.data;
  }

  // Get quiz session details
  async getQuizSession(sessionId: string): Promise<QuizSession> {
    const response = await this.api.get(`/quiz-sessions/${sessionId}`);
    return response.data;
  }

  // Get available topics
  async getTopics(): Promise<string[]> {
    const response = await this.api.get('/topics');
    return response.data;
  }

  // Get user's quiz progress
  async getUserProgress(): Promise<any> {
    const response = await this.api.get('/quizzes/user-progress');
    return response.data;
  }
}

export const quizService = new QuizService(); 