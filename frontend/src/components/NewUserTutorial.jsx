import { useState } from 'react';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';
import { Sparkles, Zap, MessageSquare, Trophy, FileText, X, ArrowRight, Check } from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;const STEPS = [
  {
    icon: Sparkles,
    color: '#22d3ee',
    gradient: 'from-cyan-500/20 to-cyan-500/5',
    border: 'border-cyan-500/30',
    title: 'Welcome to AceIt AI!',
    subtitle: 'Your smart BNPS Grade 8 exam prep companion',
    description: 'AceIt AI is built specifically for your school curriculum. Everything — AI tutor, quizzes, and mock exams — is based on your exact Grade 8 chapters.',
    highlight: 'Brooklyn National Public School • Grade 8 Curriculum',
    highlightColor: 'text-cyan-400',
  },
  {
    icon: Zap,
    color: '#fbbf24',
    gradient: 'from-amber-500/20 to-amber-500/5',
    border: 'border-amber-500/30',
    title: 'Credits System',
    subtitle: 'You start with 100 free credits',
    description: 'You start with 100 free credits. Spend them on AI chat and quizzes. Earn bonus credits back by completing quizzes — the more correct answers, the more you earn!',
    items: [
      { label: 'AI Tutor chat', cost: '2–10 credits / message' },
      { label: 'Generate a Quiz', cost: '15 credits' },
      { label: 'Your first quiz', cost: 'FREE!' },
      { label: 'Complete any quiz', cost: '+1 to +5 credits back' },
    ],
    highlight: 'Starting balance: 100 credits',
    highlightColor: 'text-amber-400',
  },
  {
    icon: MessageSquare,
    color: '#8b5cf6',
    gradient: 'from-violet-500/20 to-violet-500/5',
    border: 'border-violet-500/30',
    title: 'AI Tutor',
    subtitle: 'Your 24/7 personal CBSE teacher',
    description: 'Select any chapter from your syllabus and start chatting. The AI explains concepts, gives examples, embeds mini-quizzes, and adapts to your learning style over time.',
    items: [
      { label: 'Chapter-locked conversations' },
      { label: 'Inline quick-check quizzes' },
      { label: 'YouTube visual boosts' },
      { label: 'Adapts to your progress' },
    ],
    highlight: 'Tip: Try "Give me a quiz" in chat!',
    highlightColor: 'text-violet-400',
  },
  {
    icon: Trophy,
    color: '#10b981',
    gradient: 'from-emerald-500/20 to-emerald-500/5',
    border: 'border-emerald-500/30',
    title: 'Quiz Arena',
    subtitle: 'Test your knowledge chapter by chapter',
    description: 'Generate AI-powered MCQ quizzes for any chapter. After each quiz, the AI tutor automatically explains your wrong answers. Track your scores and improve over time.',
    items: [
      { label: 'Chapter-specific MCQ quizzes' },
      { label: 'Adaptive difficulty (Easy/Medium/Hard)' },
      { label: 'Auto-analysis of wrong answers' },
    ],
    highlight: 'First quiz is on us!',
    highlightColor: 'text-emerald-400',
  },
  {
    icon: FileText,
    color: '#f43f5e',
    gradient: 'from-rose-500/20 to-rose-500/5',
    border: 'border-rose-500/30',
    title: 'Mock Exams & More',
    subtitle: 'Full exam simulation + Rankings + Study Plan',
    description: 'Take full timed mock exams in CBSE pattern with MCQ, Short Answer, and Application sections. Climb the leaderboard, build a study plan, and track your overall progress.',
    items: [
      { label: 'Timed CBSE-pattern mock exams' },
      { label: 'School leaderboard & rankings' },
      { label: 'AI-generated study plan' },
      { label: 'Progress tracking & analytics' },
    ],
    highlight: "You're all set — let's start learning!",
    highlightColor: 'text-rose-400',
  },
];

export function shouldShowTutorial() {
  return !localStorage.getItem('aceit_tutorial_seen');
}

export function markTutorialSeen() {
  localStorage.setItem('aceit_tutorial_seen', 'true');
}

async function markSeenInDB() {
  try {
    await axios.patch(`${API}/auth/tutorial/seen`, {}, { withCredentials: true });
  } catch (e) { /* non-critical */ }
}

export default function NewUserTutorial({ onClose }) {
  const [step, setStep] = useState(0);
  const current = STEPS[step];
  const Icon = current.icon;
  const isLast = step === STEPS.length - 1;

  const handleNext = () => {
    if (isLast) {
      markTutorialSeen();
      markSeenInDB();
      onClose?.();
    } else {
      setStep(s => s + 1);
    }
  };

  const handleSkip = () => {
    markTutorialSeen();
    markSeenInDB();
    onClose?.();
  };

  return (
    <div className="fixed inset-0 z-[110] flex items-center justify-center p-4 bg-black/70 backdrop-blur-md"
      data-testid="new-user-tutorial">
      <motion.div
        initial={{ opacity: 0, y: 24, scale: 0.97 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: 16, scale: 0.97 }}
        className={`w-full max-w-md rounded-2xl bg-zinc-900 border ${current.border} overflow-hidden shadow-2xl`}>

        {/* Progress bar */}
        <div className="flex gap-1 p-4 pb-0">
          {STEPS.map((_, i) => (
            <div key={i} className="flex-1 h-1 rounded-full transition-all duration-300"
              style={{ background: i <= step ? current.color : 'rgba(255,255,255,0.1)' }} />
          ))}
        </div>

        {/* Close button */}
        <button onClick={handleSkip} data-testid="tutorial-skip-btn"
          className="absolute top-3 right-3 p-1.5 rounded-lg text-zinc-500 hover:text-white hover:bg-white/5 transition-all">
          <X size={16} />
        </button>

        <AnimatePresence mode="wait">
          <motion.div key={step}
            initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.2 }}
            className="p-6 pt-4">

            {/* Icon */}
            <div className={`w-14 h-14 rounded-2xl bg-gradient-to-br ${current.gradient} border ${current.border} flex items-center justify-center mb-4`}>
              <Icon size={26} style={{ color: current.color }} />
            </div>

            {/* Step label */}
            <p className="text-zinc-500 text-xs font-body uppercase tracking-widest mb-1">
              Step {step + 1} of {STEPS.length}
            </p>

            <h2 className="text-white text-xl font-heading font-black mb-1">{current.title}</h2>
            <p className="text-zinc-400 text-sm font-body mb-4">{current.subtitle}</p>
            <p className="text-zinc-300 text-sm font-body leading-relaxed mb-4">{current.description}</p>

            {/* Items list */}
            {current.items && (
              <div className="space-y-2 mb-4">
                {current.items.map((item, i) => (
                  <div key={i} className="flex items-center justify-between gap-3">
                    <div className="flex items-center gap-2 text-sm text-zinc-300 font-body">
                      <Check size={14} style={{ color: current.color }} className="flex-shrink-0" />
                      {item.label}
                    </div>
                    {item.cost && (
                      <span className="text-xs font-body font-semibold" style={{ color: current.color }}>
                        {item.cost}
                      </span>
                    )}
                  </div>
                ))}
              </div>
            )}

            {/* Highlight */}
            <div className={`px-3 py-2 rounded-xl bg-white/5 border border-white/10 mb-5`}>
              <p className={`text-sm font-body font-semibold ${current.highlightColor}`}>{current.highlight}</p>
            </div>

            {/* Buttons */}
            <div className="flex items-center gap-3">
              {step > 0 && (
                <button onClick={() => setStep(s => s - 1)}
                  className="px-4 py-2.5 rounded-xl text-zinc-400 hover:text-white font-body text-sm transition-all">
                  Back
                </button>
              )}
              {step === 0 && (
                <button onClick={handleSkip} data-testid="tutorial-skip-all-btn"
                  className="px-4 py-2.5 rounded-xl text-zinc-500 hover:text-zinc-400 font-body text-sm transition-all">
                  Skip tour
                </button>
              )}
              <button onClick={handleNext} data-testid="tutorial-next-btn"
                className="ml-auto flex items-center gap-2 px-5 py-2.5 rounded-xl font-heading font-bold text-sm text-black transition-all"
                style={{ background: current.color }}>
                {isLast ? 'Get Started' : 'Next'}
                <ArrowRight size={14} />
              </button>
            </div>
          </motion.div>
        </AnimatePresence>
      </motion.div>
    </div>
  );
}
