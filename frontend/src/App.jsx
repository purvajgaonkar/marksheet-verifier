import { BrowserRouter, Routes, Route, Link } from "react-router-dom";
import { FileQuestion } from "lucide-react";
import Layout from "./components/Layout";
import LandingPage from "./pages/LandingPage";
import UploadPage from "./pages/UploadPage";
import AdminDashboard from "./pages/AdminDashboard";
import CaseDetail from "./pages/CaseDetail";
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

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* All pages share the Layout shell (sidebar + navbar). */}
        <Route element={<Layout />}>
          <Route path="/" element={<LandingPage />} />
          <Route path="/upload" element={<UploadPage />} />
          <Route path="/admin" element={<AdminDashboard />} />
          <Route path="/cases/:caseId" element={<CaseDetail />} />
          <Route path="*" element={<NotFound />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
