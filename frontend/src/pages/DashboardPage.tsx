import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { TopicSelector } from '../components/TopicSelector';
import { QuizCustomizer } from '../components/QuizCustomizer';
import { LearningProgressChart } from '../components/LearningProgressChart';
import { StudyRecommendations } from '../components/StudyRecommendations';
import { AchievementDisplay } from '../components/AchievementDisplay';
import { AnalyticsDashboard } from '../components/AnalyticsDashboard';
import { quizService } from '../services/quizService';
import { learningService } from '../services/learningService';
import type { QuizCustomization } from '../services/learningService';

export function DashboardPage() {
  const navigate = useNavigate();
  const [selectedTopic, setSelectedTopic] = useState<string>('');
  const [activeSection, setActiveSection] = useState<'topics' | 'customize' | 'progress' | 'achievements' | 'analytics'>('topics');
  const [loading, setLoading] = useState(false);

  const handleTopicSelect = (topicId: string) => {
    setSelectedTopic(topicId);
    setActiveSection('customize');
  };

  const handleStartQuiz = async (customization: QuizCustomization) => {
    try {
      setLoading(true);
      
      // Generate quiz with customization
      const quiz = await quizService.generateQuiz(customization);
      
      // Navigate to quiz page
      navigate(`/quiz/${quiz.id}`);
    } catch (error) {
      console.error('Error starting quiz:', error);
      alert('Failed to start quiz. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectRecommendation = (topic: string, difficulty: string) => {
    setSelectedTopic(topic);
    setActiveSection('customize');
  };

  const navigationItems = [
    { id: 'topics', label: 'Topics', icon: '📚' },
    { id: 'customize', label: 'Customize', icon: '⚙️' },
    { id: 'progress', label: 'Progress', icon: '📊' },
    { id: 'achievements', label: 'Achievements', icon: '🏆' },
    { id: 'analytics', label: 'Analytics', icon: '📈' },
  ] as const;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Learning Dashboard</h1>
          <p className="text-gray-600 mt-1">Master your topics with personalized quizzes</p>
        </div>
        <button
          onClick={() => navigate('/quiz')}
          className="bg-primary-600 hover:bg-primary-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
        >
          Quick Quiz
        </button>
      </div>

      {/* Navigation Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-8">
          {navigationItems.map((item) => (
            <button
              key={item.id}
              onClick={() => setActiveSection(item.id)}
              className={`
                flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm transition-colors
                ${activeSection === item.id
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }
              `}
            >
              <span>{item.icon}</span>
              <span>{item.label}</span>
            </button>
          ))}
        </nav>
      </div>

      {/* Content Sections */}
      <div className="space-y-8">
        {activeSection === 'topics' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <div className="lg:col-span-2">
              <TopicSelector
                selectedTopic={selectedTopic}
                onTopicSelect={handleTopicSelect}
              />
            </div>
            <div className="space-y-6">
              <StudyRecommendations
                onSelectRecommendation={handleSelectRecommendation}
              />
            </div>
          </div>
        )}

        {activeSection === 'customize' && (
          <div className="max-w-2xl mx-auto">
            <QuizCustomizer
              selectedTopic={selectedTopic}
              onStartQuiz={handleStartQuiz}
              loading={loading}
            />
            {!selectedTopic && (
              <div className="mt-6 p-4 bg-amber-50 border border-amber-200 rounded-lg">
                <div className="flex items-center">
                  <svg className="w-5 h-5 text-amber-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <p className="text-amber-700">
                    Go to the <button onClick={() => setActiveSection('topics')} className="underline font-medium">Topics</button> section to select a topic first.
                  </p>
                </div>
              </div>
            )}
          </div>
        )}

        {activeSection === 'progress' && (
          <div>
            <LearningProgressChart />
          </div>
        )}

        {activeSection === 'achievements' && (
          <div>
            <AchievementDisplay />
          </div>
        )}

        {activeSection === 'analytics' && (
          <div>
            <AnalyticsDashboard userId="user-123" />
          </div>
        )}
      </div>

      {/* Quick Actions - Always visible at bottom */}
      <div className="bg-gray-50 rounded-lg p-6 mt-8">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button
            onClick={() => {
              // Start a random quiz
              handleStartQuiz({ difficulty: 'medium', num_questions: 10, question_types: ['multiple_choice'] });
            }}
            className="flex items-center justify-center space-x-2 p-4 bg-white border border-gray-200 rounded-lg hover:shadow-md transition-shadow"
          >
            <svg className="w-5 h-5 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            <span className="font-medium text-gray-900">Random Quiz</span>
          </button>
          
          <button
            onClick={() => setActiveSection('progress')}
            className="flex items-center justify-center space-x-2 p-4 bg-white border border-gray-200 rounded-lg hover:shadow-md transition-shadow"
          >
            <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
            <span className="font-medium text-gray-900">View Progress</span>
          </button>
          
          <button
            onClick={() => setActiveSection('achievements')}
            className="flex items-center justify-center space-x-2 p-4 bg-white border border-gray-200 rounded-lg hover:shadow-md transition-shadow"
          >
            <svg className="w-5 h-5 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
            </svg>
            <span className="font-medium text-gray-900">Achievements</span>
          </button>
        </div>
      </div>
    </div>
  );
} 