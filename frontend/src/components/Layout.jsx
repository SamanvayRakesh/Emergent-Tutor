import { useState } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion';
import { Menu } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import SchoolSelectModal from './SchoolSelectModal';
import Sidebar from './Sidebar';
import CreditBadge from './CreditBadge';
import FeedbackModal from './FeedbackModal';

export default function Layout() {
  const { user } = useAuth();
  const reduceMotion = useReducedMotion();
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [showFeedback, setShowFeedback] = useState(false);

  // Wait for the school to be saved before mounting curriculum pages.
  if (!user?.school) {
    return (
      <div className="min-h-screen bg-zinc-950">
        <SchoolSelectModal />
      </div>
    );
  }

  return (
    <div className="ace-app-shell flex h-screen bg-zinc-950 overflow-hidden">
      <div className="hidden lg:block w-64 flex-shrink-0">
        <Sidebar onFeedbackOpen={() => setShowFeedback(true)} />
      </div>

      <AnimatePresence>
        {sidebarOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/60 z-40 lg:hidden"
              onClick={() => setSidebarOpen(false)}
            />
            <motion.div
              initial={{ x: reduceMotion ? 0 : -280 }}
              animate={{ x: 0 }}
              exit={{ x: reduceMotion ? 0 : -280 }}
              transition={reduceMotion ? { duration: 0 } : { type: 'spring', damping: 29, stiffness: 320, mass: 0.8 }}
              className="fixed left-0 top-0 bottom-0 w-64 z-50 lg:hidden"
            >
              <Sidebar
                onClose={() => setSidebarOpen(false)}
                onFeedbackOpen={() => setShowFeedback(true)}
              />
            </motion.div>
          </>
        )}
      </AnimatePresence>

      <div className="flex-1 flex flex-col overflow-hidden relative">
        <div className="hidden lg:flex absolute top-3 right-4 z-30">
          <CreditBadge />
        </div>

        <div className="lg:hidden flex items-center gap-3 px-4 py-3 border-b border-white/5 glass">
          <button
            type="button"
            aria-label="Open menu"
            onClick={() => setSidebarOpen(true)}
            data-testid="mobile-menu-btn"
            className="p-2 rounded-lg hover:bg-white/5 text-zinc-400 hover:text-white transition-colors"
          >
            <Menu size={20} />
          </button>
          <div className="flex-1 flex items-center">
            <img
              src="/aceit-logo.png"
              alt="Ace It"
              className="h-12 w-auto object-contain"
            />
          </div>
          <CreditBadge />
        </div>

        <main className="flex-1 overflow-y-auto">
          <AnimatePresence mode="wait">
            <motion.div
              key={`${user.user_id}:${user.school}:${user.class_level}:${location.pathname}`}
              initial={reduceMotion ? false : { opacity: 0, y: 18, scale: 0.992 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={reduceMotion ? { opacity: 1 } : { opacity: 0, y: -8, scale: 0.996 }}
              transition={reduceMotion ? { duration: 0 } : { type: 'spring', stiffness: 290, damping: 30, mass: 0.65, opacity: { duration: 0.16 } }}
              className="ace-route h-full"
            >
              <Outlet />
            </motion.div>
          </AnimatePresence>
        </main>
      </div>

      {showFeedback && (
        <FeedbackModal
          externalOpen
          onExternalClose={() => setShowFeedback(false)}
        />
      )}
    </div>
  );
}