import { Link } from "react-router-dom";

export default function Home() {
  return (
    <div className="flex flex-col items-center justify-center h-[calc(100vh-64px)] bg-gray-50 text-center px-4">
      <h1 className="text-5xl font-bold text-gray-800 mb-4">
        Your AI-Powered Business Assistant
      </h1>
      <p className="text-lg text-gray-600 max-w-2xl mb-8">
        Project Aria.PA helps MSME CEOs like you stay on top of everything —
        from reminders and reports to intelligent insights — all in one place.
      </p>
      <Link
        to="/login"
        className="bg-blue-600 text-white px-6 py-3 rounded-lg text-lg font-medium hover:bg-blue-700"
      >
        Get Started
      </Link>
    </div>
  );
}
