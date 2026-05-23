import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CalendarDays, Target, Clock, Zap, BookOpen, ChevronDown, Sparkles, Check, ChevronRight, Award, Users } from 'lucide-react';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const SUBJECTS = ['Mathematics', 'Physics', 'Chemistry', 'Biology', 'English', 'Social Science', 'Computer Science', 'Science'];

export default function StudyPlanPage() {
  const { user } = useAuth();
  const [existingPlan, setExistingPlan] = useState(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [form, setForm] = useState({
    exam_date: '', target_score: 90, daily_hours: 2,
    class_level: user?.class_level || '10', subjects: []
  });
  const [phase, setPhase] = useState('setup');
  const [referralCode, setReferralCode] = useState(null);
  const [referralInput, setReferralInput] = useState('');
  const [referralMsg, setReferralMsg] = useState('');

  useEffect(() => {
    Promise.all([
      axios.get(`${API}/study-plan`, { withCredentials: true }),
      axios.get(`${API}/referral/code`, { withCredentials: true })
    ]).then(([planRes, refRes]) => {
      if (planRes.data.plan) { setExistingPlan(planRes.data); setPhase('plan'); }
      setReferralCode(refRes.data);
    }).catch(() => {}).finally(() => setLoading(false));
  }, []);

  const toggleSubject = (subj) => {
    setForm(p => ({
      ...p,
      subjects: p.subjects.includes(subj) ? p.subjects.filter(s => s !== subj) : [...p.subjects, subj]
    }));
  };

  const generate = async () => {
    if (!form.exam_date) return;
    setGenerating(true);
    try {
      const { data } = await axios.post(`${API}/study-plan`, form, { withCredentials: true });
      setExistingPlan(data);
      setPhase('plan');
    } catch (e) { console.error(e); }
    setGenerating(false);
  };

  const applyReferral = async () => {
    try {
      const { data } = await axios.post(`${API}/referral/apply`, { code: referralInput }, { withCredentials: true });
      setReferralMsg(`✓ ${data.message}`);
      setReferralCode(p => ({ ...p, referral_count: (p?.referral_count || 0) + 1 }));
    } catch (e) {
      setReferralMsg(e.response?.data?.detail || 'Error applying code');
    }
  };

  const minDate = new Date(); minDate.setDate(minDate.getDate() + 1);
  const minDateStr = minDate.toISOString().split('T')[0];

  if (loading) return (
    <div className="p-6 space-y-4">
      {[...Array(3)].map((_, i) => <div key={i} className="h-24 rounded-2xl shimmer bg-zinc-900" />)}
    </div>
  );

  const plan = existingPlan?.plan;
  const daysLeft = existingPlan?.days_remaining ?? existingPlan?.days_until_exam;

  return (
    <div className="p-4 sm:p-6 max-w-3xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl sm:text-3xl font-heading font-black text-white flex items-center gap-3">
          <CalendarDays size={28} className="text-violet-400" /> Study Plan
        </h1>
        <p className="text-zinc-500 text-sm font-body mt-1">AI-generated personalized exam preparation</p>
      </div>

      {/* Exam countdown banner */}
      {phase === 'plan' && daysLeft !== undefined && (
        <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}
          className="p-4 rounded-2xl border flex items-center gap-4"
          style={{ background: daysLeft <= 14 ? 'rgba(239,68,68,0.06)' : 'rgba(34,211,238,0.06)', borderColor: daysLeft <= 14 ? 'rgba(239,68,68,0.2)' : 'rgba(34,211,238,0.2)' }}>
          <div className="text-center flex-shrink-0">
            <p className="text-4xl font-heading font-black" style={{ color: daysLeft <= 14 ? '#ef4444' : '#22d3ee' }}>{daysLeft}</p>
            <p className="text-zinc-500 text-xs font-body">days left</p>
          </div>
          <div>
            <p className="text-white font-heading font-bold">Exam Countdown</p>
            <p className="text-zinc-500 text-sm font-body">Target: {existingPlan?.target_score}% • {existingPlan?.daily_hours}h/day plan</p>
          </div>
          <button onClick={() => setPhase('setup')}
            className="ml-auto px-3 py-1.5 rounded-xl border border-white/10 text-zinc-400 text-xs font-body hover:text-white hover:border-white/20 transition-all flex-shrink-0">
            Edit Plan
          </button>
        </motion.div>
      )}

      <AnimatePresence mode="wait">
        {phase === 'setup' && (
          <motion.div key="setup" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="glass rounded-2xl p-5 border border-white/10 space-y-4">
            <h2 className="text-white font-heading font-bold">Create Your Study Plan</h2>

            <div className="grid sm:grid-cols-2 gap-3">
              <div>
                <label className="text-zinc-500 text-xs font-body mb-1.5 block">Exam Date</label>
                <input type="date" min={minDateStr} value={form.exam_date}
                  onChange={e => setForm(p => ({ ...p, exam_date: e.target.value }))}
                  data-testid="exam-date-input"
                  className="w-full bg-zinc-900 border border-white/10 rounded-xl px-4 py-3 text-white text-sm font-body focus:outline-none focus:border-violet-500/50 [color-scheme:dark]" />
              </div>
              <div>
                <label className="text-zinc-500 text-xs font-body mb-1.5 block">Target Score</label>
                <div className="flex gap-2">
                  {[70, 80, 90, 95].map(s => (
                    <button key={s} onClick={() => setForm(p => ({ ...p, target_score: s }))} data-testid={`target-${s}`}
                      className={`flex-1 py-3 rounded-xl text-sm font-heading font-bold transition-all ${form.target_score === s ? 'bg-violet-500/20 text-violet-400 border border-violet-500/40' : 'bg-zinc-900 text-zinc-500 border border-white/10 hover:text-zinc-300'}`}>
                      {s}%
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <div>
              <label className="text-zinc-500 text-xs font-body mb-1.5 block">Daily Study Hours: <span className="text-white">{form.daily_hours}h</span></label>
              <input type="range" min="0.5" max="6" step="0.5" value={form.daily_hours}
                onChange={e => setForm(p => ({ ...p, daily_hours: +e.target.value }))}
                className="w-full accent-violet-500" />
              <div className="flex justify-between text-zinc-700 text-xs font-body mt-1">
                <span>0.5h</span><span>3h</span><span>6h</span>
              </div>
            </div>

            <div>
              <label className="text-zinc-500 text-xs font-body mb-2 block">Subjects to Focus On</label>
              <div className="flex flex-wrap gap-2">
                {SUBJECTS.map(s => (
                  <button key={s} onClick={() => toggleSubject(s)} data-testid={`subject-toggle-${s}`}
                    className={`px-3 py-1.5 rounded-full text-xs font-body border transition-all ${form.subjects.includes(s) ? 'bg-violet-500/20 text-violet-400 border-violet-500/40' : 'bg-zinc-900/50 text-zinc-500 border-white/10 hover:text-zinc-300 hover:border-white/20'}`}>
                    {form.subjects.includes(s) && <span className="mr-1">✓</span>}{s}
                  </button>
                ))}
              </div>
            </div>

            <button onClick={generate} disabled={!form.exam_date || generating} data-testid="generate-plan-btn"
              className="w-full py-3 rounded-xl bg-violet-500 hover:bg-violet-400 disabled:opacity-40 text-white font-heading font-bold flex items-center justify-center gap-2 transition-all">
              {generating ? <><div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />Generating your plan...</> : <><Sparkles size={16} /> Generate AI Study Plan</>}
            </button>
          </motion.div>
        )}

        {phase === 'plan' && plan && (
          <motion.div key="plan" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="space-y-4">
            {/* Overview */}
            <div className="glass rounded-2xl p-4 border border-violet-500/15" style={{ background: 'rgba(139,92,246,0.04)' }}>
              <div className="flex items-center gap-2 mb-2">
                <Sparkles size={16} className="text-violet-400" />
                <p className="text-violet-400 text-sm font-body font-semibold">AI Strategy</p>
              </div>
              <p className="text-zinc-300 text-sm font-body leading-relaxed">{plan.overview}</p>
            </div>

            {/* Tips */}
            {plan.tips?.length > 0 && (
              <div className="grid sm:grid-cols-3 gap-3">
                {plan.tips.slice(0, 3).map((tip, i) => (
                  <div key={i} className="glass-surface rounded-xl p-3 border border-white/5">
                    <div className="w-6 h-6 rounded-full bg-violet-500/20 flex items-center justify-center mb-2">
                      <Check size={12} className="text-violet-400" />
                    </div>
                    <p className="text-zinc-300 text-xs font-body leading-relaxed">{tip}</p>
                  </div>
                ))}
              </div>
            )}

            {/* Weekly plan */}
            <div className="space-y-3">
              <h3 className="text-white font-heading font-bold">Week-by-Week Plan</h3>
              {plan.weeks?.slice(0, 4).map((week, i) => (
                <motion.div key={i} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.08 }}
                  className="glass-surface rounded-2xl border border-white/5 overflow-hidden">
                  <div className="flex items-center justify-between p-4 cursor-pointer">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-lg bg-violet-500/20 flex items-center justify-center text-violet-400 font-heading font-bold text-sm">{i + 1}</div>
                      <div>
                        <p className="text-white font-body font-semibold text-sm">Week {week.week}: {week.theme}</p>
                        <p className="text-zinc-600 text-xs font-body">{week.goal}</p>
                      </div>
                    </div>
                  </div>
                  <div className="px-4 pb-3 flex flex-wrap gap-1.5">
                    {week.focus?.slice(0, 4).map(f => (
                      <span key={f} className="px-2.5 py-1 rounded-full text-xs font-body bg-violet-500/10 text-violet-300 border border-violet-500/20">{f}</span>
                    ))}
                  </div>
                </motion.div>
              ))}
            </div>

            {/* Exam week */}
            {plan.exam_week && (
              <div className="p-4 rounded-2xl border border-red-500/20 bg-red-500/5">
                <p className="text-red-400 font-body font-semibold text-sm mb-1">Exam Week Strategy</p>
                <p className="text-zinc-300 text-sm font-body">{plan.exam_week}</p>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Referral Section */}
      {referralCode && (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}
          className="glass-surface rounded-2xl p-5 border border-white/5">
          <div className="flex items-center gap-2 mb-4">
            <Users size={18} className="text-fuchsia-400" />
            <h3 className="text-white font-heading font-bold">Invite Friends & Earn XP</h3>
          </div>
          <div className="grid sm:grid-cols-2 gap-4">
            <div>
              <p className="text-zinc-500 text-xs font-body mb-2">Your referral code</p>
              <div className="flex items-center gap-2">
                <div className="flex-1 bg-zinc-900 border border-fuchsia-500/20 rounded-xl px-4 py-2.5 text-fuchsia-400 font-heading font-black text-lg tracking-widest text-center">
                  {referralCode.code}
                </div>
                <button onClick={() => { navigator.clipboard.writeText(referralCode.code); }}
                  className="p-2.5 rounded-xl bg-fuchsia-500/15 text-fuchsia-400 hover:bg-fuchsia-500/25 transition-all border border-fuchsia-500/20">
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><rect width="14" height="14" x="8" y="8" rx="2"/><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/></svg>
                </button>
              </div>
              <p className="text-zinc-600 text-xs font-body mt-1.5">{referralCode.referral_count} friends referred • +{referralCode.xp_per_referral} XP each</p>
            </div>
            <div>
              <p className="text-zinc-500 text-xs font-body mb-2">Apply a friend's code</p>
              <div className="flex gap-2">
                <input value={referralInput} onChange={e => setReferralInput(e.target.value.toUpperCase())}
                  placeholder="ENTER CODE" maxLength={8} data-testid="referral-input"
                  className="flex-1 bg-zinc-900 border border-white/10 rounded-xl px-3 py-2.5 text-white text-sm font-heading font-bold tracking-widest uppercase focus:outline-none focus:border-fuchsia-500/50 placeholder-zinc-700" />
                <button onClick={applyReferral} disabled={!referralInput.trim()} data-testid="apply-referral-btn"
                  className="px-4 py-2.5 rounded-xl bg-fuchsia-500/20 text-fuchsia-400 border border-fuchsia-500/30 hover:bg-fuchsia-500/30 disabled:opacity-40 text-sm font-heading font-bold transition-all">
                  Apply
                </button>
              </div>
              {referralMsg && <p className={`text-xs font-body mt-1.5 ${referralMsg.startsWith('✓') ? 'text-green-400' : 'text-red-400'}`}>{referralMsg}</p>}
              <p className="text-zinc-600 text-xs font-body mt-1">You get +{referralCode.referred_xp} XP when you apply one</p>
            </div>
          </div>
        </motion.div>
      )}
    </div>
  );
}
