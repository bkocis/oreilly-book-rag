import { useState } from 'react';
import type { QuizResult, Quiz } from '../types/quiz';
import { QuestionDisplay } from './QuestionDisplay';

interface QuizResultsProps {
  result: QuizResult;
  quiz: Quiz;
  onRetry: () => void;
  onExit: () => void;
}

export function QuizResults({ result, quiz, onRetry, onExit }: QuizResultsProps) {
  const [showReview, setShowReview] = useState(false);
  const [reviewQuestionIndex, setReviewQuestionIndex] = useState(0);

  const scorePercentage = Math.round((result.score / result.total_questions) * 100);
  const formatTime = (seconds: number): string => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  const getScoreColor = (percentage: number) => {
    if (percentage >= 90) return 'text-green-600';
    if (percentage >= 70) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getScoreMessage = (percentage: number) => {
    if (percentage >= 90) return 'Excellent work! 🎉';
    if (percentage >= 70) return 'Good job! 👍';
    if (percentage >= 50) return 'Not bad, keep practicing! 📚';
    return 'Keep studying and try again! 💪';
  };

  const correctAnswers = result.answers.filter(a => a.is_correct);
  const incorrectAnswers = result.answers.filter(a => !a.is_correct);

  if (showReview) {
    const currentAnswer = result.answers[reviewQuestionIndex];
    const currentQuestion = quiz.questions.find(q => q.id === currentAnswer.question_id);

    if (!currentQuestion) {
      return <div>Question not found</div>;
    }

    return (
      <div className="max-w-4xl mx-auto">
        {/* Review Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Review Questions</h1>
            <p className="text-gray-600 mt-1">
              Question {reviewQuestionIndex + 1} of {result.answers.length}
            </p>
          </div>
          <button
            onClick={() => setShowReview(false)}
            className="px-4 py-2 text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-lg transition-colors"
          >
            Back to Results
          </button>
        </div>

        {/* Question Review */}
        <QuestionDisplay
          question={currentQuestion}
          selectedAnswer={currentAnswer.user_answer}
          onAnswerSelect={() => {}} // Read-only in review mode
          showExplanation={true}
          isCorrect={currentAnswer.is_correct}
        />

        {/* Review Navigation */}
        <div className="flex items-center justify-between mt-8">
          <div>
            {reviewQuestionIndex > 0 && (
              <button
                onClick={() => setReviewQuestionIndex(prev => prev - 1)}
                className="flex items-center px-6 py-3 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
                Previous
              </button>
            )}
          </div>

          <div className="text-sm text-gray-500">
            {reviewQuestionIndex + 1} of {result.answers.length}
          </div>

          <div>
            {reviewQuestionIndex < result.answers.length - 1 ? (
              <button
                onClick={() => setReviewQuestionIndex(prev => prev + 1)}
                className="flex items-center px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
              >
                Next
                <svg className="w-5 h-5 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </button>
            ) : (
              <button
                onClick={() => setShowReview(false)}
                className="flex items-center px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
              >
                Finish Review
                <svg className="w-5 h-5 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </button>
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="text-center mb-8">
        <div className="w-20 h-20 mx-auto mb-6 rounded-full bg-gradient-to-r from-primary-500 to-blue-600 flex items-center justify-center">
          <svg className="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Quiz Complete!</h1>
        <p className="text-gray-600">{getScoreMessage(scorePercentage)}</p>
      </div>

      {/* Score Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white border border-gray-200 rounded-lg p-6 text-center">
          <div className={`text-4xl font-bold mb-2 ${getScoreColor(scorePercentage)}`}>
            {scorePercentage}%
          </div>
          <div className="text-gray-600">Final Score</div>
        </div>
        
        <div className="bg-white border border-gray-200 rounded-lg p-6 text-center">
          <div className="text-4xl font-bold text-green-600 mb-2">
            {result.correct_answers}
          </div>
          <div className="text-gray-600">Correct Answers</div>
          <div className="text-sm text-gray-500 mt-1">
            out of {result.total_questions}
          </div>
        </div>
        
        <div className="bg-white border border-gray-200 rounded-lg p-6 text-center">
          <div className="text-4xl font-bold text-blue-600 mb-2">
            {formatTime(result.time_spent)}
          </div>
          <div className="text-gray-600">Time Spent</div>
        </div>
      </div>

      {/* Performance Breakdown */}
      <div className="bg-white border border-gray-200 rounded-lg p-6 mb-8">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Performance Breakdown</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Correct Answers */}
          <div>
            <h3 className="font-medium text-green-800 mb-3 flex items-center">
              <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              Correct ({correctAnswers.length})
            </h3>
            <div className="space-y-2 max-h-48 overflow-y-auto">
              {correctAnswers.map((answer, index) => {
                const question = quiz.questions.find(q => q.id === answer.question_id);
                return (
                  <div key={answer.question_id} className="text-sm p-2 bg-green-50 rounded border-l-4 border-green-400">
                    <div className="font-medium text-green-800">Q{index + 1}</div>
                    <div className="text-green-700 truncate">
                      {question?.question.substring(0, 80)}...
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Incorrect Answers */}
          <div>
            <h3 className="font-medium text-red-800 mb-3 flex items-center">
              <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
              Incorrect ({incorrectAnswers.length})
            </h3>
            <div className="space-y-2 max-h-48 overflow-y-auto">
              {incorrectAnswers.map((answer, index) => {
                const question = quiz.questions.find(q => q.id === answer.question_id);
                return (
                  <div key={answer.question_id} className="text-sm p-2 bg-red-50 rounded border-l-4 border-red-400">
                    <div className="font-medium text-red-800">Q{index + 1}</div>
                    <div className="text-red-700 truncate">
                      {question?.question.substring(0, 80)}...
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex flex-col sm:flex-row justify-center space-y-3 sm:space-y-0 sm:space-x-4">
        <button
          onClick={() => setShowReview(true)}
          className="flex items-center justify-center px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
          </svg>
          Review Answers
        </button>
        
        <button
          onClick={onRetry}
          className="flex items-center justify-center px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
        >
          <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          Try Again
        </button>
        
        <button
          onClick={onExit}
          className="flex items-center justify-center px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
        >
          <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2H5a2 2 0 00-2-2z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 5a2 2 0 012-2h2a2 2 0 012 2v2H8V5z" />
          </svg>
          Back to Dashboard
        </button>
      </div>
    </div>
  );
} 