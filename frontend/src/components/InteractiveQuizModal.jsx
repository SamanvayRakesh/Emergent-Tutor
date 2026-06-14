import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, CheckCircle2, XCircle, Trophy, ChevronRight, Loader2, Clock } from 'lucide-react';
import axios from 'axios';
import { MathText } from './MathRenderer';

const API = process.env.REACT_APP_BACKEND_URL;

const QUESTION_TIME_LIMIT = 45; // seconds per question (for timing analytics)

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

  // Track time per question
  useEffect(() => {
    setQStartTime(Date.now());
    setFillInput('');
  }, [currentQ]);

  function recordTime(qIdx) {
    const secs = Math.round((Date.now() - qStartTime) / 1000);
    setTimeSpent(prev => ({ ...prev, [qIdx]: secs }));
  }

  function selectAnswer(answer) {
    recordTime(currentQ);
    setAnswers(prev => ({ ...prev, [currentQ]: answer }));
  }

  function nextQuestion() {
    if (fillInput.trim() && question?.type === 'fill_blank') {
      selectAnswer(fillInput.trim());
    }
    if (currentQ < questions.length - 1) {
      setCurrentQ(q => q + 1);
    }
  }

  async function submitQuiz() {
    // Record time for last question
    recordTime(currentQ);

    // Compile answers
    const submissionAnswers = questions.map((q, i) => ({
      question_index: i,
      selected_answer: answers[i] ?? '',
      time_spent_s: timeSpent[i] ?? 0,
    }));

    setSubmitting(true);
    try {
      const { data } = await axios.post(
        `${API}/api/quiz/${quizData.quiz_id}/submit`,
        { answers: submissionAnswers },
        { withCredentials: true }
      );
      setResults(data);
      setPhase('results');
      if (onComplete) onComplete(data);
    } catch (err) {
      // Compute local score as fallback
      let correct = 0;
      const resultsList = questions.map((q, i) => {
        const userAns = (answers[i] ?? '').toString().toLowerCase().trim();
        const correct_ans = (q.correct_answer ?? '').toString().toLowerCase().trim();
        const isCorrect = userAns === correct_ans ||
          (q.options && q.options.findIndex(o => o.toLowerCase() === userAns) === q.correct_index);
        if (isCorrect) correct++;
        return { question: q.question, correct: isCorrect, user_answer: answers[i], correct_answer: q.correct_answer, explanation: q.explanation };
      });
      const score_pct = Math.round((correct / questions.length) * 100);
      setResults({ score: score_pct, correct_count: correct, total_questions: questions.length, results: resultsList, xp_earned: correct * 5 });
      setPhase('results');
      if (onComplete) onComplete({ score: score_pct, correct_count: correct });
    } finally {
      setSubmitting(false);
    }
  }

  const canAdvance = answers[currentQ] !== undefined || (question?.type === 'fill_blank' && fillInput.trim());
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
                          background: question?.type === 'mcq' ? '#1e3a8a' : question?.type === 'true_false' ? '#14532d' : '#451a03',
                          color: question?.type === 'mcq' ? '#93c5fd' : question?.type === 'true_false' ? '#86efac' : '#fde68a',
                        }}>
                        {question?.type === 'mcq' ? 'Multiple Choice' : question?.type === 'true_false' ? 'True / False' : question?.type === 'fill_blank' ? 'Fill in the Blank' : 'Short Answer'}
                      </span>
                    </div>

                    <p className="text-white text-base font-medium mb-5 leading-relaxed" data-testid="question-text">
                      <MathText text={question?.question || ''} />
                    </p>

                    {/* MCQ options */}
                    {(question?.type === 'mcq') && (
                      <div className="space-y-3" data-testid="mcq-options">
                        {(question?.options || []).map((opt, i) => {
                          const isSelected = answers[currentQ] === opt || answers[currentQ] === i;
                          return (
                            <button
                              key={i}
                              onClick={() => selectAnswer(opt)}
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
                    {question?.type === 'true_false' && (
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
                    {question?.type === 'fill_blank' && (
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
                    {question?.type === 'short_answer' && (
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

          {/* Results phase */}
          {phase === 'results' && results && (
            <div className="p-6" data-testid="quiz-results">
              <div className="text-center mb-6">
                <div className="text-5xl font-black font-heading mb-1" style={{
                  color: results.score >= 80 ? '#22c55e' : results.score >= 60 ? '#fbbf24' : '#ef4444'
                }}>
                  {results.score}%
                </div>
                <p className="text-zinc-400 text-sm">
                  {results.correct_count}/{results.total_questions} correct
                  {results.xp_earned ? ` · +${results.xp_earned} XP` : ''}
                </p>
                <p className="text-zinc-300 text-sm mt-1 font-medium">
                  {results.score >= 80 ? 'Excellent work!' : results.score >= 60 ? 'Good effort!' : 'Keep practising!'}
                </p>
              </div>

              {/* Per-question results */}
              <div className="space-y-3 max-h-64 overflow-y-auto pr-1" data-testid="results-list">
                {(results.results || []).map((r, i) => (
                  <div key={i} className="rounded-xl p-3 border"
                    style={{
                      background: r.correct ? 'rgba(34,197,94,0.07)' : 'rgba(239,68,68,0.07)',
                      borderColor: r.correct ? 'rgba(34,197,94,0.2)' : 'rgba(239,68,68,0.2)',
                    }}>
                    <div className="flex items-start gap-2">
                      {r.correct ? <CheckCircle2 size={16} className="text-green-400 mt-0.5 flex-shrink-0" />
                                 : <XCircle size={16} className="text-red-400 mt-0.5 flex-shrink-0" />}
                      <div className="flex-1 min-w-0">
                        <p className="text-zinc-300 text-xs leading-relaxed"><MathText text={r.question} /></p>
                        {!r.correct && (
                          <p className="text-zinc-500 text-xs mt-1">
                            Correct: <span className="text-green-400"><MathText text={String(r.correct_answer)} /></span>
                          </p>
                        )}
                        {r.explanation && (
                          <p className="text-zinc-500 text-xs mt-1 italic"><MathText text={r.explanation} /></p>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              <button
                onClick={onClose}
                data-testid="close-results-btn"
                className="w-full mt-5 py-3 rounded-xl font-heading font-bold text-white text-sm"
                style={{ background: '#dc2626' }}
              >
                Back to Chat
              </button>
            </div>
          )}
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
