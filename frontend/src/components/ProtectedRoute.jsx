// ---------------------------------------------------------------------------
// ProtectedRoute.jsx (Phase 9)
// ---------------------------------------------------------------------------
// Route guards used in App.jsx:
//   * <ProtectedRoute>            - requires a logged-in user (any role)
//   * <RoleProtectedRoute roles>  - requires one of the given roles
//
// While the auth state is still hydrating we show a spinner so we never flash a
// redirect. Unauthenticated users go to /login; wrong-role users see a clear
// "no access" card instead of leaking the protected page.
// ---------------------------------------------------------------------------

import { Link, Navigate, useLocation } from "react-router-dom";
import { Loader2, Lock } from "lucide-react";

import { useAuth } from "../context/AuthContext";
import { buttonVariants } from "../lib/utils";

function FullScreenSpinner() {
  return (
    <div className="flex items-center justify-center py-24 text-slate-400">
      <Loader2 className="h-6 w-6 animate-spin" />
    </div>
  );
}

function NoAccess({ user }) {
  // Send the user back to a home that makes sense for their role.
  const home = user?.role === "student" ? "/track" : "/";
  return (
    <div className="flex flex-col items-center justify-center py-24 text-center">
      <span className="flex h-12 w-12 items-center justify-center rounded-full bg-red-50 text-red-600">
        <Lock className="h-6 w-6" />
      </span>
      <h2 className="mt-4 text-xl font-semibold text-slate-900">Access restricted</h2>
      <p className="mt-1 max-w-sm text-sm text-slate-500">
        Your account doesn't have permission to view this page. Admin and reviewer
        tools are limited to staff accounts.
      </p>
      <Link to={home} className={buttonVariants({ variant: "primary" }) + " mt-6"}>
        Go back
      </Link>
    </div>
  );
}

/** Requires a logged-in user; optionally restricts to `roles`. */
export function ProtectedRoute({ roles, children }) {
  const { isAuthenticated, loading, user } = useAuth();
  const location = useLocation();

  if (loading) return <FullScreenSpinner />;
  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }
  if (roles && roles.length > 0 && !roles.includes(user.role)) {
    return <NoAccess user={user} />;
  }
  return children;
}

/** Convenience wrapper that requires one of `roles` (e.g. admin/reviewer). */
export function RoleProtectedRoute({ roles, children }) {
  return <ProtectedRoute roles={roles}>{children}</ProtectedRoute>;
}

export default ProtectedRoute;
