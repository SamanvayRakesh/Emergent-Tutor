import { useState } from 'react';
import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import SchoolSelectModal from './SchoolSelectModal';
import { motion, AnimatePresence } from 'framer-motion';
import Sidebar from './Sidebar';
import CreditBadge from './CreditBadge';
import { Menu, X } from 'lucide-react';

export default function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="flex h-screen bg-zinc-950 overflow-hidden">
      {/* Desktop Sidebar */}
      <div className="hidden lg:block w-64 flex-shrink-0">
        <Sidebar />
      </div>

      {/* Mobile Sidebar Overlay */}
      <AnimatePresence>
        {sidebarOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/60 z-40 lg:hidden"
              onClick={() => setSidebarOpen(false)}
            />
            <motion.div
              initial={{ x: -280 }} animate={{ x: 0 }} exit={{ x: -280 }}
              transition={{ type: 'spring', damping: 25, stiffness: 200 }}
              className="fixed left-0 top-0 bottom-0 w-64 z-50 lg:hidden"
            >
              <Sidebar onClose={() => setSidebarOpen(false)} />
            </motion.div>
          </>
        )}
      </AnimatePresence>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden relative">
        {/* Global Credit Badge — top-right, floating */}
        <div className="hidden lg:flex absolute top-3 right-4 z-30">
          <CreditBadge />
        </div>

        {/* Mobile Header */}
        <div className="lg:hidden flex items-center gap-3 px-4 py-3 border-b border-white/5 glass">
          <button onClick={() => setSidebarOpen(true)} data-testid="mobile-menu-btn"
            className="p-2 rounded-lg hover:bg-white/5 text-zinc-400 hover:text-white transition-colors">
            <Menu size={20} />
          </button>
          <span className="font-heading font-bold text-white flex-1">
            <span className="gradient-text">Neura</span>Learn
          </span>
          <CreditBadge />
        </div>

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto">
          <AnimatePresence mode="wait">
            <motion.div
              key={window.location.pathname}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.25 }}
              className="h-full"
            >
              <Outlet />
            </motion.div>
          </AnimatePresence>
        </main>
      </div>

      {/* School selection onboarding modal — shown to users without a school */}
      <SchoolSelectModal />
    </div>
  );
}
