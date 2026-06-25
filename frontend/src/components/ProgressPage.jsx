import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { TrendingUp, BookOpen, Target, Award, Zap, BarChart3, Flame, Trophy, CheckCircle2, XCircle, Clock } from 'lucide-react';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid } from 'recharts';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const COLORS = {
  Mathematics: '#22d3ee', Science: '#8b5cf6', Physics: '#06b6d4',
  Chemistry: '#d946ef', Biology: '#10b981', English: '#f59e0b',
  'Social Science': '#3b82f6', 'Computer Science': '#ef4444'
};

function StatCard({ label, value, icon: Icon, color, delay = 0 }) {
  return (
    <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} transition={{ delay }}
      className="glass-surface rounded-2xl p-4 border border-white/5">
      <div className="p-2 rounded-xl mb-2 inline-block" style={{ background: color + '20' }}>
        <Icon size={18} style={{ color }} />
      </div>
      <p className="text-2xl font-heading font-bold text-white">{value}</p>
      <p className="text-zinc-500 text-xs font-body mt-0.5">{label}</p>
    </motion.div>
  );
}

function MasteryBar({ subject, mastery, color }) {
  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between">
        <span className="text-zinc-300 text-sm font-body">{subject}</span>
        <span className="text-sm font-heading font-bold" style={{ color }}>{mastery}%</span>
      </div>
      <div className="h-2 bg-zinc-800 rounded-full overflow-hidden">
        <motion.div className="h-full rounded-full" style={{ background: color }}
          initial={{ width: 0 }} animate={{ width: `${mastery}%` }} transition={{ duration: 0.9, delay: 0.2 }} />
      </div>
    </div>
  );
}

export default function ProgressPage() {
  const [progress, setProgress]       = useState(null);
  const [gamification, setGamification] = useState(null);
  const [quizHistory, setQuizHistory] = useState([]);
  const [loading, setLoading]         = useState(true);

  useEffect(() => {
    Promise.all([
      axios.get(`${API}/progress`, { withCredentials: true }),
      axios.get(`${API}/gamification/stats`, { withCredentials: true }),
      axios.get(`${API}/quiz/history`, { withCredentials: true }).catch(() => ({ data: [] })),
    ]).then(([pRes, gRes, qRes]) => {
      setProgress(pRes.data);
      setGamification(gRes.data);
      setQuizHistory(Array.isArray(qRes.data) ? qRes.data.filter(q => q.completed) : []);
    }).catch(() => {}).finally(() => setLoading(false));
  }, []);

  if (loading) return (
    <div className="p-6 space-y-4">
      {[...Array(4)].map((_, i) => <div key={i} className="h-24 rounded-2xl shimmer bg-zinc-900" />)}
    </div>
  );

  const subjectEntries = Object.entries(progress?.subject_progress || {});
  const pieData = subjectEntries.map(([name, data]) => ({ name, value: data.avg_mastery, color: COLORS[name] || '#22d3ee' }));

  // Quiz accuracy trend (last 8 quizzes)
  const recentQuizzes = quizHistory.slice(0, 8).reverse().map((q, i) => ({
    name: `Q${i + 1}`,
    score: q.score || 0,
    topic: q.topic || 'Quiz',
    subject: q.subject || '',
  }));

  // Accuracy stat from quizzes
  const avgAccuracy = quizHistory.length
    ? Math.round(quizHistory.reduce((s, q) => s + (q.score || 0), 0) / quizHistory.length)
    : 0;

  const streak        = gamification?.streak || 0;
  const longestStreak = gamification?.longest_streak || 0;

  // Milestones
  const milestones = [
    { id: 'first_session', label: 'First Session', desc: 'Started your learning journey', met: (gamification?.session_count || 0) >= 1, color: '#22d3ee' },
    { id: 'quiz_starter', label: 'Quiz Starter', desc: 'Completed first quiz', met: (gamification?.quiz_count || 0) >= 1, color: '#10b981' },
    { id: 'quiz_5', label: 'Quiz Pro', desc: '5 quizzes completed', met: (gamification?.quiz_count || 0) >= 5, color: '#f59e0b' },
    { id: 'streak_3', label: '3-Day Streak', desc: 'Studied 3 days in a row', met: streak >= 3, color: '#ef4444' },
    { id: 'streak_7', label: 'Week Warrior', desc: '7-day study streak', met: streak >= 7, color: '#8b5cf6' },
    { id: 'sessions_10', label: 'Dedicated Learner', desc: '10 AI tutor sessions', met: (gamification?.session_count || 0) >= 10, color: '#d946ef' },
    { id: 'xp_500', label: 'Rising Star', desc: 'Earned 500 XP', met: (gamification?.xp || 0) >= 500, color: '#06b6d4' },
    { id: 'xp_1000', label: 'Champion', desc: 'Earned 1000 XP', met: (gamification?.xp || 0) >= 1000, color: '#fbbf24' },
  ];
  const metCount = milestones.filter(m => m.met).length;

  return (
    <div className="p-4 sm:p-6 max-w-5xl mx-auto space-y-6" data-testid="progress-page">
      <div>
        <h1 className="text-2xl sm:text-3xl font-heading font-black text-white flex items-center gap-3">
          <TrendingUp size={28} className="text-cyan-400" /> Your Progress
        </h1>
        <p className="text-zinc-500 text-sm font-body mt-1">Track your learning journey</p>
      </div>

      {/* ── Core stats ───────────────────────────────────────────────── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <StatCard label="Overall Mastery" value={`${progress?.overall_mastery || 0}%`} icon={Target} color="#22d3ee" delay={0} />
        <StatCard label="Chapters Studied" value={progress?.total_chapters_studied || 0} icon={BookOpen} color="#8b5cf6" delay={0.05} />
        <StatCard label="Total XP" value={gamification?.xp || 0} icon={Zap} color="#f59e0b" delay={0.1} />
        <StatCard label="Quiz Accuracy" value={`${avgAccuracy}%`} icon={Trophy} color="#10b981" delay={0.15} />
      </div>

      {/* ── Streak cards ─────────────────────────────────────────────── */}
      <div className="grid grid-cols-2 gap-3">
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}
          className="glass-surface rounded-2xl p-4 border flex items-center gap-4"
          style={{ borderColor: streak >= 3 ? 'rgba(239,68,68,0.3)' : 'rgba(255,255,255,0.05)', background: streak >= 3 ? 'rgba(239,68,68,0.05)' : undefined }}>
          <Flame size={32} style={{ color: streak >= 3 ? '#ef4444' : '#52525b' }} />
          <div>
            <p className="text-3xl font-heading font-black text-white">{streak}</p>
            <p className="text-zinc-500 text-xs font-body">Current Streak</p>
          </div>
        </motion.div>
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.25 }}
          className="glass-surface rounded-2xl p-4 border border-white/5 flex items-center gap-4">
          <Award size={32} className="text-amber-400" />
          <div>
            <p className="text-3xl font-heading font-black text-white">{longestStreak}</p>
            <p className="text-zinc-500 text-xs font-body">Longest Streak</p>
          </div>
        </motion.div>
      </div>

      {/* ── Subject mastery + pie ─────────────────────────────────────── */}
      {subjectEntries.length > 0 ? (
        <div className="grid lg:grid-cols-2 gap-5">
          <motion.div initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.2 }}
            className="glass-surface rounded-2xl p-5 border border-white/5">
            <h2 className="text-white font-heading font-bold mb-4 flex items-center gap-2">
              <BarChart3 size={18} className="text-cyan-400" /> Subject Mastery
            </h2>
            <div className="space-y-4">
              {subjectEntries.map(([subj, data]) => (
                <MasteryBar key={subj} subject={subj} mastery={data.avg_mastery} color={COLORS[subj] || '#22d3ee'} />
              ))}
            </div>
          </motion.div>

          {pieData.length > 0 && (
            <motion.div initial={{ opacity: 0, x: 10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.3 }}
              className="glass-surface rounded-2xl p-5 border border-white/5">
              <h2 className="text-white font-heading font-bold mb-4">Progress Distribution</h2>
              <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                  <Pie data={pieData} cx="50%" cy="50%" innerRadius={50} outerRadius={80} dataKey="value">
                    {pieData.map((entry, i) => <Cell key={entry.name || i} fill={entry.color} />)}
                  </Pie>
                  <Tooltip formatter={(v) => [`${v}%`, 'Mastery']}
                    contentStyle={{ background: '#18181b', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px', color: '#fff' }} />
                </PieChart>
              </ResponsiveContainer>
              <div className="flex flex-wrap gap-2 mt-2">
                {pieData.map(e => (
                  <div key={e.name} className="flex items-center gap-1.5 text-xs font-body">
                    <div className="w-2.5 h-2.5 rounded-full" style={{ background: e.color }} />
                    <span className="text-zinc-400">{e.name}</span>
                  </div>
                ))}
              </div>
            </motion.div>
          )}
        </div>
      ) : (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}
          className="text-center py-12 glass-surface rounded-2xl border border-white/5">
          <BookOpen size={40} className="text-zinc-700 mx-auto mb-3" />
          <p className="text-zinc-400 font-body">No progress tracked yet</p>
          <p className="text-zinc-600 text-sm font-body mt-1">Start AI tutoring sessions to see your mastery here</p>
        </motion.div>
      )}

      {/* ── Quiz performance history ──────────────────────────────────── */}
      {recentQuizzes.length > 0 && (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.35 }}
          className="glass-surface rounded-2xl p-5 border border-white/5" data-testid="quiz-history-chart">
          <h2 className="text-white font-heading font-bold mb-4 flex items-center gap-2">
            <Trophy size={18} className="text-amber-400" /> Quiz Performance
          </h2>
          <ResponsiveContainer width="100%" height={160}>
            <BarChart data={recentQuizzes} barSize={28}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis dataKey="name" tick={{ fill: '#71717a', fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis domain={[0, 100]} tick={{ fill: '#71717a', fontSize: 11 }} axisLine={false} tickLine={false} />
              <Tooltip
                formatter={(v) => [`${v}%`, 'Score']}
                contentStyle={{ background: '#18181b', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '10px', color: '#fff', fontSize: 12 }}
                labelFormatter={(_, payload) => payload?.[0]?.payload?.topic || ''}
              />
              <Bar dataKey="score" radius={[6, 6, 0, 0]}
                fill="url(#quizBarGrad)" />
              <defs>
                <linearGradient id="quizBarGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#22d3ee" />
                  <stop offset="100%" stopColor="#7c3aed" />
                </linearGradient>
              </defs>
            </BarChart>
          </ResponsiveContainer>
          <div className="mt-3 grid grid-cols-3 gap-3 text-center">
            <div>
              <p className="text-xl font-heading font-bold text-white">{quizHistory.length}</p>
              <p className="text-zinc-600 text-xs font-body">Quizzes Taken</p>
            </div>
            <div>
              <p className="text-xl font-heading font-bold" style={{ color: '#22d3ee' }}>{avgAccuracy}%</p>
              <p className="text-zinc-600 text-xs font-body">Avg Accuracy</p>
            </div>
            <div>
              <p className="text-xl font-heading font-bold text-white">{quizHistory.filter(q => (q.score || 0) >= 80).length}</p>
              <p className="text-zinc-600 text-xs font-body">Scores ≥ 80%</p>
            </div>
          </div>
        </motion.div>
      )}

      {/* ── Weak topics ──────────────────────────────────────────────── */}
      {subjectEntries.some(([, d]) => d.weak_topics?.length > 0) && (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }}
          className="glass-surface rounded-2xl p-5 border border-red-500/10">
          <h2 className="text-white font-heading font-bold mb-4 flex items-center gap-2">
            <Target size={18} className="text-red-400" /> Weak Topics — Needs Revision
          </h2>
          <div className="flex flex-wrap gap-2">
            {subjectEntries.flatMap(([subj, data]) =>
              (data.weak_topics || []).map(t => (
                <span key={`${subj}-${t}`} className="px-3 py-1.5 rounded-full text-xs font-body border border-red-500/20 text-red-300"
                  style={{ background: 'rgba(239,68,68,0.07)' }}>
                  {subj}: {t}
                </span>
              ))
            )}
          </div>
        </motion.div>
      )}

      {/* ── Milestones ───────────────────────────────────────────────── */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.45 }}
        className="glass-surface rounded-2xl p-5 border border-white/5" data-testid="milestones-section">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-white font-heading font-bold flex items-center gap-2">
            <Award size={18} className="text-violet-400" /> Milestones
          </h2>
          <span className="text-zinc-500 text-xs font-body">{metCount}/{milestones.length} unlocked</span>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {milestones.map(m => (
            <div key={m.id}
              className={`p-3 rounded-xl border transition-all ${m.met ? 'border-white/15' : 'border-white/5 opacity-50'}`}
              style={{ background: m.met ? m.color + '0f' : 'rgba(255,255,255,0.02)' }}>
              <div className="w-8 h-8 rounded-lg flex items-center justify-center mb-2"
                style={{ background: m.met ? m.color + '20' : 'rgba(255,255,255,0.05)' }}>
                {m.met
                  ? <CheckCircle2 size={16} style={{ color: m.color }} />
                  : <Clock size={16} className="text-zinc-600" />}
              </div>
              <p className="text-white text-xs font-body font-semibold leading-tight">{m.label}</p>
              <p className="text-zinc-600 text-xs font-body mt-0.5 leading-tight">{m.desc}</p>
            </div>
          ))}
        </div>
      </motion.div>
    </div>
  );
}
