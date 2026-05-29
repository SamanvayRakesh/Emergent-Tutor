import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Zap } from 'lucide-react';
import { useCredits } from '../contexts/CreditsContext';

/**
 * Minimal top-right credits chip. Glows + pulses when the balance drops.
 * Subscribes to CreditsContext so deductions animate live across the app.
 */
export default function CreditBadge() {
  const { credits, lowThreshold } = useCredits();
  const nav = useNavigate();
  const [bump, setBump] = useState(false);
  const [prev, setPrev] = useState(credits);

  useEffect(() => {
    if (credits == null || prev == null) { setPrev(credits); return; }
    if (credits !== prev) {
      setBump(true);
      const t = setTimeout(() => setBump(false), 600);
      setPrev(credits);
      return () => clearTimeout(t);
    }
  }, [credits, prev]);

  if (credits == null) return null;
  const low = credits <= (lowThreshold ?? 10);

  return (
    <button onClick={() => nav('/upgrade')} data-testid="credit-badge"
      className={`group inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-full border transition-all backdrop-blur-md ${low ? 'border-rose-400/50 bg-rose-500/15 hover:bg-rose-500/25' : 'border-amber-400/40 bg-amber-500/12 hover:bg-amber-500/20'}`}
      title={low ? 'Low credits — tap to top up' : `${credits} credits available`}>
      <motion.span
        animate={bump ? { scale: [1, 1.4, 1], rotate: [0, -12, 0] } : {}}
        transition={{ duration: 0.5 }}
        className="flex items-center">
        <Zap size={13} className={low ? 'text-rose-300' : 'text-amber-300'} fill={low ? '#fda4af' : '#fcd34d'} />
      </motion.span>
      <AnimatePresence mode="wait" initial={false}>
        <motion.span key={credits}
          initial={{ y: -8, opacity: 0 }} animate={{ y: 0, opacity: 1 }} exit={{ y: 8, opacity: 0 }}
          transition={{ duration: 0.18 }}
          className={`font-heading font-bold text-xs tabular-nums ${low ? 'text-rose-200' : 'text-amber-200'}`}>
          {credits}
        </motion.span>
      </AnimatePresence>
    </button>
  );
}
