import { BrowserRouter, Routes, Route, Link } from "react-router-dom";
import { FileQuestion } from "lucide-react";
import Layout from "./components/Layout";
import LandingPage from "./pages/LandingPage";
import UploadPage from "./pages/UploadPage";
import AdminDashboard from "./pages/AdminDashboard";
import CaseDetail from "./pages/CaseDetail";
import PolicyAssistant from "./pages/PolicyAssistant";
import StudentUpload from "./pages/StudentUpload";
import StudentStatus from "./pages/StudentStatus";
import Login from "./pages/Login";
import Register from "./pages/Register";
import { AuthProvider } from "./context/AuthContext";
import { ProtectedRoute, RoleProtectedRoute } from "./components/ProtectedRoute";
import { buttonVariants } from "./lib/utils";

// A tiny 404 fallback so unknown URLs do not show a blank screen.
function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center text-center py-24">
      <FileQuestion className="h-12 w-12 text-slate-300" />
      <h2 className="mt-4 text-xl font-semibold text-slate-900">Page not found</h2>
      <p className="mt-1 text-sm text-slate-500">
        The page you are looking for does not exist.
      </p>
      <Link to="/" className={buttonVariants({ variant: "primary" }) + " mt-6"}>
        Back to Home
      </Link>
    </div>
  );
}

// Staff-only roles for admin/reviewer pages.
const STAFF = ["admin", "reviewer"];

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* All pages share the Layout shell (sidebar + navbar). */}
          <Route element={<Layout />}>
            {/* Public */}
            <Route path="/" element={<LandingPage />} />
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />

            {/* Student-only (requires login) */}
            <Route
              path="/student-upload"
              element={
                <ProtectedRoute roles={["student"]}>
                  <StudentUpload />
                </ProtectedRoute>
              }
            />
            <Route
              path="/track"
              element={
                <ProtectedRoute roles={["student"]}>
                  <StudentStatus />
                </ProtectedRoute>
              }
            />

            {/* Admin / reviewer only */}
            <Route
              path="/admin"
              element={
                <RoleProtectedRoute roles={STAFF}>
                  <AdminDashboard />
                </RoleProtectedRoute>
              }
            />
            <Route
              path="/cases/:caseId"
              element={
                <RoleProtectedRoute roles={STAFF}>
                  <CaseDetail />
                </RoleProtectedRoute>
              }
            />
            <Route
              path="/assistant"
              element={
                <RoleProtectedRoute roles={STAFF}>
                  <PolicyAssistant />
                </RoleProtectedRoute>
              }
            />
            {/* Legacy dev upload page — staff only (not linked in nav) */}
            <Route
              path="/upload"
              element={
                <RoleProtectedRoute roles={STAFF}>
                  <UploadPage />
                </RoleProtectedRoute>
              }
            />

            <Route path="*" element={<NotFound />} />
          </Route>
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
