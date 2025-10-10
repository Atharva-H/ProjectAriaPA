import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

export default function Dashboard() {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(false);
  const [user, setUser] = useState(null);
  const navigate = useNavigate();

  // 🪄 STEP 1: Check if token is in URL and save it
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const token = params.get("token");
    if (token) {
      localStorage.setItem("jwt", token);
      window.history.replaceState({}, document.title, "/dashboard"); // Clean URL
    }

    const stored = localStorage.getItem("jwt");
    if (!stored) navigate("/login");
  }, [navigate]);

  // 🧠 Fetch user info
  const fetchUserInfo = async () => {
    const token = localStorage.getItem("jwt");
    if (!token) return navigate("/login");

    try {
      const res = await fetch("http://localhost:8000/auth/me", {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();

      // If token is expired but refreshable
      if (data.refresh && data.token) {
        localStorage.setItem("jwt", data.token);
        console.log("🔁 Token refreshed from /me");
        return fetchUserInfo(); // retry once
      }

      if (data.name) {
        setUser(data);
      } else {
        navigate("/login");
      }
    } catch (err) {
      console.error("Error fetching user info:", err);
      navigate("/login");
    }
  };

  // 📆 Fetch today's calendar events
const fetchEvents = async () => {
  setLoading(true);
  try {
    const token = localStorage.getItem("jwt");
    if (!token) {
      alert("Session expired. Please log in again.");
      navigate("/login");
      return;
    }

    const res = await fetch("http://localhost:8000/auth/calendar/today", {
      headers: { Authorization: `Bearer ${token}` },
    });

    const data = await res.json();

    if (data.error) {
      alert(data.error);
      if (data.error.includes("expired")) {
        localStorage.removeItem("jwt");
        navigate("/login");
      }
      return;
    }

    setEvents(data.events || []);
  } catch (err) {
    console.error(err);
    alert("Error fetching events");
  } finally {
    setLoading(false);
  }
};


  // Load user info on mount
  useEffect(() => {
    fetchUserInfo();
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center pt-24 px-4">
      {user ? (
        <>
          {/* Welcome message */}
          <h1 className="text-3xl font-bold text-gray-800 mb-4">
            Welcome, {user.name.split(" ")[0]} 👋
          </h1>
          <p className="text-gray-500 mb-8 text-center max-w-lg">
            You’re signed in as <span className="font-medium">{user.email}</span>.
            Click below to view today’s Google Calendar events.
          </p>

          {/* Fetch events button */}
          <button
            onClick={fetchEvents}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-all mb-8"
          >
            {loading ? "Fetching..." : "Fetch Today's Events"}
          </button>

          {/* Events card */}
          <div className="w-full max-w-2xl bg-white rounded-2xl shadow p-6">
            {events.length === 0 ? (
              <p className="text-gray-600 text-center py-10">
                No events to display yet.
              </p>
            ) : (
              <div className="space-y-4">
                {events.map((event, i) => (
                  <div key={i} className="border-b pb-3 last:border-none">
                    <p className="font-medium text-gray-800">{event.summary}</p>
                    <p className="text-sm text-gray-500">
                      {new Date(event.start).toLocaleString()}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </>
      ) : (
        <p className="text-gray-600 text-lg mt-20">Loading user info...</p>
      )}
    </div>
  );
}
