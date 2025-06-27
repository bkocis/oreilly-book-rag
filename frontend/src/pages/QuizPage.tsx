import { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { QuizInterface } from '../components/QuizInterface';
import { QuizResults } from '../components/QuizResults';
import { quizService } from '../services/quizService';
import type { Quiz, QuizResult } from '../types/quiz';

type QuizState = 'loading' | 'taking' | 'completed' | 'selecting';

export function QuizPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [quiz, setQuiz] = useState<Quiz | null>(null);
  const [quizResult, setQuizResult] = useState<QuizResult | null>(null);
  const [state, setState] = useState<QuizState>('loading');
  const [error, setError] = useState<string | null>(null);

  const quizId = searchParams.get('id');

  useEffect(() => {
    if (quizId) {
      loadQuiz(quizId);
    } else {
      setState('selecting');
    }
  }, [quizId]);

  const loadQuiz = async (id: string) => {
    try {
      setState('loading');
      const quizData = await quizService.getQuiz(id);
      setQuiz(quizData);
      setState('taking');
    } catch (err) {
      console.error('Failed to load quiz:', err);
      setError('Failed to load quiz. Please try again.');
      setState('selecting');
    }
  };

  const handleQuizComplete = async (sessionId: string) => {
    try {
      const result = await quizService.completeQuiz(sessionId);
      setQuizResult(result);
      setState('completed');
    } catch (err) {
      console.error('Failed to complete quiz:', err);
      setError('Failed to complete quiz. Please try again.');
    }
  };

  const handleRetryQuiz = () => {
    setQuizResult(null);
    setState('taking');
  };

  const handleExitQuiz = () => {
    navigate('/dashboard');
  };

  const handleStartDemo = async () => {
    try {
      setState('loading');
      // Generate a demo quiz
      const demoQuiz = await quizService.generateQuiz({
        topic: 'Python Programming',
        difficulty: 'medium',
        num_questions: 5,
        question_types: ['multiple_choice', 'true_false']
      });
      setQuiz(demoQuiz);
      setState('taking');
    } catch (err) {
      console.error('Failed to generate demo quiz:', err);
      setError('Failed to generate demo quiz. Please try again.');
    }
  };

  if (state === 'loading') {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center justify-center h-64">
          <div className="flex items-center space-x-3">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
            <span className="text-gray-600">Loading quiz...</span>
          </div>
        </div>
      </div>
    );
  }

  if (state === 'completed' && quizResult && quiz) {
    return (
      <QuizResults
        result={quizResult}
        quiz={quiz}
        onRetry={handleRetryQuiz}
        onExit={handleExitQuiz}
      />
    );
  }

  if (state === 'taking' && quiz) {
    return (
      <QuizInterface
        quiz={quiz}
        onComplete={handleQuizComplete}
        onExit={handleExitQuiz}
      />
    );
  }

  // Quiz selection/demo state
  return (
    <div className="max-w-4xl mx-auto">
      <div className="card">
        <h1 className="text-3xl font-bold text-gray-900 mb-6">Take a Quiz</h1>
        
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <div className="flex items-center">
              <svg className="w-5 h-5 text-red-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.5 0L4.268 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
              <span className="text-red-800">{error}</span>
            </div>
          </div>
        )}
        
        <div className="text-center py-12">
          <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
          </div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Ready to Test Your Knowledge?</h2>
          <p className="text-gray-600 mb-8">
            Take a quiz powered by RAG technology to test your understanding of various topics.
          </p>
          
          <div className="space-y-4">
            <button
              onClick={handleStartDemo}
              className="w-full sm:w-auto px-8 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors font-medium"
            >
              Start Demo Quiz
            </button>
            
            <div className="text-sm text-gray-500">
              <p>Or navigate from the dashboard to take a specific quiz</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
} 