import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Trophy, ChevronRight, Loader2 } from 'lucide-react';
import axios from 'axios';
import { MathText } from './MathRenderer';

const API = process.env.REACT_APP_BACKEND_URL;

/**
 * InteractiveQuizModal
 * Opens when the AI decides to quiz the student.
 * Supports: MCQ, True/False, Fill-in-blank, Short answer.
 * On completion: submits to /api/quiz/{quiz_id}/submit and shows score.
 */
export default function InteractiveQuizModal({ quizData, onClose, onComplete }) {
  const [phase, setPhase] = useState('quiz'); // quiz | results
  const [currentQ, setCurrentQ] = useState(0);
  const [answers, setAnswers] = useState({});
  const [timeSpent, setTimeSpent] = useState({}); // questionIndex → seconds
  const [qStartTime, setQStartTime] = useState(Date.now());
  const [submitting, setSubmitting] = useState(false);
  const [results, setResults] = useState(null);
  const [fillInput, setFillInput] = useState('');

  const questions = quizData?.questions || [];
  const question  = questions[currentQ];
  // Infer type from structure if backend didn't include it (MCQ if options exist)
  const qType = question?.type || (question?.options?.length ? 'mcq' : 'short_answer');

  // Track time per question
  useEffect(() => {
    setQStartTime(Date.now());
    setFillInput('');
  }, [currentQ]);

  function recordTime(qIdx) {
    const secs = Math.round((Date.now() - qStartTime) / 1000);
    setTimeSpent(prev => ({ ...prev, [qIdx]: secs }));
  }

  function selectAnswer(answer, optionIndex = null) {
    recordTime(currentQ);
    // For MCQ: store letter (A/B/C/D) if index given, otherwise store the value as-is
    const stored = optionIndex !== null
      ? String.fromCharCode(65 + optionIndex)  // A, B, C, D
      : answer;
    setAnswers(prev => ({ ...prev, [currentQ]: stored }));
  }

  function nextQuestion() {
    if (fillInput.trim() && ['fill_blank', 'short_answer'].includes(qType)) {
      selectAnswer(fillInput.trim());
    }
    if (currentQ < questions.length - 1) {
      setCurrentQ(q => q + 1);
    }
  }

  async function submitQuiz() {
    // Record time for last question
    recordTime(currentQ);

    // Convert answers to dict format expected by backend {index: letter/answer}
    const answersDict = {};
    questions.forEach((q, i) => {
      const ans = answers[i];
      if (ans !== undefined && ans !== null) {
        // For MCQ: store only the first char (letter) to match backend scoring
        answersDict[String(i)] = typeof ans === 'string' && ans.length > 1 && ans.match(/^[A-D]/)
          ? ans.charAt(0)
          : String(ans);
      } else {
        answersDict[String(i)] = '';
      }
    });

    setSubmitting(true);
    try {
      const { data } = await axios.post(
        `${API}/api/quiz/${quizData.quiz_id}/submit`,
        { answers: answersDict },
        { withCredentials: true }
      );
      // Normalize: backend returns is_correct, display layer uses correct
      const normalized = {
        ...data,
        results: (data.results || []).map(r => ({ ...r, correct: r.is_correct ?? r.correct })),
      };
      setResults(normalized);
      setPhase('results');
      if (onComplete) onComplete(normalized);
    } catch (err) {
      // Compute local score as fallback
      let correct = 0;
      const resultsList = questions.map((q, i) => {
        const userAns = (answers[i] ?? '').toString().toLowerCase().trim();
        const correct_ans = (q.correct ?? q.correct_answer ?? '').toString().toLowerCase().trim();
        const isCorrect = userAns === correct_ans ||
          (q.options && q.options.findIndex(o => o.toLowerCase() === userAns) === q.correct_index);
        if (isCorrect) correct++;
        return { question: q.question, correct: isCorrect, user_answer: answers[i], correct_answer: q.correct ?? q.correct_answer, explanation: q.explanation };
      });
      const score_pct = Math.round((correct / questions.length) * 100);
      const fallbackResults = { score: score_pct, correct_count: correct, total_questions: questions.length, results: resultsList, xp_earned: correct * 5 };
      setResults(fallbackResults);
      setPhase('results');
      if (onComplete) onComplete(fallbackResults);
    } finally {
      setSubmitting(false);
    }
  }

  const canAdvance = answers[currentQ] !== undefined || (['fill_blank', 'short_answer'].includes(qType) && fillInput.trim());
  const isLastQ    = currentQ === questions.length - 1;
  const answered   = Object.keys(answers).length;
  const progress   = ((answered) / questions.length) * 100;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 flex items-center justify-center p-4"
        style={{ background: 'rgba(0,0,0,0.85)', backdropFilter: 'blur(12px)' }}
        data-testid="quiz-modal"
      >
        <motion.div
          initial={{ scale: 0.92, y: 20 }}
          animate={{ scale: 1, y: 0 }}
          exit={{ scale: 0.92, y: 20 }}
          className="w-full max-w-2xl rounded-2xl overflow-hidden"
          style={{ background: '#0f0f17', border: '1px solid rgba(255,255,255,0.08)' }}
        >
          {phase === 'quiz' && (
            <>
              {/* Header */}
              <div className="flex items-center justify-between px-6 py-4 border-b border-white/5">
                <div>
                  <h2 className="text-white font-heading font-bold text-lg" data-testid="quiz-title">
                    {quizData?.topic || 'Quick Quiz'}
                  </h2>
                  <p className="text-zinc-500 text-xs mt-0.5">
                    Question {currentQ + 1} of {questions.length}
                  </p>
                </div>
                <button onClick={onClose} className="text-zinc-500 hover:text-white transition-colors p-1">
                  <X size={20} />
                </button>
              </div>

              {/* Progress bar */}
              <div className="h-1 bg-white/5">
                <motion.div
                  className="h-full rounded-full"
                  style={{ background: '#dc2626', width: `${((currentQ) / questions.length) * 100}%` }}
                  animate={{ width: `${((currentQ) / questions.length) * 100}%` }}
                />
              </div>

              {/* Question */}
              <div className="p-6">
                <AnimatePresence mode="wait">
                  <motion.div
                    key={currentQ}
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -20 }}
                    transition={{ duration: 0.2 }}
                  >
                    <div className="mb-2">
                      <span className="text-xs font-semibold px-2 py-1 rounded-md"
                        style={{
                          background: qType === 'mcq' ? '#1e3a8a' : qType === 'true_false' ? '#14532d' : '#451a03',
                          color: qType === 'mcq' ? '#93c5fd' : qType === 'true_false' ? '#86efac' : '#fde68a',
                        }}>
                        {qType === 'mcq' ? 'Multiple Choice' : qType === 'true_false' ? 'True / False' : qType === 'fill_blank' ? 'Fill in the Blank' : 'Short Answer'}
                      </span>
                    </div>

                    <p className="text-white text-base font-medium mb-5 leading-relaxed" data-testid="question-text">
                      <MathText text={question?.question || ''} />
                    </p>

                    {/* MCQ options */}
                    {qType === 'mcq' && (
                      <div className="space-y-3" data-testid="mcq-options">
                        {(question?.options || []).map((opt, i) => {
                          const letter = String.fromCharCode(65 + i);
                          const isSelected = answers[currentQ] === letter;
                          return (
                            <button
                              key={i}
                              onClick={() => selectAnswer(opt, i)}
                              data-testid={`option-${i}`}
                              className="w-full text-left px-4 py-3 rounded-xl text-sm transition-all duration-150 border"
                              style={{
                                background: isSelected ? 'rgba(220,38,38,0.15)' : 'rgba(255,255,255,0.03)',
                                borderColor: isSelected ? '#dc2626' : 'rgba(255,255,255,0.08)',
                                color: isSelected ? '#f87171' : '#d4d4d8',
                              }}
                            >
                              <span className="font-semibold mr-3 text-zinc-500">
                                {String.fromCharCode(65 + i)}.
                              </span>
                              <MathText text={opt} />
                            </button>
                          );
                        })}
                      </div>
                    )}

                    {/* True / False */}
                    {qType === 'true_false' && (
                      <div className="flex gap-3" data-testid="true-false-options">
                        {['True', 'False'].map(opt => {
                          const isSelected = answers[currentQ] === opt;
                          return (
                            <button
                              key={opt}
                              onClick={() => selectAnswer(opt)}
                              data-testid={`tf-${opt.toLowerCase()}`}
                              className="flex-1 py-4 rounded-xl font-heading font-bold text-sm transition-all border"
                              style={{
                                background: isSelected ? (opt === 'True' ? 'rgba(34,197,94,0.15)' : 'rgba(239,68,68,0.15)') : 'rgba(255,255,255,0.03)',
                                borderColor: isSelected ? (opt === 'True' ? '#22c55e' : '#ef4444') : 'rgba(255,255,255,0.08)',
                                color: isSelected ? (opt === 'True' ? '#86efac' : '#fca5a5') : '#a1a1aa',
                              }}
                            >
                              {opt}
                            </button>
                          );
                        })}
                      </div>
                    )}

                    {/* Fill in blank */}
                    {qType === 'fill_blank' && (
                      <input
                        type="text"
                        placeholder="Type your answer…"
                        value={fillInput}
                        onChange={e => setFillInput(e.target.value)}
                        onKeyDown={e => e.key === 'Enter' && canAdvance && (isLastQ ? submitQuiz() : nextQuestion())}
                        data-testid="fill-blank-input"
                        className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white text-sm placeholder:text-zinc-600 focus:outline-none focus:border-blue-500"
                        autoFocus
                      />
                    )}

                    {/* Short answer */}
                    {qType === 'short_answer' && (
                      <textarea
                        placeholder="Write your answer…"
                        value={fillInput}
                        onChange={e => setFillInput(e.target.value)}
                        rows={3}
                        data-testid="short-answer-input"
                        className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white text-sm placeholder:text-zinc-600 focus:outline-none focus:border-blue-500 resize-none"
                        autoFocus
                      />
                    )}
                  </motion.div>
                </AnimatePresence>

                {/* Nav buttons */}
                <div className="flex justify-between items-center mt-6">
                  <button
                    onClick={() => currentQ > 0 && setCurrentQ(q => q - 1)}
                    className="text-zinc-500 text-sm hover:text-white transition-colors"
                    disabled={currentQ === 0}
                  >
                    ← Back
                  </button>
                  {isLastQ ? (
                    <button
                      onClick={submitQuiz}
                      disabled={!canAdvance || submitting}
                      data-testid="submit-quiz-btn"
                      className="px-6 py-2.5 rounded-xl font-heading font-bold text-sm text-white flex items-center gap-2 disabled:opacity-40 transition-all"
                      style={{ background: canAdvance ? '#dc2626' : '#374151' }}
                    >
                      {submitting ? <Loader2 size={16} className="animate-spin" /> : <Trophy size={16} />}
                      {submitting ? 'Scoring…' : 'Submit Quiz'}
                    </button>
                  ) : (
                    <button
                      onClick={nextQuestion}
                      disabled={!canAdvance}
                      data-testid="next-question-btn"
                      className="px-5 py-2.5 rounded-xl font-heading font-bold text-sm text-white flex items-center gap-2 disabled:opacity-40 transition-all"
                      style={{ background: canAdvance ? '#2563eb' : '#374151' }}
                    >
                      Next <ChevronRight size={16} />
                    </button>
                  )}
                </div>
              </div>
            </>
          )}

          {/* Results phase — brief score only; full validation is in the chat */}
          {phase === 'results' && results && (
            <div className="p-8 text-center" data-testid="quiz-results">
              <Trophy size={44} className="mx-auto mb-4 text-amber-400" />
              <div
                className="text-6xl font-black font-heading mb-2"
                style={{ color: results.score >= 80 ? '#22c55e' : results.score >= 60 ? '#fbbf24' : '#ef4444' }}
              >
                {results.score}%
              </div>
              <p className="text-zinc-300 text-base font-medium mb-1">
                {results.correct_count}/{results.total_questions} correct
                {results.xp_earned ? ` · +${results.xp_earned} XP` : ''}
              </p>
              <p className="text-zinc-500 text-sm mb-2">
                {results.score >= 80 ? 'Excellent work!' : results.score >= 60 ? 'Good effort!' : 'Keep practising!'}
              </p>
              <p className="text-zinc-600 text-xs mb-6 flex items-center justify-center gap-1.5">
                <Loader2 size={12} className="animate-spin text-cyan-400" />
                <span className="text-cyan-500">AI Tutor is reviewing your answers…</span>
              </p>
              <button
                onClick={onClose}
                data-testid="close-results-btn"
                className="w-full py-3 rounded-xl font-heading font-bold text-white text-sm transition-all hover:opacity-90"
                style={{ background: '#dc2626' }}
              >
                Back to Chat &amp; See Feedback
              </button>
            </div>
          )}
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
