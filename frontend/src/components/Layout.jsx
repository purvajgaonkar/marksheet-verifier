import { Outlet, useLocation } from "react-router-dom";
import { motion, AnimatePresence } from "motion/react";
import Sidebar from "./Sidebar";
import Navbar from "./Navbar";

/**
 * Layout is the app shell: a fixed left Sidebar, a top Navbar, and the routed
 * page content in the main area. Each route change fades/slides in gently via
 * AnimatePresence keyed on the pathname.
 */
export default function Layout() {
  const location = useLocation();

  return (
    <div className="min-h-screen bg-slate-50">
      <Sidebar />

      {/* md:pl-64 leaves room for the fixed sidebar on larger screens. */}
      <div className="md:pl-64 flex min-h-screen flex-col">
        <Navbar />

        <main className="flex-1 px-4 md:px-8 py-6 md:py-8">
          <AnimatePresence mode="wait">
            <motion.div
              key={location.pathname}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.25, ease: "easeOut" }}
              className="mx-auto w-full max-w-6xl"
            >
              <Outlet />
            </motion.div>
          </AnimatePresence>
        </main>
      </div>
    </div>
  );
}
