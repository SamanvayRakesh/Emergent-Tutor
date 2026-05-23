import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Trophy, Medal, Crown, Flame, Zap, TrendingUp, Star, Users } from 'lucide-react';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const RANK_COLORS = { 1: { bg: '#fbbf24', glow: 'rgba(251,191,36,0.4)', label: 'gold' }, 2: { bg: '#94a3b8', glow: 'rgba(148,163,184,0.4)', label: 'silver' }, 3: { bg: '#cd7c2f', glow: 'rgba(205,124,47,0.4)', label: 'bronze' } };

function PodiumCard({ entry, height }) {
  const col = RANK_COLORS[entry.rank] || { bg: '#22d3ee', glow: 'rgba(34,211,238,0.2)' };
  return (
    <motion.div initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: entry.rank * 0.1 }}
      className="flex flex-col items-center gap-2">
      <div className="w-14 h-14 rounded-full flex items-center justify-center text-black font-heading font-black text-xl border-2"
        style={{ background: col.bg, borderColor: col.bg, boxShadow: `0 0 20px ${col.glow}` }}>
        {entry.name?.[0]?.toUpperCase()}
      </div>
      <div className="text-center">
        <p className="text-white text-sm font-body font-bold truncate max-w-[80px]">{entry.name?.split(' ')[0]}</p>
        <p className="text-zinc-500 text-xs font-body">Lv{entry.level}</p>
      </div>
      <div className="flex flex-col items-center justify-end rounded-t-2xl py-3 px-4 w-24 relative overflow-hidden"
        style={{ height, background: `linear-gradient(180deg, ${col.bg}25, ${col.bg}10)`, border: `1px solid ${col.bg}40` }}>
        {entry.rank === 1 && <Crown size={20} style={{ color: col.bg }} className="absolute top-3" />}
        <p className="font-heading font-black text-lg mt-auto" style={{ color: col.bg }}>{entry.rank}</p>
        <p className="text-zinc-400 text-xs font-body">{entry.xp.toLocaleString()} XP</p>
      </div>
    </motion.div>
  );
}

function LeaderRow({ entry, isCurrentUser, index }) {
  const col = RANK_COLORS[entry.rank];
  return (
    <motion.div initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: index * 0.04 }}
      className={`flex items-center gap-3 p-3 rounded-xl transition-all ${isCurrentUser ? 'border border-cyan-500/30 bg-cyan-500/5' : 'border border-white/5 bg-zinc-900/30 hover:bg-zinc-900/50'}`}>
      <div className="w-8 text-center flex-shrink-0">
        {col ? (
          <div className="w-7 h-7 rounded-full flex items-center justify-center mx-auto" style={{ background: col.bg + '25' }}>
            <span className="font-heading font-black text-xs" style={{ color: col.bg }}>{entry.rank}</span>
          </div>
        ) : (
          <span className="text-zinc-600 text-sm font-heading font-bold">{entry.rank}</span>
        )}
      </div>
      <div className="w-9 h-9 rounded-full flex items-center justify-center text-black font-heading font-black text-sm flex-shrink-0"
        style={{ background: isCurrentUser ? 'linear-gradient(135deg,#22d3ee,#8b5cf6)' : '#3f3f46' }}>
        {entry.name?.[0]?.toUpperCase()}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <p className={`text-sm font-body font-semibold truncate ${isCurrentUser ? 'text-cyan-400' : 'text-white'}`}>
            {entry.name} {isCurrentUser && <span className="text-zinc-500">(you)</span>}
          </p>
          {isCurrentUser && <span className="text-xs text-cyan-500 font-body">← You</span>}
        </div>
        <p className="text-zinc-600 text-xs font-body">Class {entry.class_level} • Lv{entry.level}</p>
      </div>
      <div className="flex items-center gap-3 flex-shrink-0">
        {entry.streak > 0 && (
          <div className="flex items-center gap-1">
            <Flame size={12} className="text-orange-400" />
            <span className="text-orange-400 text-xs font-body">{entry.streak}</span>
          </div>
        )}
        <div className="flex items-center gap-1">
          <Zap size={12} className="text-amber-400" />
          <span className="text-amber-400 text-sm font-heading font-bold">{entry.xp.toLocaleString()}</span>
        </div>
      </div>
    </motion.div>
  );
}

export default function LeaderboardPage() {
  const { user } = useAuth();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios.get(`${API}/leaderboard`, { withCredentials: true })
      .then(r => setData(r.data))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return (
    <div className="p-6 space-y-3">
      {[...Array(6)].map((_, i) => <div key={i} className="h-14 rounded-xl shimmer bg-zinc-900" />)}
    </div>
  );

  const top3 = data?.leaderboard?.slice(0, 3) || [];
  const rest = data?.leaderboard?.slice(3) || [];

  return (
    <div className="p-4 sm:p-6 max-w-2xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl sm:text-3xl font-heading font-black text-white flex items-center gap-3">
          <Trophy size={28} className="text-amber-400" /> Rankings
        </h1>
        <p className="text-zinc-500 text-sm font-body mt-1">
          <span className="text-cyan-400 font-semibold">{data?.total_users || 0}</span> learners competing worldwide
          {data?.user_rank && <span> • You're ranked <span className="text-amber-400 font-bold">#{data.user_rank}</span></span>}
        </p>
      </div>

      {/* Podium */}
      {top3.length >= 3 && (
        <div className="mb-6 py-6 glass rounded-2xl border border-white/5">
          <div className="flex items-end justify-center gap-3">
            {[top3[1], top3[0], top3[2]].map((entry, i) => (
              <PodiumCard key={entry?.user_id} entry={entry} height={i === 1 ? 120 : i === 0 ? 100 : 80} />
            ))}
          </div>
        </div>
      )}

      {/* Current user not in top 3 */}
      {data?.user_rank && data.user_rank > 3 && data.current_user && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}
          className="mb-4 p-3 rounded-xl border border-cyan-500/20 bg-cyan-500/5">
          <p className="text-zinc-500 text-xs font-body mb-2">Your Position</p>
          <LeaderRow entry={data.current_user} isCurrentUser={true} index={0} />
        </motion.div>
      )}

      {/* Full List */}
      <div className="space-y-2">
        {data?.leaderboard?.map((entry, i) => (
          <LeaderRow key={entry.user_id} entry={entry} isCurrentUser={entry.user_id === user?.user_id} index={i} />
        ))}
      </div>

      {!data?.leaderboard?.length && (
        <div className="text-center py-16 text-zinc-600 font-body">
          <Users size={40} className="mx-auto mb-3 opacity-30" />
          <p>Be the first on the leaderboard!</p>
        </div>
      )}
    </div>
  );
}
