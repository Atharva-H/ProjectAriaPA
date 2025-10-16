import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import API from "../services/api";
import { User, Mail, Calendar, Shield, LogOut, MessageSquare, Phone } from "lucide-react";

export default function AccountDetails() {
  const { user, token, logout } = useAuth();
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    if (!token) {
      navigate("/login");
      return;
    }
    setLoading(false);
  }, [token, navigate]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="minimal-text-secondary">Loading account details...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    navigate("/login");
    return null;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="minimal-container py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="minimal-heading minimal-heading-xl mb-2">Account Details</h1>
          <p className="minimal-text-secondary">Manage your account information and settings</p>
        </div>

        <div className="minimal-grid minimal-grid-2 max-w-4xl mx-auto">
          {/* Profile Card */}
          <div className="minimal-card p-8">
            <div className="flex items-center space-x-6 mb-8">
              <img
                src={user.picture}
                alt="Profile"
                className="w-20 h-20 rounded-full border-2 border-blue-600"
              />
              <div>
                <h2 className="minimal-heading minimal-heading-lg mb-2">{user.name}</h2>
                <p className="minimal-text-secondary">{user.email}</p>
              </div>
            </div>

            <div className="space-y-4">
              <div className="flex items-center space-x-3">
                <User className="w-5 h-5 text-gray-400" />
                <div>
                  <p className="minimal-text-tertiary">Account Type</p>
                  <p className="minimal-text">Google OAuth</p>
                </div>
              </div>

              <div className="flex items-center space-x-3">
                <Mail className="w-5 h-5 text-gray-400" />
                <div>
                  <p className="minimal-text-tertiary">Email Status</p>
                  <p className="minimal-text">Verified</p>
                </div>
              </div>

              {user.whatsapp_no && (
                <div className="flex items-center space-x-3">
                  <MessageSquare className="w-5 h-5 text-gray-400" />
                  <div>
                    <p className="minimal-text-tertiary">WhatsApp Number</p>
                    <p className="minimal-text">{user.whatsapp_no}</p>
                  </div>
                </div>
              )}

              <div className="flex items-center space-x-3">
                <Calendar className="w-5 h-5 text-gray-400" />
                <div>
                  <p className="minimal-text-tertiary">Member Since</p>
                  <p className="minimal-text">{new Date().toLocaleDateString()}</p>
                </div>
              </div>
            </div>
          </div>

          {/* Settings Card */}
          <div className="minimal-card p-8">
            <h3 className="minimal-heading minimal-heading-md mb-6">Account Settings</h3>
            
            <div className="space-y-6">
              <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center space-x-3">
                  <Shield className="w-5 h-5 text-green-600" />
                  <div>
                    <p className="minimal-text font-medium">Account Security</p>
                    <p className="minimal-text-tertiary">Your account is secure</p>
                  </div>
                </div>
                <span className="status-indicator status-success">Active</span>
              </div>

              <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center space-x-3">
                  <Calendar className="w-5 h-5 text-blue-600" />
                  <div>
                    <p className="minimal-text font-medium">Calendar Integration</p>
                    <p className="minimal-text-tertiary">Google Calendar connected</p>
                  </div>
                </div>
                <span className="status-indicator status-success">Connected</span>
              </div>

              <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center space-x-3">
                  <Mail className="w-5 h-5 text-red-600" />
                  <div>
                    <p className="minimal-text font-medium">Gmail Integration</p>
                    <p className="minimal-text-tertiary">Gmail connected</p>
                  </div>
                </div>
                <span className="status-indicator status-success">Connected</span>
              </div>
            </div>

            <div className="mt-8 pt-6 border-t border-gray-200">
              <button
                onClick={() => {
                  logout();
                  navigate("/");
                }}
                className="w-full minimal-button minimal-button-secondary text-red-600 hover:bg-red-50"
              >
                <LogOut className="w-4 h-4 mr-2" />
                Sign Out
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
