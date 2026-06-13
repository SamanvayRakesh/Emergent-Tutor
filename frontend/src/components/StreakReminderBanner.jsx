import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Flame, Bell, BellOff, X, ArrowRight, Heart } from 'lucide-react';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const DISMISS_KEY = 'aceit_streak_dismiss';

export default function StreakReminderBanner() {
  const [data, setData] = useState(null);
  const [dismissed, setDismissed] = useState(false);
  const [notifPermission, setNotifPermission] = useState(
    typeof Notification !== 'undefined' ? Notification.permission : 'denied'
  );
  const nav = useNavigate();

  useEffect(() => {
    // Hide if dismissed today
    const dismissDate = sessionStorage.getItem(DISMISS_KEY);
    if (dismissDate === new Date().toDateString()) {
      setDismissed(true);
      return;
    }
    axios.get(`${API}/streak-reminder`, { withCredentials: true })
      .then(r => {
        setData(r.data);
        // Fire a native browser notification if permission granted + at risk
        if (r.data?.at_risk && typeof Notification !== 'undefined' && Notification.permission === 'granted') {
          try {
            const n = new Notification('🔥 Don\'t break your streak!', {
              body: r.data.message,
              tag: 'aceit-streak',
              icon: '/favicon.ico',
            });
            n.onclick = () => { window.focus(); nav('/chat'); n.close(); };
          } catch {}
        }
      })
      .catch(() => {});
  }, [nav]);

  const handleDismiss = () => {
    sessionStorage.setItem(DISMISS_KEY, new Date().toDateString());
    setDismissed(true);
  };

  const handleEnableNotif = async () => {
    if (typeof Notification === 'undefined') return;
    const perm = await Notification.requestPermission();
    setNotifPermission(perm);
    if (perm === 'granted') {
      try {
        new Notification('AceIt AI is on duty 🔥', {
          body: 'We\'ll nudge you when your streak is at risk. Now go crush a quiz!',
          icon: '/favicon.ico',
        });
      } catch {}
    }
  };

  // Show only when meaningful (at risk, broken, or active with streak ≥2)
  if (dismissed || !data) return null;
  const showBanner = data.at_risk || data.broken || (data.active_today && data.streak >= 2);
  if (!showBanner) return null;

  const accent = data.at_risk ? '#f59e0b' : data.broken ? '#ef4444' : '#10b981';
  const Icon = data.broken ? Heart : Flame;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }}
        data-testid="streak-reminder-banner"
        className="relative overflow-hidden rounded-2xl p-4 border"
        style={{ background: accent + '0d', borderColor: accent + '40' }}>
        <div className="absolute -top-10 -right-10 w-32 h-32 rounded-full blur-3xl pointer-events-none opacity-30" style={{ background: accent }} />

        <div className="relative z-10 flex items-center gap-3">
          <div className="w-11 h-11 rounded-xl flex items-center justify-center flex-shrink-0"
            style={{ background: accent + '22', border: `1px solid ${accent}50` }}>
            <Icon size={20} style={{ color: accent }} className={data.at_risk ? 'animate-pulse' : ''} />
          </div>

          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-0.5">
              <span className="text-[10px] font-body uppercase tracking-widest font-semibold" style={{ color: accent }}>
                {data.at_risk ? 'Streak at Risk' : data.broken ? 'Streak Broken' : `${data.streak}-Day Streak Active`}
              </span>
              {data.days_to_exam !== null && data.days_to_exam !== undefined && (
                <span className="text-zinc-500 text-[10px] font-body">• {data.days_to_exam}d to exam</span>
              )}
            </div>
            <p className="text-white font-body text-sm leading-snug">{data.message}</p>
          </div>

          <div className="flex items-center gap-1.5 flex-shrink-0">
            {notifPermission === 'default' && (
              <button onClick={handleEnableNotif} data-testid="enable-notifications-btn" title="Enable browser notifications"
                className="p-2 rounded-lg text-zinc-400 hover:text-white hover:bg-white/5 transition-all">
                <Bell size={14} />
              </button>
            )}
            {notifPermission === 'denied' && (
              <button disabled title="Notifications blocked in browser settings"
                className="p-2 rounded-lg text-zinc-700 cursor-not-allowed">
                <BellOff size={14} />
              </button>
            )}
            <button onClick={() => nav('/chat')} data-testid="streak-cta-btn"
              className="px-3 py-2 rounded-lg font-heading font-bold text-xs flex items-center gap-1.5 transition-all whitespace-nowrap"
              style={{ background: accent, color: data.broken ? 'white' : 'black' }}>
              {data.cta} <ArrowRight size={12} />
            </button>
            <button onClick={handleDismiss} data-testid="dismiss-streak-btn"
              className="p-1.5 rounded-lg text-zinc-500 hover:text-white hover:bg-white/5 transition-all">
              <X size={14} />
            </button>
          </div>
        </div>
      </motion.div>
    </AnimatePresence>
  );
}
