import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Sparkles, GraduationCap, Target, AlertTriangle, Palette, ArrowRight, Check } from 'lucide-react';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const CLASSES = ['6', '7', '8', '9', '10', '11', '12'];
const EXAM_GOALS = ['Class 10 Boards', 'Class 12 Boards', 'JEE', 'NEET', 'Improve grades', 'Just exploring'];
const SUBJECTS = ['Mathematics', 'Science', 'English', 'Social Science', 'Physics', 'Chemistry', 'Biology'];
const STYLES = [
  { id: 'visual',       label: 'Visual diagrams',       desc: 'Charts, mind-maps, videos' },
  { id: 'quizzes',      label: 'Quizzes & practice',    desc: 'Learn by doing' },
  { id: 'explanations', label: 'Deep explanations',     desc: 'Step-by-step concepts' },
  { id: 'interactive',  label: 'Interactive chat',      desc: 'Q&A back and forth' },
  { id: 'balanced',     label: 'A bit of everything',   desc: 'Adaptive mix' },
];

export default function OnboardingModal({ onComplete }) {
  const { user, setUser } = useAuth();
  const [step, setStep] = useState(0);
  const [submitting, setSubmitting] = useState(false);
  const [form, setForm] = useState({
    name: user?.name || '',
    class_level: user?.class_level || '9',
    exam_goal: '',
    weak_subjects: [],
    learning_style: 'balanced',
  });

  const STEPS = [
    {
      icon: Sparkles, color: '#fbbf24',
      title: 'Welcome to AceIt AI',
      subtitle: "Let's personalize your AI tutor in 30 seconds.",
      key: 'name',
      content: (
        <input
          type="text" placeholder="What should we call you?"
          value={form.name} autoFocus data-testid="onb-name-input"
          onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
          className="w-full px-4 py-3 rounded-xl text-lg font-body bg-zinc-900/40 border-2 border-amber-400/30 focus:border-amber-400 outline-none transition-all" />
      ),
      canProceed: () => form.name.trim().length >= 2,
    },
    {
      icon: GraduationCap, color: '#2563eb',
      title: 'Which grade are you in?',
      subtitle: 'This locks your syllabus to your real class — no distractions.',
      key: 'class',
      content: (
        <div className="grid grid-cols-4 gap-2">
          {CLASSES.map(c => (
            <button key={c} data-testid={`onb-class-${c}`}
              onClick={() => setForm(f => ({ ...f, class_level: c }))}
              className={`py-4 rounded-xl font-heading font-bold text-lg transition-all border-2 ${form.class_level === c ? 'bg-blue-500 text-white border-blue-300 scale-105' : 'bg-zinc-900/40 border-blue-400/20 hover:border-blue-400/50'}`}>
              Class {c}
            </button>
          ))}
        </div>
      ),
      canProceed: () => CLASSES.includes(form.class_level),
    },
    {
      icon: Target, color: '#dc2626',
      title: 'What\'s your main goal?',
      subtitle: 'We\'ll tune the AI tutor to push you toward this.',
      key: 'goal',
      content: (
        <div className="grid grid-cols-2 gap-2">
          {EXAM_GOALS.map(g => (
            <button key={g} data-testid={`onb-goal-${g}`}
              onClick={() => setForm(f => ({ ...f, exam_goal: g }))}
              className={`py-3 px-3 rounded-xl text-sm font-body font-semibold text-left transition-all border-2 ${form.exam_goal === g ? 'bg-red-500 text-white border-red-300' : 'bg-zinc-900/40 border-red-400/20 hover:border-red-400/50'}`}>
              {g}
            </button>
          ))}
        </div>
      ),
      canProceed: () => form.exam_goal.length > 0,
    },
    {
      icon: AlertTriangle, color: '#f59e0b',
      title: 'Any subjects you find tough?',
      subtitle: 'Pick as many as you want — we\'ll prioritise these. (Optional)',
      key: 'weak',
      content: (
        <div className="grid grid-cols-2 gap-2">
          {SUBJECTS.map(s => {
            const sel = form.weak_subjects.includes(s);
            return (
              <button key={s} data-testid={`onb-subj-${s}`}
                onClick={() => setForm(f => ({
                  ...f, weak_subjects: sel ? f.weak_subjects.filter(x => x !== s) : [...f.weak_subjects, s],
                }))}
                className={`py-2.5 px-3 rounded-xl text-sm font-body font-semibold text-left transition-all border-2 flex items-center justify-between ${sel ? 'bg-amber-500 text-white border-amber-300' : 'bg-zinc-900/40 border-amber-400/20 hover:border-amber-400/50'}`}>
                {s} {sel && <Check size={14} />}
              </button>
            );
          })}
        </div>
      ),
      canProceed: () => true,
    },
    {
      icon: Palette, color: '#7c3aed',
      title: 'How do you learn best?',
      subtitle: 'Pick your favourite learning style.',
      key: 'style',
      content: (
        <div className="space-y-2">
          {STYLES.map(s => (
            <button key={s.id} data-testid={`onb-style-${s.id}`}
              onClick={() => setForm(f => ({ ...f, learning_style: s.id }))}
              className={`w-full py-3 px-4 rounded-xl text-left transition-all border-2 ${form.learning_style === s.id ? 'bg-violet-500 text-white border-violet-300' : 'bg-zinc-900/40 border-violet-400/20 hover:border-violet-400/50'}`}>
              <p className="font-heading font-bold text-sm">{s.label}</p>
              <p className="text-xs font-body opacity-80">{s.desc}</p>
            </button>
          ))}
        </div>
      ),
      canProceed: () => true,
    },
  ];

  const current = STEPS[step];

  const submit = async () => {
    setSubmitting(true);
    try {
      const { data } = await axios.post(`${API}/onboarding/submit`, form, { withCredentials: true });
      if (setUser && data.data) {
        setUser(u => ({ ...u, ...data.data, is_onboarded: true }));
      }
      onComplete?.();
    } catch (e) {
      console.error(e);
    }
    setSubmitting(false);
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/60 backdrop-blur-md" data-testid="onboarding-modal">
      <motion.div
        initial={{ opacity: 0, y: 20, scale: 0.96 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        className="w-full max-w-lg rounded-3xl glass border-2 p-6 relative overflow-hidden"
        style={{ borderColor: current.color + '60' }}>
        <div className="absolute -top-20 -right-20 w-48 h-48 rounded-full blur-3xl opacity-30 pointer-events-none" style={{ background: current.color }} />

        {/* Step dots */}
        <div className="flex gap-1.5 mb-5">
          {STEPS.map((_, i) => (
            <div key={i} className="flex-1 h-1 rounded-full transition-all"
              style={{ background: i <= step ? current.color : 'rgba(255,255,255,0.15)' }} />
          ))}
        </div>

        <AnimatePresence mode="wait">
          <motion.div key={step}
            initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}>
            <div className="flex items-center gap-3 mb-3">
              <div className="w-11 h-11 rounded-2xl flex items-center justify-center"
                style={{ background: current.color + '22', border: `2px solid ${current.color}55` }}>
                <current.icon size={22} style={{ color: current.color }} />
              </div>
              <span className="text-zinc-500 text-xs font-body uppercase tracking-widest">Step {step + 1} of {STEPS.length}</span>
            </div>
            <h2 className="text-white text-2xl sm:text-3xl font-heading font-black mb-1">{current.title}</h2>
            <p className="text-zinc-400 text-sm font-body mb-5">{current.subtitle}</p>

            <div className="mb-6">{current.content}</div>
          </motion.div>
        </AnimatePresence>

        <div className="flex items-center gap-2">
          {step > 0 && (
            <button onClick={() => setStep(s => s - 1)} data-testid="onb-back-btn"
              className="px-4 py-2.5 rounded-xl text-zinc-400 hover:text-white font-body font-semibold text-sm transition-all">
              Back
            </button>
          )}
          <button
            onClick={() => step < STEPS.length - 1 ? setStep(s => s + 1) : submit()}
            disabled={!current.canProceed() || submitting}
            data-testid="onb-next-btn"
            className="ml-auto px-5 py-2.5 rounded-xl font-heading font-bold text-sm flex items-center gap-2 transition-all disabled:opacity-40 disabled:cursor-not-allowed"
            style={{ background: current.color, color: 'white' }}>
            {submitting ? <div className="w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin" /> :
              step < STEPS.length - 1 ? <>Continue <ArrowRight size={14} /></> : <>Get Started <Sparkles size={14} /></>}
          </button>
        </div>
      </motion.div>
    </div>
  );
}
