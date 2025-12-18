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
  const [tasks, setTasks] = useState([]);
  const [notifications] = useState([
    { id: 1, type: "meeting", message: "Team standup in 15 minutes", time: "9:45 AM" },
    { id: 2, type: "task", message: "Budget review due today", time: "2:00 PM" },
    { id: 3, type: "reminder", message: "Client call tomorrow at 10 AM", time: "4:30 PM" },
  ]);

  useEffect(() => {
    const fetchEventsAndTasks = async () => {
      console.log("📊 Dashboard: Checking auth...", { token: !!token, authLoading });

      if (!token) {
        console.warn("⚠️ Dashboard: No token found, redirecting to login");
        navigate("/login");
        return;
      }

      try {
        const [eventsRes, tasksRes] = await Promise.all([
          API.get("/calendar/today", { headers: { Authorization: `Bearer ${token}` } }),
          API.get("/tasks", { headers: { Authorization: `Bearer ${token}` } })
        ]);

        if (eventsRes.data.error) {
          setErrorMsg(eventsRes.data.error);
          setEvents([]);
        } else {
          setEvents(eventsRes.data.events || []);
        }

        setTasks(tasksRes.data || []);

      } catch (err) {
        console.error("❌ Error fetching dashboard data:", err);
        setErrorMsg("Failed to fetch dashboard data.");
      } finally {
        setLoading(false);
      }
    };

    if (!authLoading) fetchEventsAndTasks();
  }, [token, authLoading, navigate]);

  // ... (keep loading and auth checks)

  const completedTasks = tasks.filter(t => t.status === 'done').length;
  const pendingTasksList = tasks.filter(t => t.status !== 'done');

  // Categorize tasks for Eisenhower Matrix
  const urgentImportant = pendingTasksList.filter(t => t.is_urgent && t.is_important);
  const notUrgentImportant = pendingTasksList.filter(t => !t.is_urgent && t.is_important);
  const urgentNotImportant = pendingTasksList.filter(t => t.is_urgent && !t.is_important);
  const notUrgentNotImportant = pendingTasksList.filter(t => !t.is_urgent && !t.is_important);

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
        {/* ... (keep header and stats) */}

        {/* Task Matrix Grid */}
        <div className="mb-8">
          <h2 className="minimal-heading minimal-heading-md mb-4">Task Priority Matrix</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Quadrant 1: Do First */}
            <div className="minimal-card p-4 border-l-4 border-red-500">
              <h3 className="font-semibold text-red-700 mb-3 flex items-center">
                <AlertCircle className="w-4 h-4 mr-2" /> Do First (Urgent & Important)
              </h3>
              <div className="space-y-2">
                {urgentImportant.length === 0 && <p className="text-sm text-gray-400 italic">No tasks</p>}
                {urgentImportant.map(t => (
                  <div key={t.id} className="p-2 bg-white rounded shadow-sm text-sm flex justify-between">
                    <span>{t.title}</span>
                    <span className="text-xs text-gray-500">{t.due_at ? formatDate(t.due_at) : ''}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Quadrant 2: Schedule */}
            <div className="minimal-card p-4 border-l-4 border-blue-500">
              <h3 className="font-semibold text-blue-700 mb-3 flex items-center">
                <Calendar className="w-4 h-4 mr-2" /> Schedule (Important, Not Urgent)
              </h3>
              <div className="space-y-2">
                {notUrgentImportant.length === 0 && <p className="text-sm text-gray-400 italic">No tasks</p>}
                {notUrgentImportant.map(t => (
                  <div key={t.id} className="p-2 bg-white rounded shadow-sm text-sm flex justify-between">
                    <span>{t.title}</span>
                    <span className="text-xs text-gray-500">{t.due_at ? formatDate(t.due_at) : ''}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Quadrant 3: Delegate */}
            <div className="minimal-card p-4 border-l-4 border-orange-500">
              <h3 className="font-semibold text-orange-700 mb-3 flex items-center">
                <Users className="w-4 h-4 mr-2" /> Delegate (Urgent, Not Important)
              </h3>
              <div className="space-y-2">
                {urgentNotImportant.length === 0 && <p className="text-sm text-gray-400 italic">No tasks</p>}
                {urgentNotImportant.map(t => (
                  <div key={t.id} className="p-2 bg-white rounded shadow-sm text-sm flex justify-between">
                    <span>{t.title}</span>
                    <span className="text-xs text-gray-500">{t.due_at ? formatDate(t.due_at) : ''}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Quadrant 4: Delete/Later */}
            <div className="minimal-card p-4 border-l-4 border-gray-400">
              <h3 className="font-semibold text-gray-700 mb-3 flex items-center">
                <Clock className="w-4 h-4 mr-2" /> Later (Neither)
              </h3>
              <div className="space-y-2">
                {notUrgentNotImportant.length === 0 && <p className="text-sm text-gray-400 italic">No tasks</p>}
                {notUrgentNotImportant.map(t => (
                  <div key={t.id} className="p-2 bg-white rounded shadow-sm text-sm flex justify-between">
                    <span>{t.title}</span>
                    <span className="text-xs text-gray-500">{t.due_at ? formatDate(t.due_at) : ''}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        <div className="minimal-grid minimal-grid-2">
          {/* Today's Meetings (keep existing code) */}
          <div className="minimal-card p-6">
            {/* ... existing meeting code ... */}
            <div className="flex items-center justify-between mb-6">
              <h2 className="minimal-heading minimal-heading-md">Today's Meetings</h2>
              <button className="minimal-button minimal-button-secondary">
                <Plus className="w-4 h-4 mr-2" />
                Add
              </button>
            </div>
            {/* ... rest of meeting code ... */}
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

          {/* All Tasks List (keep as secondary view or remove if matrix is enough, but user asked for grid) */}
          {/* Let's keep a simple list or maybe remove it to avoid duplication. 
              The user asked for a grid. I'll replace the old tasks list with the matrix above 
              and maybe keep a simple "Recent Tasks" list here or just remove the second column.
              Actually, the user said "in ur we will make a grid in dashboard page".
              So the matrix should probably replace the old task list.
              But the layout is 2 columns: Meetings | Tasks.
              Putting a 2x2 grid inside the right column might be tight.
              Maybe put the matrix full width above or below?
              I placed it above.
              I will remove the old task list from the 2-column layout.
          */}
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
