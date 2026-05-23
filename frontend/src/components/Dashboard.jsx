import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { MessageSquare, BookOpen, Trophy, TrendingUp, Flame, Zap, Star, ArrowRight, Play, Calendar, Target, RefreshCw, Sparkles, Compass, FileText } from 'lucide-react';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';
import StreakReminderBanner from './StreakReminderBanner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const SUBJECT_COLORS = {
  Mathematics: '#22d3ee', Science: '#8b5cf6', Physics: '#06b6d4',
  Chemistry: '#d946ef', Biology: '#10b981', English: '#f59e0b',
  'Social Science': '#3b82f6', 'Computer Science': '#ef4444'
};

// Map recommendation icon/action names to lucide icons + accent colours
const REC_META = {
  play:    { Icon: Play,        color: '#22d3ee' },
  refresh: { Icon: RefreshCw,   color: '#f59e0b' },
  target:  { Icon: Target,      color: '#ef4444' },
  trophy:  { Icon: FileText,    color: '#8b5cf6' },
  book:    { Icon: Compass,     color: '#10b981' },
};

function MissionCard({ rec, onClick, delay }) {
  const meta = REC_META[rec.icon] || { Icon: Sparkles, color: '#22d3ee' };
  const { Icon, color } = meta;
  return (
    <motion.button
      initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay }}
      onClick={onClick} data-testid={`mission-${rec.type}`}
      className="group relative overflow-hidden rounded-2xl p-4 border text-left transition-all hover:-translate-y-0.5 card-3d"
      style={{ background: color + '0d', borderColor: color + '30' }}>
      <div className="absolute -top-8 -right-8 w-24 h-24 rounded-full blur-2xl opacity-40 pointer-events-none" style={{ background: color }} />
      <div className="relative z-10 flex items-start gap-3">
        <div className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0" style={{ background: color + '25', border: `1px solid ${color}40` }}>
          <Icon size={18} style={{ color }} />
        </div>
        <div className="min-w-0 flex-1">
          <p className="text-white font-heading font-bold text-sm leading-tight mb-1">{rec.title}</p>
          <p className="text-zinc-400 text-xs font-body leading-snug">{rec.description}</p>
        </div>
        <ArrowRight size={14} className="text-zinc-600 group-hover:text-white transition-colors flex-shrink-0 mt-1" />
      </div>
    </motion.button>
  );
}

function StatCard({ icon: Icon, label, value, color, delay = 0 }) {
  return (
    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay }}
      className="glass-surface rounded-2xl p-4 border border-white/5 hover:border-white/10 transition-all card-3d">
      <div className="flex items-center gap-3 mb-2">
        <div className="p-2 rounded-xl" style={{ background: color + '20' }}>
          <Icon size={18} style={{ color }} />
        </div>
        <p className="text-zinc-500 text-sm font-body">{label}</p>
      </div>
      <p className="text-white text-2xl font-heading font-bold">{value}</p>
    </motion.div>
  );
}

export default function Dashboard() {
  const { user } = useAuth();
  const nav = useNavigate();
  const [stats, setStats] = useState(null);
  const [recentSessions, setRecentSessions] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const [statsRes, sessionsRes, recsRes] = await Promise.all([
          axios.get(`${API}/gamification/stats`, { withCredentials: true }),
          axios.get(`${API}/chat/sessions`, { withCredentials: true }),
          axios.get(`${API}/recommendations`, { withCredentials: true })
        ]);
        setStats(statsRes.data);
        setRecentSessions(sessionsRes.data.slice(0, 4));
        setRecommendations(recsRes.data?.recommendations || []);
      } catch {}
      setLoading(false);
    };
    load();
  }, []);

  const handleMissionClick = (rec) => {
    switch (rec.action) {
      case 'chat': {
        const d = rec.data || {};
        if (d.session_id) nav(`/chat/${d.session_id}`);
        else if (d.subject) nav('/chat', { state: { subject: d.subject, chapter: d.chapter, chapterId: d.chapter_id, classLevel: d.class_level } });
        else nav('/chat');
        break;
      }
      case 'quiz': nav('/quiz'); break;
      case 'mock_exam': nav('/mock-exams'); break;
      case 'syllabus': nav('/syllabus'); break;
      default: nav('/chat');
    }
  };

  const hour = new Date().getHours();
  const greeting = hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening';

  if (loading) return (
    <div className="p-6 space-y-4">
      {[...Array(4)].map((_, i) => <div key={i} className="h-20 rounded-2xl shimmer bg-zinc-900" />)}
    </div>
  );

  return (
    <div className="p-4 sm:p-6 max-w-5xl mx-auto space-y-6">
      {/* Streak Reminder Banner — appears when streak is at risk, broken, or active ≥2 days */}
      <StreakReminderBanner />

      {/* Hero greeting */}
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}
        className="relative overflow-hidden rounded-2xl p-6 glass border border-white/5"
        style={{ background: 'linear-gradient(135deg, rgba(34,211,238,0.08), rgba(139,92,246,0.06))' }}>
        <div className="absolute top-0 right-0 w-64 h-64 bg-cyan-500/5 rounded-full blur-3xl pointer-events-none" />
        <div className="flex items-center justify-between">
          <div>
            <p className="text-zinc-400 text-sm font-body mb-1">{greeting},</p>
            <h1 className="text-2xl sm:text-3xl font-heading font-black text-white">{user?.name?.split(' ')[0] || 'Student'}</h1>
            <p className="text-zinc-500 text-sm font-body mt-1">Class {user?.class_level || '9'} • Keep the momentum going!</p>
          </div>
          <div className="hidden sm:flex flex-col items-center gap-1">
            <div className="w-16 h-16 rounded-full bg-gradient-to-br from-cyan-400 to-violet-600 flex items-center justify-center text-black font-heading font-black text-2xl">
              {user?.name?.[0]?.toUpperCase() || 'S'}
            </div>
          </div>
        </div>

        {/* Quick CTA */}
        <button onClick={() => nav('/chat')} data-testid="start-learning-btn"
          className="mt-4 flex items-center gap-2 px-5 py-2.5 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-black font-heading font-bold text-sm transition-all">
          <Play size={16} fill="currentColor" />
          Start AI Tutoring
        </button>
      </motion.div>

      {/* Stats row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <StatCard icon={Zap} label="Total XP" value={stats?.xp || 0} color="#f59e0b" delay={0.1} />
        <StatCard icon={Flame} label="Day Streak" value={stats?.streak || 0} color="#ef4444" delay={0.15} />
        <StatCard icon={MessageSquare} label="AI Sessions" value={stats?.session_count || 0} color="#22d3ee" delay={0.2} />
        <StatCard icon={Trophy} label="Quizzes Done" value={stats?.quiz_count || 0} color="#8b5cf6" delay={0.25} />
      </div>

      {/* Level Progress */}
      {stats && (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}
          className="glass-surface rounded-2xl p-4 border border-white/5">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Star size={18} className="text-amber-400" />
              <span className="text-white font-heading font-bold">Level {stats.level}</span>
            </div>
            <span className="text-zinc-500 text-sm font-body">{stats.xp_in_level} / 500 XP</span>
          </div>
          <div className="h-2 bg-zinc-800 rounded-full overflow-hidden">
            <motion.div className="h-full rounded-full"
              style={{ background: 'linear-gradient(90deg, #f59e0b, #d946ef)' }}
              initial={{ width: 0 }}
              animate={{ width: `${(stats.xp_in_level / 500) * 100}%` }}
              transition={{ duration: 1.2, delay: 0.4 }} />
          </div>
          <p className="text-zinc-600 text-xs font-body mt-2">{stats.xp_to_next} XP to Level {stats.level + 1}</p>
        </motion.div>
      )}

      {/* Today's Missions — AI Recommendations */}
      {recommendations.length > 0 && (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.32 }} data-testid="missions-section">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Sparkles size={18} className="text-fuchsia-400" />
              <h2 className="text-white font-heading font-bold">Today's Missions</h2>
            </div>
            <span className="text-zinc-600 text-xs font-body uppercase tracking-wider">Personalized for you</span>
          </div>
          <div className="grid sm:grid-cols-2 gap-3">
            {recommendations.map((rec, i) => (
              <MissionCard key={rec.type + i} rec={rec} delay={0.4 + i * 0.06} onClick={() => handleMissionClick(rec)} />
            ))}
          </div>
        </motion.div>
      )}

      <div className="grid lg:grid-cols-2 gap-5">
        {/* Daily Challenge */}
        {stats?.daily_challenge && (
          <motion.div initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.35 }}
            className="glass-surface rounded-2xl p-5 border border-cyan-500/15 hover:border-cyan-500/30 transition-all cursor-pointer"
            onClick={() => nav('/quiz')}>
            <div className="flex items-center gap-2 mb-3">
              <Target size={18} className="text-cyan-400" />
              <span className="text-xs font-body uppercase tracking-widest text-cyan-400">Daily Challenge</span>
            </div>
            <h3 className="text-white font-heading font-bold text-lg mb-1">{stats.daily_challenge.topic}</h3>
            <p className="text-zinc-500 text-sm font-body mb-4">Test your knowledge and earn XP</p>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-amber-400/15 border border-amber-400/20">
                <Zap size={14} className="text-amber-400" />
                <span className="text-amber-400 text-sm font-heading font-bold">+{stats.daily_challenge.xp_reward} XP</span>
              </div>
              <div className="flex items-center gap-1 text-cyan-400 text-sm font-body">
                Start Quiz <ArrowRight size={14} />
              </div>
            </div>
          </motion.div>
        )}

        {/* Achievements */}
        {stats?.achievements?.length > 0 && (
          <motion.div initial={{ opacity: 0, x: 10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.4 }}
            className="glass-surface rounded-2xl p-5 border border-white/5">
            <div className="flex items-center gap-2 mb-3">
              <Trophy size={18} className="text-violet-400" />
              <span className="text-xs font-body uppercase tracking-widest text-violet-400">Achievements</span>
            </div>
            <div className="grid grid-cols-2 gap-2">
              {stats.achievements.slice(0, 4).map(a => (
                <div key={a.id} className="flex items-center gap-2 p-2 rounded-xl bg-zinc-900/50">
                  <div className="w-7 h-7 rounded-lg flex items-center justify-center" style={{ background: a.color + '20' }}>
                    <Star size={14} style={{ color: a.color }} />
                  </div>
                  <div>
                    <p className="text-white text-xs font-body font-semibold">{a.name}</p>
                    <p className="text-zinc-600 text-xs font-body leading-tight">{a.description.slice(0, 25)}...</p>
                  </div>
                </div>
              ))}
            </div>
          </motion.div>
        )}
      </div>

      {/* Recent Sessions */}
      {recentSessions.length > 0 && (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.45 }}>
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-white font-heading font-bold">Recent Sessions</h2>
            <button onClick={() => nav('/chat')} className="text-cyan-400 text-sm font-body flex items-center gap-1 hover:text-cyan-300 transition-colors">
              New Chat <ArrowRight size={14} />
            </button>
          </div>
          <div className="grid sm:grid-cols-2 gap-3">
            {recentSessions.map((s, i) => (
              <motion.button key={s.session_id} initial={{ opacity: 0, y: 5 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.5 + i * 0.05 }}
                onClick={() => nav(`/chat/${s.session_id}`)} data-testid={`recent-session-${i}`}
                className="flex items-center gap-3 p-3 rounded-xl glass-surface border border-white/5 hover:border-white/10 transition-all text-left group">
                <div className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0"
                  style={{ background: (SUBJECT_COLORS[s.subject] || '#22d3ee') + '20' }}>
                  <BookOpen size={18} style={{ color: SUBJECT_COLORS[s.subject] || '#22d3ee' }} />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-white text-sm font-body font-semibold truncate">{s.subject}</p>
                  <p className="text-zinc-500 text-xs font-body truncate">{s.chapter}</p>
                </div>
                <ArrowRight size={14} className="text-zinc-700 group-hover:text-zinc-400 transition-colors flex-shrink-0" />
              </motion.button>
            ))}
          </div>
        </motion.div>
      )}

      {/* Quick subjects */}
      {recentSessions.length === 0 && (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }}>
          <h2 className="text-white font-heading font-bold mb-3">Start Learning</h2>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {Object.entries(SUBJECT_COLORS).slice(0, 4).map(([subj, color], i) => (
              <motion.button key={subj} initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: 0.5 + i * 0.05 }}
                onClick={() => nav('/syllabus')} data-testid={`subject-card-${subj}`}
                className="p-4 rounded-2xl border transition-all hover:-translate-y-1 text-left card-3d"
                style={{ background: color + '10', borderColor: color + '30' }}>
                <div className="w-8 h-8 rounded-lg mb-2 flex items-center justify-center" style={{ background: color + '25' }}>
                  <BookOpen size={16} style={{ color }} />
                </div>
                <p className="text-white text-sm font-body font-semibold">{subj}</p>
              </motion.button>
            ))}
          </div>
        </motion.div>
      )}
    </div>
  );
}
