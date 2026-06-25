import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  CalendarDays, Target, Clock, Zap, BookOpen, ChevronDown, Sparkles,
  Check, ChevronRight, Award, Users, Lock, ArrowRight, Brain, TrendingUp,
  TrendingDown, AlertTriangle, BarChart3, RefreshCw, CheckCircle2, Sun, Sunset, Moon, Shuffle
} from 'lucide-react';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';
import { useSubscription } from '../contexts/SubscriptionContext';
import { useNavigate } from 'react-router-dom';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const SUBJECTS = ['Mathematics', 'Physics', 'Chemistry', 'Biology', 'English', 'Social Science', 'Computer Science', 'Science'];
const DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
const SESSION_OPTS = [
  { value: 'morning',   label: 'Morning',   icon: Sun,     desc: '6am–12pm' },
  { value: 'afternoon', label: 'Afternoon', icon: Sunset,  desc: '12pm–6pm' },
  { value: 'evening',   label: 'Evening',   icon: Moon,    desc: '6pm–10pm' },
  { value: 'flexible',  label: 'Flexible',  icon: Shuffle, desc: 'Any time' },
];
const TYPE_COLORS = { learn: '#22d3ee', revise: '#8b5cf6', practice: '#f59e0b', test: '#ef4444' };

export default function StudyPlanPage() {
  const { user } = useAuth();
  const { plan }  = useSubscription();
  const nav       = useNavigate();
  const isFree    = !plan || plan.plan_id === 'free';

  const [existingPlan, setExistingPlan] = useState(null);
  const [context, setContext]           = useState(null);
  const [ctxLoading, setCtxLoading]     = useState(true);
  const [loading, setLoading]           = useState(true);
  const [generating, setGenerating]     = useState(false);
  const [phase, setPhase]               = useState('setup');
  const [referralCode, setReferralCode] = useState(null);
  const [referralInput, setReferralInput] = useState('');
  const [referralMsg, setReferralMsg]   = useState('');

  const [form, setForm] = useState({
    exam_date: '', target_score: 90, daily_hours: 2,
    class_level: user?.class_level || '10', subjects: [],
    available_days: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'],
    session_preference: 'flexible',
  });

  useEffect(() => {
    Promise.all([
      axios.get(`${API}/study-plan`, { withCredentials: true }),
      axios.get(`${API}/referral/code`, { withCredentials: true }),
    ]).then(([planRes, refRes]) => {
      if (planRes.data.plan) { setExistingPlan(planRes.data); setPhase('plan'); }
      setReferralCode(refRes.data);
    }).catch((e) => { console.warn('Study plan fetch failed:', e); }).finally(() => setLoading(false));

    // Load learning context (quiz history + weak areas)
    axios.get(`${API}/study-plan/context`, { withCredentials: true })
      .then(r => setContext(r.data))
      .catch(() => setContext(null))
      .finally(() => setCtxLoading(false));
  }, []);

  const toggleSubject = (s) =>
    setForm(p => ({ ...p, subjects: p.subjects.includes(s) ? p.subjects.filter(x => x !== s) : [...p.subjects, s] }));
  const toggleDay = (d) =>
    setForm(p => ({ ...p, available_days: p.available_days.includes(d) ? p.available_days.filter(x => x !== d) : [...p.available_days, d] }));

  const generate = async () => {
    if (!form.exam_date) return;
    setGenerating(true);
    try {
      const { data } = await axios.post(`${API}/study-plan`, form, { withCredentials: true });
      setExistingPlan(data);
      setPhase('plan');
    } catch (e) {
      const msg = e.response?.data?.detail || 'Generation failed';
      alert(typeof msg === 'string' ? msg : JSON.stringify(msg));
    }
    setGenerating(false);
  };

  const applyReferral = async () => {
    try {
      const { data } = await axios.post(`${API}/referral/apply`, { code: referralInput }, { withCredentials: true });
      setReferralMsg(`✓ ${data.message}`);
    } catch (e) { setReferralMsg(e.response?.data?.detail || 'Error applying code'); }
  };

  const minDate = new Date(); minDate.setDate(minDate.getDate() + 1);
  const minDateStr = minDate.toISOString().split('T')[0];

  // ── Free gate ───────────────────────────────────────────────────────────────
  if (!loading && isFree) return (
    <div className="p-4 sm:p-6 max-w-3xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl sm:text-3xl font-heading font-black text-white flex items-center gap-3">
          <CalendarDays size={28} className="text-violet-400" /> Study Plan
        </h1>
      </div>
      <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}
        className="rounded-2xl border border-violet-500/20 p-10 text-center"
        style={{ background: 'rgba(139,92,246,0.05)' }}>
        <div className="w-16 h-16 rounded-full bg-violet-500/15 border border-violet-500/20 flex items-center justify-center mx-auto mb-5">
          <Lock size={28} className="text-violet-400" />
        </div>
        <h2 className="text-white text-xl font-heading font-bold mb-2">Study Plans are a Pro Feature</h2>
        <p className="text-zinc-400 text-sm font-body mb-6 max-w-sm mx-auto">
          Upgrade your plan to access personalised AI Study Plans built around your quiz history and weak areas.
        </p>
        <button onClick={() => nav('/pricing')}
          className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-violet-500 hover:bg-violet-400 text-white font-heading font-bold text-sm transition-all">
          Upgrade to Pro <ArrowRight size={16} />
        </button>
      </motion.div>
    </div>
  );

  if (loading) return (
    <div className="p-6 space-y-4">
      {[...Array(3)].map((_, i) => <div key={i} className="h-24 rounded-2xl shimmer bg-zinc-900" />)}
    </div>
  );

  const studyPlan  = existingPlan?.plan;
  const daysLeft   = existingPlan?.days_remaining ?? existingPlan?.days_until_exam;
  const ctxUsed    = existingPlan?.context_used;

  return (
    <div className="p-4 sm:p-6 max-w-3xl mx-auto space-y-6" data-testid="study-plan-page">
      <div>
        <h1 className="text-2xl sm:text-3xl font-heading font-black text-white flex items-center gap-3">
          <CalendarDays size={28} className="text-violet-400" /> Study Plan
        </h1>
        <p className="text-zinc-500 text-sm font-body mt-1">AI-generated, personalised from your learning history</p>
      </div>

      {/* Exam countdown */}
      {phase === 'plan' && daysLeft !== undefined && (
        <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}
          className="p-4 rounded-2xl border flex items-center gap-4"
          style={{ background: daysLeft <= 14 ? 'rgba(239,68,68,0.06)' : 'rgba(34,211,238,0.06)', borderColor: daysLeft <= 14 ? 'rgba(239,68,68,0.2)' : 'rgba(34,211,238,0.2)' }}>
          <div className="text-center flex-shrink-0">
            <p className="text-4xl font-heading font-black" style={{ color: daysLeft <= 14 ? '#ef4444' : '#22d3ee' }}>{daysLeft}</p>
            <p className="text-zinc-500 text-xs font-body">days left</p>
          </div>
          <div className="flex-1">
            <p className="text-white font-heading font-bold">Exam Countdown</p>
            <p className="text-zinc-500 text-sm font-body">Target: {existingPlan?.target_score}% • {existingPlan?.daily_hours}h/day</p>
            {ctxUsed?.personalised && (
              <p className="text-violet-400 text-xs font-body mt-1 flex items-center gap-1">
                <Brain size={11} /> Personalised from {ctxUsed.quiz_count} quiz{ctxUsed.quiz_count !== 1 ? 'zes' : ''} + {ctxUsed.exam_count} exam{ctxUsed.exam_count !== 1 ? 's' : ''}
              </p>
            )}
          </div>
          <button onClick={() => setPhase('setup')}
            className="px-3 py-1.5 rounded-xl border border-white/10 text-zinc-400 text-xs font-body hover:text-white hover:border-white/20 transition-all flex-shrink-0">
            Edit Plan
          </button>
        </motion.div>
      )}

      <AnimatePresence mode="wait">

        {/* ── SETUP FORM ──────────────────────────────────────── */}
        {phase === 'setup' && (
          <motion.div key="setup" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="space-y-4">

            {/* Learning data context preview */}
            {ctxLoading ? (
              <div className="h-16 rounded-2xl shimmer bg-zinc-900" />
            ) : context ? (
              <motion.div initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }}
                className="rounded-2xl border p-4" data-testid="learning-context-preview"
                style={{ background: 'rgba(139,92,246,0.05)', borderColor: 'rgba(139,92,246,0.2)' }}>
                <div className="flex items-center gap-2 mb-3">
                  <Brain size={15} className="text-violet-400" />
                  <p className="text-violet-300 text-sm font-body font-semibold">Learning Data Detected</p>
                  {context.has_history && (
                    <span className="ml-auto text-[10px] px-2 py-0.5 rounded-full font-heading font-bold bg-violet-500/20 text-violet-300 border border-violet-500/25">PERSONALISED</span>
                  )}
                </div>
                <div className="grid grid-cols-3 gap-3 mb-3">
                  <div className="text-center">
                    <p className="text-xl font-heading font-bold text-white">{context.quiz_count}</p>
                    <p className="text-zinc-600 text-xs font-body">Quizzes</p>
                  </div>
                  <div className="text-center">
                    <p className="text-xl font-heading font-bold text-white">{context.exam_count}</p>
                    <p className="text-zinc-600 text-xs font-body">Mock Exams</p>
                  </div>
                  <div className="text-center">
                    <p className="text-xl font-heading font-bold" style={{ color: '#ef4444' }}>{context.weak_topics?.length || 0}</p>
                    <p className="text-zinc-600 text-xs font-body">Weak Topics</p>
                  </div>
                </div>
                {context.weak_topics?.length > 0 && (
                  <div>
                    <p className="text-zinc-500 text-xs font-body mb-1.5 flex items-center gap-1">
                      <TrendingDown size={11} className="text-red-400" /> Will be prioritised in your plan:
                    </p>
                    <div className="flex flex-wrap gap-1.5">
                      {context.weak_topics.slice(0, 6).map(t => (
                        <span key={t.topic} className="px-2 py-0.5 rounded-full text-xs font-body border border-red-500/20 text-red-300"
                          style={{ background: 'rgba(239,68,68,0.07)' }}>
                          {t.topic}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                {context.strong_topics?.length > 0 && (
                  <div className="mt-2">
                    <p className="text-zinc-500 text-xs font-body mb-1.5 flex items-center gap-1">
                      <TrendingUp size={11} className="text-green-400" /> Strong topics (light revision only):
                    </p>
                    <div className="flex flex-wrap gap-1.5">
                      {context.strong_topics.slice(0, 4).map(t => (
                        <span key={t} className="px-2 py-0.5 rounded-full text-xs font-body border border-green-500/20 text-green-300"
                          style={{ background: 'rgba(16,185,129,0.07)' }}>
                          {t}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                {!context.has_history && (
                  <p className="text-zinc-500 text-xs font-body">No quiz or exam history yet — a balanced plan will be generated. Take quizzes to get a personalised plan next time!</p>
                )}
              </motion.div>
            ) : null}

            <div className="glass rounded-2xl p-5 border border-white/10 space-y-4">
              <h2 className="text-white font-heading font-bold">Plan Configuration</h2>

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

              {/* Daily hours */}
              <div>
                <label className="text-zinc-500 text-xs font-body mb-1.5 block">
                  Daily Study Hours: <span className="text-white">{form.daily_hours}h</span>
                </label>
                <input type="range" min="0.5" max="6" step="0.5" value={form.daily_hours}
                  onChange={e => setForm(p => ({ ...p, daily_hours: +e.target.value }))}
                  className="w-full accent-violet-500" />
                <div className="flex justify-between text-zinc-700 text-xs font-body mt-1">
                  <span>0.5h</span><span>3h</span><span>6h</span>
                </div>
              </div>

              {/* Available days */}
              <div>
                <label className="text-zinc-500 text-xs font-body mb-2 block">Available Days</label>
                <div className="flex gap-2 flex-wrap" data-testid="available-days-picker">
                  {DAYS.map(d => (
                    <button key={d} onClick={() => toggleDay(d)}
                      data-testid={`day-toggle-${d}`}
                      className={`px-3 py-1.5 rounded-xl text-xs font-heading font-bold transition-all border ${form.available_days.includes(d) ? 'bg-cyan-500/20 text-cyan-400 border-cyan-500/40' : 'bg-zinc-900 text-zinc-600 border-white/10 hover:text-zinc-400'}`}>
                      {d}
                    </button>
                  ))}
                </div>
              </div>

              {/* Session preference */}
              <div>
                <label className="text-zinc-500 text-xs font-body mb-2 block">Study Session Preference</label>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2" data-testid="session-preference-picker">
                  {SESSION_OPTS.map(({ value, label, icon: Icon, desc }) => (
                    <button key={value} onClick={() => setForm(p => ({ ...p, session_preference: value }))}
                      data-testid={`session-${value}`}
                      className={`p-3 rounded-xl border text-left transition-all ${form.session_preference === value ? 'border-cyan-500/40 bg-cyan-500/10' : 'border-white/10 bg-zinc-900/50 hover:border-white/20'}`}>
                      <Icon size={15} className={form.session_preference === value ? 'text-cyan-400 mb-1' : 'text-zinc-600 mb-1'} />
                      <p className={`text-xs font-body font-semibold ${form.session_preference === value ? 'text-white' : 'text-zinc-400'}`}>{label}</p>
                      <p className="text-zinc-600 text-[10px] font-body">{desc}</p>
                    </button>
                  ))}
                </div>
              </div>

              {/* Subjects */}
              <div>
                <label className="text-zinc-500 text-xs font-body mb-2 block">Subjects to Focus On</label>
                <div className="flex flex-wrap gap-2">
                  {SUBJECTS.map(s => (
                    <button key={s} onClick={() => toggleSubject(s)} data-testid={`subject-toggle-${s}`}
                      className={`px-3 py-1.5 rounded-full text-xs font-body border transition-all ${form.subjects.includes(s) ? 'bg-violet-500/20 text-violet-400 border-violet-500/40' : 'bg-zinc-900/50 text-zinc-500 border-white/10 hover:text-zinc-300 hover:border-white/20'}`}>
                      {form.subjects.includes(s) && '✓ '}{s}
                    </button>
                  ))}
                </div>
              </div>

              <button onClick={generate} disabled={!form.exam_date || generating || form.available_days.length === 0}
                data-testid="generate-plan-btn"
                className="w-full py-3 rounded-xl bg-violet-500 hover:bg-violet-400 disabled:opacity-40 text-white font-heading font-bold flex items-center justify-center gap-2 transition-all">
                {generating
                  ? <><div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />Generating personalised plan…</>
                  : <><Sparkles size={16} /> Generate{context?.has_history ? ' Personalised' : ''} Study Plan</>}
              </button>
            </div>
          </motion.div>
        )}

        {/* ── PLAN VIEW ───────────────────────────────────────── */}
        {phase === 'plan' && studyPlan && (
          <motion.div key="plan" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="space-y-4">

            {/* Personalisation badge */}
            {ctxUsed?.personalised && (
              <motion.div initial={{ opacity: 0, y: -6 }} animate={{ opacity: 1, y: 0 }}
                className="flex items-center gap-2 px-4 py-2.5 rounded-xl border border-violet-500/20"
                style={{ background: 'rgba(139,92,246,0.06)' }} data-testid="personalisation-badge">
                <Brain size={15} className="text-violet-400 flex-shrink-0" />
                <p className="text-violet-300 text-xs font-body">
                  Personalised using <strong>{ctxUsed.quiz_count} quiz{ctxUsed.quiz_count !== 1 ? 'zes' : ''}</strong> + <strong>{ctxUsed.exam_count} mock exam{ctxUsed.exam_count !== 1 ? 's' : ''}</strong>
                  {ctxUsed.weak_topics?.length > 0 && <> · focusing on: <span className="text-red-300">{ctxUsed.weak_topics.slice(0, 3).join(', ')}</span></>}
                </p>
              </motion.div>
            )}

            {/* AI Overview */}
            <div className="glass rounded-2xl p-4 border border-violet-500/15" style={{ background: 'rgba(139,92,246,0.04)' }}>
              <div className="flex items-center gap-2 mb-2">
                <Sparkles size={16} className="text-violet-400" />
                <p className="text-violet-400 text-sm font-body font-semibold">AI Strategy</p>
              </div>
              <p className="text-zinc-300 text-sm font-body leading-relaxed">{studyPlan.overview}</p>
            </div>

            {/* Weak area strategy */}
            {studyPlan.weak_area_strategy && (
              <div className="p-4 rounded-2xl border border-red-500/15 bg-red-500/5" data-testid="weak-area-strategy">
                <p className="text-red-400 font-body font-semibold text-sm mb-1 flex items-center gap-1.5">
                  <AlertTriangle size={14} /> Weak Area Strategy
                </p>
                <p className="text-zinc-300 text-sm font-body leading-relaxed">{studyPlan.weak_area_strategy}</p>
              </div>
            )}

            {/* Tips */}
            {studyPlan.tips?.length > 0 && (
              <div className="grid sm:grid-cols-3 gap-3">
                {studyPlan.tips.slice(0, 3).map((tip, i) => (
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
              {studyPlan.weeks?.map((week, i) => (
                <motion.div key={week.week || i} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.07 }}
                  className="glass-surface rounded-2xl border border-white/5 overflow-hidden">
                  <div className="flex items-center gap-3 p-4">
                    <div className="w-9 h-9 rounded-xl bg-violet-500/20 flex items-center justify-center text-violet-400 font-heading font-bold text-sm flex-shrink-0">
                      W{week.week}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-white font-body font-semibold text-sm">{week.theme}</p>
                      <p className="text-zinc-600 text-xs font-body truncate">{week.goal}</p>
                    </div>
                  </div>
                  {/* Focus topics */}
                  <div className="px-4 pb-2 flex flex-wrap gap-1.5">
                    {week.focus?.slice(0, 5).map(f => (
                      <span key={f} className="px-2.5 py-1 rounded-full text-xs font-body bg-violet-500/10 text-violet-300 border border-violet-500/20">{f}</span>
                    ))}
                  </div>
                  {/* Daily tasks */}
                  {week.daily_tasks?.length > 0 && (
                    <div className="px-4 pb-4 space-y-1.5">
                      <p className="text-zinc-600 text-[10px] font-body uppercase tracking-wider mb-2">Daily Tasks</p>
                      {week.daily_tasks.slice(0, 5).map((task, j) => (
                        <div key={`${task.day}-${j}`} className="flex items-center gap-2.5 p-2 rounded-lg bg-zinc-900/50">
                          <span className="text-zinc-500 text-xs font-heading font-bold w-8 flex-shrink-0">{task.day}</span>
                          <span className="px-2 py-0.5 rounded text-[10px] font-heading font-bold capitalize"
                            style={{ background: (TYPE_COLORS[task.type] || '#94a3b8') + '20', color: TYPE_COLORS[task.type] || '#94a3b8' }}>
                            {task.type}
                          </span>
                          <span className="text-zinc-300 text-xs font-body flex-1 truncate">{task.subject}: {task.topic}</span>
                          <span className="text-zinc-600 text-xs font-body flex-shrink-0">{task.hours}h</span>
                        </div>
                      ))}
                    </div>
                  )}
                </motion.div>
              ))}
            </div>

            {/* Exam week */}
            {studyPlan.exam_week && (
              <div className="p-4 rounded-2xl border border-amber-500/20 bg-amber-500/5">
                <p className="text-amber-400 font-body font-semibold text-sm mb-1 flex items-center gap-1.5">
                  <Award size={14} /> Exam Week Strategy
                </p>
                <p className="text-zinc-300 text-sm font-body leading-relaxed">{studyPlan.exam_week}</p>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Referral */}
      {referralCode && (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}
          className="glass-surface rounded-2xl p-5 border border-white/5">
          <div className="flex items-center gap-2 mb-4">
            <Users size={18} className="text-fuchsia-400" />
            <h3 className="text-white font-heading font-bold">Invite Friends &amp; Earn XP</h3>
          </div>
          <div className="grid sm:grid-cols-2 gap-4">
            <div>
              <p className="text-zinc-500 text-xs font-body mb-2">Your referral code</p>
              <div className="flex items-center gap-2">
                <div className="flex-1 bg-zinc-900 border border-fuchsia-500/20 rounded-xl px-4 py-2.5 text-fuchsia-400 font-heading font-black text-lg tracking-widest text-center">
                  {referralCode.code}
                </div>
                <button onClick={() => navigator.clipboard.writeText(referralCode.code)}
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
