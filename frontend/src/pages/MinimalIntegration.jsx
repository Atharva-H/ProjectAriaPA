import { useState, useEffect } from "react";
import { useAuth } from "../hooks/useAuth";
import API from "../services/api";
import { 
  Calendar, 
  Mail, 
  MessageSquare, 
  Database,
  CheckCircle2, 
  XCircle, 
  ExternalLink,
  RefreshCw,
  Settings,
  X
} from "lucide-react";

export default function MinimalIntegration() {
  const { token } = useAuth();
  const [integrations, setIntegrations] = useState({
    google_calendar: { connected: false, loading: false },
    google_gmail: { connected: false, loading: false },
    whatsapp: { connected: false, loading: false },
    tally: { connected: false, loading: false },
  });
  const [whatsappModal, setWhatsappModal] = useState({ show: false, step: 'phone', phone: '', code: '' });
  const [tallyModal, setTallyModal] = useState({ show: false, serverUrl: '', companyName: '' });

  useEffect(() => {
    if (token) {
      fetchIntegrationStatus();
      
      // Check if we're returning from OAuth callback
      const params = new URLSearchParams(window.location.search);
      if (params.get('connected')) {
        // Remove the query parameter from URL
        window.history.replaceState({}, '', '/integration');
        // Refresh status after a short delay to ensure backend has updated
        setTimeout(() => {
          fetchIntegrationStatus();
        }, 500);
      }
    }
  }, [token]);

  const fetchIntegrationStatus = async () => {
    try {
      const res = await API.get("/integrations/status", {
        headers: { Authorization: `Bearer ${token}` }
      });
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
      if (service === 'whatsapp') {
        // WhatsApp uses phone number verification, not OAuth
        setWhatsappModal({ show: true, step: 'phone', phone: '', code: '' });
        setIntegrations(prev => ({
          ...prev,
          [service]: { ...prev[service], loading: false }
        }));
      } else if (service === 'tally') {
        // Tally uses server configuration
        setTallyModal({ show: true, serverUrl: 'http://192.168.1.195:9000', companyName: 'Paricott India Papercup Pvt. Ltd. (24-26)' });
        setIntegrations(prev => ({
          ...prev,
          [service]: { ...prev[service], loading: false }
        }));
      } else {
        // Google services use OAuth
        const endpointMap = {
          'google_calendar': 'calendar',
          'google_gmail': 'gmail'
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
      if (service === 'google_calendar') {
        await API.post("/integrations/google/calendar/disconnect", {}, {
          headers: { Authorization: `Bearer ${token}` }
        });
      } else if (service === 'whatsapp') {
        await API.post("/whatsapp/unlink", {}, {
          headers: { Authorization: `Bearer ${token}` }
        });
      } else if (service === 'tally') {
        await API.post("/integrations/tally/disconnect", {}, {
          headers: { Authorization: `Bearer ${token}` }
        });
      } else {
        await API.post(`/integrations/${service}/disconnect`);
      }
      
      setIntegrations(prev => ({
        ...prev,
        [service]: { connected: false, loading: false }
      }));
    } catch (err) {
      console.error(`Failed to disconnect ${service}:`, err);
    }
  };

  const handleWhatsappPhoneSubmit = async () => {
    if (!whatsappModal.phone) return;
    
    try {
      await API.post("/whatsapp/link", 
        { number: whatsappModal.phone },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setWhatsappModal(prev => ({ ...prev, step: 'code' }));
    } catch (err) {
      console.error("Failed to send verification code:", err);
      alert("Failed to send verification code. Please try again.");
    }
  };

  const handleWhatsappCodeSubmit = async () => {
    if (!whatsappModal.code) return;
    
    try {
      await API.post("/whatsapp/verify", 
        { number: whatsappModal.phone, code: whatsappModal.code },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setWhatsappModal({ show: false, step: 'phone', phone: '', code: '' });
      fetchIntegrationStatus();
    } catch (err) {
      console.error("Failed to verify code:", err);
      alert("Invalid verification code. Please try again.");
    }
  };

  const handleTallyConnect = async () => {
    if (!tallyModal.serverUrl) return;
    
    try {
      await API.post("/integrations/tally/connect", 
        { 
          server_url: tallyModal.serverUrl,
          company_name: tallyModal.companyName || null
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setTallyModal({ show: false, serverUrl: '', companyName: '' });
      fetchIntegrationStatus();
    } catch (err) {
      console.error("Failed to connect to Tally:", err);
      alert("Failed to connect to Tally server. Please check the server URL and try again.");
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
    },
    {
      key: "tally",
      name: "Tally Prime",
      description: "Connect to your Tally accounting system",
      icon: Database,
      color: "purple",
      features: ["View ledgers", "Track vouchers", "Monitor inventory"]
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
                      config.color === 'green' ? 'bg-green-100' :
                      'bg-purple-100'
                    }`}>
                      <Icon className={`w-6 h-6 ${
                        config.color === 'blue' ? 'text-blue-600' :
                        config.color === 'red' ? 'text-red-600' :
                        config.color === 'green' ? 'text-green-600' :
                        'text-purple-600'
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
                          <span className="minimal-text font-medium">
                            Connected{config.key === 'whatsapp' && integration.number ? ` (${integration.number})` : ''}
                          </span>
                        </div>
                        {(config.key === 'google_calendar' || config.key === 'google_gmail') && (
                          <button
                            onClick={() => handleConnect(config.key)}
                            disabled={isLoading}
                            className="minimal-button minimal-button-secondary flex items-center space-x-2"
                            title="Re-authenticate to refresh your token"
                          >
                            {isLoading ? (
                              <>
                                <RefreshCw className="w-4 h-4 animate-spin" />
                                <span>Syncing...</span>
                              </>
                            ) : (
                              <>
                                <RefreshCw className="w-4 h-4" />
                                <span>Sync Again</span>
                              </>
                            )}
                          </button>
                        )}
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

      {/* WhatsApp Verification Modal */}
      {whatsappModal.show && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="minimal-heading minimal-heading-md">Connect WhatsApp</h3>
              <button
                onClick={() => setWhatsappModal({ show: false, step: 'phone', phone: '', code: '' })}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {whatsappModal.step === 'phone' ? (
              <div>
                <p className="minimal-text-secondary mb-4">
                  Enter your WhatsApp number to receive a verification code.
                </p>
                <div className="mb-4">
                  <label className="block minimal-text font-medium mb-2">Phone Number</label>
                  <input
                    type="tel"
                    value={whatsappModal.phone}
                    onChange={(e) => setWhatsappModal(prev => ({ ...prev, phone: e.target.value }))}
                    placeholder="+919876543210"
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
                <div className="flex justify-end space-x-2">
                  <button
                    onClick={() => setWhatsappModal({ show: false, step: 'phone', phone: '', code: '' })}
                    className="minimal-button minimal-button-secondary"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleWhatsappPhoneSubmit}
                    disabled={!whatsappModal.phone}
                    className="minimal-button minimal-button-primary"
                  >
                    Send Code
                  </button>
                </div>
              </div>
            ) : (
              <div>
                <p className="minimal-text-secondary mb-4">
                  Enter the verification code sent to {whatsappModal.phone}
                </p>
                <div className="mb-4">
                  <label className="block minimal-text font-medium mb-2">Verification Code</label>
                  <input
                    type="text"
                    value={whatsappModal.code}
                    onChange={(e) => setWhatsappModal(prev => ({ ...prev, code: e.target.value }))}
                    placeholder="123456"
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
                <div className="flex justify-end space-x-2">
                  <button
                    onClick={() => setWhatsappModal(prev => ({ ...prev, step: 'phone' }))}
                    className="minimal-button minimal-button-secondary"
                  >
                    Back
                  </button>
                  <button
                    onClick={handleWhatsappCodeSubmit}
                    disabled={!whatsappModal.code}
                    className="minimal-button minimal-button-primary"
                  >
                    Verify
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tally Connection Modal */}
      {tallyModal.show && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="minimal-heading minimal-heading-md">Connect Tally Prime</h3>
              <button
                onClick={() => setTallyModal({ show: false, serverUrl: '', companyName: '' })}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div>
              <p className="minimal-text-secondary mb-4">
                Enter your Tally Prime server details to connect.
              </p>
              <div className="mb-4">
                <label className="block minimal-text font-medium mb-2">Server URL</label>
                <input
                  type="url"
                  value={tallyModal.serverUrl}
                  onChange={(e) => setTallyModal(prev => ({ ...prev, serverUrl: e.target.value }))}
                  placeholder="http://192.168.1.195:9000"
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <div className="mb-4">
                <label className="block minimal-text font-medium mb-2">Company Name (Optional)</label>
                <input
                  type="text"
                  value={tallyModal.companyName}
                  onChange={(e) => setTallyModal(prev => ({ ...prev, companyName: e.target.value }))}
                  placeholder="Paricott India Papercup Pvt. Ltd. (24-26)"
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <div className="flex justify-end space-x-2">
                <button
                  onClick={() => setTallyModal({ show: false, serverUrl: '', companyName: '' })}
                  className="minimal-button minimal-button-secondary"
                >
                  Cancel
                </button>
                <button
                  onClick={handleTallyConnect}
                  disabled={!tallyModal.serverUrl}
                  className="minimal-button minimal-button-primary"
                >
                  Connect
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
