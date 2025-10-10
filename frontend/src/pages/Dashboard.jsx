// src/pages/Dashboard.jsx
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import API from "../services/api";
import { formatDate } from "../utils/formatDate";
import { Paperclip, Users, MapPin, Link as LinkIcon, CheckCircle, Clock, AlertTriangle, Bot } from "lucide-react";

export default function Dashboard() {
  const { user, token, loading: authLoading } = useAuth();
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState("");
  const navigate = useNavigate();

  // Dummy data
  const dummyTasks = [
    { title: "Review purchase order", priority: "high" },
    { title: "Check factory inventory", priority: "medium" },
    { title: "Reply to vendor email", priority: "low" },
  ];

  const dummyWork = [
    { time: "9:30 AM", activity: "Had a call with paper supplier" },
    { time: "11:00 AM", activity: "Reviewed packaging design" },
    { time: "2:00 PM", activity: "Follow-up with logistics team" },
  ];

  const dummyAssistant = [
    { time: "10:15 AM", action: "Sent meeting summary email to team" },
    { time: "12:30 PM", action: "Synced new events from Google Calendar" },
    { time: "4:45 PM", action: "Drafted WhatsApp reply for vendor query" },
  ];

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
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <p className="text-gray-600 text-lg">Fetching your dashboard...</p>
      </div>
    );
  }

  if (!user) {
    navigate("/login");
    return null;
  }

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 flex flex-col items-center">
      <div className="max-w-5xl w-full space-y-10">
        {/* HEADER */}
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-800 mb-2">
            Welcome, {user.name?.split(" ")[0]} 👋
          </h1>
          <p className="text-gray-600">
            Here’s your overview for today — meetings, tasks & assistant activity.
          </p>
        </div>

        {/* SECTION 1: TODAY’S MEETINGS */}
        <section>
          <h2 className="text-2xl font-semibold text-gray-800 mb-4">
            🗓️ Today’s Meetings
          </h2>

          {errorMsg && (
            <div className="bg-red-50 border border-red-200 text-red-700 p-3 rounded mb-4">
              {errorMsg}
            </div>
          )}

          {events.length === 0 ? (
            <div className="text-gray-500 text-center py-10 bg-white shadow rounded-xl">
              No meetings scheduled for today 🎉
            </div>
          ) : (
            <div className="grid gap-4 md:grid-cols-2">
              {events.map((event) => (
                <div
                  key={event.id}
                  className="bg-white shadow-md rounded-2xl p-5 border border-gray-100 hover:shadow-lg transition"
                >
                  <h3 className="text-lg font-semibold text-gray-800 mb-1">
                    {event.summary || "Untitled Meeting"}
                  </h3>
                  <p className="text-sm text-gray-500 mb-2">
                    {formatDate(event.start)} → {formatDate(event.end)}
                  </p>

                  {event.location && (
                    <div className="flex items-center text-gray-600 text-sm mb-1">
                      <MapPin className="w-4 h-4 mr-2" />
                      <span>{event.location}</span>
                    </div>
                  )}

                  {event.attendees?.length > 0 && (
                    <div className="flex items-start text-gray-600 text-sm mb-1">
                      <Users className="w-4 h-4 mr-2 mt-0.5" />
                      <span>
                        {event.attendees.map((a) => a.email).join(", ")}
                      </span>
                    </div>
                  )}

                  {event.hangoutLink && (
                    <a
                      href={event.hangoutLink}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center text-blue-600 text-sm mt-2 hover:underline"
                    >
                      <LinkIcon className="w-4 h-4 mr-1" /> Join Meeting
                    </a>
                  )}
                </div>
              ))}
            </div>
          )}
        </section>

        {/* SECTION 2: PENDING TASKS */}
        <section>
          <h2 className="text-2xl font-semibold text-gray-800 mb-4">
            ✅ Pending Tasks <span className="text-sm text-gray-500">(Coming soon)</span>
          </h2>
          <div className="bg-white rounded-xl shadow p-6 space-y-3">
            {dummyTasks.map((task, i) => {
              const color =
                task.priority === "high"
                  ? "border-red-400 text-red-600 bg-red-50"
                  : task.priority === "medium"
                  ? "border-yellow-400 text-yellow-600 bg-yellow-50"
                  : "border-green-400 text-green-600 bg-green-50";
              return (
                <div
                  key={i}
                  className={`p-3 border rounded-lg flex items-center justify-between ${color} opacity-60`}
                >
                  <span className="font-medium">{task.title}</span>
                  {task.priority === "high" ? (
                    <AlertTriangle className="w-5 h-5" />
                  ) : task.priority === "medium" ? (
                    <Clock className="w-5 h-5" />
                  ) : (
                    <CheckCircle className="w-5 h-5" />
                  )}
                </div>
              );
            })}
          </div>
        </section>

        {/* SECTION 3: WHAT YOU DID TODAY */}
        <section>
          <h2 className="text-2xl font-semibold text-gray-800 mb-4">
            📋 What You Did Today <span className="text-sm text-gray-500">(Coming soon)</span>
          </h2>
          <div className="bg-white rounded-xl shadow p-6 space-y-2 opacity-70">
            {dummyWork.map((item, i) => (
              <p key={i} className="text-gray-600 text-sm">
                <span className="font-medium text-gray-800">{item.time}</span> — {item.activity}
              </p>
            ))}
          </div>
        </section>

        {/* SECTION 4: ASSISTANT’S ACTIVITIES */}
        <section>
          <h2 className="text-2xl font-semibold text-gray-800 mb-4">
            🤖 Assistant’s Activities <span className="text-sm text-gray-500">(Coming soon)</span>
          </h2>
          <div className="bg-white rounded-xl shadow p-6 space-y-2 opacity-70">
            {dummyAssistant.map((item, i) => (
              <p key={i} className="text-gray-600 text-sm flex items-center">
                <Bot className="w-4 h-4 mr-2 text-gray-500" />
                <span>
                  <span className="font-medium text-gray-800">{item.time}</span> — {item.action}
                </span>
              </p>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
