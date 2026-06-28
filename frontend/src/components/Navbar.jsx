import { useEffect, useState } from "react";
import { NavLink, useLocation, useNavigate } from "react-router-dom";
import {
  ShieldCheck,
  Home,
  Upload,
  Search,
  LayoutDashboard,
  MessageSquareText,
  LogIn,
  UserPlus,
  LogOut,
} from "lucide-react";
import { getHealth } from "../api";
import { cn } from "../lib/utils";
import { useAuth } from "../context/AuthContext";

// Map a route path to a friendly page title shown in the top bar.
function titleForPath(pathname) {
  if (pathname === "/") return "Overview";
  if (pathname.startsWith("/login")) return "Sign in";
  if (pathname.startsWith("/register")) return "Create account";
  if (pathname.startsWith("/student-upload")) return "Student Upload";
  if (pathname.startsWith("/track")) return "My Submissions";
  if (pathname.startsWith("/upload")) return "Upload Marksheet";
  if (pathname.startsWith("/admin")) return "Admin Dashboard";
  if (pathname.startsWith("/assistant")) return "Policy Assistant";
  if (pathname.startsWith("/cases/")) return "Case Detail";
  return "Marksheet Verifier";
}

// Compact nav shown only on small screens, computed from the auth state.
function mobileNavFor(user) {
  const home = { to: "/", Icon: Home, end: true, label: "Home" };
  if (!user) {
    return [home, { to: "/login", Icon: LogIn, label: "Login" }, { to: "/register", Icon: UserPlus, label: "Register" }];
  }
  if (user.role === "student") {
    return [home, { to: "/student-upload", Icon: Upload, label: "Submit" }, { to: "/track", Icon: Search, label: "Track" }];
  }
  return [home, { to: "/admin", Icon: LayoutDashboard, label: "Admin" }, { to: "/assistant", Icon: MessageSquareText, label: "Assistant" }];
}

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
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const mobileNav = mobileNavFor(user);

  async function handleLogout() {
    await logout();
    navigate("/login", { replace: true });
  }

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

        <div className="flex items-center gap-3">
          <HealthPill />
          {user ? (
            <button
              onClick={handleLogout}
              className="inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-medium text-slate-600 hover:bg-slate-50 hover:text-slate-900"
              title={`Signed in as ${user.email} (${user.role})`}
            >
              <LogOut className="h-3.5 w-3.5" />
              <span className="hidden sm:inline">Logout</span>
            </button>
          ) : (
            <NavLink
              to="/login"
              className="inline-flex items-center gap-1.5 rounded-full bg-indigo-600 px-3 py-1 text-xs font-medium text-white hover:bg-indigo-700"
            >
              <LogIn className="h-3.5 w-3.5" />
              <span className="hidden sm:inline">Sign in</span>
            </NavLink>
          )}
        </div>
      </div>

      {/* Mobile nav row */}
      <nav className="flex items-center gap-1 border-t border-slate-100 px-2 py-1.5 md:hidden">
        {mobileNav.map(({ to, Icon, label, end }) => (
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
