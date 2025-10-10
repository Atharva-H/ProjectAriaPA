import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

export default function AccountDetails() {
  const [user, setUser] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    const token = localStorage.getItem("jwt");
    if (!token) return navigate("/login");

    fetch("http://localhost:8000/auth/me", {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.name) setUser(data);
        else navigate("/login");
      })
      .catch((err) => {
        console.error("Error fetching account details:", err);
        navigate("/login");
      });
  }, [navigate]);

  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center text-gray-600">
        Loading account details...
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center pt-24 px-4">
      <div className="bg-white shadow-md rounded-2xl p-8 max-w-lg w-full">
        <div className="flex flex-col items-center text-center">
          <img
            src={user.picture}
            alt="Profile"
            className="w-24 h-24 rounded-full border-4 border-blue-600 mb-4"
          />
          <h2 className="text-2xl font-bold text-gray-800 mb-1">{user.name}</h2>
          <p className="text-gray-500 mb-6">{user.email}</p>
        </div>

        <div className="divide-y divide-gray-200">
          <div className="py-4">
            <p className="text-sm text-gray-500 mb-1">Google Account ID</p>
            <p className="text-gray-800 font-medium">
              Connected via Google OAuth
            </p>
          </div>
          <div className="py-4">
            <p className="text-sm text-gray-500 mb-1">Account Created</p>
            <p className="text-gray-800 font-medium">
              {new Date().toLocaleDateString()}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
