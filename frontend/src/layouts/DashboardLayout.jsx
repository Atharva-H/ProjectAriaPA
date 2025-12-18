// src/layouts/DashboardLayout.jsx
import { Outlet, Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { useState, useEffect, useRef } from "react";
import chatService from "../services/chatService";
import {
  Calendar,
  MessageSquare,
  Users,
  Zap,
  Calculator,
  BarChart3,
  Settings,
  LogOut,
  Menu,
  X,
  Plus,
  Search,
  HelpCircle,
  ChevronUp
} from "lucide-react";
import { APP_NAME } from "../utils/constants";

export default function DashboardLayout() {
  const { user, logout, token } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
  const userMenuRef = useRef(null);

  // Chat History State
  const [chatDates, setChatDates] = useState([]);
  const [selectedDate, setSelectedDate] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");

  // Close user menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (userMenuRef.current && !userMenuRef.current.contains(event.target)) {
        setIsUserMenuOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const navItems = [
    { name: "Chat", path: "/chat", icon: MessageSquare },
    { name: "Dashboard", path: "/dashboard", icon: Calendar },
    {
      name: "Accounting",
      path: "/accounting",
      icon: Calculator,
      subItems: [
        { name: "Overview", path: "/accounting/dashboard", icon: BarChart3 }
      ]
    },
  ];

  // Fetch chat dates
  useEffect(() => {
    const loadChatDates = async () => {
      if (!token) return;
      try {
        const datesData = await chatService.getChatDates();
        setChatDates(datesData.dates || []);
      } catch (err) {
        console.error('Error loading chat dates:', err);
      }
    };
    loadChatDates();
  }, [token]);

  // Group dates logic
  const groupDates = () => {
    const today = new Date().toISOString().split('T')[0];
    const yesterday = new Date(Date.now() - 86400000).toISOString().split('T')[0];

    const groups = {
      'Today': [],
      'Yesterday': [],
      'Previous 7 Days': [],
      'Older': []
    };

    // Filter by search query if present
    const filteredDates = searchQuery
      ? chatDates.filter(item => item.date.includes(searchQuery)) // Simple date search for now
      : chatDates;

    filteredDates.forEach(item => {
      const date = item.date;
      if (date === today) {
        groups['Today'].push(item);
      } else if (date === yesterday) {
        groups['Yesterday'].push(item);
      } else {
        const dateObj = new Date(date);
        const diffTime = Math.abs(new Date() - dateObj);
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

        if (diffDays <= 7) {
          groups['Previous 7 Days'].push(item);
        } else {
          groups['Older'].push(item);
        }
      }
    });

    return groups;
  };

  const handleLogout = () => {
    logout();
    navigate("/");
  };

  const handleChatHistoryClick = (date) => {
    setSelectedDate(date);
    navigate('/chat');
    setIsMobileMenuOpen(false);
  };

  const handleNewChat = () => {
    setSelectedDate(null);
    navigate('/chat');
    setIsMobileMenuOpen(false);
  }

  return (
    <div className="flex h-screen bg-white dark:bg-[#343541]">
      {/* Mobile Menu Overlay */}
      {isMobileMenuOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 md:hidden"
          onClick={() => setIsMobileMenuOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside className={`
        fixed inset-y-0 left-0 z-50 w-[260px] bg-[#202123] text-white transition-transform duration-300 transform
        ${isMobileMenuOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}
        flex flex-col border-r border-white/10
      `}>
        {/* Header */}
        <div className="p-4 flex items-center gap-3 border-b border-white/10">
          <div className="w-8 h-8 bg-[#10a37f] rounded-lg flex items-center justify-center">
            <span className="text-white font-bold text-sm">PA</span>
          </div>
          <span className="font-semibold text-lg tracking-tight">{APP_NAME}</span>
          <button
            onClick={() => setIsMobileMenuOpen(false)}
            className="md:hidden ml-auto text-gray-400 hover:text-white"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Navigation Content */}
        <div className="flex-1 overflow-y-auto custom-scrollbar">
          {/* Main Menu */}
          <nav className="p-3 space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname.startsWith(item.path);

              return (
                <div key={item.path}>
                  <Link
                    to={item.path}
                    onClick={() => setIsMobileMenuOpen(false)}
                    className={`flex items-center gap-3 px-3 py-3 rounded-md text-sm transition-colors ${isActive
                        ? "bg-[#343541] text-white"
                        : "text-gray-300 hover:bg-[#2A2B32] hover:text-white"
                      }`}
                  >
                    <Icon className="w-4 h-4" />
                    <span className="flex-1">{item.name}</span>
                  </Link>

                  {/* Sub-items */}
                  {item.subItems && isActive && (
                    <div className="ml-4 mt-1 space-y-1 border-l border-white/10 pl-2">
                      {item.subItems.map((subItem) => {
                        const SubIcon = subItem.icon;
                        const isSubActive = location.pathname === subItem.path;
                        return (
                          <Link
                            key={subItem.path}
                            to={subItem.path}
                            onClick={() => setIsMobileMenuOpen(false)}
                            className={`flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors ${isSubActive
                                ? "text-white bg-white/5"
                                : "text-gray-400 hover:text-white hover:bg-white/5"
                              }`}
                          >
                            <SubIcon className="w-3 h-3" />
                            <span>{subItem.name}</span>
                          </Link>
                        );
                      })}
                    </div>
                  )}
                </div>
              );
            })}
          </nav>

          {/* Search Chat */}
          <div className="px-3 py-2">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search chat..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-[#202123] border border-white/20 rounded-md py-2 pl-9 pr-3 text-sm text-white placeholder-gray-400 focus:outline-none focus:border-white/40 transition-colors"
              />
            </div>
          </div>

          {/* Divider */}
          <div className="h-px bg-white/10 mx-3 my-2" />

          {/* Chat History Section */}
          <div className="px-3 pb-2">
            <h3 className="text-xs font-medium text-gray-400 px-3 mb-2 uppercase tracking-wider">
              your chats
            </h3>

            {Object.entries(groupDates()).map(([group, items]) => (
              items.length > 0 && (
                <div key={group} className="mb-4">
                  <h4 className="text-xs font-medium text-gray-500 px-3 mb-2">
                    {group}
                  </h4>
                  <div className="space-y-1">
                    {items.map((item) => (
                      <button
                        key={item.date}
                        onClick={() => handleChatHistoryClick(item.date)}
                        className={`w-full text-left px-3 py-3 rounded-md flex items-center gap-3 text-sm transition-colors group relative overflow-hidden ${selectedDate === item.date && location.pathname === '/chat' ? 'bg-[#343541]' : 'hover:bg-[#2A2B32]'
                          }`}
                      >
                        <MessageSquare className="w-4 h-4 text-gray-400" />
                        <span className="truncate flex-1 text-gray-300">
                          {new Date(item.date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
                        </span>
                      </button>
                    ))}
                  </div>
                </div>
              )
            ))}
          </div>
        </div>

        {/* User Profile / Footer Menu */}
        <div className="p-3 border-t border-white/10 relative" ref={userMenuRef}>
          {isUserMenuOpen && (
            <div className="absolute bottom-full left-0 w-full mb-2 px-3 z-50">
              <div className="bg-[#2A2B32] rounded-lg shadow-lg border border-white/10 overflow-hidden">
                <Link
                  to="/settings"
                  onClick={() => setIsUserMenuOpen(false)}
                  className="flex items-center gap-3 px-4 py-3 text-sm text-gray-300 hover:bg-[#343541] hover:text-white transition-colors"
                >
                  <Settings className="w-4 h-4" />
                  Edit Profile
                </Link>
                <Link
                  to="/integration"
                  onClick={() => setIsUserMenuOpen(false)}
                  className="flex items-center gap-3 px-4 py-3 text-sm text-gray-300 hover:bg-[#343541] hover:text-white transition-colors"
                >
                  <Zap className="w-4 h-4" />
                  Integration
                </Link>
                <Link
                  to="/contacts"
                  onClick={() => setIsUserMenuOpen(false)}
                  className="flex items-center gap-3 px-4 py-3 text-sm text-gray-300 hover:bg-[#343541] hover:text-white transition-colors"
                >
                  <Users className="w-4 h-4" />
                  Contacts
                </Link>
                <Link
                  to="/help"
                  onClick={() => setIsUserMenuOpen(false)}
                  className="flex items-center gap-3 px-4 py-3 text-sm text-gray-300 hover:bg-[#343541] hover:text-white transition-colors"
                >
                  <HelpCircle className="w-4 h-4" />
                  Help
                </Link>
                <div className="h-px bg-white/10 my-1" />
                <button
                  onClick={handleLogout}
                  className="w-full flex items-center gap-3 px-4 py-3 text-sm text-red-400 hover:bg-[#343541] hover:text-red-300 transition-colors"
                >
                  <LogOut className="w-4 h-4" />
                  Logout
                </button>
              </div>
            </div>
          )}

          <button
            onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
            className={`flex items-center gap-3 w-full px-3 py-3 rounded-md transition-colors cursor-pointer group ${isUserMenuOpen ? 'bg-[#2A2B32]' : 'hover:bg-[#2A2B32]'}`}
          >
            {user?.picture ? (
              <img src={user.picture} alt="Profile" className="w-8 h-8 rounded-full" />
            ) : (
              <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-emerald-400 to-cyan-500 flex items-center justify-center text-white font-bold text-xs">
                {user?.name?.charAt(0) || 'U'}
              </div>
            )}
            <div className="flex-1 min-w-0 text-left">
              <p className="text-sm font-medium text-white truncate">{user?.name || 'User'}</p>
              <p className="text-xs text-gray-400 truncate">{user?.email}</p>
            </div>
            <ChevronUp className={`w-4 h-4 text-gray-400 transition-transform ${isUserMenuOpen ? 'rotate-180' : ''}`} />
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col md:pl-[260px] h-full overflow-hidden">
        {/* Mobile Header */}
        <div className="md:hidden flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-800 bg-white dark:bg-[#343541]">
          <button
            onClick={() => setIsMobileMenuOpen(true)}
            className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
          >
            <Menu className="w-6 h-6" />
          </button>
          <span className="font-semibold text-gray-900 dark:text-white">{APP_NAME}</span>
          <div className="w-6" /> {/* Spacer for centering */}
        </div>

        <main className="flex-1 overflow-y-auto bg-gray-50 dark:bg-[#343541]">
          <Outlet context={{ selectedDate, setSelectedDate }} />
        </main>
      </div>
    </div>
  );
}
