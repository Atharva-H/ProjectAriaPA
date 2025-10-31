// src/router/index.jsx
import { BrowserRouter, Routes, Route } from "react-router-dom";
import MinimalHome from "../pages/MinimalHome";
import MinimalLogin from "../pages/MinimalLogin";
import MinimalSignup from "../pages/MinimalSignup";
import MinimalDashboard from "../pages/MinimalDashboard";
import MinimalIntegration from "../pages/MinimalIntegration";
import MinimalContacts from "../pages/MinimalContacts";
import AccountingDashboard from "../pages/AccountingDashboard";
import Chat from "../pages/Chat";
import About from "../pages/About";
import Settings from "../pages/Settings";
import AccountDetails from "../pages/AccountDetails";
import NotFound from "../pages/NotFound";
import AuthLayout from "../layouts/AuthLayout";
import MainLayout from "../layouts/MainLayout";
import DashboardLayout from "../layouts/DashboardLayout";
import ProtectedRoute from "../components/ProtectedRoute";

export default function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public pages with Navbar */}
        <Route element={<MainLayout />}>
          <Route path="/" element={<MinimalHome />} />
          <Route path="/about" element={<About />} />
        </Route>

        {/* Auth pages (no Navbar) */}
        <Route element={<AuthLayout />}>
          <Route path="/login" element={<MinimalLogin />} />
          <Route path="/signup" element={<MinimalSignup />} />
        </Route>

        {/* Dashboard pages (protected) */}
        <Route
          element={
            <ProtectedRoute>
              <DashboardLayout />
            </ProtectedRoute>
          }
        >
          <Route path="/dashboard" element={<MinimalDashboard />} />
          <Route path="/chat" element={<Chat />} />
          <Route path="/integration" element={<MinimalIntegration />} />
          <Route path="/contacts" element={<MinimalContacts />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/account" element={<AccountDetails />} />
          {/* Accounting routes */}
          <Route path="/accounting/dashboard" element={<AccountingDashboard />} />
        </Route>

        {/* 404 Route - Catch all unmatched routes */}
        <Route path="*" element={<NotFound />} />
      </Routes>
    </BrowserRouter>
  );
}
