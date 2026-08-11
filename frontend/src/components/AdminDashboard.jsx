import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { ShieldCheck, Users, TrendingUp, GraduationCap, Eye, EyeOff, CheckCircle, XCircle, RefreshCw, IndianRupee, MessageSquarePlus, Crown, Zap, ArrowUpRight, Calendar, BadgeCheck, Clock } from 'lucide-react';
import { toast } from 'sonner';
import { useAuth } from '../contexts/AuthContext';

const API  = `${process.env.REACT_APP_BACKEND_URL}/api`;
const TABS = ['earnings', 'leaderboard', 'grade-requests', 'feedback'];
const PLAN_PRICES = { starter: 399, pro: 699, free: 0 };
const PLAN_COLOR  = { starter: 'text-cyan-400', pro: 'text-violet-400', free: 'text-zinc-500' };

const fmt     = (n) => `₹${(n || 0).toLocaleString('en-IN')}`;
const fmtDate = (iso) => iso ? new Date(iso).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }) : '—';

export default function AdminDashboard() {
  const { user } = useAuth();
  const [tab, setTab]     = useState('earnings');
  const [data, setData]   = useState({});
  const [loading, setLoading] = useState(false);

  const fetchTab = useCallback(async (t) => {
    setLoading(true);
    try {
      const urlMap = {
        earnings:         `${API}/admin/earnings`,
        leaderboard:      `${API}/admin/leaderboard/users`,
        'grade-requests': `${API}/admin/grade-requests`,
        feedback:         `${API}/admin/feedback`,
      };
      const { data: res } = await axios.get(urlMap[t], { withCredentials: true });
      setData(prev => ({ ...prev, [t]: res }));
    } catch { toast.error('Failed to load data'); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { fetchTab(tab); }, [tab, fetchTab]);

  const toggleLeaderboard = async (userId, hidden) => {
    try {
      await axios.post(`${API}/admin/leaderboard/hide/${userId}`, {}, { withCredentials: true });
      toast.success(hidden ? 'User removed from leaderboard' : 'User restored to leaderboard');
      fetchTab('leaderboard');
    } catch { toast.error('Failed to update'); }
  };

  const resolveGrade = async (reqId, action) => {
    try {
      await axios.post(`${API}/admin/grade-requests/${reqId}/resolve`, { action }, { withCredentials: true });
      toast.success(`Grade change request ${action}d`);
      fetchTab('grade-requests');
    } catch { toast.error('Failed to resolve'); }
  };

  const resolveFeedback = async (fbId) => {
    try {
      await axios.patch(`${API}/admin/feedback/${fbId}/resolve`, {}, { withCredentials: true });
      toast.success('Marked as resolved');
      fetchTab('feedback');
    } catch { toast.error('Failed to resolve'); }
  };

  const e = data.earnings || {};

  return (
    <div className="min-h-screen bg-zinc-950 text-white">
      <div className="max-w-5xl mx-auto px-4 py-8">

        {/* Header */}
        <div className="flex items-center gap-3 mb-8">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-red-500 to-amber-500 flex items-center justify-center">
            <ShieldCheck size={20} className="text-white" />
          </div>
          <div>
            <h1 className="text-xl font-heading font-black text-white">Admin Dashboard</h1>
            <p className="text-zinc-500 text-xs font-body">{user?.email}</p>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 mb-6 border-b border-white/10 pb-4 flex-wrap">
          {[
            { id: 'earnings',       label: 'Earnings',       icon: IndianRupee },
            { id: 'leaderboard',    label: 'Leaderboard',    icon: Users },
            { id: 'grade-requests', label: 'Grade Requests', icon: GraduationCap },
            { id: 'feedback',       label: 'Feedback',       icon: MessageSquarePlus },
          ].map(({ id, label, icon: Icon }) => (
            <button key={id} data-testid={`admin-tab-${id}`}
              onClick={() => setTab(id)}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-body font-semibold transition-all ${
                tab === id ? 'bg-white/10 text-white' : 'text-zinc-500 hover:text-zinc-300'
              }`}>
              <Icon size={15} />{label}
            </button>
          ))}
          <button onClick={() => fetchTab(tab)} className="ml-auto text-zinc-500 hover:text-zinc-300 transition-colors" title="Refresh">
            <RefreshCw size={15} className={loading ? 'animate-spin' : ''} />
          </button>
        </div>

        {/* ── EARNINGS TAB ── */}
        {tab === 'earnings' && (
          <div data-testid="admin-earnings-panel">
            {!data.earnings ? (
              <div className="text-center text-zinc-500 py-12 font-body">Loading earnings data...</div>
            ) : (
              <>
                {/* KPI Cards */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                  {[
                    { label: 'Total Users',    value: e.total_users || 0,           color: 'text-cyan-400',   icon: Users },
                    { label: 'Paid Users',     value: e.total_paid_users || 0,       color: 'text-emerald-400', icon: BadgeCheck },
                    { label: 'Total Collected', value: fmt(e.total_revenue_inr),     color: 'text-green-400',  icon: IndianRupee },
                    { label: 'MRR',            value: fmt(e.mrr_inr),               color: 'text-amber-400',  icon: TrendingUp },
                  ].map(({ label, value, color, icon: Icon }) => (
                    <div key={label} className="glass rounded-xl p-4 border border-white/5">
                      <div className="flex items-center gap-2 mb-2">
                        <Icon size={13} className={`${color} opacity-60`} />
                        <p className="text-zinc-500 text-xs font-body">{label}</p>
                      </div>
                      <p className={`text-xl font-heading font-black ${color}`}>{value}</p>
                    </div>
                  ))}
                </div>

                {/* Plan breakdown */}
                <div className="glass rounded-xl p-5 border border-white/5 mb-4">
                  <h3 className="text-white font-heading font-bold text-sm mb-4">Plan Breakdown</h3>
                  <div className="grid grid-cols-3 gap-3">
                    {['free', 'starter', 'pro'].map(plan => {
                      const total    = e.plan_distribution?.[plan] || 0;
                      const active   = e.active_subscriptions?.[plan] || 0;
                      const cancelled = e.cancelled_subscriptions?.[plan] || 0;
                      return (
                        <div key={plan} className="bg-white/5 rounded-xl p-3 border border-white/5">
                          <div className="flex items-center gap-1.5 mb-2">
                            {plan === 'pro' ? <Crown size={12} className="text-violet-400" /> :
                             plan === 'starter' ? <Zap size={12} className="text-cyan-400" /> :
                             <Users size={12} className="text-zinc-500" />}
                            <span className={`text-xs font-heading font-bold capitalize ${PLAN_COLOR[plan]}`}>{plan}</span>
                            <span className="ml-auto text-zinc-500 text-[10px] font-body">
                              {plan !== 'free' ? `${fmt(PLAN_PRICES[plan])}/mo` : 'Free'}
                            </span>
                          </div>
                          <p className="text-2xl font-heading font-black text-white">{total}</p>
                          {plan !== 'free' && (
                            <div className="mt-1 space-y-0.5">
                              {active > 0 && <p className="text-[10px] text-emerald-400 font-body">{active} active (renewing)</p>}
                              {cancelled > 0 && <p className="text-[10px] text-amber-400 font-body">{cancelled} cancelled</p>}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Monthly revenue */}
                {Object.keys(e.monthly_revenue || {}).length > 0 && (
                  <div className="glass rounded-xl p-5 border border-white/5 mb-4">
                    <h3 className="text-white font-heading font-bold text-sm mb-3 flex items-center gap-2">
                      <Calendar size={14} className="text-zinc-400" /> Monthly Revenue
                    </h3>
                    <div className="space-y-2">
                      {Object.entries(e.monthly_revenue).sort((a, b) => b[0].localeCompare(a[0])).map(([month, amt]) => (
                        <div key={month} className="flex items-center justify-between py-1.5 border-b border-white/5 last:border-0">
                          <span className="text-zinc-400 text-sm font-body">{month}</span>
                          <span className="text-green-400 font-heading font-bold text-sm">{fmt(amt)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Paid Users List */}
                {(e.paid_users?.length > 0) ? (
                  <div className="glass rounded-xl p-5 border border-white/5 mb-4">
                    <h3 className="text-white font-heading font-bold text-sm mb-3 flex items-center gap-2">
                      <BadgeCheck size={14} className="text-emerald-400" /> Paid Users ({e.paid_users.length})
                    </h3>
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="text-left border-b border-white/10">
                            <th className="pb-2 text-zinc-500 text-xs font-body font-semibold pr-4">User</th>
                            <th className="pb-2 text-zinc-500 text-xs font-body font-semibold pr-4">Plan</th>
                            <th className="pb-2 text-zinc-500 text-xs font-body font-semibold pr-4">Status</th>
                            <th className="pb-2 text-zinc-500 text-xs font-body font-semibold pr-4">Amount</th>
                            <th className="pb-2 text-zinc-500 text-xs font-body font-semibold">Renews / Ends</th>
                          </tr>
                        </thead>
                        <tbody>
                          {e.paid_users.map((u, i) => (
                            <tr key={i} className="border-b border-white/5 last:border-0">
                              <td className="py-2.5 pr-4">
                                <p className="text-white font-body font-semibold text-xs">{u.name}</p>
                                <p className="text-zinc-500 text-[10px]">{u.email}</p>
                              </td>
                              <td className="py-2.5 pr-4">
                                <span className={`text-xs font-heading font-bold capitalize ${PLAN_COLOR[u.plan] || 'text-white'}`}>
                                  {u.plan}
                                </span>
                              </td>
                              <td className="py-2.5 pr-4">
                                {u.status === 'active' ? (
                                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-400 font-semibold">Active</span>
                                ) : (
                                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-amber-500/15 text-amber-400 font-semibold">Cancelled</span>
                                )}
                              </td>
                              <td className="py-2.5 pr-4 text-green-400 font-semibold text-xs">{fmt(u.amount_inr || PLAN_PRICES[u.plan])}</td>
                              <td className="py-2.5 text-zinc-400 text-[11px] font-body">{fmtDate(u.expires_at)}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                ) : (
                  <div className="glass rounded-xl p-8 border border-white/5 mb-4 text-center">
                    <IndianRupee size={24} className="text-zinc-700 mx-auto mb-2" />
                    <p className="text-zinc-500 text-sm font-body">No paid users yet. Payments will appear here once processed.</p>
                  </div>
                )}

                {/* Recent PayU transactions */}
                {e.recent_payments?.length > 0 && (
                  <div className="glass rounded-xl p-5 border border-white/5">
                    <h3 className="text-white font-heading font-bold text-sm mb-3 flex items-center gap-2">
                      <ArrowUpRight size={14} className="text-zinc-400" /> Recent Transactions
                    </h3>
                    <div className="space-y-1">
                      {e.recent_payments.map((p, i) => (
                        <div key={i} className="flex items-center justify-between py-2 border-b border-white/5 last:border-0">
                          <div className="min-w-0 flex-1">
                            <p className="text-white text-xs font-body font-semibold truncate">{p.user_name}</p>
                            <p className="text-zinc-500 text-[10px] truncate">{p.user_email} · {p.txnid}</p>
                          </div>
                          <div className="flex items-center gap-3 ml-3 shrink-0">
                            <span className={`text-[10px] font-heading font-bold capitalize ${PLAN_COLOR[p.plan] || 'text-white'}`}>{p.plan}</span>
                            <span className="text-green-400 font-heading font-bold text-sm">{fmt(p.amount)}</span>
                            <span className="text-zinc-600 text-[10px] font-body hidden sm:block">{fmtDate(p.created_at)}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        )}

        {/* ── LEADERBOARD TAB ── */}
        {tab === 'leaderboard' && (
          <div data-testid="admin-leaderboard-panel">
            <p className="text-zinc-500 text-xs font-body mb-4">Toggle visibility of users on the public leaderboard.</p>
            <div className="glass rounded-xl border border-white/5 overflow-hidden">
              {data.leaderboard?.users?.map((u) => (
                <div key={u.user_id} className="flex items-center justify-between px-5 py-3 border-b border-white/5 last:border-0">
                  <div>
                    <p className="text-white text-sm font-body font-semibold">{u.name}</p>
                    <p className="text-zinc-500 text-xs">{u.email} · Class {u.class_level} · {u.xp} XP</p>
                  </div>
                  <button
                    data-testid={`leaderboard-toggle-${u.user_id}`}
                    onClick={() => toggleLeaderboard(u.user_id, !u.hide_from_leaderboard)}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                      u.hide_from_leaderboard
                        ? 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700'
                        : 'bg-green-500/10 text-green-400 hover:bg-red-500/10 hover:text-red-400 border border-green-500/20 hover:border-red-500/20'
                    }`}>
                    {u.hide_from_leaderboard ? <><EyeOff size={12} /> Hidden</> : <><Eye size={12} /> Visible</>}
                  </button>
                </div>
              ))}
              {!data.leaderboard?.users?.length && (
                <div className="text-center text-zinc-500 py-8 font-body text-sm">No users found</div>
              )}
            </div>
          </div>
        )}

        {/* ── GRADE REQUESTS TAB ── */}
        {tab === 'grade-requests' && (
          <div data-testid="admin-grade-requests-panel">
            <div className="glass rounded-xl border border-white/5 overflow-hidden">
              {data['grade-requests']?.requests?.map((req) => (
                <div key={req.request_id} className="flex items-center justify-between px-5 py-4 border-b border-white/5 last:border-0">
                  <div>
                    <p className="text-white text-sm font-body font-semibold">{req.user_name}</p>
                    <p className="text-zinc-500 text-xs">{req.user_email}</p>
                    <p className="text-zinc-400 text-xs mt-0.5">
                      Class {req.old_class || '?'} → Class {req.new_class || '?'}
                      <span className={`ml-2 px-1.5 py-0.5 rounded text-[10px] font-semibold ${
                        req.status === 'approved' ? 'bg-green-500/20 text-green-400' :
                        req.status === 'denied'   ? 'bg-red-500/20 text-red-400' :
                                                    'bg-amber-500/20 text-amber-400'
                      }`}>{req.status}</span>
                    </p>
                  </div>
                  {req.status === 'pending' && (
                    <div className="flex gap-2">
                      <button onClick={() => resolveGrade(req.request_id, 'approve')}
                        data-testid={`approve-grade-${req.request_id}`}
                        className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-green-500/10 text-green-400 text-xs font-semibold hover:bg-green-500/20 transition-all">
                        <CheckCircle size={12} /> Approve
                      </button>
                      <button onClick={() => resolveGrade(req.request_id, 'deny')}
                        data-testid={`deny-grade-${req.request_id}`}
                        className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-red-500/10 text-red-400 text-xs font-semibold hover:bg-red-500/20 transition-all">
                        <XCircle size={12} /> Deny
                      </button>
                    </div>
                  )}
                </div>
              ))}
              {!data['grade-requests']?.requests?.length && (
                <div className="text-center text-zinc-500 py-8 font-body text-sm">No grade change requests yet</div>
              )}
            </div>
          </div>
        )}

        {/* ── FEEDBACK TAB ── */}
        {tab === 'feedback' && (
          <div data-testid="admin-feedback-panel">
            <div className="glass rounded-xl border border-white/5 overflow-hidden divide-y divide-white/5">
              {data.feedback?.feedback?.map((fb) => (
                <div key={fb.feedback_id} className="px-5 py-4">
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full font-body ${
                          fb.type === 'bug'        ? 'bg-rose-500/20 text-rose-400' :
                          fb.type === 'suggestion' ? 'bg-amber-500/20 text-amber-400' :
                                                     'bg-cyan-500/20 text-cyan-400'
                        }`}>{fb.type === 'bug' ? 'Bug' : fb.type === 'suggestion' ? 'Suggestion' : 'General'}</span>
                        <span className="text-zinc-500 text-xs font-body">{fb.user_name} · {fb.user_email}</span>
                      </div>
                      <p className="text-white text-sm font-body">{fb.message}</p>
                      <p className="text-zinc-600 text-xs font-body mt-1">{new Date(fb.created_at).toLocaleString()}</p>
                    </div>
                    {fb.status === 'open' ? (
                      <button onClick={() => resolveFeedback(fb.feedback_id)}
                        className="flex-shrink-0 flex items-center gap-1 px-3 py-1.5 rounded-lg bg-emerald-500/10 text-emerald-400 text-xs font-semibold hover:bg-emerald-500/20 transition-all">
                        <CheckCircle size={12} /> Resolve
                      </button>
                    ) : (
                      <span className="flex-shrink-0 text-xs font-body text-emerald-500 font-semibold">Resolved</span>
                    )}
                  </div>
                </div>
              ))}
              {!data.feedback?.feedback?.length && (
                <div className="text-center text-zinc-500 py-10 font-body text-sm">No feedback yet</div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
