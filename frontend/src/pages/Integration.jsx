import { useEffect, useState } from "react";

export default function Integration() {
  const [status, setStatus] = useState("loading"); // loading, linked, pending, none
  const [number, setNumber] = useState("");
  const [code, setCode] = useState("");
  const [message, setMessage] = useState("");
  const token = localStorage.getItem("jwt");

  useEffect(() => {
    // fetch user to see if already linked
    const init = async () => {
      if (!token) return;
      try {
        const res = await fetch("http://localhost:8000/auth/me", {
          headers: { Authorization: `Bearer ${token}` },
        });
        const data = await res.json();
        if (data.name) {
          // optionally you can fetch user's whatsapp status via a /user endpoint
          // for simplicity we assume if they have whatsapp_no in /auth/me we return it (extend backend if needed)
          // For now just show 'linked' UI to encourage linking
          setStatus("none");
        } else {
          setStatus("none");
        }
      } catch {
        setStatus("none");
      }
    };
    init();
  }, [token]);

  const sendCode = async () => {
    setMessage("");
    if (!number) {
      setMessage("Enter number in E.164 format (eg +9198...)");
      return;
    }
    try {
      const res = await fetch("http://localhost:8000/whatsapp/link", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ number }),
      });
      const data = await res.json();
      if (res.ok) {
        setStatus("pending");
        setMessage("Verification code sent. Check WhatsApp (join the sandbox if needed).");
      } else {
        setMessage(data.detail || data.error || "Failed to send code");
      }
    } catch (err) {
      setMessage("Network error");
    }
  };

  const verifyCode = async () => {
    setMessage("");
    try {
      const res = await fetch("http://localhost:8000/whatsapp/verify", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ number, code }),
      });
      const data = await res.json();
      if (res.ok) {
        setStatus("linked");
        setMessage("Number verified and linked.");
      } else {
        setMessage(data.detail || data.error || "Verification failed");
      }
    } catch {
      setMessage("Network error");
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center pt-24 px-4">
      <div className="bg-white shadow-md rounded-2xl p-8 max-w-lg w-full">
        <h2 className="text-2xl font-bold text-gray-800 mb-4">WhatsApp Integration</h2>

        <p className="text-sm text-gray-600 mb-4">
          Connect your WhatsApp number to receive personal notifications and interact with ProjectAria.PA from WhatsApp.
        </p>

        <div className="mb-4">
          <label className="block text-sm text-gray-700 mb-1">Phone number (E.164)</label>
          <input
            value={number}
            onChange={(e) => setNumber(e.target.value)}
            placeholder="+919876543210"
            className="w-full border px-3 py-2 rounded-lg"
          />
        </div>

        <div className="flex gap-2 mb-4">
          <button onClick={sendCode} className="bg-blue-600 text-white px-4 py-2 rounded-lg">Send verification code</button>
          <button onClick={() => setNumber("")} className="bg-gray-200 px-4 py-2 rounded-lg">Clear</button>
        </div>

        {status === "pending" && (
          <div className="mb-4">
            <label className="block text-sm text-gray-700 mb-1">Enter code</label>
            <input value={code} onChange={(e) => setCode(e.target.value)} className="w-full border px-3 py-2 rounded-lg mb-2" />
            <div className="flex gap-2">
              <button onClick={verifyCode} className="bg-green-600 text-white px-4 py-2 rounded-lg">Verify</button>
            </div>
          </div>
        )}

        <div className="text-sm text-red-600">{message}</div>

        <hr className="my-6" />
        <div className="text-sm text-gray-600">
          <p>Dev notes:</p>
          <ul className="list-disc pl-5">
            <li>For sandbox: send the Twilio join code to the sandbox number from your WhatsApp before verification.</li>
            <li>If you use ngrok, set your Twilio webhook to the ngrok URL + <code>/whatsapp/webhook</code>.</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
