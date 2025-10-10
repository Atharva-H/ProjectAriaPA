import { useState } from "react";
import { Link } from "react-router-dom";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const handleEmailLogin = (e) => {
    e.preventDefault();
    alert(`Email login not implemented yet.\nEmail: ${email}\nPassword: ${password}`);
  };

  const handleGoogleLogin = () => {
    window.location.href = "http://localhost:8000/auth/login";
  };

  return (
    <div className="flex flex-col md:flex-row h-[calc(100vh-64px)] bg-gray-50">
      {/* Left: Email login */}
      <div className="flex flex-col justify-center items-center w-full md:w-1/2 bg-white border-r">
        <div className="w-3/4 max-w-sm">
          <h1 className="text-3xl font-bold text-gray-800 mb-6">
            Welcome Back 👋
          </h1>
          <form onSubmit={handleEmailLogin} className="flex flex-col gap-4">
            <div>
              <label className="block text-sm text-gray-600 mb-1">Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                className="w-full border border-gray-300 px-3 py-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>

            <div>
              <label className="block text-sm text-gray-600 mb-1">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full border border-gray-300 px-3 py-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>

            <button
              type="submit"
              className="bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 transition-all mt-2"
            >
              Login
            </button>

            <p className="text-sm text-gray-500 mt-3 text-center">
              Don’t have an account?{" "}
              <Link to="/signup" className="text-blue-600 hover:underline">
                Create one
              </Link>
            </p>
          </form>
        </div>
      </div>

      {/* Right: Google Sign-In */}
      <div className="flex flex-col justify-center items-center w-full md:w-1/2 bg-gradient-to-br from-blue-600 to-indigo-700 text-white">
        <div className="text-center max-w-sm">
          <h2 className="text-3xl font-semibold mb-4">Login with Google</h2>
          <p className="mb-6 text-blue-100">
            Securely sign in with your Google account to access your dashboard.
          </p>
          <button
            onClick={handleGoogleLogin}
            className="bg-white text-blue-600 font-semibold px-6 py-2 rounded-lg shadow hover:bg-gray-100 transition-all"
          >
            Continue with Google
          </button>
        </div>
      </div>
    </div>
  );
}
