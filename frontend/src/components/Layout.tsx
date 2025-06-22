import { type ReactNode } from 'react';
import { Link, useLocation } from 'react-router-dom';

interface LayoutProps {
  children: ReactNode;
}

export function Layout({ children }: LayoutProps) {
  const location = useLocation();

  const isActive = (path: string) => {
    return location.pathname === path ? 'text-primary-600 border-primary-600' : 'text-gray-600 hover:text-gray-900';
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <nav className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <Link to="/" className="text-xl font-bold text-gray-900">
                O'Reilly Quiz RAG
              </Link>
            </div>
            <div className="flex items-center space-x-8">
              <Link 
                to="/" 
                className={`px-3 py-2 text-sm font-medium border-b-2 border-transparent ${isActive('/')}`}
              >
                Home
              </Link>
              <Link 
                to="/quiz" 
                className={`px-3 py-2 text-sm font-medium border-b-2 border-transparent ${isActive('/quiz')}`}
              >
                Take Quiz
              </Link>
              <Link 
                to="/dashboard" 
                className={`px-3 py-2 text-sm font-medium border-b-2 border-transparent ${isActive('/dashboard')}`}
              >
                Dashboard
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        {children}
      </main>
    </div>
  );
} 