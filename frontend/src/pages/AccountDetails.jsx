import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import API from "../services/api";
import { User, Mail, Calendar, Shield, LogOut, MessageSquare, Phone, Clock, Check, X } from "lucide-react";

export default function AccountDetails() {
  const { user, token, logout } = useAuth();
  const [loading, setLoading] = useState(true);
  const [isEditing, setIsEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [workingHours, setWorkingHours] = useState({
    start: user?.working_hours_start || 9,
    end: user?.working_hours_end || 18,
  });
  const [workingDays, setWorkingDays] = useState(() => {
    if (user?.working_days) {
      if (Array.isArray(user.working_days)) {
        return user.working_days;
      } else if (typeof user.working_days === 'string') {
        return user.working_days.split(',');
      }
    }
    return ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'];
  });
  const navigate = useNavigate();

  useEffect(() => {
    if (!token) {
      navigate("/login");
      return;
    }
    setLoading(false);
    if (user) {
      setWorkingHours({
        start: user.working_hours_start || 9,
        end: user.working_hours_end || 18,
      });
      // Handle working_days as either array or comma-separated string
      let days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']; // Default
      if (user.working_days) {
        if (Array.isArray(user.working_days)) {
          days = user.working_days;
        } else if (typeof user.working_days === 'string') {
          days = user.working_days.split(',');
        }
      }
      setWorkingDays(days);
    }
  }, [token, navigate, user]);

  const handleSave = async () => {
    setSaving(true);
    try {
      const response = await API.put('/users/me', {
        working_hours_start: parseInt(workingHours.start),
        working_hours_end: parseInt(workingHours.end),
        working_days: workingDays, // Send as array, backend will handle JSON conversion
      });
      
      if (response.data) {
        setIsEditing(false);
        // Update the user context if available
        if (window.location.reload) {
          window.location.reload();
        }
      }
    } catch (error) {
      console.error('Failed to save working hours:', error);
      alert('Failed to save working hours. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  const toggleDay = (day) => {
    if (workingDays.includes(day)) {
      setWorkingDays(workingDays.filter(d => d !== day));
    } else {
      setWorkingDays([...workingDays, day]);
    }
  };

  const allDays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

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

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-6xl mx-auto">
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

          {/* Working Hours Card */}
          <div className="minimal-card p-8">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-blue-100 rounded-lg">
                  <Clock className="w-5 h-5 text-blue-600" />
                </div>
                <div>
                  <h3 className="minimal-heading minimal-heading-md">Working Hours & Days</h3>
                  <p className="minimal-text-tertiary">Configure your availability for calendar features</p>
                </div>
              </div>
              {!isEditing ? (
                <button
                  onClick={() => setIsEditing(true)}
                  className="minimal-button minimal-button-secondary"
                >
                  Edit
                </button>
              ) : (
                <div className="flex space-x-2">
                  <button
                    onClick={handleSave}
                    disabled={saving}
                    className="minimal-button minimal-button-primary"
                  >
                    <Check className="w-4 h-4 mr-2" />
                    {saving ? 'Saving...' : 'Save'}
                  </button>
                  <button
                    onClick={() => setIsEditing(false)}
                    className="minimal-button minimal-button-secondary"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              )}
            </div>

            {!isEditing ? (
              <div className="space-y-4">
                <div className="p-4 bg-gray-50 rounded-lg">
                  <p className="minimal-text-tertiary mb-2">Working Hours</p>
                  <p className="minimal-text font-medium">
                    {workingHours.start > 12 
                      ? `${workingHours.start - 12} PM` 
                      : workingHours.start === 12 
                        ? '12 PM' 
                        : `${workingHours.start} AM`} - {workingHours.end > 12 
                      ? `${workingHours.end - 12} PM` 
                      : workingHours.end === 12 
                        ? '12 PM' 
                        : `${workingHours.end} AM`}
                  </p>
                </div>
                <div className="p-4 bg-gray-50 rounded-lg">
                  <p className="minimal-text-tertiary mb-2">Working Days</p>
                  <div className="flex flex-wrap gap-2">
                    {workingDays.map((day) => (
                      <span
                        key={day}
                        className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm font-medium"
                      >
                        {day}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <div className="space-y-6">
                <div>
                  <label className="minimal-text font-medium mb-2 block">Start Time</label>
                  <input
                    type="number"
                    min="0"
                    max="23"
                    value={workingHours.start}
                    onChange={(e) => setWorkingHours({ ...workingHours, start: parseInt(e.target.value) || 0 })}
                    className="w-full minimal-input"
                  />
                  <p className="minimal-text-tertiary text-sm mt-1">24-hour format (0-23). Default: 9 (9 AM)</p>
                </div>

                <div>
                  <label className="minimal-text font-medium mb-2 block">End Time</label>
                  <input
                    type="number"
                    min="0"
                    max="23"
                    value={workingHours.end}
                    onChange={(e) => setWorkingHours({ ...workingHours, end: parseInt(e.target.value) || 0 })}
                    className="w-full minimal-input"
                  />
                  <p className="minimal-text-tertiary text-sm mt-1">24-hour format (0-23). Default: 18 (6 PM)</p>
                </div>

                <div>
                  <label className="minimal-text font-medium mb-2 block">Working Days</label>
                  <div className="grid grid-cols-2 gap-2">
                    {allDays.map((day) => (
                      <label
                        key={day}
                        className={`flex items-center space-x-2 p-3 border rounded-lg cursor-pointer hover:bg-gray-50 ${
                          workingDays.includes(day) ? 'bg-blue-50 border-blue-500' : 'bg-white border-gray-300'
                        }`}
                      >
                        <input
                          type="checkbox"
                          checked={workingDays.includes(day)}
                          onChange={() => toggleDay(day)}
                          className="w-4 h-4 text-blue-600 rounded"
                        />
                        <span className="minimal-text">{day}</span>
                      </label>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
