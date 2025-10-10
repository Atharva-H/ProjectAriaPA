import { useState } from "react";
import { useAuth } from "../hooks/useAuth";
import API from "../services/api";
import {
  Calendar,
  MessageCircle,
  Mail,
  CheckCircle,
  XCircle,
  RefreshCw,
  Phone,
} from "lucide-react";

export default function Integration() {
  const { user, token } = useAuth();
  const [number, setNumber] = useState(user?.whatsapp_no || "");
  const [verified, setVerified] = useState(user?.whatsapp_verified || false);
  const [loading, setLoading] = useState(false);
  const [changing, setChanging] = useState(false);

  // Send verification message
  const sendVerification = async () => {
    if (!number.startsWith("+")) {
      alert("Enter a valid phone number with country code (e.g. +919876543210)");
      return;
    }
    setLoading(true);
    try {
      await API.post(
        "/whatsapp/link",
        { number },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      alert("Verification code sent to your WhatsApp!");
    } catch (err) {
      console.error(err);
      alert("Failed to send verification message.");
    } finally {
      setLoading(false);
    }
  };

  // Verify code
  const verifyCode = async () => {
    const code = prompt("Enter the 6-digit verification code sent to WhatsApp:");
    if (!code) return;
    setLoading(true);
    try {
      const res = await API.post(
        "/whatsapp/verify",
        { number, code },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (res.data.status === "verified") {
        alert("✅ WhatsApp linked successfully!");
        setVerified(true);
      }
    } catch (err) {
      alert("Invalid or expired verification code.");
    } finally {
      setLoading(false);
    }
  };

  // Disconnect WhatsApp
  const unlinkWhatsapp = async () => {
    if (!confirm("Are you sure you want to disconnect WhatsApp?")) return;
    try {
      await API.post(
        "/whatsapp/unlink",
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setVerified(false);
      setNumber("");
      alert("WhatsApp disconnected successfully.");
    } catch (err) {
      alert("Failed to unlink WhatsApp.");
    }
  };

  // Change number flow
  const startChange = () => {
    setChanging(true);
    setVerified(false);
    setNumber("");
  };

  return (
    <div className="min-h-screen flex flex-col items-center bg-gray-50 py-10 px-4">
      <h1 className="text-3xl font-bold text-gray-800 mb-8">
        Integrations Center
      </h1>

      <div className="grid gap-6 w-full max-w-3xl">
        {/* Google Calendar */}
        <div className="bg-white shadow-md rounded-xl p-6 flex items-center justify-between border">
          <div className="flex items-center gap-4">
            <Calendar className="text-blue-600 w-8 h-8" />
            <div>
              <h2 className="text-lg font-semibold">Google Calendar</h2>
              <p className="text-sm text-gray-500">
                Automatically sync your meetings and events.
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <CheckCircle className="text-green-600 w-5 h-5" />
            <span className="text-green-600 font-medium">Connected</span>
          </div>
        </div>

        {/* WhatsApp */}
        <div className="bg-white shadow-md rounded-xl p-6 border flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <MessageCircle className="text-green-600 w-8 h-8" />
              <div>
                <h2 className="text-lg font-semibold">WhatsApp</h2>
                <p className="text-sm text-gray-500">
                  Connect your WhatsApp to receive updates and interact via chat.
                </p>
              </div>
            </div>
            {verified ? (
              <div className="flex items-center gap-2 text-green-600 font-medium">
                <CheckCircle className="w-5 h-5" />
                Connected
              </div>
            ) : (
              <div className="flex items-center gap-2 text-red-500 font-medium">
                <XCircle className="w-5 h-5" />
                Not Connected
              </div>
            )}
          </div>

          {verified ? (
            <div className="flex items-center justify-between mt-2">
              <div className="text-gray-700">
                <Phone className="inline mr-2 w-4 h-4 text-gray-500" />
                <span className="font-medium">{user?.whatsapp_no}</span>
              </div>
              <div className="flex gap-3">
                <button
                  onClick={startChange}
                  className="text-sm text-blue-600 hover:underline"
                >
                  Change Number
                </button>
                <button
                  onClick={unlinkWhatsapp}
                  className="text-sm text-red-500 hover:underline"
                >
                  Disconnect
                </button>
              </div>
            </div>
          ) : (
            <div className="mt-4">
              <input
                type="text"
                placeholder="+91XXXXXXXXXX"
                value={number}
                onChange={(e) => setNumber(e.target.value)}
                className="border p-2 rounded w-full mb-3"
              />
              <div className="flex gap-3">
                <button
                  onClick={sendVerification}
                  disabled={loading}
                  className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 disabled:bg-green-400"
                >
                  {loading ? "Sending..." : "Send Code"}
                </button>
                <button
                  onClick={verifyCode}
                  disabled={loading}
                  className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:bg-blue-400"
                >
                  Verify
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Email */}
        <div className="bg-white shadow-md rounded-xl p-6 flex items-center justify-between border opacity-60">
          <div className="flex items-center gap-4">
            <Mail className="text-gray-400 w-8 h-8" />
            <div>
              <h2 className="text-lg font-semibold">Email</h2>
              <p className="text-sm text-gray-500">
                Email notifications and summaries (coming soon).
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2 text-gray-400 font-medium">
            <RefreshCw className="w-5 h-5" />
            Coming Soon
          </div>
        </div>
      </div>
    </div>
  );
}
