import { Link, useNavigate } from "react-router-dom";
import { useState, useRef, useEffect, useContext } from "react";
import { AuthContext } from "../context/AuthContext";
import { APP_NAME } from "../utils/constants";
import { Menu, X, User, Settings, LogOut, Calendar, Users, Zap } from "lucide-react";

export default function MinimalNavbar() {
  const navigate = useNavigate();
  const { user, logout, token } = useContext(AuthContext);
  const [menuOpen, setMenuOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const menuRef = useRef(null);
  const profileRef = useRef(null);

  // Close dropdowns when clicking outside
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        setMenuOpen(false);
      }
      if (profileRef.current && !profileRef.current.contains(e.target)) {
        setProfileOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const navItems = [
    { name: "Dashboard", path: "/dashboard", icon: Calendar },
    { name: "Contacts", path: "/contacts", icon: Users },
    { name: "Integration", path: "/integration", icon: Zap },
  ];

  return (
    <nav className="bg-white border-b border-gray-200 sticky top-0 z-50">
      <div className="minimal-container">
        <div className="flex items-center justify-between h-16">
          {/* Brand */}
          <Link to="/" className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">PA</span>
            </div>
            <span className="minimal-heading minimal-heading-md text-gray-900">
              {APP_NAME}
            </span>
          </Link>

          {/* Desktop Navigation */}
          {user && (
            <div className="hidden md:flex items-center space-x-1">
              {navItems.map((item) => {
                const Icon = item.icon;
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    className="flex items-center space-x-2 px-3 py-2 rounded-lg text-sm font-medium text-gray-600 hover:text-gray-900 hover:bg-gray-50 transition-colors"
                  >
                    <Icon className="w-4 h-4" />
                    <span>{item.name}</span>
                  </Link>
                );
              })}
            </div>
          )}

          {/* Right Side */}
          <div className="flex items-center space-x-4">
            {user ? (
              <>
                {/* Profile Dropdown */}
                <div className="relative" ref={profileRef}>
                  <button
                    onClick={() => setProfileOpen(!profileOpen)}
                    className="flex items-center space-x-2 p-2 rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    <img
                      src={user.picture}
                      alt="Profile"
                      className="w-8 h-8 rounded-full"
                    />
                    <span className="minimal-text font-medium">{user.name?.split(" ")[0]}</span>
                  </button>

                  {profileOpen && (
                    <div className="absolute right-0 mt-2 w-48 minimal-card animate-fade-in">
                      <div className="p-2">
                        <div className="px-3 py-2 border-b border-gray-100">
                          <p className="minimal-text font-medium">{user.name}</p>
                          <p className="minimal-text-tertiary">{user.email}</p>
                        </div>
                        <Link
                          to="/account"
                          onClick={() => setProfileOpen(false)}
                          className="flex items-center space-x-2 px-3 py-2 text-sm text-gray-700 hover:bg-gray-50 rounded-lg"
                        >
                          <User className="w-4 h-4" />
                          <span>Account</span>
                        </Link>
                        <Link
                          to="/settings"
                          onClick={() => setProfileOpen(false)}
                          className="flex items-center space-x-2 px-3 py-2 text-sm text-gray-700 hover:bg-gray-50 rounded-lg"
                        >
                          <Settings className="w-4 h-4" />
                          <span>Settings</span>
                        </Link>
                        <button
                          onClick={() => {
                            setProfileOpen(false);
                            logout();
                            navigate("/");
                          }}
                          className="w-full flex items-center space-x-2 px-3 py-2 text-sm text-red-600 hover:bg-red-50 rounded-lg"
                        >
                          <LogOut className="w-4 h-4" />
                          <span>Logout</span>
                        </button>
                      </div>
                    </div>
                  )}
                </div>

                {/* Mobile Menu */}
                <div className="md:hidden relative" ref={menuRef}>
                  <button
                    onClick={() => setMenuOpen(!menuOpen)}
                    className="p-2 rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    {menuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
                  </button>

                  {menuOpen && (
                    <div className="absolute right-0 mt-2 w-48 minimal-card animate-fade-in">
                      <div className="p-2">
                        {navItems.map((item) => {
                          const Icon = item.icon;
                          return (
                            <Link
                              key={item.path}
                              to={item.path}
                              onClick={() => setMenuOpen(false)}
                              className="flex items-center space-x-2 px-3 py-2 text-sm text-gray-700 hover:bg-gray-50 rounded-lg"
                            >
                              <Icon className="w-4 h-4" />
                              <span>{item.name}</span>
                            </Link>
                          );
                        })}
                      </div>
                    </div>
                  )}
                </div>
              </>
            ) : (
              <div className="flex items-center space-x-3">
                <Link
                  to="/login"
                  className="minimal-button minimal-button-secondary"
                >
                  Login
                </Link>
                <Link
                  to="/signup"
                  className="minimal-button minimal-button-primary"
                >
                  Sign Up
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}
