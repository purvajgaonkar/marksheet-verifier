import { NavLink, useNavigate } from "react-router-dom";
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
  UserCircle2,
} from "lucide-react";
import { cn } from "../lib/utils";
import { useAuth } from "../context/AuthContext";

// Build the navigation list for the current auth state / role (Phase 9).
function navItemsFor(user) {
  const home = { to: "/", label: "Home", Icon: Home, end: true };
  if (!user) {
    return [home, { to: "/login", label: "Login", Icon: LogIn }, { to: "/register", label: "Register", Icon: UserPlus }];
  }
  if (user.role === "student") {
    return [
      home,
      { to: "/student-upload", label: "Student Upload", Icon: Upload },
      { to: "/track", label: "Track My Submissions", Icon: Search },
    ];
  }
  // admin / reviewer
  return [
    home,
    { to: "/admin", label: "Admin Dashboard", Icon: LayoutDashboard },
    { to: "/assistant", label: "Policy Assistant", Icon: MessageSquareText },
  ];
}

export default function Sidebar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const items = navItemsFor(user);

  async function handleLogout() {
    await logout();
    navigate("/login", { replace: true });
  }

  return (
    <aside className="hidden md:flex md:w-64 md:flex-col md:fixed md:inset-y-0 border-r border-slate-200 bg-white">
      {/* Brand */}
      <div className="flex items-center gap-2.5 px-6 h-16 border-b border-slate-200">
        <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-indigo-600 text-white shadow-sm shadow-indigo-600/30">
          <ShieldCheck className="h-5 w-5" />
        </span>
        <div className="leading-tight">
          <p className="text-sm font-semibold text-slate-900">Marksheet</p>
          <p className="text-xs font-medium text-indigo-600">Verifier</p>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        <p className="px-3 pb-2 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
          Navigation
        </p>
        {items.map(({ to, label, Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              cn(
                "group relative flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-indigo-50 text-indigo-700"
                  : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
              )
            }
          >
            {({ isActive }) => (
              <>
                <span
                  className={cn(
                    "absolute left-0 top-1.5 bottom-1.5 w-1 rounded-r-full bg-indigo-600 transition-opacity",
                    isActive ? "opacity-100" : "opacity-0"
                  )}
                />
                <Icon className="h-[18px] w-[18px] shrink-0" />
                {label}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Footer: signed-in user + logout, or ethics note when signed out */}
      <div className="px-4 py-4 border-t border-slate-200">
        {user ? (
          <div className="space-y-2">
            <div className="flex items-center gap-2.5 rounded-lg bg-slate-50 px-3 py-2.5">
              <UserCircle2 className="h-7 w-7 shrink-0 text-slate-400" />
              <div className="min-w-0 leading-tight">
                <p className="truncate text-sm font-medium text-slate-800">
                  {user.full_name || user.email}
                </p>
                <p className="text-[11px] font-medium capitalize text-indigo-600">{user.role}</p>
              </div>
            </div>
            <button
              onClick={handleLogout}
              className="flex w-full items-center justify-center gap-2 rounded-lg border border-slate-200 px-3 py-2 text-sm font-medium text-slate-600 transition-colors hover:bg-slate-50 hover:text-slate-900"
            >
              <LogOut className="h-4 w-4" />
              Logout
            </button>
          </div>
        ) : (
          <div className="rounded-lg bg-slate-50 p-3">
            <p className="text-[11px] font-medium text-slate-600">Review signals only</p>
            <p className="mt-0.5 text-[11px] leading-relaxed text-slate-400">
              Final decisions require human verification.
            </p>
          </div>
        )}
      </div>
    </aside>
  );
}
