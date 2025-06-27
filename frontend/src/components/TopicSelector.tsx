import React, { useState, useEffect } from 'react';
import { learningService } from '../services/learningService';
import type { Topic } from '../services/learningService';

interface TopicSelectorProps {
  selectedTopic?: string;
  onTopicSelect: (topic: string) => void;
}

export function TopicSelector({ selectedTopic, onTopicSelect }: TopicSelectorProps) {
  const [topics, setTopics] = useState<Topic[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchTopics = async () => {
      try {
        setLoading(true);
        const fetchedTopics = await learningService.getTopics();
        setTopics(fetchedTopics);
      } catch (err) {
        setError('Failed to load topics');
        console.error('Error fetching topics:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchTopics();
  }, []);

  if (loading) {
    return (
      <div className="animate-pulse">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="h-32 bg-gray-200 rounded-lg"></div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-8">
        <div className="text-red-500 mb-2">{error}</div>
        <button 
          onClick={() => window.location.reload()} 
          className="text-primary-600 hover:text-primary-700"
        >
          Try again
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-gray-900">Select a Topic</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {topics.map((topic) => (
          <div
            key={topic.id}
            onClick={() => onTopicSelect(topic.id)}
            className={`
              cursor-pointer rounded-lg border-2 p-4 transition-all hover:shadow-md
              ${selectedTopic === topic.id 
                ? 'border-primary-500 bg-primary-50' 
                : 'border-gray-200 hover:border-gray-300'
              }
            `}
          >
            <div className="flex items-start justify-between mb-3">
              <h4 className="font-medium text-gray-900 text-sm">{topic.name}</h4>
              {topic.completion_rate !== undefined && (
                <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded-full">
                  {Math.round(topic.completion_rate)}%
                </span>
              )}
            </div>
            
            <p className="text-sm text-gray-600 mb-3 line-clamp-2">
              {topic.description}
            </p>
            
            <div className="flex items-center justify-between text-xs text-gray-500">
              <span>{topic.question_count} questions</span>
              <div className="flex space-x-1">
                {topic.difficulty_levels.map((level) => (
                  <span
                    key={level}
                    className={`
                      px-1.5 py-0.5 rounded text-xs
                      ${level === 'easy' ? 'bg-green-100 text-green-700' :
                        level === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                        'bg-red-100 text-red-700'
                      }
                    `}
                  >
                    {level}
                  </span>
                ))}
              </div>
            </div>
            
            {topic.completion_rate !== undefined && (
              <div className="mt-3">
                <div className="w-full bg-gray-200 rounded-full h-1.5">
                  <div
                    className="bg-primary-500 h-1.5 rounded-full transition-all"
                    style={{ width: `${topic.completion_rate}%` }}
                  ></div>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
} 