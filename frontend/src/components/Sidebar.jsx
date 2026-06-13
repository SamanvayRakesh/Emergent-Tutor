import { useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { LayoutDashboard, MessageSquare, BookOpen, TrendingUp, Trophy, User, LogOut, Zap, X, Flame, ChevronRight, Crown, FileText, CalendarDays, Sparkles } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { useSubscription } from '../contexts/SubscriptionContext';

const NAV = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard', exact: true },
  { to: '/chat', icon: MessageSquare, label: 'AI Tutor' },
  { to: '/syllabus', icon: BookOpen, label: 'Syllabus' },
  { to: '/progress', icon: TrendingUp, label: 'Progress' },
  { to: '/quiz', icon: Trophy, label: 'Quiz Arena' },
  { to: '/mock-exams', icon: FileText, label: 'Mock Exams' },
  { to: '/study-plan', icon: CalendarDays, label: 'Study Plan' },
  { to: '/leaderboard', icon: Crown, label: 'Rankings' },
  { to: '/profile', icon: User, label: 'Profile' },
];

export default function Sidebar({ onClose }) {
  const { user, logout } = useAuth();
  const { plan, isPaid } = useSubscription();
  const nav = useNavigate();

  const handleLogout = async () => {
    await logout();
    nav('/login', { replace: true });
  };

  const xp = user?.xp || 0;
  const level = Math.max(1, Math.floor(xp / 500) + 1);
  const xpInLevel = xp % 500;

  return (
    <div className="h-full flex flex-col bg-zinc-950 border-r border-white/5 py-4">
      {/* Logo */}
      <div className="px-5 mb-6 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-400 to-violet-600 flex items-center justify-center flex-shrink-0">
            <BookOpen size={16} className="text-white" />
          </div>
          <span className="font-heading font-black text-lg">
            <span className="text-white">AceIt</span>
            <span style={{ color: '#dc2626' }}> AI</span>
          </span>
        </div>
        {onClose && (
          <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-white/5 text-zinc-500 hover:text-white transition-colors">
            <X size={16} />
          </button>
        )}
      </div>

      {/* User Card */}
      {user && (
        <div className="mx-3 mb-4 p-3 rounded-xl glass-surface border border-white/5">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-9 h-9 rounded-full bg-gradient-to-br from-cyan-400 to-violet-500 flex items-center justify-center text-black font-heading font-black text-sm flex-shrink-0">
              {user.name?.[0]?.toUpperCase() || 'U'}
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-white text-sm font-body font-semibold truncate">{user.name}</p>
              <p className="text-zinc-500 text-xs font-body">Class {user.class_level || '9'} Student</p>
            </div>
            <div className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-amber-400/15 border border-amber-400/30">
              <Zap size={11} className="text-amber-400" />
              <span className="text-amber-400 text-xs font-heading font-bold">Lv{level}</span>
            </div>
          </div>

          {/* XP Bar */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <span className="text-zinc-600 text-xs font-body">{xp} XP</span>
              <span className="text-zinc-600 text-xs font-body">{500 - xpInLevel} to next</span>
            </div>
            <div className="h-1.5 bg-zinc-800 rounded-full overflow-hidden">
              <motion.div
                className="h-full rounded-full"
                style={{ background: 'linear-gradient(90deg, #22d3ee, #8b5cf6)' }}
                initial={{ width: 0 }}
                animate={{ width: `${(xpInLevel / 500) * 100}%` }}
                transition={{ duration: 1, delay: 0.3 }}
              />
            </div>
          </div>

          {/* Streak */}
          {user.streak > 0 && (
            <div className="flex items-center gap-1.5 mt-2">
              <Flame size={13} className="text-orange-400" />
              <span className="text-orange-400 text-xs font-body font-medium">{user.streak} day streak</span>
            </div>
          )}
        </div>
      )}

      {/* Navigation */}
      <nav className="flex-1 px-3 space-y-0.5">
        {NAV.map(({ to, icon: Icon, label, exact }) => (
          <NavLink
            key={to}
            to={to}
            end={exact}
            data-testid={`nav-${label.toLowerCase().replace(' ', '-')}`}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-200 group ${
                isActive
                  ? 'bg-cyan-500/10 border border-cyan-500/20 text-cyan-400'
                  : 'text-zinc-500 hover:text-white hover:bg-white/5'
              }`
            }
          >
            {({ isActive }) => (
              <>
                <Icon size={18} className={isActive ? 'text-cyan-400' : 'text-zinc-500 group-hover:text-white transition-colors'} />
                <span className="text-sm font-body font-medium flex-1">{label}</span>
                {isActive && <ChevronRight size={14} className="text-cyan-500/50" />}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Bottom */}
      <div className="px-3 mt-2 space-y-2">
        {/* Upgrade CTA — only for free users */}
        {plan && !isPaid && (
          <button onClick={() => nav('/upgrade')} data-testid="sidebar-upgrade-btn"
            className="w-full flex items-center gap-2 px-3 py-2.5 rounded-xl text-amber-300 bg-gradient-to-r from-amber-500/15 via-rose-500/15 to-violet-500/15 border border-amber-400/30 hover:border-amber-400/60 transition-all text-sm font-body font-bold relative overflow-hidden group">
            <motion.div className="absolute inset-0 bg-gradient-to-r from-transparent via-amber-400/10 to-transparent"
              animate={{ x: ['-100%', '100%'] }} transition={{ duration: 2.5, repeat: Infinity, ease: 'linear' }} />
            <Sparkles size={16} className="relative z-10 text-amber-400" />
            <span className="relative z-10 flex-1 text-left">Upgrade to Pro</span>
            <span className="relative z-10 text-amber-400 text-[10px] font-body uppercase tracking-wider">₹299</span>
          </button>
        )}
        {plan && isPaid && (
          <div className="flex items-center gap-2 px-3 py-2 rounded-xl bg-gradient-to-r from-amber-500/20 to-rose-500/20 border border-amber-400/40">
            <Crown size={14} className="text-amber-400" />
            <span className="text-amber-300 text-xs font-heading font-bold flex-1">{plan.plan_name} Active</span>
          </div>
        )}

        <button onClick={handleLogout} data-testid="logout-btn"
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-zinc-500 hover:text-red-400 hover:bg-red-500/5 transition-all text-sm font-body">
          <LogOut size={18} />
          <span>Sign Out</span>
        </button>
      </div>
    </div>
  );
}
