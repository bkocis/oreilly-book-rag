import React, { useState, useEffect } from 'react';
import { learningService } from '../services/learningService';
import { quizService } from '../services/quizService';
import { analyticsService } from '../services/analyticsService';

interface ApiTestResult {
  endpoint: string;
  status: 'success' | 'error' | 'loading';
  data?: any;
  error?: string;
}

const ApiTestComponent: React.FC = () => {
  const [testResults, setTestResults] = useState<ApiTestResult[]>([]);
  
  const testEndpoints = async () => {
    const tests: { name: string; fn: () => Promise<any> }[] = [
      {
        name: 'Difficulty Levels',
        fn: () => learningService.getDifficultyLevels()
      },
      {
        name: 'Topics',
        fn: () => learningService.getTopics()
      },
      {
        name: 'Analytics Health',
        fn: () => analyticsService.healthCheck()
      }
    ];

    const results: ApiTestResult[] = [];
    
    for (const test of tests) {
      try {
        setTestResults(prev => [...prev.filter(r => r.endpoint !== test.name), 
          { endpoint: test.name, status: 'loading' }]);
        
        const data = await test.fn();
        results.push({
          endpoint: test.name,
          status: 'success',
          data: data
        });
      } catch (error) {
        results.push({
          endpoint: test.name,
          status: 'error',
          error: error instanceof Error ? error.message : 'Unknown error'
        });
      }
    }
    
    setTestResults(results);
  };

  useEffect(() => {
    testEndpoints();
  }, []);

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h2 className="text-2xl font-bold mb-6">API Connection Test</h2>
      
      <button 
        onClick={testEndpoints}
        className="mb-6 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
      >
        Run Tests Again
      </button>

      <div className="space-y-4">
        {testResults.map((result) => (
          <div key={result.endpoint} 
               className={`p-4 rounded border-l-4 ${
                 result.status === 'success' ? 'border-green-500 bg-green-50' :
                 result.status === 'error' ? 'border-red-500 bg-red-50' :
                 'border-yellow-500 bg-yellow-50'
               }`}>
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-semibold">{result.endpoint}</h3>
              <span className={`px-2 py-1 rounded text-sm ${
                result.status === 'success' ? 'bg-green-200 text-green-800' :
                result.status === 'error' ? 'bg-red-200 text-red-800' :
                'bg-yellow-200 text-yellow-800'
              }`}>
                {result.status}
              </span>
            </div>
            
            {result.status === 'error' && (
              <div className="text-red-600 text-sm">
                Error: {result.error}
              </div>
            )}
            
            {result.status === 'success' && result.data && (
              <div className="mt-2">
                <details className="cursor-pointer">
                  <summary className="text-sm text-gray-600">View Response Data</summary>
                  <pre className="mt-2 p-2 bg-gray-100 rounded text-xs overflow-auto max-h-40">
                    {JSON.stringify(result.data, null, 2)}
                  </pre>
                </details>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default ApiTestComponent; 