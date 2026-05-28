import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Crown, ArrowRight, X, Lock } from 'lucide-react';
import { useSubscription } from '../contexts/SubscriptionContext';

export default function UpgradePromptModal() {
  const { upgradePrompt, dismissUpgrade } = useSubscription();
  const nav = useNavigate();
  if (!upgradePrompt) return null;

  const targetPlan = upgradePrompt.upgrade_to === 'elite' ? 'Elite' : 'Pro';

  return (
    <AnimatePresence>
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
        className="fixed inset-0 z-[150] flex items-center justify-center p-4 bg-black/70 backdrop-blur-md"
        data-testid="upgrade-prompt-modal">
        <motion.div initial={{ scale: 0.85, y: 20 }} animate={{ scale: 1, y: 0 }} exit={{ scale: 0.9, y: 10 }}
          className="w-full max-w-md rounded-3xl bg-gradient-to-br from-amber-500/20 via-rose-500/15 to-violet-600/20 border-2 border-amber-400/40 backdrop-blur-xl overflow-hidden relative">
          <div className="absolute -top-16 -right-16 w-48 h-48 rounded-full blur-3xl bg-amber-400/40 pointer-events-none" />
          <div className="absolute -bottom-20 -left-20 w-56 h-56 rounded-full blur-3xl bg-rose-500/30 pointer-events-none" />

          <button onClick={dismissUpgrade} data-testid="upgrade-close-btn"
            className="absolute top-3 right-3 z-10 p-1.5 rounded-full text-zinc-400 hover:text-white hover:bg-white/10 transition-all">
            <X size={16} />
          </button>

          <div className="relative z-10 p-6 text-center">
            <motion.div initial={{ scale: 0, rotate: -180 }} animate={{ scale: 1, rotate: 0 }} transition={{ type: 'spring', delay: 0.1 }}
              className="w-16 h-16 mx-auto mb-3 rounded-2xl flex items-center justify-center bg-gradient-to-br from-amber-400 to-rose-500 shadow-lg shadow-amber-500/50">
              <Crown size={28} className="text-white" />
            </motion.div>

            <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-zinc-900/60 border border-amber-400/30 mb-3">
              <Lock size={10} className="text-amber-400" />
              <span className="text-amber-400 text-[10px] font-body uppercase tracking-widest font-bold">
                {upgradePrompt.feature?.replace(/_/g, ' ') || 'Premium Feature'}
              </span>
            </div>

            <h3 className="text-white text-2xl font-heading font-black mb-2">
              Time to go {targetPlan}
            </h3>
            <p className="text-zinc-300 text-sm font-body mb-1 leading-relaxed">
              {upgradePrompt.message || "You've hit the limit of your Free plan."}
            </p>
            {upgradePrompt.limit_info && (
              <p className="text-zinc-500 text-xs font-body mb-4">
                {upgradePrompt.limit_info.current} / {upgradePrompt.limit_info.limit} {upgradePrompt.limit_info.unit} used
              </p>
            )}

            <div className="grid grid-cols-2 gap-2 my-4 text-left">
              {[
                'Unlimited AI tutoring',
                'Adaptive weak-topic quizzes',
                '5x more mock exams',
                'Full leaderboard rankings',
              ].map(line => (
                <div key={line} className="flex items-center gap-1.5 text-xs font-body text-zinc-200">
                  <span className="text-amber-400">✓</span> {line}
                </div>
              ))}
            </div>

            <button onClick={() => { dismissUpgrade(); nav('/upgrade'); }} data-testid="upgrade-prompt-cta"
              className="w-full py-3 rounded-xl bg-gradient-to-r from-amber-400 to-rose-500 text-white font-heading font-bold text-sm flex items-center justify-center gap-2 hover:scale-[1.02] transition-transform">
              See Plans <ArrowRight size={14} />
            </button>
            <button onClick={dismissUpgrade} data-testid="upgrade-prompt-later"
              className="w-full py-2 mt-2 text-zinc-500 hover:text-white text-xs font-body transition-colors">
              Maybe later
            </button>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
