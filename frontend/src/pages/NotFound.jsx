import { Link } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { Home, ArrowLeft, Search, AlertCircle } from "lucide-react";

export default function NotFound() {
  const { user } = useAuth();

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="text-center max-w-md mx-auto px-4">
        {/* 404 Icon */}
        <div className="mb-8">
          <div className="w-24 h-24 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <AlertCircle className="w-12 h-12 text-red-600" />
          </div>
          <h1 className="minimal-heading minimal-heading-xl text-6xl font-bold text-gray-900 mb-2">
            404
          </h1>
          <h2 className="minimal-heading minimal-heading-lg text-gray-600 mb-4">
            Page Not Found
          </h2>
          <p className="minimal-text-secondary mb-8">
            The page you're looking for doesn't exist or has been moved.
          </p>
        </div>

        {/* Action Buttons */}
        <div className="space-y-4">
          {user ? (
            <Link
              to="/dashboard"
              className="minimal-button minimal-button-primary w-full"
            >
              <Home className="w-4 h-4 mr-2" />
              Go to Dashboard
            </Link>
          ) : (
            <Link
              to="/"
              className="minimal-button minimal-button-primary w-full"
            >
              <Home className="w-4 h-4 mr-2" />
              Go to Home
            </Link>
          )}
          
          <button
            onClick={() => window.history.back()}
            className="minimal-button minimal-button-secondary w-full"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Go Back
          </button>
        </div>

        {/* Help Text */}
        <div className="mt-8 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-center space-x-2 mb-2">
            <Search className="w-4 h-4 text-blue-600" />
            <span className="minimal-text font-medium text-blue-800">Need Help?</span>
          </div>
          <p className="minimal-text-tertiary text-blue-700">
            If you think this is an error, please contact support or try refreshing the page.
          </p>
        </div>
      </div>
    </div>
  );
}
