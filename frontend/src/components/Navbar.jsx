import { useEffect, useState } from "react";
import { NavLink, useLocation } from "react-router-dom";
import { ShieldCheck, Home, Upload, LayoutDashboard, MessageSquareText } from "lucide-react";
import { getHealth } from "../api";
import { cn } from "../lib/utils";

// Map a route path to a friendly page title shown in the top bar.
function titleForPath(pathname) {
  if (pathname === "/") return "Overview";
  if (pathname.startsWith("/upload")) return "Upload Marksheet";
  if (pathname.startsWith("/admin")) return "Admin Dashboard";
  if (pathname.startsWith("/cases/")) return "Case Detail";
  return "Marksheet Verifier";
}

// Compact nav shown only on small screens, where the sidebar is hidden.
const MOBILE_NAV = [
  { to: "/", Icon: Home, end: true, label: "Home" },
  { to: "/upload", Icon: Upload, label: "Upload" },
  { to: "/admin", Icon: LayoutDashboard, label: "Admin" },
  { to: "/assistant", Icon: MessageSquareText, label: "Assistant" },
];

// Small connection indicator: checks the backend /health endpoint on mount.
function HealthPill() {
  const [status, setStatus] = useState("checking"); // checking | online | offline

  useEffect(() => {
    let active = true;
    getHealth()
      .then(() => active && setStatus("online"))
      .catch(() => active && setStatus("offline"));
    return () => {
      active = false;
    };
  }, []);

  const config = {
    checking: { text: "Checking…", dot: "bg-slate-300", ring: "ring-slate-200", color: "text-slate-500", pulse: true },
    online: { text: "Backend online", dot: "bg-emerald-500", ring: "ring-emerald-200", color: "text-emerald-700", pulse: false },
    offline: { text: "Backend offline", dot: "bg-red-500", ring: "ring-red-200", color: "text-red-700", pulse: false },
  }[status];

  return (
    <span
      className={cn(
        "inline-flex items-center gap-2 rounded-full bg-white px-3 py-1 text-xs font-medium ring-1 ring-inset",
        config.ring,
        config.color
      )}
      title={`Backend status: ${status}`}
    >
      <span className={cn("h-2 w-2 rounded-full", config.dot, config.pulse && "animate-pulse")} />
      <span className="hidden sm:inline">{config.text}</span>
    </span>
  );
}

export default function Navbar() {
  const location = useLocation();
  return (
    <header className="sticky top-0 z-10 border-b border-slate-200 bg-white/80 backdrop-blur">
      <div className="flex h-16 items-center justify-between px-4 md:px-8">
        {/* Mobile brand (sidebar is hidden on small screens) */}
        <div className="flex items-center gap-2.5 md:hidden">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-600 text-white">
            <ShieldCheck className="h-4.5 w-4.5" style={{ height: 18, width: 18 }} />
          </span>
          <span className="text-sm font-semibold text-slate-900">Marksheet Verifier</span>
        </div>

        {/* Desktop page title */}
        <div className="hidden md:block">
          <h1 className="text-base font-semibold text-slate-900">
            {titleForPath(location.pathname)}
          </h1>
          <p className="hidden lg:block text-xs text-slate-400">
            Academic document verification &amp; tampering signal analysis
          </p>
        </div>

        <HealthPill />
      </div>

      {/* Mobile nav row */}
      <nav className="flex items-center gap-1 border-t border-slate-100 px-2 py-1.5 md:hidden">
        {MOBILE_NAV.map(({ to, Icon, label, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              cn(
                "flex flex-1 items-center justify-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition-colors",
                isActive ? "bg-indigo-50 text-indigo-700" : "text-slate-500 hover:bg-slate-100"
              )
            }
          >
            <Icon className="h-4 w-4" />
            {label}
          </NavLink>
        ))}
      </nav>
    </header>
  );
}
