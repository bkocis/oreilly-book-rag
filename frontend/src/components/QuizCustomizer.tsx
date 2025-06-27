import React, { useState, useEffect } from 'react';
import { learningService } from '../services/learningService';
import type { QuizCustomization } from '../services/learningService';

interface QuizCustomizerProps {
  selectedTopic?: string;
  onStartQuiz: (customization: QuizCustomization) => void;
  loading?: boolean;
}

export function QuizCustomizer({ selectedTopic, onStartQuiz, loading = false }: QuizCustomizerProps) {
  const [difficultyLevels, setDifficultyLevels] = useState<string[]>([]);
  const [customization, setCustomization] = useState<QuizCustomization>({
    difficulty: 'medium',
    num_questions: 10,
    question_types: ['multiple_choice'],
    time_limit: 30,
  });

  useEffect(() => {
    const fetchDifficultyLevels = async () => {
      try {
        const levels = await learningService.getDifficultyLevels();
        setDifficultyLevels(levels);
      } catch (error) {
        console.error('Error fetching difficulty levels:', error);
        setDifficultyLevels(['easy', 'medium', 'hard']);
      }
    };

    fetchDifficultyLevels();
  }, []);

  useEffect(() => {
    if (selectedTopic) {
      setCustomization(prev => ({ ...prev, topic: selectedTopic }));
    }
  }, [selectedTopic]);

  const questionTypes = [
    { id: 'multiple_choice', label: 'Multiple Choice', description: 'Choose from several options' },
    { id: 'true_false', label: 'True/False', description: 'Binary choice questions' },
    { id: 'fill_blank', label: 'Fill in the Blank', description: 'Complete the missing parts' },
    { id: 'short_answer', label: 'Short Answer', description: 'Brief written responses' },
  ];

  const handleQuestionTypeToggle = (typeId: string) => {
    setCustomization(prev => {
      const currentTypes = prev.question_types || [];
      const newTypes = currentTypes.includes(typeId)
        ? currentTypes.filter(t => t !== typeId)
        : [...currentTypes, typeId];
      
      return { ...prev, question_types: newTypes.length > 0 ? newTypes : ['multiple_choice'] };
    });
  };

  const handleStartQuiz = () => {
    onStartQuiz(customization);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">Customize Your Quiz</h3>
        {!selectedTopic && (
          <span className="text-sm text-amber-600 bg-amber-50 px-3 py-1 rounded-full">
            Select a topic first
          </span>
        )}
      </div>

      {/* Difficulty Level */}
      <div className="space-y-3">
        <label className="block text-sm font-medium text-gray-700">
          Difficulty Level
        </label>
        <div className="grid grid-cols-3 gap-3">
          {difficultyLevels.map((level) => (
            <button
              key={level}
              onClick={() => setCustomization(prev => ({ ...prev, difficulty: level as any }))}
              className={`
                p-3 rounded-lg border-2 text-sm font-medium transition-all
                ${customization.difficulty === level
                  ? 'border-primary-500 bg-primary-50 text-primary-700'
                  : 'border-gray-200 hover:border-gray-300 text-gray-700'
                }
              `}
            >
              <div className="flex items-center justify-center space-x-2">
                <span className={`
                  w-2 h-2 rounded-full
                  ${level === 'easy' ? 'bg-green-500' :
                    level === 'medium' ? 'bg-yellow-500' :
                    'bg-red-500'
                  }
                `}></span>
                <span className="capitalize">{level}</span>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Number of Questions */}
      <div className="space-y-3">
        <label className="block text-sm font-medium text-gray-700">
          Number of Questions
        </label>
        <div className="grid grid-cols-4 gap-3">
          {[5, 10, 15, 20].map((num) => (
            <button
              key={num}
              onClick={() => setCustomization(prev => ({ ...prev, num_questions: num }))}
              className={`
                p-3 rounded-lg border-2 text-sm font-medium transition-all
                ${customization.num_questions === num
                  ? 'border-primary-500 bg-primary-50 text-primary-700'
                  : 'border-gray-200 hover:border-gray-300 text-gray-700'
                }
              `}
            >
              {num}
            </button>
          ))}
        </div>
      </div>

      {/* Question Types */}
      <div className="space-y-3">
        <label className="block text-sm font-medium text-gray-700">
          Question Types
        </label>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {questionTypes.map((type) => (
            <label
              key={type.id}
              className={`
                cursor-pointer p-3 rounded-lg border-2 transition-all
                ${customization.question_types?.includes(type.id)
                  ? 'border-primary-500 bg-primary-50'
                  : 'border-gray-200 hover:border-gray-300'
                }
              `}
            >
              <div className="flex items-start space-x-3">
                <input
                  type="checkbox"
                  checked={customization.question_types?.includes(type.id) || false}
                  onChange={() => handleQuestionTypeToggle(type.id)}
                  className="mt-1 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                />
                <div>
                  <div className="text-sm font-medium text-gray-900">{type.label}</div>
                  <div className="text-xs text-gray-600">{type.description}</div>
                </div>
              </div>
            </label>
          ))}
        </div>
      </div>

      {/* Time Limit */}
      <div className="space-y-3">
        <label className="block text-sm font-medium text-gray-700">
          Time Limit (minutes)
        </label>
        <div className="grid grid-cols-4 gap-3">
          {[15, 30, 45, 60].map((time) => (
            <button
              key={time}
              onClick={() => setCustomization(prev => ({ ...prev, time_limit: time }))}
              className={`
                p-3 rounded-lg border-2 text-sm font-medium transition-all
                ${customization.time_limit === time
                  ? 'border-primary-500 bg-primary-50 text-primary-700'
                  : 'border-gray-200 hover:border-gray-300 text-gray-700'
                }
              `}
            >
              {time}m
            </button>
          ))}
        </div>
        <label className="flex items-center space-x-2">
          <input
            type="checkbox"
            checked={!customization.time_limit}
            onChange={(e) => setCustomization(prev => ({ 
              ...prev, 
              time_limit: e.target.checked ? undefined : 30 
            }))}
            className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
          />
          <span className="text-sm text-gray-600">No time limit</span>
        </label>
      </div>

      {/* Start Quiz Button */}
      <div className="pt-4">
        <button
          onClick={handleStartQuiz}
          disabled={!selectedTopic || loading}
          className={`
            w-full py-3 px-4 rounded-lg font-medium transition-all
            ${!selectedTopic || loading
              ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
              : 'bg-primary-600 hover:bg-primary-700 text-white shadow-lg hover:shadow-xl'
            }
          `}
        >
          {loading ? (
            <div className="flex items-center justify-center space-x-2">
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
              <span>Creating Quiz...</span>
            </div>
          ) : (
            'Start Quiz'
          )}
        </button>
      </div>
    </div>
  );
} 