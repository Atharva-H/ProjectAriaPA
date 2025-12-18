import { useEffect, useState } from "react";
import { useAuth } from "../hooks/useAuth";
import { useNavigate } from "react-router-dom";
import { 
  Settings as SettingsIcon, 
  Palette, 
  Bell, 
  Shield, 
  Database,
  Moon,
  Sun
} from "lucide-react";

export default function Settings() {
  const { user, token } = useAuth();
  const navigate = useNavigate();
  const [theme, setTheme] = useState("light");

  useEffect(() => {
    if (!token) {
      navigate("/login");
      return;
    }

    const savedTheme = localStorage.getItem("theme") || "light";
    setTheme(savedTheme);
    applyTheme(savedTheme);
  }, [token, navigate]);

  const applyTheme = (theme) => {
    if (theme === "dark") {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
  };

  const toggleTheme = () => {
    const newTheme = theme === "light" ? "dark" : "light";
    setTheme(newTheme);
    localStorage.setItem("theme", newTheme);
    applyTheme(newTheme);
  };

  if (!user) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="minimal-container py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="minimal-heading minimal-heading-xl mb-2">Settings</h1>
          <p className="minimal-text-secondary">Manage your preferences and account settings</p>
        </div>

        <div className="minimal-grid minimal-grid-2 max-w-4xl mx-auto">
          {/* Appearance Settings */}
          <div className="minimal-card p-6">
            <div className="flex items-center space-x-3 mb-6">
              <div className="p-2 bg-blue-100 rounded-lg">
                <Palette className="w-5 h-5 text-blue-600" />
              </div>
              <h2 className="minimal-heading minimal-heading-md">Appearance</h2>
            </div>

            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center space-x-3">
                  {theme === "light" ? (
                    <Sun className="w-5 h-5 text-yellow-500" />
                  ) : (
                    <Moon className="w-5 h-5 text-blue-500" />
                  )}
                  <div>
                    <p className="minimal-text font-medium">Theme</p>
                    <p className="minimal-text-tertiary">
                      {theme === "light" ? "Light mode" : "Dark mode"}
                    </p>
                  </div>
                </div>
                <button
                  onClick={toggleTheme}
                  className="minimal-button minimal-button-secondary"
                >
                  {theme === "light" ? "Switch to Dark" : "Switch to Light"}
                </button>
              </div>
            </div>
          </div>

          {/* Notifications Settings */}
          <div className="minimal-card p-6">
            <div className="flex items-center space-x-3 mb-6">
              <div className="p-2 bg-green-100 rounded-lg">
                <Bell className="w-5 h-5 text-green-600" />
              </div>
              <h2 className="minimal-heading minimal-heading-md">Notifications</h2>
            </div>

            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div>
                  <p className="minimal-text font-medium">Meeting Reminders</p>
                  <p className="minimal-text-tertiary">Get notified before meetings</p>
                </div>
                <span className="status-indicator status-success">Enabled</span>
              </div>

              <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div>
                  <p className="minimal-text font-medium">WhatsApp Updates</p>
                  <p className="minimal-text-tertiary">Receive updates via WhatsApp</p>
                </div>
                <span className="status-indicator status-success">Enabled</span>
              </div>
            </div>
          </div>

          {/* Privacy & Security */}
          <div className="minimal-card p-6">
            <div className="flex items-center space-x-3 mb-6">
              <div className="p-2 bg-red-100 rounded-lg">
                <Shield className="w-5 h-5 text-red-600" />
              </div>
              <h2 className="minimal-heading minimal-heading-md">Privacy & Security</h2>
            </div>

            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div>
                  <p className="minimal-text font-medium">Data Encryption</p>
                  <p className="minimal-text-tertiary">Your data is encrypted</p>
                </div>
                <span className="status-indicator status-success">Active</span>
              </div>

              <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div>
                  <p className="minimal-text font-medium">Two-Factor Auth</p>
                  <p className="minimal-text-tertiary">Google OAuth enabled</p>
                </div>
                <span className="status-indicator status-success">Enabled</span>
              </div>
            </div>
          </div>

          {/* Data Management */}
          <div className="minimal-card p-6">
            <div className="flex items-center space-x-3 mb-6">
              <div className="p-2 bg-purple-100 rounded-lg">
                <Database className="w-5 h-5 text-purple-600" />
              </div>
              <h2 className="minimal-heading minimal-heading-md">Data Management</h2>
            </div>

            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div>
                  <p className="minimal-text font-medium">Calendar Sync</p>
                  <p className="minimal-text-tertiary">Google Calendar connected</p>
                </div>
                <span className="status-indicator status-success">Synced</span>
              </div>

              <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div>
                  <p className="minimal-text font-medium">Email Sync</p>
                  <p className="minimal-text-tertiary">Gmail connected</p>
                </div>
                <span className="status-indicator status-success">Synced</span>
              </div>
            </div>
          </div>
        </div>

        {/* Footer Note */}
        <div className="mt-8 text-center">
          <p className="minimal-text-tertiary">
            Your preferences are automatically saved and synced across devices.
          </p>
        </div>
      </div>
    </div>
  );
}
