import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Trophy, Sparkles, ChevronDown, CheckCircle, XCircle,
  ArrowRight, RotateCcw, Zap, Brain, Target, TrendingUp, BookOpen
} from 'lucide-react';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';
import { MathText } from './MathRenderer';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const DIFF_COLORS = { easy: '#10b981', medium: '#f59e0b', hard: '#ef4444' };

const sel = 'w-full bg-zinc-900 border border-white/10 rounded-xl px-4 py-3 text-white text-sm font-body focus:outline-none focus:border-cyan-500/50 appearance-none';

export default function QuizArena() {
  const { user } = useAuth();
  const userClass = user?.class_level || '9';

  const [subjects, setSubjects]     = useState([]);
  const [chapters, setChapters]     = useState([]);
  const [mastery, setMastery]       = useState(null);   // adaptive difficulty hint
  const [form, setForm]             = useState({ subject: '', chapter: '', topic: '', difficulty: 'medium', num: 5 });
  const [quiz, setQuiz]             = useState(null);
  const [answers, setAnswers]       = useState({});
  const [result, setResult]         = useState(null);
  const [loading, setLoading]       = useState(false);
  const [phase, setPhase]           = useState('setup');
  const [history, setHistory]       = useState([]);
  const [current, setCurrent]       = useState(0);
  const [adaptiveUsed, setAdaptiveUsed] = useState(false);

  useEffect(() => {
    axios.get(`${API}/syllabus/${userClass}/subjects`, { withCredentials: true })
      .then(r => setSubjects(r.data)).catch(() => {});
    axios.get(`${API}/quiz/history`, { withCredentials: true })
      .then(r => setHistory(r.data)).catch(() => {});
  }, [userClass]);

  // Fetch chapters when subject changes
  const onSubjectChange = async (subject) => {
    setForm(p => ({ ...p, subject, chapter: '', topic: '' }));
    setChapters([]);
    setMastery(null);
    if (!subject) return;
    try {
      const { data } = await axios.get(`${API}/syllabus/${userClass}/${encodeURIComponent(subject)}/chapters`, { withCredentials: true });
      setChapters(Array.isArray(data) ? data : data.chapters || []);
    } catch { setChapters([]); }
  };

  // Auto-fill topic and fetch adaptive difficulty when chapter changes
  const onChapterChange = async (chapter) => {
    setForm(p => ({ ...p, chapter, topic: chapter }));
    setMastery(null);
    if (!chapter) return;
    try {
      const { data } = await axios.get(`${API}/quiz/topic-mastery`, {
        params: { topic: chapter }, withCredentials: true,
      });
      setMastery(data);
      // Auto-set difficulty to adaptive recommendation
      setForm(p => ({ ...p, chapter, topic: chapter, difficulty: data.recommended_difficulty }));
      setAdaptiveUsed(true);
    } catch { setAdaptiveUsed(false); }
  };

  const generateQuiz = async () => {
    if (!form.subject || !form.topic) return;
    setLoading(true);
    try {
      const { data } = await axios.post(`${API}/quiz/generate`, {
        class_level: userClass, subject: form.subject,
        chapter: form.chapter || form.topic,
        topic: form.topic, difficulty: form.difficulty, num_questions: form.num,
      }, { withCredentials: true });
      setQuiz(data); setAnswers({}); setCurrent(0); setPhase('quiz');
    } catch (e) {
      const msg = e.response?.data?.detail?.message || e.response?.data?.detail || 'Generation failed';
      alert(msg);
    }
    setLoading(false);
  };

  const submitQuiz = async () => {
    if (!quiz) return;
    setLoading(true);
    try {
      const { data } = await axios.post(`${API}/quiz/${quiz.quiz_id}/submit`,
        { quiz_id: quiz.quiz_id, answers }, { withCredentials: true });
      // Normalize is_correct → correct
      const normalized = {
        ...data,
        results: (data.results || []).map(r => ({ ...r, correct: r.is_correct ?? r.correct })),
      };
      setResult(normalized);
      setPhase('result');
      // Refresh history
      axios.get(`${API}/quiz/history`, { withCredentials: true }).then(r => setHistory(r.data)).catch(() => {});
      // Refresh mastery hint
      if (form.topic) {
        axios.get(`${API}/quiz/topic-mastery`, { params: { topic: form.topic }, withCredentials: true })
          .then(r => setMastery(r.data)).catch(() => {});
      }
    } catch { }
    setLoading(false);
  };

  const reset = () => { setPhase('setup'); setQuiz(null); setResult(null); setAnswers({}); setAdaptiveUsed(false); };

  return (
    <div className="p-4 sm:p-6 max-w-3xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl sm:text-3xl font-heading font-black text-white flex items-center gap-3">
          <Trophy size={28} className="text-amber-400" /> Quiz Arena
        </h1>
        <p className="text-zinc-500 text-sm font-body mt-1">AI-powered quizzes with adaptive difficulty</p>
      </div>

      <AnimatePresence mode="wait">

        {/* ── SETUP ─────────────────────────────────────────── */}
        {phase === 'setup' && (
          <motion.div key="setup" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} className="space-y-5">
            <div className="glass rounded-2xl p-5 border border-white/10 space-y-3">
              <h2 className="text-white font-heading font-bold mb-1">Configure Your Quiz</h2>

              {/* Class (locked) + Subject */}
              <div className="grid grid-cols-2 gap-3">
                <div className="px-3 py-3 rounded-xl border border-amber-400/30 bg-amber-500/10 text-amber-300 text-sm font-body font-semibold flex items-center gap-2"
                  data-testid="quiz-class-locked">
                  <Sparkles size={14} /> Class {userClass}
                </div>
                <div className="relative">
                  <select value={form.subject} onChange={e => onSubjectChange(e.target.value)}
                    data-testid="quiz-subject-select" className={sel}>
                    <option value="">Subject</option>
                    {subjects.map(s => <option key={s.name} value={s.name}>{s.name}</option>)}
                  </select>
                  <ChevronDown size={14} className="absolute right-3 top-3.5 text-zinc-500 pointer-events-none" />
                </div>
              </div>

              {/* Chapter dropdown (populated after subject) */}
              {chapters.length > 0 && (
                <div className="relative">
                  <select value={form.chapter} onChange={e => onChapterChange(e.target.value)}
                    data-testid="quiz-chapter-select" className={sel}>
                    <option value="">Select Chapter</option>
                    {chapters.map(c => <option key={c.id || c.name} value={c.name}>{c.name}</option>)}
                  </select>
                  <ChevronDown size={14} className="absolute right-3 top-3.5 text-zinc-500 pointer-events-none" />
                </div>
              )}

              {/* Topic (editable, pre-filled from chapter) */}
              <input value={form.topic} onChange={e => setForm(p => ({ ...p, topic: e.target.value }))}
                placeholder="Topic (e.g., Photosynthesis, Newton's Laws…)"
                data-testid="quiz-topic-input"
                className="w-full bg-zinc-900 border border-white/10 rounded-xl px-4 py-3 text-white text-sm font-body focus:outline-none focus:border-cyan-500/50 placeholder-zinc-600" />

              {/* Adaptive mastery hint */}
              {mastery && mastery.attempts > 0 && (
                <div className="flex items-center gap-2 px-3 py-2 rounded-xl bg-violet-500/10 border border-violet-500/20 text-xs font-body">
                  <Brain size={13} className="text-violet-400" />
                  <span className="text-zinc-300">
                    Topic mastery: <span className="font-bold" style={{ color: DIFF_COLORS[mastery.recommended_difficulty] }}>{mastery.mastery_pct}%</span>
                  </span>
                  <span className="text-zinc-500">•</span>
                  <span className="text-violet-300">Adaptive difficulty: <strong>{mastery.recommended_difficulty}</strong></span>
                  {adaptiveUsed && <span className="ml-auto px-1.5 py-0.5 rounded bg-violet-500/20 text-violet-300 text-[10px] font-bold uppercase">Auto-set</span>}
                </div>
              )}

              {/* Difficulty + Questions count */}
              <div className="grid grid-cols-2 gap-3">
                <div className="relative">
                  <select value={form.difficulty} onChange={e => { setForm(p => ({ ...p, difficulty: e.target.value })); setAdaptiveUsed(false); }}
                    data-testid="quiz-difficulty-select" className={sel}>
                    <option value="easy">Easy</option>
                    <option value="medium">Medium</option>
                    <option value="hard">Hard</option>
                  </select>
                  <ChevronDown size={14} className="absolute right-3 top-3.5 text-zinc-500 pointer-events-none" />
                </div>
                <div className="relative">
                  <select value={form.num} onChange={e => setForm(p => ({ ...p, num: Number(e.target.value) }))} className={sel}>
                    {[3, 5, 10].map(n => <option key={n} value={n}>{n} Questions</option>)}
                  </select>
                  <ChevronDown size={14} className="absolute right-3 top-3.5 text-zinc-500 pointer-events-none" />
                </div>
              </div>

              <button onClick={generateQuiz} disabled={!form.subject || !form.topic || loading}
                data-testid="generate-quiz-btn"
                className="w-full py-3 rounded-xl bg-amber-400 hover:bg-amber-300 disabled:opacity-40 text-black font-heading font-bold text-sm transition-all flex items-center justify-center gap-2">
                {loading
                  ? <div className="w-4 h-4 border-2 border-black/30 border-t-black rounded-full animate-spin" />
                  : <><Sparkles size={16} /> Generate AI Quiz</>}
              </button>
            </div>

            {/* Recent history */}
            {history.filter(q => q.completed).length > 0 && (
              <div>
                <h3 className="text-zinc-400 text-sm font-body font-semibold mb-3 uppercase tracking-wider">Recent Scores</h3>
                <div className="space-y-2">
                  {history.filter(q => q.completed).slice(0, 5).map(q => (
                    <div key={q.quiz_id} className="flex items-center gap-3 p-3 glass-surface rounded-xl border border-white/5">
                      <div className="w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0"
                        style={{ background: q.score >= 70 ? '#10b98120' : '#ef444420' }}>
                        <Trophy size={16} style={{ color: q.score >= 70 ? '#10b981' : '#ef4444' }} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-white text-sm font-body font-medium truncate">{q.topic}</p>
                        <p className="text-zinc-600 text-xs font-body">{q.subject} • Class {q.class_level} • <span className="capitalize">{q.difficulty}</span></p>
                      </div>
                      <span className="font-heading font-bold text-sm" style={{ color: q.score >= 70 ? '#10b981' : '#ef4444' }}>{q.score}%</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </motion.div>
        )}

        {/* ── QUIZ ──────────────────────────────────────────── */}
        {phase === 'quiz' && quiz && (
          <motion.div key="quiz" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }}>
            <div className="mb-5">
              <div className="flex items-center justify-between mb-2">
                <span className="text-zinc-400 text-sm font-body">Question {current + 1} of {quiz.questions.length}</span>
                <div className="flex items-center gap-2">
                  <span className="px-2 py-0.5 rounded-full text-[11px] font-heading font-bold capitalize"
                    style={{ background: DIFF_COLORS[form.difficulty] + '20', color: DIFF_COLORS[form.difficulty] }}>
                    {form.difficulty}
                  </span>
                  <div className="flex gap-1">
                    {quiz.questions.map((_, i) => (
                      <button key={i} onClick={() => setCurrent(i)}
                        className={`w-6 h-1.5 rounded-full transition-all ${i === current ? 'bg-cyan-400' : answers[i] ? 'bg-green-500/60' : 'bg-zinc-700'}`} />
                    ))}
                  </div>
                </div>
              </div>
              <div className="h-1 bg-zinc-800 rounded-full overflow-hidden">
                <motion.div className="h-full bg-gradient-to-r from-cyan-400 to-violet-500 rounded-full"
                  animate={{ width: `${((current + 1) / quiz.questions.length) * 100}%` }} />
              </div>
            </div>

            <AnimatePresence mode="wait">
              <motion.div key={current} initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}
                className="glass rounded-2xl p-5 border border-white/10 mb-4">
                <div className="flex items-start gap-3 mb-5">
                  <div className="w-7 h-7 rounded-lg bg-cyan-500/20 flex items-center justify-center flex-shrink-0 text-cyan-400 text-xs font-heading font-bold">
                    {current + 1}
                  </div>
                  <p className="text-white font-body text-base leading-relaxed">
                    <MathText text={quiz.questions[current]?.question} />
                  </p>
                </div>
                <div className="space-y-2">
                  {quiz.questions[current]?.options?.map((opt, i) => {
                    const letter = opt.charAt(0);
                    const isSelected = answers[current] === letter;
                    return (
                      <button key={i} onClick={() => !result && setAnswers(p => ({ ...p, [current]: letter }))}
                        data-testid={`quiz-option-${letter}`}
                        className={`w-full text-left px-4 py-3 rounded-xl border text-sm font-body transition-all flex items-center gap-3
                          ${isSelected ? 'border-cyan-500/50 bg-cyan-500/10 text-white' : 'border-white/10 bg-zinc-900/50 text-zinc-300 hover:border-white/20 hover:bg-zinc-800/50'}`}>
                        <span className={`w-6 h-6 rounded-full border flex items-center justify-center text-xs font-heading font-bold flex-shrink-0
                          ${isSelected ? 'border-cyan-400 text-cyan-400' : 'border-zinc-600 text-zinc-500'}`}>
                          {letter}
                        </span>
                        {opt.slice(3)}
                      </button>
                    );
                  })}
                </div>
              </motion.div>
            </AnimatePresence>

            <div className="flex items-center justify-between">
              <button onClick={() => setCurrent(Math.max(0, current - 1))} disabled={current === 0}
                className="px-4 py-2 rounded-xl border border-white/10 text-zinc-400 text-sm font-body disabled:opacity-30 hover:border-white/20 hover:text-white transition-all">
                Previous
              </button>
              {current < quiz.questions.length - 1 ? (
                <button onClick={() => setCurrent(current + 1)} data-testid="next-question-btn"
                  className="px-4 py-2 rounded-xl bg-zinc-800 hover:bg-zinc-700 text-white text-sm font-body transition-all flex items-center gap-2">
                  Next <ArrowRight size={14} />
                </button>
              ) : (
                <button onClick={submitQuiz} disabled={Object.keys(answers).length < quiz.questions.length || loading}
                  data-testid="submit-quiz-btn"
                  className="px-5 py-2 rounded-xl bg-cyan-500 hover:bg-cyan-400 disabled:opacity-40 text-black font-heading font-bold text-sm transition-all flex items-center gap-2">
                  {loading ? <div className="w-4 h-4 border-2 border-black/30 border-t-black rounded-full animate-spin" /> : <><CheckCircle size={14} /> Submit Quiz</>}
                </button>
              )}
            </div>
            <p className="text-center text-zinc-600 text-xs font-body mt-3">{Object.keys(answers).length}/{quiz.questions.length} answered</p>
          </motion.div>
        )}

        {/* ── RESULT ────────────────────────────────────────── */}
        {phase === 'result' && result && (
          <motion.div key="result" initial={{ opacity: 0, scale: 0.97 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0 }}>
            {/* Score */}
            <div className="text-center py-8 glass rounded-2xl border mb-5"
              style={{ borderColor: result.score >= 70 ? '#10b98130' : '#ef444430', background: result.score >= 70 ? 'rgba(16,185,129,0.04)' : 'rgba(239,68,68,0.04)' }}>
              <div className="text-6xl font-heading font-black mb-2" style={{ color: result.score >= 70 ? '#10b981' : '#ef4444' }}>
                {result.score}%
              </div>
              <p className="text-white font-heading font-bold text-xl mb-1">
                {result.score >= 90 ? 'Outstanding!' : result.score >= 70 ? 'Well Done!' : result.score >= 50 ? 'Good Effort!' : 'Keep Practicing!'}
              </p>
              <p className="text-zinc-500 font-body text-sm">{result.correct_count}/{result.total_questions} correct</p>
              <div className="flex items-center justify-center gap-1.5 mt-3">
                <Zap size={16} className="text-amber-400" />
                <span className="text-amber-400 font-heading font-bold">+{result.xp_earned} XP</span>
              </div>

              {/* Adaptive next-difficulty hint */}
              {mastery && (
                <div className="mt-4 inline-flex items-center gap-2 px-4 py-2 rounded-full text-xs font-body"
                  style={{ background: DIFF_COLORS[mastery.recommended_difficulty] + '15', border: `1px solid ${DIFF_COLORS[mastery.recommended_difficulty]}30` }}>
                  <TrendingUp size={12} style={{ color: DIFF_COLORS[mastery.recommended_difficulty] }} />
                  <span className="text-zinc-300">Next recommended difficulty: </span>
                  <span className="font-bold capitalize" style={{ color: DIFF_COLORS[mastery.recommended_difficulty] }}>{mastery.recommended_difficulty}</span>
                  <span className="text-zinc-500">•</span>
                  <span className="text-zinc-400">Mastery: {mastery.mastery_pct}%</span>
                </div>
              )}
            </div>

            {/* Per-question results */}
            <div className="space-y-3 mb-5">
              {result.results?.map((r, i) => (
                <div key={i} className={`p-4 rounded-xl border ${r.correct || r.is_correct ? 'border-green-500/20 bg-green-500/5' : 'border-red-500/20 bg-red-500/5'}`}>
                  <div className="flex items-start gap-3">
                    {(r.correct || r.is_correct)
                      ? <CheckCircle size={18} className="text-green-400 mt-0.5 flex-shrink-0" />
                      : <XCircle size={18} className="text-red-400 mt-0.5 flex-shrink-0" />}
                    <div className="flex-1">
                      <p className="text-white text-sm font-body leading-relaxed"><MathText text={r.question} /></p>
                      {!(r.correct || r.is_correct) && (
                        <p className="text-zinc-400 text-xs font-body mt-1">
                          Your: <span className="text-red-400">{r.user_answer ?? '–'}</span> • Correct: <span className="text-green-400">{r.correct_answer ?? ''}</span>
                        </p>
                      )}
                      {r.explanation && <p className="text-zinc-500 text-xs font-body mt-1 leading-relaxed"><MathText text={r.explanation} /></p>}
                    </div>
                  </div>
                </div>
              ))}
            </div>

            <div className="flex gap-3">
              <button onClick={reset} data-testid="try-again-btn"
                className="flex-1 py-3 rounded-xl glass border border-white/10 hover:border-white/20 text-white font-heading font-bold text-sm transition-all flex items-center justify-center gap-2">
                <RotateCcw size={16} /> New Quiz
              </button>
              {mastery && result.score < 70 && (
                <button onClick={() => {
                  setForm(p => ({ ...p, difficulty: 'easy' })); reset();
                }}
                  className="flex-1 py-3 rounded-xl border border-amber-500/30 bg-amber-500/10 hover:bg-amber-500/20 text-amber-300 font-heading font-bold text-sm transition-all flex items-center justify-center gap-2">
                  <BookOpen size={16} /> Retry (Easy)
                </button>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
