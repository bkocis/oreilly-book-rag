export interface Question {
  id: string;
  type: 'multiple_choice' | 'true_false' | 'fill_blank' | 'short_answer';
  question: string;
  options?: string[];
  correct_answer: string | number;
  explanation: string;
  difficulty: 'easy' | 'medium' | 'hard';
  topic: string;
  source_document?: string;
}

export interface Quiz {
  id: string;
  title: string;
  description: string;
  questions: Question[];
  time_limit?: number; // in minutes
  difficulty: 'easy' | 'medium' | 'hard';
  topic: string;
  created_at: string;
}

export interface QuizSession {
  id: string;
  quiz_id: string;
  user_answers: Record<string, string | number>;
  current_question: number;
  start_time: string;
  end_time?: string;
  score?: number;
  time_spent: number; // in seconds
  completed: boolean;
}

export interface QuizResult {
  session_id: string;
  quiz_id: string;
  score: number;
  total_questions: number;
  correct_answers: number;
  time_spent: number;
  answers: Array<{
    question_id: string;
    user_answer: string | number;
    correct_answer: string | number;
    is_correct: boolean;
    explanation: string;
  }>;
}

export interface QuizProgress {
  current_question: number;
  total_questions: number;
  percentage: number;
  time_remaining?: number; // in seconds
} 