// src/layouts/DashboardLayout.jsx
import { Outlet, Link, useLocation } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import MinimalNavbar from "../components/MinimalNavbar";

export default function DashboardLayout() {
  const { user } = useAuth();
  const location = useLocation();

  const navItems = [
    { name: "Dashboard", path: "/dashboard" },
    { name: "Integration", path: "/integration" },
    { name: "Contacts", path: "/contacts" },
    { name: "Settings", path: "/settings" },
  ];

  return (
    <div className="flex min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Sidebar
      <aside className="hidden md:flex flex-col w-64 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 p-6">
        <h2 className="text-xl font-semibold text-blue-600 mb-8">
          Welcome, {user?.name?.split(" ")[0] || "User"} 👋
        </h2>
        <nav className="flex flex-col gap-3">
          {navItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={`px-4 py-2 rounded-lg font-medium ${
                location.pathname === item.path
                  ? "bg-blue-600 text-white"
                  : "text-gray-700 dark:text-gray-300 hover:bg-blue-50 dark:hover:bg-gray-700"
              }`}
            >
              {item.name}
            </Link>
          ))}
        </nav>
      </aside> */}

      {/* Main content */}
      <div className="flex-1 flex flex-col">
        <MinimalNavbar />
        <main className="flex-1 p-6 overflow-y-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
