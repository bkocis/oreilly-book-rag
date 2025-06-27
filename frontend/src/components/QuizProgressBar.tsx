import type { QuizProgress } from '../types/quiz';

interface QuizProgressBarProps {
  progress: QuizProgress;
}

export function QuizProgressBar({ progress }: QuizProgressBarProps) {
  const formatTime = (seconds: number): string => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 mb-6 shadow-sm">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium text-gray-700">
          Question {progress.current_question} of {progress.total_questions}
        </span>
        {progress.time_remaining !== undefined && (
          <div className="flex items-center text-sm text-gray-600">
            <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                    d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            {formatTime(progress.time_remaining)}
          </div>
        )}
      </div>
      
      <div className="w-full bg-gray-200 rounded-full h-3">
        <div 
          className="bg-primary-600 h-3 rounded-full transition-all duration-300 ease-out"
          style={{ width: `${progress.percentage}%` }}
        />
      </div>
      
      <div className="mt-2 text-xs text-gray-500 text-center">
        {progress.percentage.toFixed(0)}% Complete
      </div>
    </div>
  );
} 