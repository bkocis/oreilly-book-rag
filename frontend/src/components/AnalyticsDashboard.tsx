import React, { useState, useEffect } from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  BarChart, Bar, PieChart, Pie, Cell, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar,
  AreaChart, Area, ComposedChart, ScatterChart, Scatter
} from 'recharts';
import { analyticsService, AnalyticsPeriod, PerformanceMetrics, ProgressVisualizationData, KnowledgeAnalysis, LearningInsight } from '../services/analyticsService';

interface AnalyticsDashboardProps {
  userId: string;
}

export function AnalyticsDashboard({ userId }: AnalyticsDashboardProps) {
  const [period, setPeriod] = useState<AnalyticsPeriod>('month');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'performance' | 'knowledge' | 'timeline' | 'insights'>('overview');
  
  // Data states
  const [performanceMetrics, setPerformanceMetrics] = useState<PerformanceMetrics | null>(null);
  const [visualizationData, setVisualizationData] = useState<ProgressVisualizationData | null>(null);
  const [knowledgeAnalysis, setKnowledgeAnalysis] = useState<KnowledgeAnalysis | null>(null);
  const [learningInsights, setLearningInsights] = useState<LearningInsight[]>([]);

  // Chart color schemes
  const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#F97316', '#06B6D4', '#84CC16'];
  const SEVERITY_COLORS = { low: '#10B981', medium: '#F59E0B', high: '#EF4444' };

  useEffect(() => {
    fetchAnalyticsData();
  }, [userId, period]);

  const fetchAnalyticsData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [metrics, visualization, knowledge, insights] = await Promise.all([
        analyticsService.getPerformanceMetrics(userId, period),
        analyticsService.getProgressVisualizationData(userId, period),
        analyticsService.analyzeKnowledgeGaps(userId, 0.6, true),
        analyticsService.getLearningInsights(userId, 10, 0.5)
      ]);

      setPerformanceMetrics(metrics);
      setVisualizationData(visualization);
      setKnowledgeAnalysis(knowledge);
      setLearningInsights(insights);
    } catch (err) {
      console.error('Error fetching analytics data:', err);
      setError('Failed to load analytics data');
    } finally {
      setLoading(false);
    }
  };

  const handleExportData = async (format: 'json' | 'csv') => {
    try {
      const blob = await analyticsService.exportAnalyticsData(userId, format, period, true);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `analytics_${userId}_${period}.${format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Export failed:', error);
      alert('Export failed. Please try again.');
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric'
    });
  };

  const getInsightIcon = (type: string) => {
    switch (type) {
      case 'knowledge_gap': return '🔴';
      case 'strength': return '🟢';
      case 'improvement': return '📈';
      case 'regression': return '📉';
      case 'mastery_achieved': return '🏆';
      default: return '📊';
    }
  };

  const getSeverityColor = (severity: 'low' | 'medium' | 'high') => {
    return SEVERITY_COLORS[severity];
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <h2 className="text-2xl font-bold text-gray-900">Analytics Dashboard</h2>
          <div className="animate-pulse h-8 w-32 bg-gray-200 rounded"></div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="animate-pulse h-32 bg-gray-200 rounded-lg"></div>
          ))}
        </div>
        <div className="animate-pulse h-64 bg-gray-200 rounded-lg"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-8">
        <div className="text-red-500 mb-4">{error}</div>
        <button
          onClick={fetchAnalyticsData}
          className="bg-primary-600 hover:bg-primary-700 text-white px-4 py-2 rounded-lg"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">Analytics Dashboard</h2>
        <div className="flex space-x-4">
          <select
            value={period}
            onChange={(e) => setPeriod(e.target.value as AnalyticsPeriod)}
            className="border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
          >
            <option value="week">Last Week</option>
            <option value="month">Last Month</option>
            <option value="quarter">Last Quarter</option>
            <option value="year">Last Year</option>
            <option value="all_time">All Time</option>
          </select>
          <div className="flex space-x-2">
            <button
              onClick={() => handleExportData('json')}
              className="bg-gray-600 hover:bg-gray-700 text-white px-3 py-2 rounded-lg text-sm"
            >
              Export JSON
            </button>
            <button
              onClick={() => handleExportData('csv')}
              className="bg-green-600 hover:bg-green-700 text-white px-3 py-2 rounded-lg text-sm"
            >
              Export CSV
            </button>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-8">
          {[
            { id: 'overview', label: 'Overview', icon: '📊' },
            { id: 'performance', label: 'Performance', icon: '📈' },
            { id: 'knowledge', label: 'Knowledge Gaps', icon: '🎯' },
            { id: 'timeline', label: 'Timeline', icon: '📅' },
            { id: 'insights', label: 'Insights', icon: '💡' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`
                flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm transition-colors
                ${activeTab === tab.id
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }
              `}
            >
              <span>{tab.icon}</span>
              <span>{tab.label}</span>
            </button>
          ))}
        </nav>
      </div>

      {/* Overview Tab */}
      {activeTab === 'overview' && performanceMetrics && (
        <div className="space-y-6">
          {/* Key Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <div className="flex items-center">
                <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                  <span className="text-2xl">📚</span>
                </div>
                <div className="ml-4">
                  <p className="text-sm text-gray-600">Total Sessions</p>
                  <p className="text-2xl font-bold text-gray-900">{performanceMetrics.total_sessions}</p>
                </div>
              </div>
            </div>

            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <div className="flex items-center">
                <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                  <span className="text-2xl">🎯</span>
                </div>
                <div className="ml-4">
                  <p className="text-sm text-gray-600">Accuracy</p>
                  <p className="text-2xl font-bold text-gray-900">{Math.round(performanceMetrics.accuracy_rate)}%</p>
                </div>
              </div>
            </div>

            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <div className="flex items-center">
                <div className="w-12 h-12 bg-yellow-100 rounded-lg flex items-center justify-center">
                  <span className="text-2xl">⚡</span>
                </div>
                <div className="ml-4">
                  <p className="text-sm text-gray-600">Avg Score</p>
                  <p className="text-2xl font-bold text-gray-900">{Math.round(performanceMetrics.average_score)}%</p>
                </div>
              </div>
            </div>

            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <div className="flex items-center">
                <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center">
                  <span className="text-2xl">🔥</span>
                </div>
                <div className="ml-4">
                  <p className="text-sm text-gray-600">Streak</p>
                  <p className="text-2xl font-bold text-gray-900">{performanceMetrics.streak_days} days</p>
                </div>
              </div>
            </div>
          </div>

          {/* Performance Overview Chart */}
          {visualizationData && (
            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Score Trend</h3>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={visualizationData.timeline_data}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" tickFormatter={formatDate} />
                  <YAxis />
                  <Tooltip labelFormatter={(label) => formatDate(label)} />
                  <Legend />
                  <Line type="monotone" dataKey="score" stroke="#3B82F6" strokeWidth={2} />
                  <Line type="monotone" dataKey="accuracy" stroke="#10B981" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      )}

      {/* Performance Tab */}
      {activeTab === 'performance' && visualizationData && (
        <div className="space-y-6">
          {/* Performance Trends */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Performance Trends</h3>
              <ResponsiveContainer width="100%" height={300}>
                <ComposedChart data={visualizationData.timeline_data}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" tickFormatter={formatDate} />
                  <YAxis />
                  <Tooltip labelFormatter={(label) => formatDate(label)} />
                  <Legend />
                  <Area type="monotone" dataKey="score" fill="#3B82F6" fillOpacity={0.3} stroke="#3B82F6" />
                  <Line type="monotone" dataKey="accuracy" stroke="#10B981" strokeWidth={2} />
                </ComposedChart>
              </ResponsiveContainer>
            </div>

            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Topic Performance</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={Object.entries(visualizationData.topic_breakdown).map(([topic, stats]) => ({
                  topic: topic.length > 15 ? topic.substring(0, 15) + '...' : topic,
                  accuracy: stats.accuracy,
                  sessions: stats.sessions
                }))}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="topic" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="accuracy" fill="#3B82F6" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Skill Progression Radar */}
          {Object.keys(visualizationData.skill_progression).length > 0 && (
            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Skill Progression</h3>
              <ResponsiveContainer width="100%" height={400}>
                <RadarChart data={Object.entries(visualizationData.skill_progression).map(([skill, level]) => ({
                  skill: skill.length > 10 ? skill.substring(0, 10) + '...' : skill,
                  level: level * 100
                }))}>
                  <PolarGrid />
                  <PolarAngleAxis dataKey="skill" />
                  <PolarRadiusAxis angle={45} domain={[0, 100]} />
                  <Radar name="Skill Level" dataKey="level" stroke="#3B82F6" fill="#3B82F6" fillOpacity={0.3} />
                  <Tooltip />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      )}

      {/* Knowledge Gaps Tab */}
      {activeTab === 'knowledge' && knowledgeAnalysis && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Knowledge Gaps */}
            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Knowledge Gaps</h3>
              <div className="space-y-4">
                {knowledgeAnalysis.knowledge_gaps.map((gap, index) => (
                  <div key={index} className="border-l-4 pl-4 py-2" style={{ borderColor: getSeverityColor(gap.severity) }}>
                    <div className="flex justify-between items-start">
                      <div>
                        <h4 className="font-medium text-gray-900">{gap.topic}</h4>
                        <p className="text-sm text-gray-600">{gap.description}</p>
                        <div className="flex items-center mt-2 space-x-4">
                          <span className={`px-2 py-1 rounded text-xs font-medium text-white`} style={{ backgroundColor: getSeverityColor(gap.severity) }}>
                            {gap.severity.toUpperCase()}
                          </span>
                          <span className="text-xs text-gray-500">Confidence: {Math.round(gap.confidence * 100)}%</span>
                        </div>
                      </div>
                    </div>
                    {gap.suggested_actions.length > 0 && (
                      <div className="mt-2">
                        <p className="text-xs text-gray-500 mb-1">Suggested Actions:</p>
                        <ul className="text-xs text-gray-600 space-y-1">
                          {gap.suggested_actions.map((action, i) => (
                            <li key={i}>• {action}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Strengths */}
            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Strengths</h3>
              <div className="space-y-4">
                {knowledgeAnalysis.strengths.map((strength, index) => (
                  <div key={index} className="border-l-4 border-green-500 pl-4 py-2">
                    <div className="flex justify-between items-start">
                      <div>
                        <h4 className="font-medium text-gray-900">{strength.topic}</h4>
                        <p className="text-sm text-gray-600">{strength.description}</p>
                        <div className="flex items-center mt-2">
                          <div className="flex-1 bg-gray-200 rounded-full h-2 mr-2">
                            <div
                              className="bg-green-500 h-2 rounded-full"
                              style={{ width: `${strength.proficiency}%` }}
                            ></div>
                          </div>
                          <span className="text-xs text-gray-500">{Math.round(strength.proficiency)}%</span>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Knowledge Gap Visualization */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Knowledge Gap Distribution</h3>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={[
                    { name: 'High Severity', value: knowledgeAnalysis.knowledge_gaps.filter(g => g.severity === 'high').length, fill: SEVERITY_COLORS.high },
                    { name: 'Medium Severity', value: knowledgeAnalysis.knowledge_gaps.filter(g => g.severity === 'medium').length, fill: SEVERITY_COLORS.medium },
                    { name: 'Low Severity', value: knowledgeAnalysis.knowledge_gaps.filter(g => g.severity === 'low').length, fill: SEVERITY_COLORS.low }
                  ]}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {knowledgeAnalysis.knowledge_gaps.map((entry, index) => (
                    <Cell key={`cell-${index}`} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Timeline Tab */}
      {activeTab === 'timeline' && visualizationData && (
        <div className="space-y-6">
          {/* Study History Timeline */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Study History Timeline</h3>
            <ResponsiveContainer width="100%" height={400}>
              <ScatterChart data={visualizationData.timeline_data}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" tickFormatter={formatDate} />
                <YAxis />
                <Tooltip
                  cursor={{ strokeDasharray: '3 3' }}
                  formatter={(value, name) => [value, name]}
                  labelFormatter={(label) => `Date: ${formatDate(label)}`}
                />
                <Legend />
                <Scatter name="Score" dataKey="score" fill="#3B82F6" />
                <Scatter name="Time Spent (min)" dataKey="time_spent" fill="#10B981" />
              </ScatterChart>
            </ResponsiveContainer>
          </div>

          {/* Milestones */}
          {visualizationData.milestones.length > 0 && (
            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Milestones</h3>
              <div className="space-y-4">
                {visualizationData.milestones.map((milestone, index) => (
                  <div key={index} className="flex items-start space-x-4">
                    <div className="flex-shrink-0 w-8 h-8 bg-yellow-100 rounded-full flex items-center justify-center">
                      <span className="text-sm">🏆</span>
                    </div>
                    <div className="flex-1">
                      <h4 className="font-medium text-gray-900">{milestone.name}</h4>
                      <p className="text-sm text-gray-600">{milestone.description}</p>
                      <p className="text-xs text-gray-500 mt-1">
                        {new Date(milestone.achieved_at).toLocaleDateString('en-US', {
                          year: 'numeric',
                          month: 'long',
                          day: 'numeric'
                        })}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Insights Tab */}
      {activeTab === 'insights' && (
        <div className="space-y-6">
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Learning Insights</h3>
            <div className="space-y-4">
              {learningInsights.map((insight, index) => (
                <div key={index} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-start space-x-3">
                    <span className="flex-shrink-0 text-2xl">{getInsightIcon(insight.type)}</span>
                    <div className="flex-1">
                      <h4 className="font-medium text-gray-900">{insight.title}</h4>
                      <p className="text-sm text-gray-600 mt-1">{insight.description}</p>
                      <div className="flex items-center justify-between mt-2">
                        <div className="flex items-center space-x-4">
                          <span className="text-xs text-gray-500">Topic: {insight.topic}</span>
                          <span className="text-xs text-gray-500">Confidence: {Math.round(insight.confidence * 100)}%</span>
                        </div>
                        <span className="text-xs text-gray-500">
                          {new Date(insight.generated_at).toLocaleDateString()}
                        </span>
                      </div>
                      {insight.suggestions.length > 0 && (
                        <div className="mt-2">
                          <p className="text-xs text-gray-500 mb-1">Suggestions:</p>
                          <ul className="text-xs text-gray-600 space-y-1">
                            {insight.suggestions.map((suggestion, i) => (
                              <li key={i}>• {suggestion}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
} 