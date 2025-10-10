// src/utils/formatDate.js

/**
 * Format a date/time string or object into a readable format.
 * @param {string|Date} date - The date/time value to format.
 * @param {object} options - Intl.DateTimeFormat options.
 * @returns {string} Formatted date string.
 */
export function formatDate(date, options = {}) {
  if (!date) return "";

  const d = typeof date === "string" ? new Date(date) : date;
  if (Number.isNaN(d.getTime())) return "";

  const defaultOptions = {
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: true,
  };

  return new Intl.DateTimeFormat("en-IN", { ...defaultOptions, ...options }).format(d);
}

/**
 * Returns a "relative time" string (e.g. '2h ago', 'yesterday', etc.)
 */
export function timeAgo(date) {
  if (!date) return "";
  const d = typeof date === "string" ? new Date(date) : date;
  const diff = (Date.now() - d.getTime()) / 1000;

  if (diff < 60) return `${Math.floor(diff)}s ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  if (diff < 172800) return "yesterday";
  return `${Math.floor(diff / 86400)}d ago`;
}
