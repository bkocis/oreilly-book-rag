import React, { useState, useEffect } from 'react';
import { learningService } from '../services/learningService';
import type { LearningProgress } from '../services/learningService';

export function LearningProgressChart() {
  const [progress, setProgress] = useState<LearningProgress | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchProgress = async () => {
      try {
        setLoading(true);
        const data = await learningService.getLearningProgress();
        setProgress(data);
      } catch (err) {
        setError('Failed to load progress');
        console.error('Error fetching progress:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchProgress();
  }, []);

  const getProgressColor = (percentage: number) => {
    if (percentage >= 80) return 'bg-green-500';
    if (percentage >= 60) return 'bg-yellow-500';
    if (percentage >= 40) return 'bg-orange-500';
    return 'bg-red-500';
  };

  const getStreakColor = (days: number) => {
    if (days >= 30) return 'text-purple-600 bg-purple-100';
    if (days >= 7) return 'text-green-600 bg-green-100';
    if (days >= 3) return 'text-yellow-600 bg-yellow-100';
    return 'text-gray-600 bg-gray-100';
  };

  const getLevelColor = (level: string) => {
    switch (level.toLowerCase()) {
      case 'expert':
        return 'text-purple-600 bg-purple-100';
      case 'advanced':
        return 'text-blue-600 bg-blue-100';
      case 'intermediate':
        return 'text-green-600 bg-green-100';
      case 'beginner':
        return 'text-yellow-600 bg-yellow-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  if (loading) {
    return (
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-gray-900">Learning Progress</h3>
        <div className="animate-pulse space-y-4">
          <div className="h-32 bg-gray-200 rounded-lg"></div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-20 bg-gray-200 rounded-lg"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-gray-900">Learning Progress</h3>
        <div className="text-center py-8 bg-gray-50 rounded-lg">
          <div className="text-red-500 mb-2">{error}</div>
          <button 
            onClick={() => window.location.reload()} 
            className="text-primary-600 hover:text-primary-700"
          >
            Try again
          </button>
        </div>
      </div>
    );
  }

  if (!progress) {
    return (
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-gray-900">Learning Progress</h3>
        <div className="text-center py-8 bg-gray-50 rounded-lg">
          <div className="w-16 h-16 bg-gray-200 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
          <h4 className="text-lg font-medium text-gray-900 mb-2">No progress data yet</h4>
          <p className="text-gray-600">Start taking quizzes to track your progress!</p>
        </div>
      </div>
    );
  }

  const topicsProgress = (progress.topics_studied / progress.total_topics) * 100;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">Learning Progress</h3>
        <span className={`px-3 py-1 rounded-full text-sm font-medium ${getLevelColor(progress.level)}`}>
          {progress.level}
        </span>
      </div>

      {/* Overall Progress */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h4 className="font-medium text-gray-900">Overall Progress</h4>
          <span className="text-sm text-gray-500">{Math.round(topicsProgress)}%</span>
        </div>
        
        <div className="w-full bg-gray-200 rounded-full h-3 mb-4">
          <div
            className={`h-3 rounded-full transition-all duration-500 ${getProgressColor(topicsProgress)}`}
            style={{ width: `${topicsProgress}%` }}
          ></div>
        </div>
        
        <div className="flex justify-between text-sm text-gray-600">
          <span>{progress.topics_studied} topics studied</span>
          <span>{progress.total_topics - progress.topics_studied} remaining</span>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="flex items-center mb-2">
            <div className="w-8 h-8 bg-primary-100 rounded-lg flex items-center justify-center mr-3">
              <svg className="w-4 h-4 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div>
              <p className="text-sm text-gray-600">Quizzes</p>
              <p className="text-xl font-bold text-gray-900">{progress.quizzes_completed}</p>
            </div>
          </div>
        </div>

        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="flex items-center mb-2">
            <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center mr-3">
              <svg className="w-4 h-4 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
              </svg>
            </div>
            <div>
              <p className="text-sm text-gray-600">Avg Score</p>
              <p className="text-xl font-bold text-gray-900">{Math.round(progress.average_score)}%</p>
            </div>
          </div>
        </div>

        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="flex items-center mb-2">
            <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center mr-3">
              <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div>
              <p className="text-sm text-gray-600">Study Time</p>
              <p className="text-xl font-bold text-gray-900">{Math.round(progress.study_time)}h</p>
            </div>
          </div>
        </div>

        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="flex items-center mb-2">
            <div className="w-8 h-8 bg-orange-100 rounded-lg flex items-center justify-center mr-3">
              <svg className="w-4 h-4 text-orange-600" fill="currentColor" viewBox="0 0 24 24">
                <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
              </svg>
            </div>
            <div>
              <p className="text-sm text-gray-600">Streak</p>
              <p className="text-xl font-bold text-gray-900">{progress.streak_days}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Achievements */}
      {progress.achievements && progress.achievements.length > 0 && (
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <h4 className="font-medium text-gray-900 mb-3">Recent Achievements</h4>
          <div className="flex space-x-3 overflow-x-auto">
            {progress.achievements.slice(0, 5).map((achievement) => (
              <div
                key={achievement.id}
                className="flex-shrink-0 flex items-center space-x-2 bg-yellow-50 border border-yellow-200 rounded-lg px-3 py-2"
              >
                <div className="w-6 h-6 text-yellow-600">
                  <svg fill="currentColor" viewBox="0 0 24 24">
                    <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
                  </svg>
                </div>
                <span className="text-sm font-medium text-yellow-800">{achievement.name}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Study Streak Visualization */}
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <div className="flex items-center justify-between mb-3">
          <h4 className="font-medium text-gray-900">Study Streak</h4>
          <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStreakColor(progress.streak_days)}`}>
            {progress.streak_days} days
          </span>
        </div>
        
        <div className="flex items-center justify-center py-4">
          <div className="flex items-center space-x-2">
            <svg className="w-8 h-8 text-orange-500" fill="currentColor" viewBox="0 0 24 24">
              <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
            </svg>
            <div>
              <p className="text-2xl font-bold text-gray-900">{progress.streak_days}</p>
              <p className="text-sm text-gray-600">day streak</p>
            </div>
          </div>
        </div>
        
        <div className="text-center text-sm text-gray-600">
          {progress.streak_days > 0 
            ? "Keep it up! You're on a roll! 🔥"
            : "Start a new streak by taking a quiz today!"
          }
        </div>
      </div>
    </div>
  );
} 