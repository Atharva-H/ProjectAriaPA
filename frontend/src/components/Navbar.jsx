import { Link, useNavigate } from "react-router-dom";
import { useEffect, useState, useRef } from "react";

export default function Navbar() {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef(null);

  const loadUser = async () => {
    const token = localStorage.getItem("jwt");
    if (!token) return;

    try {
      const res = await fetch("http://localhost:8000/auth/me", {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();

      if (data.refresh && data.token) {
        localStorage.setItem("jwt", data.token);
        return loadUser();
      }

      if (data.name) setUser(data);
      else localStorage.removeItem("jwt");
    } catch (err) {
      console.error("Error loading user:", err);
      localStorage.removeItem("jwt");
    }
  };

  useEffect(() => {
    loadUser();
  }, []);

  const handleLogout = () => {
    localStorage.removeItem("jwt");
    setUser(null);
    navigate("/");
  };

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        setMenuOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <nav className="bg-white dark:bg-gray-900 shadow-sm py-3 px-6 flex justify-between items-center sticky top-0 z-10 transition-colors">
      {/* Brand */}
      <Link to="/" className="text-2xl font-bold text-blue-600 dark:text-blue-400 tracking-tight">
        Project Aria.PA
      </Link>

      {/* Navigation Links */}
      <div className="flex gap-6 text-gray-700 dark:text-gray-300 font-medium">
        {!user && (
          <>
            <Link to="/" className="hover:text-blue-600 dark:hover:text-blue-400 transition">Home</Link>
            <Link to="/about" className="hover:text-blue-600 dark:hover:text-blue-400 transition">About</Link>
          </>
        )}
        {user && (
          <Link to="/dashboard" className="hover:text-blue-600 dark:hover:text-blue-400 transition">
            Dashboard
          </Link>
        )}
      </div>

      {/* Right Side */}
      <div className="relative" ref={menuRef}>
        {user ? (
          <>
            <button
              onClick={() => setMenuOpen(!menuOpen)}
              className="flex items-center gap-3 focus:outline-none"
            >
              <span className="text-gray-800 dark:text-gray-200 font-medium">
                {user.name.split(" ")[0]}
              </span>
              <img
                src={user.picture}
                alt="Profile"
                className="w-9 h-9 rounded-full border-2 border-blue-500 hover:scale-105 transition"
              />
            </button>

            {menuOpen && (
              <div className="absolute right-0 mt-2 w-52 bg-white dark:bg-gray-800 rounded-xl shadow-lg border dark:border-gray-700 p-2 animate-fade-in">
                <Link
                  to="/account"
                  className="block px-4 py-2 rounded-md text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700"
                  onClick={() => setMenuOpen(false)}
                >
                  Account Details
                </Link>
                <Link
                  to="/integration"
                  className="block px-4 py-2 rounded-md text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700"
                  onClick={() => setMenuOpen(false)}
                >
                  Integration
                </Link>
                <Link
                  to="/settings"
                  className="block px-4 py-2 rounded-md text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700"
                  onClick={() => setMenuOpen(false)}
                >
                  Settings
                </Link>
                <button
                  onClick={handleLogout}
                  className="w-full text-left px-4 py-2 rounded-md text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20"
                >
                  Logout
                </button>
              </div>
            )}
          </>
        ) : (
          <>
            <Link
              to="/login"
              className="bg-blue-600 text-white px-4 py-1 rounded-lg hover:bg-blue-700 text-sm"
            >
              Login
            </Link>
            <Link
              to="/signup"
              className="bg-gray-200 text-gray-700 px-4 py-1 rounded-lg hover:bg-gray-300 text-sm"
            >
              Sign Up
            </Link>
          </>
        )}
      </div>
    </nav>
  );
}
