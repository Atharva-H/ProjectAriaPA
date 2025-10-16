import MinimalNavbar from "../components/MinimalNavbar";
import { Outlet } from "react-router-dom";

export default function MainLayout() {
  return (
    <div className="flex flex-col min-h-screen">
      <MinimalNavbar />
      <main className="flex-grow">
        <Outlet />
      </main>
    </div>
  );
}
