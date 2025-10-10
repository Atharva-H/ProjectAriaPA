// src/layouts/AuthLayout.jsx
import { Link, Outlet, useLocation } from "react-router-dom";
import { APP_NAME } from "../utils/constants";

export default function AuthLayout() {
  const location = useLocation();
  const fullWidthRoutes = ["/login", "/signup"];
  const isFullWidth = fullWidthRoutes.includes(location.pathname);

  return (
    <div className="min-h-screen w-full bg-gradient-to-br from-blue-50 to-white flex flex-col">
      <header className="p-6 text-center">
        <Link to="/" className="text-3xl font-bold text-blue-600">
          {APP_NAME}
        </Link>
      </header>

      <div className="flex-grow flex items-center justify-center px-6">
        {isFullWidth ? (
          <Outlet /> // your full-screen Login/Signup layout
        ) : (
          <div className="w-full max-w-md bg-white shadow-xl rounded-2xl p-8 border border-gray-100">
            <Outlet />
          </div>
        )}
      </div>

      <footer className="text-gray-500 text-sm text-center py-6">
        © {new Date().getFullYear()} {APP_NAME}. All rights reserved.
      </footer>
    </div>
  );
}
