import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { User, Mail, BookOpen, Zap, Flame, Trophy, Save, Shield, Star, Clock, Lock, Send, X, CheckCircle, AlertTriangle, Crown, ArrowRight, CreditCard, Package, Calendar, TrendingUp, LogOut } from 'lucide-react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { useAuth } from '../contexts/AuthContext';
import { useSubscription } from '../contexts/SubscriptionContext';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const CLASSES = ['6', '7', '8', '9', '10', '11', '12'];

export default function ProfilePage() {
  const { user, setUser } = useAuth();
  const { plan } = useSubscription();
  const nav = useNavigate();
  const [selectedClass, setSelectedClass] = useState(user?.class_level || '9');
  const [saving, setSaving]               = useState(false);
  const [saved, setSaved]                 = useState(false);
  const [gradeStatus, setGradeStatus]     = useState(null);
  const [appealOpen, setAppealOpen]       = useState(false);
  const [appealForm, setAppealForm]       = useState({ desired_class: '', reason: '' });
  const [appealResult, setAppealResult]   = useState(null);
  const [appealSubmitting, setAppealSubmitting] = useState(false);
  const [errorMsg, setErrorMsg]           = useState('');
  const [cancelLoading, setCancelLoading] = useState(false);
  const [credits, setCredits]             = useState(user?.credits || 0);

  useEffect(() => {
    axios.get(`${API}/users/grade-status`, { withCredentials: true })
      .then(r => setGradeStatus(r.data)).catch(() => {});
    axios.get(`${API}/users/grade-appeal`, { withCredentials: true })
      .then(r => setAppealResult(r.data.request)).catch(() => {});
    axios.get(`${API}/credits`, { withCredentials: true })
      .then(r => setCredits(r.data?.credits ?? user?.credits ?? 0)).catch(() => {});
  }, []);

  const handleCancelPlan = async () => {
    if (!window.confirm('Cancel your subscription? You will revert to the free plan at the end of the billing period.')) return;
    setCancelLoading(true);
    try {
      await axios.post(`${API}/subscription/cancel`, {}, { withCredentials: true });
      toast.success('Subscription cancelled. You will retain access until the billing period ends.');
      window.location.reload();
    } catch (e) {
      toast.error(e?.response?.data?.detail || 'Could not cancel subscription');
    }
    setCancelLoading(false);
  };

  const xp = user?.xp || 0;
  const level = Math.max(1, Math.floor(xp / 500) + 1);
  const xpInLevel = xp % 500;
  const canChange = gradeStatus?.can_change !== false;
  const daysRemaining = gradeStatus?.days_remaining || 0;

  const handleSaveClass = async () => {
    if (selectedClass === user?.class_level) return;
    setSaving(true); setErrorMsg('');
    try {
      const r = await axios.put(`${API}/users/grade`, { class_level: selectedClass }, { withCredentials: true });
      setUser(p => ({ ...p, class_level: selectedClass }));
      setGradeStatus({ class_level: selectedClass, last_grade_change_at: r.data.last_grade_change_at, can_change: false, days_remaining: 30 });
      setSaved(true);
      setTimeout(() => setSaved(false), 2500);
    } catch (e) {
      const detail = e?.response?.data?.detail;
      if (detail?.code === 'GRADE_CHANGE_COOLDOWN') {
        setGradeStatus({ class_level: detail.current_class_level, last_grade_change_at: detail.last_change_at, can_change: false, days_remaining: detail.days_remaining });
        setErrorMsg(detail.message);
      } else {
        setErrorMsg(typeof detail === 'string' ? detail : 'Could not change grade. Try again.');
      }
    }
    setSaving(false);
  };

  const submitAppeal = async () => {
    if (!appealForm.desired_class || appealForm.reason.trim().length < 10) return;
    setAppealSubmitting(true);
    try {
      const r = await axios.post(`${API}/users/grade-appeal`, appealForm, { withCredentials: true });
      setAppealResult(r.data.request);
      setAppealOpen(false);
      setAppealForm({ desired_class: '', reason: '' });
    } catch (e) {
      setErrorMsg(e?.response?.data?.detail || 'Could not submit appeal');
    }
    setAppealSubmitting(false);
  };

  const infoItems = [
    { label: 'Email', value: user?.email, icon: Mail, color: '#22d3ee' },
    { label: 'Member Since', value: user?.created_at ? new Date(user.created_at).toLocaleDateString('en-IN', { year: 'numeric', month: 'short', day: 'numeric' }) : 'Recently', icon: Clock, color: '#8b5cf6' },
    { label: 'Auth Type', value: user?.auth_type === 'google' ? 'Google' : 'Email & Password', icon: Shield, color: '#10b981' },
    { label: 'Role', value: user?.role === 'admin' ? 'Administrator' : 'Student', icon: Star, color: '#f59e0b' },
  ];

  return (
    <div className="p-4 sm:p-6 max-w-2xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl sm:text-3xl font-heading font-black text-white flex items-center gap-3">
          <User size={28} className="text-cyan-400" />
          Profile
        </h1>
        <p className="text-zinc-500 text-sm font-body mt-1">Your AceIt AI account</p>
      </div>

      {/* Avatar & Name */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
        className="glass rounded-2xl p-6 border border-white/10 text-center">
        <div className="w-20 h-20 rounded-full bg-gradient-to-br from-cyan-400 to-violet-600 flex items-center justify-center text-black font-heading font-black text-3xl mx-auto mb-3">
          {user?.name?.[0]?.toUpperCase() || 'S'}
        </div>
        <h2 className="text-white font-heading font-black text-xl">{user?.name}</h2>
        <p className="text-zinc-500 text-sm font-body mt-0.5">Class {user?.class_level} Student</p>

        {/* Level Badge */}
        <div className="inline-flex items-center gap-2 mt-3 px-4 py-2 rounded-full bg-amber-400/15 border border-amber-400/25">
          <Zap size={15} className="text-amber-400" />
          <span className="text-amber-400 font-heading font-bold">Level {level}</span>
          <span className="text-amber-600 text-xs font-body">•</span>
          <span className="text-amber-500 text-sm font-body">{xp} XP</span>
        </div>

        {/* XP Progress */}
        <div className="mt-4">
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-zinc-600 text-xs font-body">Level {level}</span>
            <span className="text-zinc-600 text-xs font-body">Level {level + 1}</span>
          </div>
          <div className="h-2 bg-zinc-800 rounded-full overflow-hidden">
            <motion.div className="h-full rounded-full" style={{ background: 'linear-gradient(90deg, #f59e0b, #d946ef)' }}
              initial={{ width: 0 }} animate={{ width: `${(xpInLevel / 500) * 100}%` }} transition={{ duration: 1, delay: 0.3 }} />
          </div>
          <p className="text-zinc-600 text-xs font-body text-center mt-1">{xp % 500} / 500 XP to next level</p>
        </div>
      </motion.div>

      {/* Quick stats */}
      <div className="grid grid-cols-2 gap-3">
        {[
          { label: 'Streak', value: `${user?.streak || 0} days`, icon: Flame, color: '#ef4444' },
          { label: 'Longest Streak', value: `${user?.longest_streak || 0} days`, icon: Trophy, color: '#f59e0b' },
        ].map(({ label, value, icon: Icon, color }, i) => (
          <motion.div key={label} initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: 0.15 + i * 0.05 }}
            className="glass-surface rounded-2xl p-4 border border-white/5">
            <div className="p-2 rounded-xl mb-2 inline-block" style={{ background: color + '20' }}>
              <Icon size={18} style={{ color }} />
            </div>
            <p className="text-xl font-heading font-bold text-white">{value}</p>
            <p className="text-zinc-500 text-xs font-body">{label}</p>
          </motion.div>
        ))}
      </div>

      {/* Academic Grade */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}
        className="glass-surface rounded-2xl p-5 border border-white/5" data-testid="grade-section">
        <h3 className="text-white font-heading font-bold mb-1 flex items-center gap-2">
          <BookOpen size={18} className="text-cyan-400" /> Academic Grade
        </h3>
        <p className="text-zinc-500 text-xs font-body mb-3">Your grade locks all syllabus, mock exams, and AI tutoring to your real class.</p>

        <div className="flex gap-2 flex-wrap mb-3">
          {CLASSES.map(cls => {
            const isCurrent = cls === user?.class_level;
            return (
              <button key={cls} onClick={() => canChange && setSelectedClass(cls)}
                disabled={!canChange}
                data-testid={`class-select-${cls}`}
                className={`w-10 h-10 rounded-xl text-sm font-heading font-bold transition-all ${selectedClass === cls
                  ? 'bg-cyan-500 text-black shadow-lg shadow-cyan-500/25'
                  : isCurrent
                    ? 'bg-amber-500/20 text-amber-300 border border-amber-400/40'
                    : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700 hover:text-white'} ${!canChange ? 'opacity-40 cursor-not-allowed' : ''}`}>
                {cls}
              </button>
            );
          })}
        </div>

        {!canChange ? (
          <div className="flex flex-wrap items-center gap-3" data-testid="grade-cooldown">
            <div className="flex items-center gap-2 px-3 py-2 rounded-xl bg-zinc-800/60 border border-amber-400/20 text-amber-300 text-xs font-body">
              <Lock size={12} />
              You can change your grade in <span className="font-bold">{daysRemaining} day{daysRemaining !== 1 ? 's' : ''}</span>
            </div>
            {appealResult?.status === 'pending' ? (
              <span className="px-3 py-2 rounded-xl bg-blue-500/15 border border-blue-400/30 text-blue-300 text-xs font-body font-semibold flex items-center gap-2">
                <Clock size={12} /> Appeal pending review
              </span>
            ) : (
              <button onClick={() => setAppealOpen(true)} data-testid="open-appeal-btn"
                className="px-3 py-2 rounded-xl bg-rose-500/15 border border-rose-400/30 text-rose-300 hover:bg-rose-500/25 text-xs font-body font-semibold transition-all">
                Request Early Grade Change
              </button>
            )}
          </div>
        ) : (
          <button onClick={handleSaveClass} disabled={saving || saved || selectedClass === user?.class_level} data-testid="save-class-btn"
            className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-heading font-bold transition-all ${saved ? 'bg-green-500/20 text-green-400 border border-green-500/30' : 'bg-cyan-500/15 text-cyan-400 border border-cyan-500/30 hover:bg-cyan-500/25'} disabled:opacity-40`}>
            {saving ? <div className="w-4 h-4 border-2 border-cyan-400/30 border-t-cyan-400 rounded-full animate-spin" /> : <Save size={15} />}
            {saved ? 'Saved!' : saving ? 'Saving...' : 'Save Grade'}
          </button>
        )}

        {errorMsg && (
          <p className="mt-3 text-rose-400 text-xs font-body flex items-center gap-1.5" data-testid="grade-error">
            <AlertTriangle size={12} /> {errorMsg}
          </p>
        )}
      </motion.div>

      {/* Appeal Modal */}
      <AnimatePresence>
        {appealOpen && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="fixed inset-0 z-[150] flex items-center justify-center p-4 bg-black/70 backdrop-blur-md"
            data-testid="appeal-modal">
            <motion.div initial={{ scale: 0.92, y: 12 }} animate={{ scale: 1, y: 0 }} exit={{ scale: 0.95 }}
              className="w-full max-w-md rounded-3xl glass border-2 border-rose-400/40 p-6 relative">
              <button onClick={() => setAppealOpen(false)} data-testid="close-appeal-btn"
                className="absolute top-3 right-3 p-1.5 rounded-full text-zinc-400 hover:text-white hover:bg-white/10 transition-all">
                <X size={16} />
              </button>
              <h3 className="text-white text-xl font-heading font-black mb-1">Request Early Grade Change</h3>
              <p className="text-zinc-400 text-sm font-body mb-4">Tell us why — our team reviews these within 48 hours.</p>

              <label className="block text-zinc-500 text-xs font-body uppercase tracking-wider mb-1">Desired class</label>
              <div className="flex flex-wrap gap-2 mb-3">
                {CLASSES.filter(c => c !== user?.class_level).map(c => (
                  <button key={c} data-testid={`appeal-class-${c}`}
                    onClick={() => setAppealForm(p => ({ ...p, desired_class: c }))}
                    className={`w-10 h-10 rounded-lg text-sm font-heading font-bold transition-all ${appealForm.desired_class === c ? 'bg-rose-500 text-white' : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700'}`}>
                    {c}
                  </button>
                ))}
              </div>

              <label className="block text-zinc-500 text-xs font-body uppercase tracking-wider mb-1">Reason</label>
              <textarea value={appealForm.reason} onChange={e => setAppealForm(p => ({ ...p, reason: e.target.value }))}
                rows={4} maxLength={400} data-testid="appeal-reason-input"
                placeholder="e.g. I selected the wrong class during signup..."
                className="w-full rounded-xl bg-zinc-900/60 border border-rose-400/20 px-3 py-2 text-white text-sm font-body focus:outline-none focus:border-rose-400/60 mb-1" />
              <p className="text-zinc-600 text-xs font-body mb-4">{appealForm.reason.length}/400 — minimum 10 characters</p>

              <button onClick={submitAppeal}
                disabled={!appealForm.desired_class || appealForm.reason.trim().length < 10 || appealSubmitting}
                data-testid="submit-appeal-btn"
                className="w-full py-2.5 rounded-xl bg-rose-500 hover:bg-rose-400 text-white font-heading font-bold text-sm flex items-center justify-center gap-2 transition-all disabled:opacity-40 disabled:cursor-not-allowed">
                {appealSubmitting ? <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : <><Send size={14} /> Submit Request</>}
              </button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Appeal Result Banner */}
      {appealResult && appealResult.status === 'pending' && (
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
          className="rounded-2xl p-4 border border-blue-400/30 bg-blue-500/10" data-testid="appeal-status-banner">
          <div className="flex items-start gap-3">
            <CheckCircle size={18} className="text-blue-400 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-blue-200 text-sm font-body font-semibold">Grade-change request submitted</p>
              <p className="text-blue-300/80 text-xs font-body mt-0.5">
                Requested: Class {appealResult.desired_class} • Status: <span className="font-bold uppercase">{appealResult.status}</span>
              </p>
            </div>
          </div>
        </motion.div>
      )}

      {/* Account Info */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.25 }}
        className="glass-surface rounded-2xl p-5 border border-white/5">
        <h3 className="text-white font-heading font-bold mb-4">Account Information</h3>
        <div className="space-y-3">
          {infoItems.map(({ label, value, icon: Icon, color }) => (
            <div key={label} className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0" style={{ background: color + '15' }}>
                <Icon size={15} style={{ color }} />
              </div>
              <div>
                <p className="text-zinc-500 text-xs font-body">{label}</p>
                <p className="text-white text-sm font-body">{value}</p>
              </div>
            </div>
          ))}
        </div>
      </motion.div>

      {/* ── Subscription Management ───────────────────────────────── */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}
        className="glass-surface rounded-2xl p-5 border border-white/5" data-testid="subscription-section">
        <h3 className="text-white font-heading font-bold mb-4 flex items-center gap-2">
          <CreditCard size={18} className="text-violet-400" /> Subscription & Credits
        </h3>

        {/* Current Plan */}
        <div className="flex items-center justify-between mb-4 p-4 rounded-xl border"
          style={{ borderColor: plan?.color ? plan.color + '30' : 'rgba(255,255,255,0.08)', background: plan?.color ? plan.color + '08' : 'rgba(255,255,255,0.02)' }}>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl flex items-center justify-center"
              style={{ background: plan?.color ? plan.color + '20' : 'rgba(255,255,255,0.08)' }}>
              <Package size={18} style={{ color: plan?.color || '#94a3b8' }} />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <p className="text-white font-heading font-bold text-base capitalize">
                  {plan?.name || plan?.plan_id || 'Free'} Plan
                </p>
                {plan?.plan_id && plan.plan_id !== 'free' && (
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-heading font-bold bg-green-500/20 text-green-400 border border-green-500/20">ACTIVE</span>
                )}
              </div>
              <p className="text-zinc-500 text-xs font-body mt-0.5">
                {plan?.plan_id === 'free' ? 'Limited features — upgrade to unlock more' : plan?.tagline || 'Full access'}
              </p>
            </div>
          </div>
          {plan?.plan_id && plan.plan_id !== 'free' && plan?.price_monthly > 0 && (
            <p className="text-white font-heading font-bold text-sm">₹{plan.price_monthly}<span className="text-zinc-500 font-body text-xs">/mo</span></p>
          )}
        </div>

        {/* Credits */}
        <div className="flex items-center gap-3 mb-4 p-3 rounded-xl bg-amber-500/8 border border-amber-500/15">
          <Zap size={16} className="text-amber-400" />
          <div className="flex-1">
            <p className="text-white text-sm font-body font-semibold">{credits} credits remaining</p>
            <p className="text-zinc-500 text-xs font-body">Credits are used for AI tutoring (2–10 per response)</p>
          </div>
        </div>

        {/* Renewal / billing info */}
        {plan?.renewal_date && (
          <div className="flex items-center gap-2 mb-4 text-xs font-body text-zinc-400">
            <Calendar size={13} />
            <span>Renews on <strong className="text-zinc-200">{new Date(plan.renewal_date).toLocaleDateString('en-IN', { year: 'numeric', month: 'long', day: 'numeric' })}</strong></span>
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-3 flex-wrap">
          {plan?.plan_id === 'free' || !plan?.plan_id ? (
            <button onClick={() => nav('/pricing')}
              data-testid="upgrade-plan-btn"
              className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-violet-500 hover:bg-violet-400 text-white font-heading font-bold text-sm transition-all">
              <Crown size={15} /> Upgrade Plan <ArrowRight size={14} />
            </button>
          ) : (
            <>
              <button onClick={() => nav('/pricing')}
                className="flex items-center gap-2 px-4 py-2.5 rounded-xl border border-violet-500/30 bg-violet-500/10 hover:bg-violet-500/20 text-violet-300 font-heading font-bold text-sm transition-all">
                <TrendingUp size={15} /> Change Plan
              </button>
              <button onClick={handleCancelPlan} disabled={cancelLoading}
                data-testid="cancel-plan-btn"
                className="flex items-center gap-2 px-4 py-2.5 rounded-xl border border-red-500/20 bg-red-500/8 hover:bg-red-500/15 text-red-400 font-heading font-bold text-sm transition-all disabled:opacity-50">
                {cancelLoading ? <div className="w-4 h-4 border-2 border-red-400/30 border-t-red-400 rounded-full animate-spin" /> : <LogOut size={14} />}
                Cancel Plan
              </button>
            </>
          )}
        </div>
      </motion.div>
    </div>
  );
}
