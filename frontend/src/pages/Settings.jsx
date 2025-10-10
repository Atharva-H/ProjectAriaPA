import { useEffect, useState } from "react";

export default function Settings() {
  const [theme, setTheme] = useState("light");

  useEffect(() => {
    const savedTheme = localStorage.getItem("theme") || "light";
    setTheme(savedTheme);
    document.documentElement.classList.toggle("dark", savedTheme === "dark");
  }, []);

  const toggleTheme = () => {
    const newTheme = theme === "light" ? "dark" : "light";
    setTheme(newTheme);
    localStorage.setItem("theme", newTheme);
    document.documentElement.classList.toggle("dark", newTheme === "dark");
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50 dark:bg-gray-900 transition-colors">
      <div className="bg-white dark:bg-gray-800 shadow-md rounded-2xl p-8 max-w-lg w-full text-center">
        <h2 className="text-2xl font-bold text-gray-800 dark:text-gray-100 mb-6">
          Settings ⚙️
        </h2>

        <div className="flex items-center justify-between border rounded-xl px-5 py-4 mb-8 dark:border-gray-700">
          <span className="text-gray-700 dark:text-gray-300 font-medium">
            Theme
          </span>
          <button
            onClick={toggleTheme}
            className={`px-5 py-2 rounded-lg font-semibold transition-all ${
              theme === "light"
                ? "bg-blue-600 text-white hover:bg-blue-700"
                : "bg-yellow-400 text-gray-900 hover:bg-yellow-500"
            }`}
          >
            {theme === "light" ? "🌞 Light Mode" : "🌙 Dark Mode"}
          </button>
        </div>

        <p className="text-sm text-gray-500 dark:text-gray-400">
          Your preference will be saved for future sessions.
        </p>
      </div>
    </div>
  );
}
