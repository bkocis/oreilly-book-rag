import React, { useState, useEffect } from 'react';
import { learningService } from '../services/learningService';
import type { Achievement } from '../services/learningService';

export function AchievementDisplay() {
  const [achievements, setAchievements] = useState<Achievement[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchAchievements = async () => {
      try {
        setLoading(true);
        const data = await learningService.getAchievements();
        setAchievements(data);
      } catch (err) {
        setError('Failed to load achievements');
        console.error('Error fetching achievements:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchAchievements();
  }, []);

  const getAchievementIcon = (icon: string, unlocked: boolean) => {
    const baseClasses = `w-8 h-8 ${unlocked ? 'text-yellow-500' : 'text-gray-400'}`;
    
    switch (icon) {
      case 'trophy':
        return (
          <svg className={baseClasses} fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
          </svg>
        );
      case 'medal':
        return (
          <svg className={baseClasses} fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
          </svg>
        );
      case 'fire':
        return (
          <svg className={baseClasses} fill="currentColor" viewBox="0 0 24 24">
            <path d="M12.017 2.972A3.78 3.78 0 0 0 8.5 6.39c0 .635.154 1.235.426 1.777-.233-.074-.482-.127-.742-.127C5.47 8.04 3.5 10.01 3.5 12.82c0 4.4 3.27 8.18 7.5 8.18s7.5-3.78 7.5-8.18c0-5.54-3.5-9.848-6.483-9.848z" />
          </svg>
        );
      case 'star':
        return (
          <svg className={baseClasses} fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
          </svg>
        );
      case 'target':
        return (
          <svg className={baseClasses} fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
      case 'lightning':
        return (
          <svg className={baseClasses} fill="currentColor" viewBox="0 0 24 24">
            <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
          </svg>
        );
      default:
        return (
          <svg className={baseClasses} fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
          </svg>
        );
    }
  };

  if (loading) {
    return (
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-gray-900">Achievements</h3>
        <div className="animate-pulse grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {[...Array(8)].map((_, i) => (
            <div key={i} className="h-24 bg-gray-200 rounded-lg"></div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-gray-900">Achievements</h3>
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

  const unlockedCount = achievements.filter(a => a.unlocked).length;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">Achievements</h3>
        <span className="text-sm text-gray-500">
          {unlockedCount} of {achievements.length} unlocked
        </span>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        {achievements.map((achievement) => (
          <div
            key={achievement.id}
            className={`
              relative p-4 rounded-lg border-2 transition-all text-center
              ${achievement.unlocked
                ? 'border-yellow-300 bg-yellow-50 shadow-md'
                : 'border-gray-200 bg-gray-50'
              }
            `}
          >
            {achievement.unlocked && (
              <div className="absolute top-2 right-2">
                <div className="w-6 h-6 bg-yellow-500 rounded-full flex items-center justify-center">
                  <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
              </div>
            )}

            <div className="flex justify-center mb-3">
              {getAchievementIcon(achievement.icon, achievement.unlocked)}
            </div>

            <h4 className={`font-medium text-sm mb-2 ${achievement.unlocked ? 'text-gray-900' : 'text-gray-500'}`}>
              {achievement.name}
            </h4>

            <p className={`text-xs ${achievement.unlocked ? 'text-gray-600' : 'text-gray-400'}`}>
              {achievement.description}
            </p>

            {achievement.unlocked && achievement.unlocked_at && (
              <div className="mt-2 text-xs text-yellow-700">
                Unlocked {new Date(achievement.unlocked_at).toLocaleDateString()}
              </div>
            )}

            {!achievement.unlocked && (
              <div className="absolute inset-0 bg-gray-200 bg-opacity-50 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
              </div>
            )}
          </div>
        ))}
      </div>

      {achievements.length === 0 && (
        <div className="text-center py-8 bg-gray-50 rounded-lg">
          <div className="w-16 h-16 bg-gray-200 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
            </svg>
          </div>
          <h4 className="text-lg font-medium text-gray-900 mb-2">No achievements yet</h4>
          <p className="text-gray-600">Start taking quizzes to unlock achievements!</p>
        </div>
      )}
    </div>
  );
} 