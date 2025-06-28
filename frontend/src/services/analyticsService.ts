import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/v1';

// Types for analytics data
export interface PerformanceMetrics {
  user_id: string;
  period: string;
  total_sessions: number;
  total_questions: number;
  accuracy_rate: number;
  average_score: number;
  time_spent_hours: number;
  improvement_rate: number;
  streak_days: number;
  completion_rate: number;
  engagement_score: number;
  skill_velocity: number;
}

export interface ProgressVisualizationData {
  user_id: string;
  timeline_data: Array<{
    date: string;
    score: number;
    accuracy: number;
    time_spent: number;
    topic: string;
  }>;
  topic_breakdown: Record<string, {
    sessions: number;
    average_score: number;
    accuracy: number;
    total_questions: number;
  }>;
  skill_progression: Record<string, number>;
  performance_trends: {
    score_trend: Array<{ date: string; value: number }>;
    accuracy_trend: Array<{ date: string; value: number }>;
    time_trend: Array<{ date: string; value: number }>;
  };
  milestones: Array<{
    name: string;
    achieved_at: string;
    description: string;
    category: string;
  }>;
  comparative_analytics: {
    percentile_ranking: number;
    peer_comparison: {
      better_than: number;
      similar_to: number;
      worse_than: number;
    };
    global_averages: {
      accuracy: number;
      score: number;
      session_length: number;
    };
  };
}

export interface KnowledgeGap {
  topic: string;
  severity: 'low' | 'medium' | 'high';
  confidence: number;
  description: string;
  impact_score: number;
  suggested_actions: string[];
}

export interface KnowledgeAnalysis {
  user_id: string;
  knowledge_gaps: KnowledgeGap[];
  strengths: Array<{
    topic: string;
    proficiency: number;
    description: string;
  }>;
  recommendations: Array<{
    title: string;
    description: string;
    priority: 'high' | 'medium' | 'low';
    estimated_time: number;
    topic: string;
    difficulty: string;
  }>;
}

export interface LearningInsight {
  id: string;
  type: 'knowledge_gap' | 'strength' | 'improvement' | 'regression' | 'mastery_achieved';
  title: string;
  description: string;
  confidence: number;
  impact_score: number;
  topic: string;
  suggestions: string[];
  generated_at: string;
}

export interface StudyRecommendationData {
  user_id: string;
  recommendations: Array<{
    title: string;
    description: string;
    priority: 'high' | 'medium' | 'low';
    estimated_time: number;
    topic: string;
    difficulty: string;
    reasoning: string;
  }>;
  spaced_repetition_items: Array<{
    topic: string;
    next_review_date: string;
    current_level: number;
    mastery_score: number;
  }>;
  optimal_study_times: string[];
  focus_areas: string[];
}

export interface AnalyticsReport {
  report_id: string;
  user_id: string;
  generated_at: string;
  period: string;
  executive_summary: {
    overall_performance: string;
    key_achievements: string[];
    areas_for_improvement: string[];
    next_steps: string[];
  };
  performance_metrics: PerformanceMetrics;
  learning_insights: LearningInsight[];
  knowledge_analysis: KnowledgeAnalysis;
  recommendations: StudyRecommendationData;
}

export type AnalyticsPeriod = 'week' | 'month' | 'quarter' | 'year' | 'all_time';
export type ExportFormat = 'json' | 'csv';

export class AnalyticsService {
  private api = axios.create({
    baseURL: `${API_BASE_URL}/analytics`,
    headers: {
      'Content-Type': 'application/json',
    },
  });

  // Performance Analytics
  async getPerformanceMetrics(
    userId: string, 
    period: AnalyticsPeriod = 'month',
    topic?: string
  ): Promise<PerformanceMetrics> {
    const params = new URLSearchParams({ period });
    if (topic) params.append('topic', topic);
    
    const response = await this.api.get(`/performance/${userId}?${params}`);
    return response.data;
  }

  // Progress Visualization Data
  async getProgressVisualizationData(
    userId: string,
    period: AnalyticsPeriod = 'month'
  ): Promise<ProgressVisualizationData> {
    const response = await this.api.get(`/progress-visualization/${userId}?period=${period}`);
    return response.data;
  }

  // Learning Insights
  async getLearningInsights(
    userId: string,
    maxInsights: number = 10,
    minConfidence: number = 0.6
  ): Promise<LearningInsight[]> {
    const response = await this.api.get(`/insights/${userId}?max_insights=${maxInsights}&min_confidence=${minConfidence}`);
    return response.data;
  }

  // Knowledge Gap Analysis
  async analyzeKnowledgeGaps(
    userId: string,
    minConfidence: number = 0.7,
    includeRecommendations: boolean = true
  ): Promise<KnowledgeAnalysis> {
    const response = await this.api.post('/knowledge-gaps', {
      user_id: userId,
      min_confidence_threshold: minConfidence,
      include_recommendations: includeRecommendations
    });
    return response.data;
  }

  // Study Recommendations
  async getStudyRecommendations(
    userId: string,
    maxRecommendations: number = 5
  ): Promise<StudyRecommendationData> {
    const response = await this.api.get(`/study-recommendations/${userId}?max_recommendations=${maxRecommendations}`);
    return response.data;
  }

  // Comprehensive Report
  async generateComprehensiveReport(
    userId: string,
    period: AnalyticsPeriod = 'month'
  ): Promise<AnalyticsReport> {
    const response = await this.api.get(`/report/${userId}?period=${period}`);
    return response.data;
  }

  // Export Analytics Data
  async exportAnalyticsData(
    userId: string,
    format: ExportFormat = 'json',
    period: AnalyticsPeriod = 'month',
    includeRawData: boolean = false
  ): Promise<Blob> {
    const params = new URLSearchParams({
      format,
      period,
      include_raw_data: includeRawData.toString()
    });
    
    const response = await this.api.get(`/export/${userId}?${params}`, {
      responseType: 'blob'
    });
    return response.data;
  }

  // Health Check
  async healthCheck(): Promise<{ status: string; service: string; timestamp: string; version: string }> {
    const response = await this.api.get('/health');
    return response.data;
  }
}

export const analyticsService = new AnalyticsService(); 