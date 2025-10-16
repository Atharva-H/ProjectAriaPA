import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import API from "../services/api";
import { formatDate } from "../utils/formatDate";
import { 
  Calendar, 
  Clock, 
  Users, 
  CheckSquare, 
  Bell, 
  Plus,
  ArrowRight,
  AlertCircle,
  CheckCircle2,
  Video,
  ExternalLink
} from "lucide-react";

export default function MinimalDashboard() {
  const { user, token, loading: authLoading } = useAuth();
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState("");
  const navigate = useNavigate();

  // Mock data for tasks and notifications
  const [tasks] = useState([
    { id: 1, title: "Review Q4 budget proposal", due: "Today", priority: "high", completed: false },
    { id: 2, title: "Call with design team", due: "Tomorrow", priority: "medium", completed: false },
    { id: 3, title: "Update project timeline", due: "This week", priority: "low", completed: true },
  ]);

  const [notifications] = useState([
    { id: 1, type: "meeting", message: "Team standup in 15 minutes", time: "9:45 AM" },
    { id: 2, type: "task", message: "Budget review due today", time: "2:00 PM" },
    { id: 3, type: "reminder", message: "Client call tomorrow at 10 AM", time: "4:30 PM" },
  ]);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const jwt = params.get("token");
  
    if (jwt) {
      localStorage.setItem("token", jwt);
      const cleanUrl = window.location.origin + window.location.pathname;
      window.history.replaceState({}, document.title, cleanUrl);
      window.location.reload();
    }
  }, []);

  useEffect(() => {
    const fetchEvents = async () => {
      if (!token) {
        navigate("/login");
        return;
      }

      try {
        const res = await API.get("/calendar/today", {
          headers: { Authorization: `Bearer ${token}` },
        });

        if (res.data.error) {
          setErrorMsg(res.data.error);
          setEvents([]);
        } else {
          setEvents(res.data.events || []);
        }
      } catch (err) {
        console.error("❌ Error fetching events:", err);
        setErrorMsg("Failed to fetch calendar data.");
      } finally {
        setLoading(false);
      }
    };

    if (!authLoading) fetchEvents();
  }, [token, authLoading, navigate]);

  if (authLoading || loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="minimal-text-secondary">Loading your dashboard...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    navigate("/login");
    return null;
  }

  const completedTasks = tasks.filter(t => t.completed).length;
  const pendingTasks = tasks.filter(t => !t.completed).length;

  // Helper function to extract Google Meet link from event
  const getMeetingLink = (event) => {
    // Check for Google Meet link in conferenceData or hangoutLink
    if (event.conferenceData?.entryPoints) {
      const meetLink = event.conferenceData.entryPoints.find(
        entry => entry.entryPointType === 'video' && entry.uri?.includes('meet.google.com')
      );
      if (meetLink) return meetLink.uri;
    }
    
    // Check for hangoutLink (legacy Google Meet)
    if (event.hangoutLink) return event.hangoutLink;
    
    // Check for meet.google.com in description
    if (event.description) {
      const meetMatch = event.description.match(/https:\/\/meet\.google\.com\/[a-z0-9-]+/i);
      if (meetMatch) return meetMatch[0];
    }
    
    return null;
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="minimal-container py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="minimal-heading minimal-heading-xl mb-2">
            Good morning, {user.name?.split(" ")[0]} 👋
          </h1>
          <p className="minimal-text-secondary">
            Here's what's happening today
          </p>
        </div>

        {/* Stats Grid */}
        <div className="minimal-grid minimal-grid-3 mb-8">
          <div className="minimal-card p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="p-2 bg-blue-100 rounded-lg">
                <Calendar className="w-5 h-5 text-blue-600" />
              </div>
              <span className="minimal-text-tertiary">Today</span>
            </div>
            <h3 className="minimal-heading minimal-heading-lg mb-1">{events.length}</h3>
            <p className="minimal-text-secondary">Meetings scheduled</p>
          </div>

          <div className="minimal-card p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="p-2 bg-green-100 rounded-lg">
                <CheckSquare className="w-5 h-5 text-green-600" />
              </div>
              <span className="minimal-text-tertiary">Tasks</span>
            </div>
            <h3 className="minimal-heading minimal-heading-lg mb-1">{completedTasks}/{tasks.length}</h3>
            <p className="minimal-text-secondary">Tasks completed</p>
          </div>

          <div className="minimal-card p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="p-2 bg-orange-100 rounded-lg">
                <Bell className="w-5 h-5 text-orange-600" />
              </div>
              <span className="minimal-text-tertiary">Alerts</span>
            </div>
            <h3 className="minimal-heading minimal-heading-lg mb-1">{notifications.length}</h3>
            <p className="minimal-text-secondary">New notifications</p>
          </div>
        </div>

        <div className="minimal-grid minimal-grid-2">
          {/* Today's Meetings */}
          <div className="minimal-card p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="minimal-heading minimal-heading-md">Today's Meetings</h2>
              <button className="minimal-button minimal-button-secondary">
                <Plus className="w-4 h-4 mr-2" />
                Add
              </button>
            </div>

            {errorMsg && (
              <div className="p-4 bg-red-50 border border-red-200 rounded-lg mb-4">
                <div className="flex items-center">
                  <AlertCircle className="w-5 h-5 text-red-600 mr-2" />
                  <p className="minimal-text text-red-700">{errorMsg}</p>
                </div>
              </div>
            )}

            {events.length === 0 ? (
              <div className="text-center py-8">
                <Calendar className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                <p className="minimal-text-secondary mb-2">No meetings today</p>
                <p className="minimal-text-tertiary">You're all caught up! 🎉</p>
              </div>
            ) : (
              <div className="space-y-3">
                {events.map((event) => {
                  const meetingLink = getMeetingLink(event);
                  return (
                    <div key={event.id} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                      <div className="flex items-center space-x-3">
                        <div className="w-2 h-2 bg-blue-600 rounded-full"></div>
                        <div>
                          <h3 className="minimal-text font-medium">{event.summary || "Untitled Meeting"}</h3>
                          <p className="minimal-text-tertiary">
                            {formatDate(event.start)} - {formatDate(event.end)}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        {meetingLink ? (
                          <a
                            href={meetingLink}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="minimal-button minimal-button-primary text-sm px-3 py-1"
                          >
                            <Video className="w-4 h-4 mr-1" />
                            Join
                          </a>
                        ) : (
                          <ArrowRight className="w-4 h-4 text-gray-400" />
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Tasks */}
          <div className="minimal-card p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="minimal-heading minimal-heading-md">Tasks</h2>
              <button className="minimal-button minimal-button-secondary">
                <Plus className="w-4 h-4 mr-2" />
                Add
              </button>
            </div>

            <div className="space-y-3">
              {tasks.map((task) => (
                <div key={task.id} className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
                  <button className="flex-shrink-0">
                    {task.completed ? (
                      <CheckCircle2 className="w-5 h-5 text-green-600" />
                    ) : (
                      <div className="w-5 h-5 border-2 border-gray-300 rounded-full"></div>
                    )}
                  </button>
                  <div className="flex-1 min-w-0">
                    <p className={`minimal-text ${task.completed ? 'line-through text-gray-500' : ''}`}>
                      {task.title}
                    </p>
                    <p className="minimal-text-tertiary">{task.due}</p>
                  </div>
                  <span className={`status-indicator ${
                    task.priority === 'high' ? 'status-error' : 
                    task.priority === 'medium' ? 'status-warning' : 'status-info'
                  }`}>
                    {task.priority}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Notifications */}
        <div className="mt-8">
          <div className="minimal-card p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="minimal-heading minimal-heading-md">Recent Activity</h2>
              <button className="minimal-text-tertiary hover:text-gray-900">View all</button>
            </div>

            <div className="space-y-4">
              {notifications.map((notification) => (
                <div key={notification.id} className="flex items-start space-x-3">
                  <div className="w-2 h-2 bg-blue-600 rounded-full mt-2 flex-shrink-0"></div>
                  <div className="flex-1">
                    <p className="minimal-text">{notification.message}</p>
                    <p className="minimal-text-tertiary">{notification.time}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
