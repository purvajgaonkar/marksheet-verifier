import { NavLink } from "react-router-dom";
import {
  ShieldCheck,
  Home,
  Upload,
  Search,
  LayoutDashboard,
  MessageSquareText,
} from "lucide-react";
import { cn } from "../lib/utils";

// Navigation items shown in the left sidebar.
const NAV_ITEMS = [
  { to: "/", label: "Home", Icon: Home, end: true },
  { to: "/student-upload", label: "Student Upload", Icon: Upload },
  { to: "/track", label: "Track Submission", Icon: Search },
  { to: "/admin", label: "Admin Dashboard", Icon: LayoutDashboard },
  { to: "/assistant", label: "Policy Assistant", Icon: MessageSquareText },
];

export default function Sidebar() {
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
        {NAV_ITEMS.map(({ to, label, Icon, end }) => (
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
                {/* Active indicator bar */}
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

      {/* Footer ethics note */}
      <div className="px-5 py-4 border-t border-slate-200">
        <div className="rounded-lg bg-slate-50 p-3">
          <p className="text-[11px] font-medium text-slate-600">Review signals only</p>
          <p className="mt-0.5 text-[11px] leading-relaxed text-slate-400">
            Final decisions require human verification.
          </p>
        </div>
      </div>
    </aside>
  );
}
