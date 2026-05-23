import { useState } from 'react';
import { motion } from 'framer-motion';
import { User, Mail, BookOpen, Zap, Flame, Trophy, Save, ChevronDown, Shield, Star, Clock } from 'lucide-react';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const CLASSES = ['6', '7', '8', '9', '10', '11', '12'];

export default function ProfilePage() {
  const { user, setUser } = useAuth();
  const [selectedClass, setSelectedClass] = useState(user?.class_level || '9');
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const xp = user?.xp || 0;
  const level = Math.max(1, Math.floor(xp / 500) + 1);
  const xpInLevel = xp % 500;

  const handleSaveClass = async () => {
    setSaving(true);
    try {
      await axios.put(`${API}/users/class`, { class_level: selectedClass }, { withCredentials: true });
      setUser(p => ({ ...p, class_level: selectedClass }));
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch {}
    setSaving(false);
  };

  const infoItems = [
    { label: 'Email', value: user?.email, icon: Mail, color: '#22d3ee' },
    { label: 'Member Since', value: user?.created_at ? new Date(user.created_at).toLocaleDateString('en-IN', { year: 'numeric', month: 'short', day: 'numeric' }) : 'Recently', icon: Clock, color: '#8b5cf6' },
    { label: 'Auth Type', value: user?.auth_type === 'google' ? 'Google' : 'Email & Password', icon: Shield, color: '#10b981' },
    { label: 'Role', value: user?.role === 'admin' ? 'Administrator' : 'Student', icon: Star, color: '#f59e0b' },
  ];

  return (
    <div className="p-4 sm:p-6 max-w-2xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl sm:text-3xl font-heading font-black text-white flex items-center gap-3">
          <User size={28} className="text-cyan-400" />
          Profile
        </h1>
        <p className="text-zinc-500 text-sm font-body mt-1">Your NeuraLearn account</p>
      </div>

      {/* Avatar & Name */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
        className="glass rounded-2xl p-6 border border-white/10 text-center">
        <div className="w-20 h-20 rounded-full bg-gradient-to-br from-cyan-400 to-violet-600 flex items-center justify-center text-black font-heading font-black text-3xl mx-auto mb-3">
          {user?.name?.[0]?.toUpperCase() || 'S'}
        </div>
        <h2 className="text-white font-heading font-black text-xl">{user?.name}</h2>
        <p className="text-zinc-500 text-sm font-body mt-0.5">Class {user?.class_level} Student</p>

        {/* Level Badge */}
        <div className="inline-flex items-center gap-2 mt-3 px-4 py-2 rounded-full bg-amber-400/15 border border-amber-400/25">
          <Zap size={15} className="text-amber-400" />
          <span className="text-amber-400 font-heading font-bold">Level {level}</span>
          <span className="text-amber-600 text-xs font-body">•</span>
          <span className="text-amber-500 text-sm font-body">{xp} XP</span>
        </div>

        {/* XP Progress */}
        <div className="mt-4">
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-zinc-600 text-xs font-body">Level {level}</span>
            <span className="text-zinc-600 text-xs font-body">Level {level + 1}</span>
          </div>
          <div className="h-2 bg-zinc-800 rounded-full overflow-hidden">
            <motion.div className="h-full rounded-full" style={{ background: 'linear-gradient(90deg, #f59e0b, #d946ef)' }}
              initial={{ width: 0 }} animate={{ width: `${(xpInLevel / 500) * 100}%` }} transition={{ duration: 1, delay: 0.3 }} />
          </div>
          <p className="text-zinc-600 text-xs font-body text-center mt-1">{xp % 500} / 500 XP to next level</p>
        </div>
      </motion.div>

      {/* Quick stats */}
      <div className="grid grid-cols-2 gap-3">
        {[
          { label: 'Streak', value: `${user?.streak || 0} days`, icon: Flame, color: '#ef4444' },
          { label: 'Longest Streak', value: `${user?.longest_streak || 0} days`, icon: Trophy, color: '#f59e0b' },
        ].map(({ label, value, icon: Icon, color }, i) => (
          <motion.div key={label} initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: 0.15 + i * 0.05 }}
            className="glass-surface rounded-2xl p-4 border border-white/5">
            <div className="p-2 rounded-xl mb-2 inline-block" style={{ background: color + '20' }}>
              <Icon size={18} style={{ color }} />
            </div>
            <p className="text-xl font-heading font-bold text-white">{value}</p>
            <p className="text-zinc-500 text-xs font-body">{label}</p>
          </motion.div>
        ))}
      </div>

      {/* Class Setting */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}
        className="glass-surface rounded-2xl p-5 border border-white/5">
        <h3 className="text-white font-heading font-bold mb-3 flex items-center gap-2">
          <BookOpen size={18} className="text-cyan-400" /> Learning Class
        </h3>
        <div className="flex gap-2 flex-wrap mb-4">
          {CLASSES.map(cls => (
            <button key={cls} onClick={() => setSelectedClass(cls)} data-testid={`class-select-${cls}`}
              className={`w-10 h-10 rounded-xl text-sm font-heading font-bold transition-all ${selectedClass === cls ? 'bg-cyan-500 text-black shadow-lg shadow-cyan-500/25' : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700 hover:text-white'}`}>
              {cls}
            </button>
          ))}
        </div>
        <button onClick={handleSaveClass} disabled={saving || saved || selectedClass === user?.class_level} data-testid="save-class-btn"
          className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-heading font-bold transition-all ${saved ? 'bg-green-500/20 text-green-400 border border-green-500/30' : 'bg-cyan-500/15 text-cyan-400 border border-cyan-500/30 hover:bg-cyan-500/25'} disabled:opacity-40`}>
          {saving ? <div className="w-4 h-4 border-2 border-cyan-400/30 border-t-cyan-400 rounded-full animate-spin" /> : <Save size={15} />}
          {saved ? 'Saved!' : saving ? 'Saving...' : 'Save Class'}
        </button>
      </motion.div>

      {/* Account Info */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.25 }}
        className="glass-surface rounded-2xl p-5 border border-white/5">
        <h3 className="text-white font-heading font-bold mb-4">Account Information</h3>
        <div className="space-y-3">
          {infoItems.map(({ label, value, icon: Icon, color }) => (
            <div key={label} className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0" style={{ background: color + '15' }}>
                <Icon size={15} style={{ color }} />
              </div>
              <div>
                <p className="text-zinc-500 text-xs font-body">{label}</p>
                <p className="text-white text-sm font-body">{value}</p>
              </div>
            </div>
          ))}
        </div>
      </motion.div>
    </div>
  );
}
