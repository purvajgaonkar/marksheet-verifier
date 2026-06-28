// ---------------------------------------------------------------------------
// AuthContext.jsx (Phase 9)
// ---------------------------------------------------------------------------
// Holds the authenticated user + JWT and exposes login/register/logout plus
// role helpers. On mount, if a token is already stored, it hydrates the user
// from GET /auth/me (and clears the token if it is invalid/expired).
// ---------------------------------------------------------------------------

import { createContext, useCallback, useContext, useEffect, useState } from "react";

import {
  getCurrentUser,
  getToken,
  loginUser,
  logoutUser,
  registerUser,
  setToken,
} from "../api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setTokenState] = useState(() => getToken());
  const [loading, setLoading] = useState(true);

  // On first load, restore the session from a stored token (if any).
  useEffect(() => {
    let active = true;
    async function hydrate() {
      const stored = getToken();
      if (!stored) {
        setLoading(false);
        return;
      }
      try {
        const me = await getCurrentUser();
        if (active) {
          setUser(me);
          setTokenState(stored);
        }
      } catch {
        // Token expired/invalid -> clear it.
        setToken(null);
        if (active) {
          setUser(null);
          setTokenState(null);
        }
      } finally {
        if (active) setLoading(false);
      }
    }
    hydrate();
    return () => {
      active = false;
    };
  }, []);

  // If any authenticated request gets a 401 (expired/invalid token), the api
  // layer clears the token and dispatches "mv:unauthorized" — reset state here
  // so ProtectedRoute redirects to /login.
  useEffect(() => {
    function onUnauthorized() {
      setUser(null);
      setTokenState(null);
    }
    window.addEventListener("mv:unauthorized", onUnauthorized);
    return () => window.removeEventListener("mv:unauthorized", onUnauthorized);
  }, []);

  const login = useCallback(async (email, password) => {
    const result = await loginUser({ email, password });
    setUser(result.user);
    setTokenState(result.access_token);
    return result.user;
  }, []);

  const register = useCallback(async (data) => {
    // Public registration always creates a student (enforced by the backend).
    return registerUser(data);
  }, []);

  const logout = useCallback(async () => {
    await logoutUser();
    setUser(null);
    setTokenState(null);
  }, []);

  const hasRole = useCallback(
    (...roles) => !!user && roles.flat().includes(user.role),
    [user]
  );

  const value = {
    user,
    token,
    loading,
    isAuthenticated: !!user,
    login,
    register,
    logout,
    hasRole,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (ctx === null) {
    throw new Error("useAuth must be used within an <AuthProvider>.");
  }
  return ctx;
}
