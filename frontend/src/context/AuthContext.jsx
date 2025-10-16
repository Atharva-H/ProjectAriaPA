// src/context/AuthContext.jsx
import { createContext, useState, useEffect } from "react";
import { getCurrentUser } from "../services/userService";
import { STORAGE_KEYS } from "../utils/constants";

export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem(STORAGE_KEYS.TOKEN));
  const [loading, setLoading] = useState(true);

  // ✅ STEP 1: Check for ?token= in URL (OAuth redirect)
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const urlToken = params.get("token");

    if (urlToken) {
      console.log("✅ OAuth token received:", urlToken);
      login(urlToken);

      // Clean up URL (remove ?token=)
      const cleanUrl = window.location.origin + window.location.pathname;
      window.history.replaceState({}, document.title, cleanUrl);
    }
  }, []); // Only once on mount

  // ✅ STEP 2: Fetch user if token exists (either from URL or localStorage)
  useEffect(() => {
    const fetchUser = async () => {
      if (!token) {
        setLoading(false);
        return;
      }

      try {
        const data = await getCurrentUser(token);

        if (data?.error) {
          console.warn("⚠️ Invalid token — logging out...");
          logout();
        } else {
          setUser(data);
        }
      } catch (err) {
        console.error("❌ Failed to fetch user:", err);
        logout();
      } finally {
        setLoading(false);
      }
    };

    fetchUser();
  }, [token]);

  // ✅ Auth actions
  const login = (newToken) => {
    setToken(newToken);
    localStorage.setItem(STORAGE_KEYS.TOKEN, newToken);
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem(STORAGE_KEYS.TOKEN);
  };

  return (
    <AuthContext.Provider value={{ user, token, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};
