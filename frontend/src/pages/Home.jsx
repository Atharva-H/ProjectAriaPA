import { Link } from "react-router-dom";
import { APP_NAME, APP_TAGLINE } from "../utils/constants";

export default function Home() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[calc(100vh-64px)] bg-gradient-to-b from-white to-gray-50 text-center px-6">
      <h1 className="text-5xl md:text-6xl font-extrabold text-gray-800 mb-4">
        {APP_NAME} <span className="text-blue-600">– AI Business Assistant</span>
      </h1>

      <p className="text-lg md:text-xl text-gray-600 max-w-2xl mb-8 leading-relaxed">
        {APP_TAGLINE} Stay on top of your schedule, WhatsApp updates,
        and daily reports — all in one place.
      </p>

      <Link
        to="/login"
        className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-3 rounded-xl text-lg font-medium transition-all duration-300 shadow-sm hover:shadow-md"
      >
        Get Started
      </Link>

      <div className="mt-12 text-gray-500 text-sm">
        <p>Built for MSME CEOs to simplify management, communication, and insights.</p>
      </div>
    </div>
  );
}
