import { Link, useNavigate } from "react-router-dom";
import { useState, useRef, useEffect, useContext } from "react";
import { AuthContext } from "../context/AuthContext";
import { APP_NAME } from "../utils/constants";
import logo from "../assets/logo.png";


export default function Navbar() {
  const navigate = useNavigate();
  const { user, logout, token } = useContext(AuthContext);
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef(null);

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
      <Link
        to="/"
        className="text-2xl font-bold text-blue-600 dark:text-blue-400 tracking-tight"
      >
        {APP_NAME}
      </Link>

      {/* Navigation Links */}
      <div className="flex gap-6 text-gray-700 dark:text-gray-300 font-medium">
        {!token && (
          <>
            <Link
              to="/"
              className="hover:text-blue-600 dark:hover:text-blue-400 transition"
            >
              Home
            </Link>
            <Link
              to="/about"
              className="hover:text-blue-600 dark:hover:text-blue-400 transition"
            >
              About
            </Link>
          </>
        )}
        {user && (
          <Link
            to="/dashboard"
            className="hover:text-blue-600 dark:hover:text-blue-400 transition"
          >
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
                {user.name?.split(" ")[0]}
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
                  onClick={() => setMenuOpen(false)}
                  className="block px-4 py-2 rounded-md text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700"
                >
                  Account Details
                </Link>
                <Link
                  to="/integration"
                  onClick={() => setMenuOpen(false)}
                  className="block px-4 py-2 rounded-md text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700"
                >
                  Integration
                </Link>
                <Link
                  to="/settings"
                  onClick={() => setMenuOpen(false)}
                  className="block px-4 py-2 rounded-md text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700"
                >
                  Settings
                </Link>
                <button
                  onClick={() => {
                    setMenuOpen(false);
                    logout();
                    navigate("/");
                  }}
                  className="w-full text-left px-4 py-2 rounded-md text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20"
                >
                  Logout
                </button>
              </div>
            )}
          </>
        ) : (
          <div className="flex gap-2">
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
          </div>
        )}
      </div>
    </nav>
  );
}
