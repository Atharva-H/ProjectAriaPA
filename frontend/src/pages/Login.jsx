import { APP_NAME } from "../utils/constants";

export default function Login() {
  const handleGoogleLogin = () => {
    window.location.href = `${import.meta.env.VITE_API_URL}/auth/login`;
  };

  return (
    <div className="flex flex-col md:flex-row min-h-screen w-full bg-gray-50">
      {/* Left Section */}
      <div className="flex flex-col justify-center items-center w-full md:w-1/2 bg-white px-8 md:px-16 py-12 border-r border-gray-200">
        <h1 className="text-4xl md:text-5xl font-bold text-gray-800 mb-6 text-center md:text-left">
          Welcome Back 👋
        </h1>
        <p className="text-gray-600 max-w-md text-center md:text-left mb-8 text-lg">
          Log in to your <strong>{APP_NAME}</strong> dashboard — your AI-powered
          business assistant for MSMEs.
        </p>
        <button
          onClick={handleGoogleLogin}
          className="bg-blue-600 text-white px-8 py-3 rounded-lg hover:bg-blue-700 text-lg transition-all"
        >
          Continue with Google
        </button>
      </div>

      {/* Right Section */}
      <div className="flex flex-col justify-center items-center w-full md:w-1/2 bg-gradient-to-br from-indigo-600 to-blue-700 text-white px-8 md:px-16 py-12">
        <h2 className="text-3xl font-semibold mb-4 text-center md:text-left">
          Smarter. Faster. Organized.
        </h2>
        <p className="text-blue-100 max-w-md text-center md:text-left leading-relaxed text-lg">
          Let {APP_NAME} handle your reminders, WhatsApp updates, and insights —
          while you focus on growth and strategy.
        </p>
      </div>
    </div>
  );
}
