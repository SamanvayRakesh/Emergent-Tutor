import { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FileText, Clock, Sparkles, ChevronDown, CheckCircle, XCircle, AlertCircle, Zap, RotateCcw, BookOpen, Target } from 'lucide-react';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';
import { MathText } from './MathRenderer';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

function Timer({ durationMinutes, onTimeUp, running }) {
  const [seconds, setSeconds] = useState(durationMinutes * 60);
  const ref = useRef(null);

  useEffect(() => {
    if (!running) return;
    ref.current = setInterval(() => {
      setSeconds(s => {
        if (s <= 1) { clearInterval(ref.current); onTimeUp(); return 0; }
        return s - 1;
      });
    }, 1000);
    return () => clearInterval(ref.current);
  }, [running, onTimeUp]);

  const pct = (seconds / (durationMinutes * 60)) * 100;
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  const urgent = seconds < 300;

  return (
    <div className={`flex items-center gap-2 px-3 py-2 rounded-xl border ${urgent ? 'border-red-500/30 bg-red-500/10' : 'border-white/10 bg-zinc-900/50'}`}>
      <Clock size={14} className={urgent ? 'text-red-400 animate-pulse' : 'text-zinc-400'} />
      <span className={`font-heading font-bold text-sm ${urgent ? 'text-red-400' : 'text-white'}`}>
        {String(mins).padStart(2, '0')}:{String(secs).padStart(2, '0')}
      </span>
    </div>
  );
}

export default function MockExamPage() {
  const { user } = useAuth();
  const userClass = user?.class_level || '9';
  const [subjects, setSubjects] = useState([]);
  const [form, setForm] = useState({ class: userClass, subject: '', duration: 60, numQ: 15 });
  const [exam, setExam] = useState(null);
  const [answers, setAnswers] = useState({});
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [phase, setPhase] = useState('setup');
  const [currentSection, setCurrentSection] = useState(0);
  const [timerRunning, setTimerRunning] = useState(false);
  const [history, setHistory]       = useState([]);
  const [weakAreas, setWeakAreas]   = useState(null);
  const [followUp, setFollowUp]     = useState(null);
  const [followUpLoading, setFollowUpLoading] = useState(false);

  useEffect(() => {
    // Grade-locked: only load subjects for user's active class
    setForm(p => ({ ...p, class: userClass }));
    axios.get(`${API}/syllabus/${userClass}/subjects`, { withCredentials: true }).then(r => setSubjects(r.data)).catch(() => {});
    axios.get(`${API}/mock-exam/history`, { withCredentials: true }).then(r => setHistory(r.data)).catch(() => {});
    axios.get(`${API}/weak-areas`, { withCredentials: true }).then(r => setWeakAreas(r.data)).catch(() => {});
  }, [userClass]);

  const onClassChange = async (cls) => {
    setForm(p => ({ ...p, class: cls, subject: '' }));
    const r = await axios.get(`${API}/syllabus/${cls}/subjects`, { withCredentials: true });
    setSubjects(r.data);
  };

  const generateExam = async () => {
    if (!form.class || !form.subject) return;
    setLoading(true);
    try {
      const { data } = await axios.post(`${API}/mock-exam/generate`, {
        class_level: form.class, subject: form.subject,
        duration_minutes: form.duration, num_questions: form.numQ
      }, { withCredentials: true });
      setExam(data);
      setAnswers({});
      setCurrentSection(0);
      setPhase('exam');
      setTimerRunning(true);
    } catch (e) { console.error(e); }
    setLoading(false);
  };

  const handleTimeUp = useCallback(() => {
    setTimerRunning(false);
    submitExam();
  }, [exam, answers]);

  const submitExam = async () => {
    if (!exam) return;
    setTimerRunning(false);
    setLoading(true);
    try {
      const { data } = await axios.post(`${API}/mock-exam/${exam.exam_id}/submit`,
        { quiz_id: exam.exam_id, answers }, { withCredentials: true });
      setResult(data);
      setPhase('result');
    } catch (e) { console.error(e); }
    setLoading(false);
  };

  const reset = () => { setPhase('setup'); setExam(null); setResult(null); setAnswers({}); setTimerRunning(false); setFollowUp(null); };

  const startFollowUp = async () => {
    if (!exam) return;
    setFollowUpLoading(true);
    try {
      const { data } = await axios.post(`${API}/mock-exam/${exam.exam_id}/followup-quiz`, {}, { withCredentials: true });
      setFollowUp({ quiz: data, answers: {}, submitted: null });
    } catch (e) {
      console.error(e);
    }
    setFollowUpLoading(false);
  };

  const submitFollowUp = async () => {
    if (!followUp?.quiz) return;
    setFollowUpLoading(true);
    try {
      // Convert {0: 'A', 1: 'B'...} answers to backend format
      const { data } = await axios.post(`${API}/quiz/${followUp.quiz.quiz_id}/submit`,
        { quiz_id: followUp.quiz.quiz_id, answers: followUp.answers }, { withCredentials: true });
      setFollowUp(p => ({ ...p, submitted: data }));
    } catch (e) { console.error(e); }
    setFollowUpLoading(false);
  };

  // Count answered
  const allQs = exam?.sections?.flatMap(s => s.questions) || [];
  const answeredCount = Object.keys(answers).length;

  const sel = 'w-full bg-zinc-900 border border-white/10 rounded-xl px-4 py-3 text-white text-sm font-body focus:outline-none focus:border-cyan-500/50 appearance-none';

  return (
    <div className="p-4 sm:p-6 max-w-4xl mx-auto">
      <div className="mb-5">
        <h1 className="text-2xl sm:text-3xl font-heading font-black text-white flex items-center gap-3">
          <FileText size={28} className="text-cyan-400" /> Mock Exam
        </h1>
        <p className="text-zinc-500 text-sm font-body mt-1">CBSE-pattern timed examinations</p>
      </div>

      <AnimatePresence mode="wait">
        {phase === 'setup' && (
          <motion.div key="setup" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
            className="grid lg:grid-cols-2 gap-5">
            <div className="glass rounded-2xl p-5 border border-white/10 space-y-4">
              <h2 className="text-white font-heading font-bold">Configure Exam</h2>
              <div className="grid grid-cols-2 gap-3">
                <div className="relative px-3 py-3 rounded-xl border border-amber-400/30 bg-amber-500/10 text-amber-300 text-sm font-body font-semibold flex items-center gap-2" data-testid="mock-class-locked">
                  <BookOpen size={14} /> Class {userClass}
                </div>
                <div className="relative">
                  <select value={form.subject} onChange={e => setForm(p => ({ ...p, subject: e.target.value }))} data-testid="mock-subject-select" className={sel} disabled={!form.class}>
                    <option value="">Subject</option>
                    {subjects.map(s => <option key={s.name} value={s.name}>{s.name}</option>)}
                  </select>
                  <ChevronDown size={14} className="absolute right-3 top-3.5 text-zinc-500 pointer-events-none" />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div className="relative">
                  <select value={form.duration} onChange={e => setForm(p => ({ ...p, duration: +e.target.value }))} className={sel}>
                    {[30, 60, 90, 180].map(d => <option key={d} value={d}>{d} min</option>)}
                  </select>
                  <ChevronDown size={14} className="absolute right-3 top-3.5 text-zinc-500 pointer-events-none" />
                </div>
                <div className="relative">
                  <select value={form.numQ} onChange={e => setForm(p => ({ ...p, numQ: +e.target.value }))} className={sel}>
                    {[10, 15, 20, 30].map(n => <option key={n} value={n}>{n} Qs</option>)}
                  </select>
                  <ChevronDown size={14} className="absolute right-3 top-3.5 text-zinc-500 pointer-events-none" />
                </div>
              </div>
              <div className="p-3 rounded-xl bg-cyan-500/5 border border-cyan-500/15 text-xs font-body text-cyan-300 space-y-1">
                <p>• AI generates real CBSE-pattern questions</p>
                <p>• 3 sections: MCQ → Short → Application</p>
                <p>• Timer runs automatically — just like the real exam</p>
              </div>
              <button onClick={generateExam} disabled={!form.class || !form.subject || loading} data-testid="generate-exam-btn"
                className="w-full py-3 rounded-xl bg-cyan-500 hover:bg-cyan-400 disabled:opacity-40 text-black font-heading font-bold flex items-center justify-center gap-2 transition-all">
                {loading ? <><div className="w-4 h-4 border-2 border-black/30 border-t-black rounded-full animate-spin" /> Generating exam...</> : <><Sparkles size={16} /> Generate Mock Exam</>}
              </button>
            </div>

            {history.filter(e => e.completed).length > 0 && (
              <div>
                <h3 className="text-zinc-400 text-sm font-body font-semibold mb-3 uppercase tracking-wider">Recent Scores</h3>
                <div className="space-y-2">
                  {history.filter(e => e.completed).map(e => (
                    <div key={e.exam_id} className={`flex items-center gap-3 p-3 rounded-xl border ${e.score >= 70 ? 'border-green-500/15 bg-green-500/5' : 'border-red-500/15 bg-red-500/5'}`}>
                      <div className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 font-heading font-black text-sm"
                        style={{ background: e.score >= 70 ? '#10b98120' : '#ef444420', color: e.score >= 70 ? '#10b981' : '#ef4444' }}>
                        {e.score}%
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-white text-sm font-body font-medium truncate">{e.title}</p>
                        <p className="text-zinc-600 text-xs font-body">{new Date(e.created_at).toLocaleDateString()}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Weak Area Tracker */}
            {weakAreas?.weak_topics?.length > 0 && (
              <div data-testid="weak-area-tracker">
                <h3 className="text-zinc-400 text-sm font-body font-semibold mb-3 uppercase tracking-wider flex items-center gap-2">
                  <Target size={14} className="text-red-400" /> Weak Areas — Needs Practice
                </h3>
                <div className="p-4 rounded-2xl border border-red-500/15 space-y-3" style={{ background: 'rgba(239,68,68,0.04)' }}>
                  <div className="flex flex-wrap gap-2">
                    {weakAreas.weak_topics.slice(0, 8).map(({ topic, frequency }) => (
                      <span key={topic}
                        className="px-3 py-1 rounded-full text-xs font-body border border-red-500/20 text-red-300"
                        style={{ background: 'rgba(239,68,68,0.07)' }}>
                        {topic}{frequency > 1 && <span className="opacity-50 ml-1">×{frequency}</span>}
                      </span>
                    ))}
                  </div>
                  <p className="text-zinc-600 text-xs font-body">
                    These topics appeared as weak areas across {weakAreas.exam_count} exam{weakAreas.exam_count !== 1 ? 's' : ''}. Focus on them to improve your score.
                  </p>
                </div>
              </div>
            )}
          </motion.div>
        )}

        {phase === 'exam' && exam && (
          <motion.div key="exam" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            {/* Exam header */}
            <div className="flex items-center justify-between mb-4 p-3 glass rounded-xl border border-white/10">
              <div>
                <p className="text-white font-heading font-bold text-sm">{exam.title}</p>
                <p className="text-zinc-500 text-xs font-body">{answeredCount}/{allQs.length} answered</p>
              </div>
              <Timer durationMinutes={exam.duration_minutes} onTimeUp={handleTimeUp} running={timerRunning} />
            </div>

            {/* Progress */}
            <div className="h-1.5 bg-zinc-800 rounded-full overflow-hidden mb-4">
              <motion.div className="h-full bg-gradient-to-r from-cyan-400 to-violet-500 rounded-full"
                animate={{ width: `${(answeredCount / allQs.length) * 100}%` }} />
            </div>

            {/* Section tabs */}
            <div className="flex gap-2 mb-4 overflow-x-auto">
              {exam.sections?.map((sec, i) => (
                <button key={sec.section} onClick={() => setCurrentSection(i)}
                  className={`flex-shrink-0 px-4 py-2 rounded-xl text-sm font-body font-semibold transition-all ${currentSection === i ? 'bg-cyan-500/15 text-cyan-400 border border-cyan-500/30' : 'bg-zinc-900/50 text-zinc-500 border border-white/5 hover:text-zinc-300'}`}>
                  Section {sec.section}
                  <span className="ml-1 text-xs opacity-60">({sec.questions?.length}Q)</span>
                </button>
              ))}
            </div>

            {/* Questions */}
            <div className="space-y-4">
              {exam.sections?.[currentSection]?.questions?.map((q, qi) => (
                <motion.div key={q.id} initial={{ opacity: 0, y: 5 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: qi * 0.03 }}
                  className={`glass-surface rounded-2xl p-4 border transition-all ${answers[q.id] ? 'border-green-500/20' : 'border-white/5'}`}>
                  <div className="flex items-start gap-3 mb-3">
                    <span className="flex-shrink-0 px-2 py-0.5 rounded text-xs font-heading font-bold" style={{ background: '#22d3ee20', color: '#22d3ee' }}>{q.id}</span>
                    <p className="text-white text-sm font-body leading-relaxed flex-1"><MathText text={q.question} /></p>
                    <span className="flex-shrink-0 text-xs text-zinc-600 font-body">[{q.marks}m]</span>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {q.options?.map((opt, oi) => {
                      const letter = opt.charAt(0);
                      const isSel = answers[q.id] === letter;
                      return (
                        <button key={oi} onClick={() => setAnswers(p => ({ ...p, [q.id]: letter }))} data-testid={`mock-opt-${q.id}-${letter}`}
                          className={`text-left px-3 py-2.5 rounded-xl border text-sm font-body transition-all flex items-center gap-2 ${isSel ? 'border-cyan-500/50 bg-cyan-500/10 text-white' : 'border-white/8 bg-zinc-900/30 text-zinc-300 hover:border-white/15'}`}>
                          <span className={`w-5 h-5 rounded-full border flex-shrink-0 flex items-center justify-center text-xs font-bold ${isSel ? 'border-cyan-400 text-cyan-400' : 'border-zinc-600 text-zinc-500'}`}>{letter}</span>
                          <span className="flex-1">{opt.slice(3)}</span>
                        </button>
                      );
                    })}
                  </div>
                </motion.div>
              ))}
            </div>

            {/* Submit */}
            <div className="mt-6 flex items-center justify-between">
              <p className="text-zinc-600 text-sm font-body">{allQs.length - answeredCount} questions remaining</p>
              <button onClick={submitExam} disabled={loading} data-testid="submit-exam-btn"
                className="px-6 py-3 rounded-xl bg-cyan-500 hover:bg-cyan-400 disabled:opacity-50 text-black font-heading font-bold transition-all flex items-center gap-2">
                {loading ? <div className="w-4 h-4 border-2 border-black/30 border-t-black rounded-full animate-spin" /> : <><CheckCircle size={16} /> Submit Exam</>}
              </button>
            </div>
          </motion.div>
        )}

        {phase === 'result' && result && (
          <motion.div key="result" initial={{ opacity: 0, scale: 0.97 }} animate={{ opacity: 1, scale: 1 }}>
            {/* Score card */}
            <div className="text-center py-8 glass rounded-2xl border mb-5"
              style={{ borderColor: result.score >= 70 ? '#10b98130' : '#ef444430' }}>
              <div className="text-7xl font-heading font-black mb-2"
                style={{ color: result.score >= 90 ? '#10b981' : result.score >= 70 ? '#22d3ee' : result.score >= 50 ? '#f59e0b' : '#ef4444' }}>
                {result.score}%
              </div>
              <p className="text-white font-heading font-bold text-xl mb-1">
                {result.score >= 90 ? 'Outstanding Performance!' : result.score >= 70 ? 'Well Done!' : result.score >= 50 ? 'Good Effort!' : 'Keep Practicing!'}
              </p>
              <p className="text-zinc-500 font-body text-sm">{result.earned_marks}/{result.total_marks} marks</p>
              <div className="flex items-center justify-center gap-1.5 mt-3">
                <Zap size={16} className="text-amber-400" />
                <span className="text-amber-400 font-heading font-bold">+{result.xp_earned} XP Earned!</span>
              </div>
            </div>

            {/* Section breakdown */}
            <div className="grid sm:grid-cols-3 gap-3 mb-5">
              {result.section_results?.map(s => (
                <div key={s.section} className="glass-surface rounded-xl p-4 border border-white/5 text-center">
                  <p className="text-zinc-500 text-xs font-body mb-1">Section {s.section}</p>
                  <p className="text-white text-xl font-heading font-black">{s.percentage}%</p>
                  <p className="text-zinc-600 text-xs font-body">{s.marks_earned}/{s.marks_total} marks</p>
                  <div className="h-1 bg-zinc-800 rounded-full overflow-hidden mt-2">
                    <div className="h-full rounded-full" style={{ width: `${s.percentage}%`, background: s.percentage >= 70 ? '#10b981' : '#ef4444' }} />
                  </div>
                </div>
              ))}
            </div>

            {/* Weak topics */}
            {result.weak_topics?.length > 0 && (
              <div className="glass-surface rounded-xl p-4 border border-orange-500/15 mb-5">
                <div className="flex items-center gap-2 mb-2">
                  <AlertCircle size={16} className="text-orange-400" />
                  <p className="text-white font-body font-semibold text-sm">Areas to Improve</p>
                </div>
                <div className="flex flex-wrap gap-2 mb-3">
                  {result.weak_topics.map(t => (
                    <span key={t} className="px-2.5 py-1 rounded-full text-xs font-body border border-orange-500/20 bg-orange-500/8 text-orange-300">{t}</span>
                  ))}
                </div>
                {!followUp && (
                  <button onClick={startFollowUp} disabled={followUpLoading} data-testid="start-followup-btn"
                    className="w-full py-2.5 rounded-xl bg-orange-500/15 hover:bg-orange-500/25 border border-orange-500/30 text-orange-300 font-heading font-bold text-sm flex items-center justify-center gap-2 transition-all disabled:opacity-50">
                    {followUpLoading ? <><div className="w-4 h-4 border-2 border-orange-300/30 border-t-orange-300 rounded-full animate-spin" /> Crafting adaptive practice...</> : <><Target size={14} /> Practice Weak Areas (5 Qs)</>}
                  </button>
                )}
              </div>
            )}

            {/* Follow-up quiz */}
            {followUp?.quiz && !followUp.submitted && (
              <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
                className="glass rounded-2xl p-5 border border-orange-500/20 mb-5 space-y-4" data-testid="followup-quiz">
                <div className="flex items-center gap-2">
                  <Target size={18} className="text-orange-400" />
                  <p className="text-white font-heading font-bold">{followUp.quiz.title}</p>
                </div>
                {followUp.quiz.questions?.map((q, qi) => (
                  <div key={qi} className="p-3 rounded-xl bg-zinc-900/40 border border-white/5">
                    <p className="text-white text-sm font-body leading-relaxed mb-2.5">
                      <span className="text-orange-400 font-heading font-bold mr-2">{qi + 1}.</span><MathText text={q.question} />
                    </p>
                    <div className="grid sm:grid-cols-2 gap-2">
                      {q.options?.map((opt, oi) => {
                        const letter = opt.charAt(0);
                        const isSel = followUp.answers[String(qi)] === letter;
                        return (
                          <button key={oi} data-testid={`followup-opt-${qi}-${letter}`}
                            onClick={() => setFollowUp(p => ({ ...p, answers: { ...p.answers, [String(qi)]: letter } }))}
                            className={`text-left px-3 py-2 rounded-lg border text-sm font-body flex items-center gap-2 transition-all ${isSel ? 'border-orange-400/60 bg-orange-500/15 text-white' : 'border-white/8 bg-zinc-900/30 text-zinc-300 hover:border-white/15'}`}>
                            <span className={`w-5 h-5 rounded-full border flex-shrink-0 flex items-center justify-center text-xs font-bold ${isSel ? 'border-orange-400 text-orange-400' : 'border-zinc-600 text-zinc-500'}`}>{letter}</span>
                            <span className="flex-1">{opt.slice(3)}</span>
                          </button>
                        );
                      })}
                    </div>
                  </div>
                ))}
                <button onClick={submitFollowUp} disabled={followUpLoading || Object.keys(followUp.answers).length === 0} data-testid="submit-followup-btn"
                  className="w-full py-2.5 rounded-xl bg-orange-500 hover:bg-orange-400 text-black font-heading font-bold text-sm transition-all disabled:opacity-40 flex items-center justify-center gap-2">
                  {followUpLoading ? <div className="w-4 h-4 border-2 border-black/30 border-t-black rounded-full animate-spin" /> : <><CheckCircle size={14} /> Submit Practice Quiz</>}
                </button>
              </motion.div>
            )}

            {followUp?.submitted && (
              <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
                className="glass rounded-2xl p-5 border border-orange-500/20 mb-5 text-center" data-testid="followup-result">
                <div className="text-5xl font-heading font-black mb-2"
                  style={{ color: followUp.submitted.score >= 80 ? '#10b981' : followUp.submitted.score >= 60 ? '#f59e0b' : '#ef4444' }}>
                  {followUp.submitted.score}%
                </div>
                <p className="text-white font-heading font-bold mb-1">
                  {followUp.submitted.score >= 80 ? 'Mastered!' : followUp.submitted.score >= 60 ? 'Getting Stronger!' : 'Keep Practicing!'}
                </p>
                <p className="text-zinc-500 text-sm font-body mb-3">{followUp.submitted.correct_count}/{followUp.submitted.total_questions} correct</p>
                <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-amber-400/15 border border-amber-400/30">
                  <Zap size={14} className="text-amber-400" />
                  <span className="text-amber-400 font-heading font-bold text-sm">+{followUp.submitted.xp_earned} XP</span>
                </div>
              </motion.div>
            )}

            <button onClick={reset} data-testid="new-exam-btn"
              className="w-full py-3 rounded-xl glass border border-white/10 hover:border-white/20 text-white font-heading font-bold flex items-center justify-center gap-2 transition-all">
              <RotateCcw size={16} /> Take Another Exam
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
