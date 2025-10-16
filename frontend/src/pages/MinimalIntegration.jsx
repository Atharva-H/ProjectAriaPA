import { useState, useEffect } from "react";
import { useAuth } from "../hooks/useAuth";
import API from "../services/api";
import { 
  Calendar, 
  Mail, 
  MessageSquare, 
  CheckCircle2, 
  XCircle, 
  ExternalLink,
  RefreshCw,
  Settings
} from "lucide-react";

export default function MinimalIntegration() {
  const { token } = useAuth();
  const [integrations, setIntegrations] = useState({
    google_calendar: { connected: false, loading: false },
    google_gmail: { connected: false, loading: false },
    whatsapp: { connected: false, loading: false },
  });

  useEffect(() => {
    if (token) fetchIntegrationStatus();
  }, [token]);

  const fetchIntegrationStatus = async () => {
    try {
      const res = await API.get("/integrations/status");
      setIntegrations(res.data);
    } catch (err) {
      console.error("Failed to fetch integration status:", err);
    }
  };

  const handleConnect = async (service) => {
    setIntegrations(prev => ({
      ...prev,
      [service]: { ...prev[service], loading: true }
    }));

    try {
      // Map service names to correct API endpoints
      const endpointMap = {
        'google_calendar': 'calendar',
        'google_gmail': 'gmail',
        'whatsapp': 'whatsapp'
      };
      
      const endpoint = endpointMap[service] || service;
      
      // Get the auth URL from the backend
      const res = await API.get(`/integrations/google/${endpoint}/connect`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      // Redirect to Google OAuth
      if (res.data.auth_url) {
        window.location.href = res.data.auth_url;
      } else {
        throw new Error(res.data.error || 'Failed to get auth URL');
      }
    } catch (err) {
      console.error(`Failed to connect ${service}:`, err);
      setIntegrations(prev => ({
        ...prev,
        [service]: { ...prev[service], loading: false }
      }));
    }
  };

  const handleDisconnect = async (service) => {
    if (!confirm(`Disconnect ${service}?`)) return;
    
    try {
      await API.post(`/integrations/${service}/disconnect`);
      setIntegrations(prev => ({
        ...prev,
        [service]: { connected: false, loading: false }
      }));
    } catch (err) {
      console.error(`Failed to disconnect ${service}:`, err);
    }
  };

  const integrationConfig = [
    {
      key: "google_calendar",
      name: "Google Calendar",
      description: "Sync your calendar events and manage meetings",
      icon: Calendar,
      color: "blue",
      features: ["View upcoming meetings", "Create new events", "Get meeting reminders"]
    },
    {
      key: "google_gmail",
      name: "Gmail",
      description: "Access your emails and extract important information",
      icon: Mail,
      color: "red",
      features: ["Read recent emails", "Extract tasks from emails", "Smart email summaries"]
    },
    {
      key: "whatsapp",
      name: "WhatsApp",
      description: "Get AI assistance and share updates via WhatsApp",
      icon: MessageSquare,
      color: "green",
      features: ["AI chat assistant", "Share meeting summaries", "Get reminders"]
    }
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="minimal-container py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="minimal-heading minimal-heading-xl mb-2">Integrations</h1>
          <p className="minimal-text-secondary">
            Connect your favorite tools to supercharge your productivity
          </p>
        </div>

        {/* Integration Cards */}
        <div className="space-y-6">
          {integrationConfig.map((config) => {
            const Icon = config.icon;
            const integration = integrations[config.key];
            const isConnected = integration.connected;
            const isLoading = integration.loading;

            return (
              <div key={config.key} className="minimal-card p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center space-x-4">
                    <div className={`p-3 rounded-lg ${
                      config.color === 'blue' ? 'bg-blue-100' :
                      config.color === 'red' ? 'bg-red-100' :
                      'bg-green-100'
                    }`}>
                      <Icon className={`w-6 h-6 ${
                        config.color === 'blue' ? 'text-blue-600' :
                        config.color === 'red' ? 'text-red-600' :
                        'text-green-600'
                      }`} />
                    </div>
                    <div>
                      <h3 className="minimal-heading minimal-heading-md">{config.name}</h3>
                      <p className="minimal-text-secondary">{config.description}</p>
                    </div>
                  </div>

                  <div className="flex items-center space-x-3">
                    {isConnected ? (
                      <>
                        <div className="flex items-center space-x-2 text-green-600">
                          <CheckCircle2 className="w-5 h-5" />
                          <span className="minimal-text font-medium">Connected</span>
                        </div>
                        <button
                          onClick={() => handleDisconnect(config.key)}
                          className="minimal-button minimal-button-secondary"
                        >
                          Disconnect
                        </button>
                      </>
                    ) : (
                      <button
                        onClick={() => handleConnect(config.key)}
                        disabled={isLoading}
                        className="minimal-button minimal-button-primary"
                      >
                        {isLoading ? (
                          <>
                            <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                            Connecting...
                          </>
                        ) : (
                          <>
                            <ExternalLink className="w-4 h-4 mr-2" />
                            Connect
                          </>
                        )}
                      </button>
                    )}
                  </div>
                </div>

                {/* Features */}
                <div className="border-t border-gray-100 pt-4">
                  <h4 className="minimal-text font-medium mb-3">What you can do:</h4>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                    {config.features.map((feature, index) => (
                      <div key={index} className="flex items-center space-x-2">
                        <div className="w-1.5 h-1.5 bg-gray-400 rounded-full"></div>
                        <span className="minimal-text-secondary text-sm">{feature}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Status Indicator */}
                {isConnected && (
                  <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-lg">
                    <div className="flex items-center space-x-2">
                      <CheckCircle2 className="w-4 h-4 text-green-600" />
                      <span className="minimal-text text-green-800">
                        {config.name} is connected and ready to use
                      </span>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Help Section */}
        <div className="mt-12 minimal-card p-6">
          <div className="flex items-start space-x-4">
            <div className="p-2 bg-gray-100 rounded-lg">
              <Settings className="w-5 h-5 text-gray-600" />
            </div>
            <div>
              <h3 className="minimal-heading minimal-heading-md mb-2">Need Help?</h3>
              <p className="minimal-text-secondary mb-4">
                Having trouble connecting your accounts? Here are some common solutions:
              </p>
              <ul className="space-y-2 minimal-text-secondary">
                <li>• Make sure you're logged into the correct Google account</li>
                <li>• Check that you've granted all necessary permissions</li>
                <li>• Try disconnecting and reconnecting the integration</li>
                <li>• Contact support if the issue persists</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
