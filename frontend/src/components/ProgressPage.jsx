import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { TrendingUp, BookOpen, Target, Award, Zap, BarChart3, ChevronDown } from 'lucide-react';
import { RadialBarChart, RadialBar, ResponsiveContainer, PieChart, Pie, Cell, Tooltip } from 'recharts';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const COLORS = { Mathematics: '#22d3ee', Science: '#8b5cf6', Physics: '#06b6d4', Chemistry: '#d946ef', Biology: '#10b981', English: '#f59e0b', 'Social Science': '#3b82f6', 'Computer Science': '#ef4444' };

function MasteryBar({ subject, mastery, color }) {
  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between">
        <span className="text-zinc-300 text-sm font-body">{subject}</span>
        <span className="text-sm font-heading font-bold" style={{ color }}>{mastery}%</span>
      </div>
      <div className="h-2 bg-zinc-800 rounded-full overflow-hidden">
        <motion.div className="h-full rounded-full" style={{ background: color }}
          initial={{ width: 0 }} animate={{ width: `${mastery}%` }} transition={{ duration: 1, delay: 0.2 }} />
      </div>
    </div>
  );
}

export default function ProgressPage() {
  const [progress, setProgress] = useState(null);
  const [gamification, setGamification] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      axios.get(`${API}/progress`, { withCredentials: true }),
      axios.get(`${API}/gamification/stats`, { withCredentials: true })
    ]).then(([pRes, gRes]) => {
      setProgress(pRes.data);
      setGamification(gRes.data);
    }).catch(() => {}).finally(() => setLoading(false));
  }, []);

  if (loading) return (
    <div className="p-6 space-y-4">
      {[...Array(4)].map((_, i) => <div key={i} className="h-24 rounded-2xl shimmer bg-zinc-900" />)}
    </div>
  );

  const subjectEntries = Object.entries(progress?.subject_progress || {});
  const pieData = subjectEntries.map(([name, data]) => ({ name, value: data.avg_mastery, color: COLORS[name] || '#22d3ee' }));

  return (
    <div className="p-4 sm:p-6 max-w-5xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl sm:text-3xl font-heading font-black text-white flex items-center gap-3">
          <TrendingUp size={28} className="text-cyan-400" />
          Your Progress
        </h1>
        <p className="text-zinc-500 text-sm font-body mt-1">Track your learning journey</p>
      </div>

      {/* Overview stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {[
          { label: 'Overall Mastery', value: `${progress?.overall_mastery || 0}%`, icon: Target, color: '#22d3ee' },
          { label: 'Chapters Studied', value: progress?.total_chapters_studied || 0, icon: BookOpen, color: '#8b5cf6' },
          { label: 'Total XP', value: gamification?.xp || 0, icon: Zap, color: '#f59e0b' },
          { label: 'Achievements', value: gamification?.achievements?.length || 0, icon: Award, color: '#d946ef' },
        ].map(({ label, value, icon: Icon, color }, i) => (
          <motion.div key={label} initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.08 }}
            className="glass-surface rounded-2xl p-4 border border-white/5">
            <div className="p-2 rounded-xl mb-2 inline-block" style={{ background: color + '20' }}>
              <Icon size={18} style={{ color }} />
            </div>
            <p className="text-2xl font-heading font-bold text-white">{value}</p>
            <p className="text-zinc-500 text-xs font-body mt-0.5">{label}</p>
          </motion.div>
        ))}
      </div>

      {/* Subject Progress */}
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

          {/* Pie Chart */}
          {pieData.length > 0 && (
            <motion.div initial={{ opacity: 0, x: 10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.3 }}
              className="glass-surface rounded-2xl p-5 border border-white/5">
              <h2 className="text-white font-heading font-bold mb-4">Progress Distribution</h2>
              <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                  <Pie data={pieData} cx="50%" cy="50%" innerRadius={50} outerRadius={80} dataKey="value">
                    {pieData.map((entry, i) => <Cell key={i} fill={entry.color} />)}
                  </Pie>
                  <Tooltip formatter={(v) => [`${v}%`, 'Mastery']} contentStyle={{ background: '#18181b', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px', color: '#fff' }} />
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
          className="text-center py-16 glass-surface rounded-2xl border border-white/5">
          <BookOpen size={40} className="text-zinc-700 mx-auto mb-3" />
          <p className="text-zinc-400 font-body">No progress tracked yet</p>
          <p className="text-zinc-600 text-sm font-body mt-1">Start AI tutoring sessions to track your mastery</p>
        </motion.div>
      )}

      {/* Weak Topics */}
      {subjectEntries.some(([, d]) => d.weak_topics?.length > 0) && (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }}
          className="glass-surface rounded-2xl p-5 border border-red-500/10">
          <h2 className="text-white font-heading font-bold mb-4 flex items-center gap-2">
            <Target size={18} className="text-red-400" /> Weak Topics (Need Revision)
          </h2>
          <div className="flex flex-wrap gap-2">
            {subjectEntries.flatMap(([subj, data]) =>
              data.weak_topics?.map(t => (
                <span key={`${subj}-${t}`} className="px-3 py-1.5 rounded-full text-xs font-body border border-red-500/20 bg-red-500/8 text-red-300">
                  {subj}: {t}
                </span>
              ))
            )}
          </div>
        </motion.div>
      )}

      {/* Achievements */}
      {gamification?.achievements?.length > 0 && (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.5 }}
          className="glass-surface rounded-2xl p-5 border border-white/5">
          <h2 className="text-white font-heading font-bold mb-4 flex items-center gap-2">
            <Award size={18} className="text-violet-400" /> Achievements Unlocked
          </h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            {gamification.achievements.map(a => (
              <div key={a.id} className="flex items-center gap-3 p-3 rounded-xl border transition-all"
                style={{ background: a.color + '08', borderColor: a.color + '25' }}>
                <div className="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0" style={{ background: a.color + '20' }}>
                  <Award size={18} style={{ color: a.color }} />
                </div>
                <div>
                  <p className="text-white text-sm font-body font-semibold">{a.name}</p>
                  <p className="text-zinc-500 text-xs font-body leading-tight">{a.description}</p>
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      )}
    </div>
  );
}
