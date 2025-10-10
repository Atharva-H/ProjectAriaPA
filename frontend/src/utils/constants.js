// src/utils/constants.js

export const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export const APP_NAME = "ProjectAria.PA";
export const APP_TAGLINE = "Your AI-powered personal assistant for MSME CEOs.";

export const STORAGE_KEYS = {
  TOKEN: "token",
  USER: "user",
};

export const ROUTES = {
  HOME: "/",
  DASHBOARD: "/dashboard",
  LOGIN: "/login",
  SIGNUP: "/signup",
  SETTINGS: "/settings",
  INTEGRATION: "/integration",
};

export const COLORS = {
  primary: "#2563eb",   // Tailwind blue-600
  secondary: "#1e293b", // Slate-800
  accent: "#0ea5e9",    // Sky-500
  light: "#f8fafc",
  dark: "#0f172a",
};
