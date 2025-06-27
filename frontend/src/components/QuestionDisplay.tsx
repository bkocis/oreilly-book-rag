import { useState } from 'react';
import type { Question } from '../types/quiz';

interface QuestionDisplayProps {
  question: Question;
  selectedAnswer: string | number | null;
  onAnswerSelect: (answer: string | number) => void;
  showExplanation?: boolean;
  isCorrect?: boolean;
}

export function QuestionDisplay({ 
  question, 
  selectedAnswer, 
  onAnswerSelect, 
  showExplanation = false,
  isCorrect 
}: QuestionDisplayProps) {
  const [fillBlankAnswer, setFillBlankAnswer] = useState('');

  const handleFillBlankSubmit = () => {
    if (fillBlankAnswer.trim()) {
      onAnswerSelect(fillBlankAnswer.trim());
    }
  };

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'easy': return 'bg-green-100 text-green-800';
      case 'medium': return 'bg-yellow-100 text-yellow-800';
      case 'hard': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const renderMultipleChoice = () => (
    <div className="space-y-3">
      {question.options?.map((option, index) => (
        <label
          key={index}
          className={`flex items-center p-4 border rounded-lg cursor-pointer transition-colors ${
            selectedAnswer === index
              ? 'border-primary-500 bg-primary-50'
              : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
          }`}
        >
          <input
            type="radio"
            name={`question-${question.id}`}
            value={index}
            checked={selectedAnswer === index}
            onChange={() => onAnswerSelect(index)}
            className="sr-only"
          />
          <div className={`w-4 h-4 rounded-full border-2 mr-3 flex items-center justify-center ${
            selectedAnswer === index
              ? 'border-primary-500 bg-primary-500'
              : 'border-gray-300'
          }`}>
            {selectedAnswer === index && (
              <div className="w-2 h-2 bg-white rounded-full" />
            )}
          </div>
          <span className="text-gray-900">{option}</span>
        </label>
      ))}
    </div>
  );

  const renderTrueFalse = () => (
    <div className="space-y-3">
      {['True', 'False'].map((option, index) => {
        const value = index === 0 ? 'true' : 'false';
        return (
          <label
            key={option}
            className={`flex items-center p-4 border rounded-lg cursor-pointer transition-colors ${
              selectedAnswer === value
                ? 'border-primary-500 bg-primary-50'
                : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
            }`}
          >
            <input
              type="radio"
              name={`question-${question.id}`}
              value={value}
              checked={selectedAnswer === value}
              onChange={() => onAnswerSelect(value)}
              className="sr-only"
            />
            <div className={`w-4 h-4 rounded-full border-2 mr-3 flex items-center justify-center ${
              selectedAnswer === value
                ? 'border-primary-500 bg-primary-500'
                : 'border-gray-300'
            }`}>
              {selectedAnswer === value && (
                <div className="w-2 h-2 bg-white rounded-full" />
              )}
            </div>
            <span className="text-gray-900">{option}</span>
          </label>
        );
      })}
    </div>
  );

  const renderFillBlank = () => (
    <div className="space-y-4">
      <div className="flex items-center space-x-3">
        <input
          type="text"
          value={fillBlankAnswer}
          onChange={(e) => setFillBlankAnswer(e.target.value)}
          placeholder="Enter your answer..."
          className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          onKeyPress={(e) => {
            if (e.key === 'Enter') {
              handleFillBlankSubmit();
            }
          }}
        />
        <button
          onClick={handleFillBlankSubmit}
          disabled={!fillBlankAnswer.trim()}
          className="px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
        >
          Submit
        </button>
      </div>
    </div>
  );

  const renderShortAnswer = () => (
    <div className="space-y-4">
      <textarea
        value={selectedAnswer as string || ''}
        onChange={(e) => onAnswerSelect(e.target.value)}
        placeholder="Enter your answer..."
        rows={4}
        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
      />
    </div>
  );

  const renderQuestionType = () => {
    switch (question.type) {
      case 'multiple_choice':
        return renderMultipleChoice();
      case 'true_false':
        return renderTrueFalse();
      case 'fill_blank':
        return renderFillBlank();
      case 'short_answer':
        return renderShortAnswer();
      default:
        return <div>Unsupported question type</div>;
    }
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
      {/* Question Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center space-x-3">
          <span className={`px-2 py-1 rounded-full text-xs font-medium ${getDifficultyColor(question.difficulty)}`}>
            {question.difficulty.charAt(0).toUpperCase() + question.difficulty.slice(1)}
          </span>
          <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs font-medium">
            {question.topic}
          </span>
        </div>
        <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
          {question.type.replace('_', ' ').toUpperCase()}
        </span>
      </div>

      {/* Question Text */}
      <div className="mb-6">
        <h3 className="text-lg font-medium text-gray-900 leading-relaxed">
          {question.question}
        </h3>
      </div>

      {/* Answer Options */}
      <div className="mb-6">
        {renderQuestionType()}
      </div>

      {/* Explanation (shown after answering) */}
      {showExplanation && (
        <div className={`mt-6 p-4 rounded-lg border-l-4 ${
          isCorrect 
            ? 'border-green-400 bg-green-50' 
            : 'border-red-400 bg-red-50'
        }`}>
          <div className="flex items-center mb-2">
            {isCorrect ? (
              <svg className="w-5 h-5 text-green-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            ) : (
              <svg className="w-5 h-5 text-red-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            )}
            <span className={`font-medium ${isCorrect ? 'text-green-800' : 'text-red-800'}`}>
              {isCorrect ? 'Correct!' : 'Incorrect'}
            </span>
          </div>
          <p className={`text-sm ${isCorrect ? 'text-green-700' : 'text-red-700'}`}>
            {question.explanation}
          </p>
        </div>
      )}
    </div>
  );
} 