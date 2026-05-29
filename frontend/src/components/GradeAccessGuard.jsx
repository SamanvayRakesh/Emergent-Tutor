import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';
import { Lock, X, ArrowRight } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

/**
 * Global toast that fires when the backend returns a grade-lock 403.
 * Mounts a single axios response interceptor; non-intrusive, animated, auto-dismisses.
 */
export default function GradeAccessGuard() {
  const { user } = useAuth();
  const [toast, setToast] = useState(null);
  const nav = useNavigate();

  useEffect(() => {
    const interceptor = axios.interceptors.response.use(
      r => r,
      err => {
        if (err?.response?.status === 403) {
          const detail = err.response.data?.detail;
          const msg = typeof detail === 'string' ? detail : detail?.message;
          // Only react if the 403 is grade-related
          if (msg && /grade|class|access/i.test(msg)) {
            setToast({ message: msg });
            // auto-dismiss after 7s
            setTimeout(() => setToast(null), 7000);
          }
        }
        return Promise.reject(err);
      },
    );
    return () => axios.interceptors.response.eject(interceptor);
  }, []);

  if (!user) return null;

  return (
    <AnimatePresence>
      {toast && (
        <motion.div
          initial={{ opacity: 0, y: 20, x: 20 }}
          animate={{ opacity: 1, y: 0, x: 0 }}
          exit={{ opacity: 0, y: 10, x: 20 }}
          className="fixed bottom-6 right-6 z-[120] max-w-sm rounded-2xl glass border border-amber-400/40 p-4 shadow-2xl shadow-amber-500/20"
          data-testid="access-block-toast"
          style={{ background: 'rgba(30, 27, 75, 0.85)' }}>
          <button onClick={() => setToast(null)} className="absolute top-2 right-2 p-1 rounded-full text-zinc-500 hover:text-white hover:bg-white/10 transition-all" data-testid="access-toast-close">
            <X size={12} />
          </button>
          <div className="flex items-start gap-3 pr-4">
            <div className="w-9 h-9 rounded-xl bg-amber-500/20 border border-amber-400/40 flex items-center justify-center flex-shrink-0">
              <Lock size={16} className="text-amber-400" />
            </div>
            <div className="min-w-0">
              <p className="text-amber-300 text-[10px] font-body uppercase tracking-widest font-bold mb-0.5">Grade lock</p>
              <p className="text-white text-sm font-body leading-snug mb-1">
                You currently only have access to <span className="font-bold">Class {user.class_level}</span> content based on your selected grade.
              </p>
              <button
                onClick={() => { setToast(null); nav('/profile'); }}
                data-testid="access-toast-cta"
                className="inline-flex items-center gap-1 text-amber-300 hover:text-amber-200 text-xs font-body font-semibold transition-colors">
                Change in Profile <ArrowRight size={11} />
              </button>
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
