import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { LogOut, ArrowRight } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

export default function PersistentLoginCheck() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [displayName, setDisplayName] = useState('');

  useEffect(() => {
    if (user) {
      setDisplayName(user.name || user.email || 'User');
    }
  }, [user]);

  const handleContinue = () => {
    navigate('/', { replace: true });
  };

  const handleLogout = async () => {
    await logout();
    navigate('/landing', { replace: true });
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-950 via-zinc-950 to-slate-950 flex items-center justify-center px-4 relative overflow-hidden">
      {/* Background effects */}
      <div className="absolute inset-0 pointer-events-none">
        <motion.div
          className="absolute top-1/4 left-1/4 w-96 h-96 bg-cyan-500/20 rounded-full blur-3xl"
          animate={{
            scale: [1, 1.3, 1],
            opacity: [0.15, 0.3, 0.15],
          }}
          transition={{ duration: 8, repeat: Infinity }}
        />
        <motion.div
          className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-violet-500/20 rounded-full blur-3xl"
          animate={{
            scale: [1, 1.3, 1],
            opacity: [0.15, 0.3, 0.15],
          }}
          transition={{ duration: 8, repeat: Infinity, delay: 2 }}
        />
      </div>

      {/* Content */}
      <motion.div
        initial={{ opacity: 0, y: 30, scale: 0.9 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.8 }}
        className="relative z-10 max-w-md w-full"
      >
        {/* Logo */}
        <motion.div
          className="mb-10 flex justify-center"
          animate={{ scale: [1, 1.05, 1] }}
          transition={{ duration: 3, repeat: Infinity }}
        >
          <img
            src="/aceit-logo.png"
            alt="AceIt"
            className="h-20 w-auto object-contain"
          />
        </motion.div>

        {/* Main card */}
        <div className="rounded-3xl border border-white/15 bg-white/[0.07] backdrop-blur-2xl p-10 text-center">
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.2, duration: 0.6 }}
          >
            <h1 className="text-3xl font-black text-white mb-2" style={{ fontFamily: '"Syne", sans-serif' }}>
              Welcome back!
            </h1>

            <p className="text-sm text-white/60 mb-6" style={{ fontFamily: '"Inter", sans-serif' }}>
              We found your account
            </p>

            {/* User info */}
            <motion.div
              className="mb-8 p-4 rounded-2xl bg-gradient-to-br from-cyan-400/15 to-violet-400/15 border border-cyan-300/30"
              animate={{ borderColor: ['rgba(103, 232, 249, 0.3)', 'rgba(168, 85, 247, 0.3)', 'rgba(103, 232, 249, 0.3)'] }}
              transition={{ duration: 4, repeat: Infinity }}
            >
              <div className="mb-2 flex justify-center">
                <div className="w-12 h-12 rounded-full bg-gradient-to-br from-cyan-400 to-violet-400 flex items-center justify-center text-white font-bold text-lg">
                  {displayName.charAt(0).toUpperCase()}
                </div>
              </div>

              <p className="text-white font-semibold" style={{ fontFamily: '"DM Sans", sans-serif' }}>
                {displayName}
              </p>
              <p className="text-xs text-white/50 mt-1" style={{ fontFamily: '"Inter", sans-serif' }}>
                {user?.email}
              </p>
            </motion.div>

            {/* Action buttons */}
            <div className="space-y-3">
              <motion.button
                onClick={handleContinue}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="w-full flex items-center justify-center gap-2 py-4 rounded-2xl bg-gradient-to-r from-cyan-400 to-blue-500 text-white font-bold transition hover:shadow-lg hover:shadow-cyan-400/50"
                style={{ fontFamily: '"Syne", sans-serif' }}
              >
                Continue to AceIt
                <ArrowRight size={20} />
              </motion.button>

              <motion.button
                onClick={handleLogout}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.95 }}
                className="w-full flex items-center justify-center gap-2 py-4 rounded-2xl border-2 border-white/20 bg-white/[0.05] text-white/80 font-semibold transition hover:border-red-400/50 hover:text-red-300"
                style={{ fontFamily: '"DM Sans", sans-serif' }}
              >
                <LogOut size={18} />
                Sign Out
              </motion.button>
            </div>
          </motion.div>

          {/* Footer text */}
          <p className="text-xs text-white/40 mt-6" style={{ fontFamily: '"Inter", sans-serif' }}>
            Your session is secured with browser cache
          </p>
        </div>
      </motion.div>
    </div>
  );
}