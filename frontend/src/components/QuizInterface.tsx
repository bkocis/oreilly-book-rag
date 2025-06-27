import { useState, useEffect, useCallback } from 'react';
import type { Quiz, QuizSession, Question, QuizProgress } from '../types/quiz';
import { QuizProgressBar } from './QuizProgressBar';
import { QuestionDisplay } from './QuestionDisplay';
import { quizService } from '../services/quizService';

interface QuizInterfaceProps {
  quiz: Quiz;
  onComplete: (sessionId: string) => void;
  onExit: () => void;
}

export function QuizInterface({ quiz, onComplete, onExit }: QuizInterfaceProps) {
  const [session, setSession] = useState<QuizSession | null>(null);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [selectedAnswer, setSelectedAnswer] = useState<string | number | null>(null);
  const [timeRemaining, setTimeRemaining] = useState<number | undefined>();
  const [isLoading, setIsLoading] = useState(false);
  const [showConfirmExit, setShowConfirmExit] = useState(false);

  const currentQuestion = quiz.questions[currentQuestionIndex];
  const isFirstQuestion = currentQuestionIndex === 0;
  const isLastQuestion = currentQuestionIndex === quiz.questions.length - 1;

  // Initialize quiz session
  useEffect(() => {
    const initializeSession = async () => {
      try {
        setIsLoading(true);
        const newSession = await quizService.startQuizSession(quiz.id);
        setSession(newSession);
        
        // Set up timer if quiz has time limit
        if (quiz.time_limit) {
          setTimeRemaining(quiz.time_limit * 60); // Convert minutes to seconds
        }
      } catch (error) {
        console.error('Failed to start quiz session:', error);
      } finally {
        setIsLoading(false);
      }
    };

    initializeSession();
  }, [quiz.id, quiz.time_limit]);

  // Timer countdown
  useEffect(() => {
    if (timeRemaining === undefined || timeRemaining <= 0) return;

    const timer = setInterval(() => {
      setTimeRemaining(prev => {
        if (prev === undefined || prev <= 1) {
          // Time's up - auto submit quiz
          handleCompleteQuiz();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [timeRemaining]);

  // Calculate progress
  const progress: QuizProgress = {
    current_question: currentQuestionIndex + 1,
    total_questions: quiz.questions.length,
    percentage: ((currentQuestionIndex + 1) / quiz.questions.length) * 100,
    time_remaining: timeRemaining,
  };

  const handleAnswerSelect = useCallback((answer: string | number) => {
    setSelectedAnswer(answer);
  }, []);

  const handleNextQuestion = async () => {
    if (!session || selectedAnswer === null) return;

    try {
      setIsLoading(true);
      
      // Submit answer to backend
      await quizService.submitAnswer(session.id, currentQuestion.id, selectedAnswer);

      if (isLastQuestion) {
        // Complete the quiz
        await handleCompleteQuiz();
      } else {
        // Move to next question
        setCurrentQuestionIndex(prev => prev + 1);
        setSelectedAnswer(null);
      }
    } catch (error) {
      console.error('Failed to submit answer:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handlePreviousQuestion = () => {
    if (!isFirstQuestion) {
      setCurrentQuestionIndex(prev => prev - 1);
      // Reset selected answer for previous question
      setSelectedAnswer(null);
    }
  };

  const handleCompleteQuiz = async () => {
    if (!session) return;

    try {
      setIsLoading(true);
      onComplete(session.id);
    } catch (error) {
      console.error('Failed to complete quiz:', error);
    }
  };

  const handleExitQuiz = () => {
    setShowConfirmExit(true);
  };

  const confirmExit = () => {
    onExit();
  };

  if (isLoading && !session) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex items-center space-x-3">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
          <span className="text-gray-600">Starting quiz...</span>
        </div>
      </div>
    );
  }

  if (!session) {
    return (
      <div className="text-center py-12">
        <div className="text-red-600 mb-4">
          <svg className="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.5 0L4.268 16.5c-.77.833.192 2.5 1.732 2.5z" />
          </svg>
        </div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">Failed to start quiz</h3>
        <p className="text-gray-600 mb-4">There was an error starting the quiz session.</p>
        <button
          onClick={onExit}
          className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
        >
          Go Back
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{quiz.title}</h1>
          <p className="text-gray-600 mt-1">{quiz.description}</p>
        </div>
        <button
          onClick={handleExitQuiz}
          className="px-4 py-2 text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-lg transition-colors"
        >
          Exit Quiz
        </button>
      </div>

      {/* Progress Bar */}
      <QuizProgressBar progress={progress} />

      {/* Question Display */}
      <QuestionDisplay
        question={currentQuestion}
        selectedAnswer={selectedAnswer}
        onAnswerSelect={handleAnswerSelect}
      />

      {/* Navigation */}
      <div className="flex items-center justify-between mt-8">
        <div>
          {!isFirstQuestion && (
            <button
              onClick={handlePreviousQuestion}
              disabled={isLoading}
              className="flex items-center px-6 py-3 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
              Previous
            </button>
          )}
        </div>

        <div className="text-sm text-gray-500">
          Question {currentQuestionIndex + 1} of {quiz.questions.length}
        </div>

        <div>
          <button
            onClick={handleNextQuestion}
            disabled={selectedAnswer === null || isLoading}
            className="flex items-center px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
          >
            {isLoading ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                Submitting...
              </>
            ) : isLastQuestion ? (
              <>
                Complete Quiz
                <svg className="w-5 h-5 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </>
            ) : (
              <>
                Next
                <svg className="w-5 h-5 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Confirm Exit Modal */}
      {showConfirmExit && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Exit Quiz?</h3>
            <p className="text-gray-600 mb-6">
              Are you sure you want to exit? Your progress will be lost.
            </p>
            <div className="flex justify-end space-x-3">
              <button
                onClick={() => setShowConfirmExit(false)}
                className="px-4 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={confirmExit}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
              >
                Exit Quiz
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
} 