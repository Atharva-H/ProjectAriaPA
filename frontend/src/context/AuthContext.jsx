// src/context/AuthContext.jsx
import { createContext, useState, useEffect } from "react";
import { getCurrentUser } from "../services/userService";
import { STORAGE_KEYS } from "../utils/constants";

export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);

  // ✅ Initialize token from URL or LocalStorage to avoid race conditions
  const [token, setToken] = useState(() => {
    const params = new URLSearchParams(window.location.search);
    const urlToken = params.get("token");
    if (urlToken) {
      localStorage.setItem(STORAGE_KEYS.TOKEN, urlToken); // Persist immediately
      return urlToken;
    }
    return localStorage.getItem(STORAGE_KEYS.TOKEN);
  });

  const [loading, setLoading] = useState(true);

  // ✅ STEP 1: Clean up URL if token was present
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get("token")) {
      const cleanUrl = window.location.origin + window.location.pathname;
      window.history.replaceState({}, document.title, cleanUrl);
    }
  }, []);

  // ✅ STEP 2: Fetch user if token exists (either from URL or localStorage)
  useEffect(() => {
    const fetchUser = async () => {
      if (!token) {
        console.log("⚠️ No token found in AuthContext, stopping fetchUser");
        setLoading(false);
        return;
      }

      console.log("🔄 Fetching user with token:", token.substring(0, 10) + "...");
      setLoading(true); // Ensure loading is true while fetching

      try {
        const data = await getCurrentUser(token);

        if (data?.error) {
          console.warn("⚠️ Invalid token response from backend:", data.error);
          logout();
        } else {
          console.log("✅ User fetched successfully:", data.email);
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
