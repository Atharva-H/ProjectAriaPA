// src/context/AuthContext.jsx
import { createContext, useState, useEffect } from "react";
import { getCurrentUser } from "../services/userService";
import { STORAGE_KEYS } from "../utils/constants";

export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem(STORAGE_KEYS.TOKEN));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
  // 🧠 STEP 1: Check for ?token= in URL (OAuth redirect)
  const params = new URLSearchParams(window.location.search);
  const urlToken = params.get("token");

  if (urlToken) {
    console.log("✅ OAuth token received:", urlToken);
    login(urlToken); // Save to state + localStorage
    // clean up URL (remove ?token=)
    window.history.replaceState({}, document.title, "/dashboard");
  }

  // 🧠 STEP 2: If token already exists, fetch user
  const fetchUser = async () => {
    if (!token && !urlToken) {
      setLoading(false);
      return;
    }

    const activeToken = urlToken || token;

    try {
      const data = await getCurrentUser(activeToken);
      setUser(data);
    } catch (err) {
      console.error("Failed to fetch user:", err);
      logout(); // token expired or invalid
    } finally {
      setLoading(false);
    }
  };
  fetchUser();
}, [token]);


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
