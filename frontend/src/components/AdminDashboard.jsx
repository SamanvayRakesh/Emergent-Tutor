import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { ShieldCheck, Users, TrendingUp, GraduationCap, Eye, EyeOff, CheckCircle, XCircle, RefreshCw, IndianRupee, MessageSquarePlus, Bug, Lightbulb, MessageCircle } from 'lucide-react';
import { toast } from 'sonner';
import { useAuth } from '../contexts/AuthContext';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const TABS = ['earnings', 'leaderboard', 'grade-requests'];

export default function AdminDashboard() {
  const { user } = useAuth();
  const [tab, setTab] = useState('earnings');
  const [data, setData] = useState({});
  const [loading, setLoading] = useState(false);

  const fetchTab = useCallback(async (t) => {
    setLoading(true);
    try {
      const urlMap = {
        'earnings':       `${API}/admin/earnings`,
        'leaderboard':    `${API}/admin/leaderboard/users`,
        'grade-requests': `${API}/admin/grade-requests`,
        'feedback':       `${API}/admin/feedback`,
      };
      const { data: res } = await axios.get(urlMap[t], { withCredentials: true });
      setData(prev => ({ ...prev, [t]: res }));
    } catch (e) {
      toast.error('Failed to load data');
    } finally {
      setLoading(false);
    }
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

  const fmt = (n) => `₹${(n || 0).toLocaleString('en-IN')}`;

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
            { id: 'earnings', label: 'Earnings', icon: IndianRupee },
            { id: 'leaderboard', label: 'Leaderboard', icon: Users },
            { id: 'grade-requests', label: 'Grade Requests', icon: GraduationCap },
            { id: 'feedback', label: 'Feedback', icon: MessageSquarePlus },
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

        {/* Earnings Tab */}
        {tab === 'earnings' && (
          <div data-testid="admin-earnings-panel">
            {data.earnings ? (
              <>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                  {[
                    { label: 'Total Users', value: data.earnings.total_users, color: 'text-cyan-400' },
                    { label: 'Total Revenue', value: fmt(data.earnings.total_revenue_inr), color: 'text-green-400' },
                    { label: 'Estimated MRR', value: fmt(data.earnings.estimated_mrr_inr), color: 'text-amber-400' },
                    { label: 'Pro Users', value: data.earnings.plan_distribution?.pro || 0, color: 'text-violet-400' },
                  ].map(({ label, value, color }) => (
                    <div key={label} className="glass rounded-xl p-4 border border-white/5">
                      <p className="text-zinc-500 text-xs font-body mb-1">{label}</p>
                      <p className={`text-xl font-heading font-black ${color}`}>{value}</p>
                    </div>
                  ))}
                </div>

                <div className="glass rounded-xl p-5 border border-white/5 mb-4">
                  <h3 className="text-white font-heading font-bold text-sm mb-3">Plan Distribution</h3>
                  {Object.entries(data.earnings.plan_distribution || {}).map(([plan, count]) => (
                    <div key={plan} className="flex items-center justify-between py-2 border-b border-white/5 last:border-0">
                      <span className="text-zinc-400 text-sm capitalize font-body">{plan}</span>
                      <div className="flex items-center gap-3">
                        <span className="text-white font-semibold text-sm">{count} users</span>
                        <span className="text-zinc-600 text-xs">
                          {plan === 'starter' ? '₹199/mo' : plan === 'pro' ? '₹499/mo' : 'Free'}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>

                {data.earnings.recent_payments?.length > 0 && (
                  <div className="glass rounded-xl p-5 border border-white/5">
                    <h3 className="text-white font-heading font-bold text-sm mb-3">Recent Payments</h3>
                    <div className="space-y-2">
                      {data.earnings.recent_payments.slice(0, 10).map((p, i) => (
                        <div key={i} className="flex items-center justify-between py-1.5 text-sm">
                          <span className="text-zinc-400 font-body">{p.user_email || 'User'}</span>
                          <div className="flex items-center gap-3">
                            <span className="text-zinc-500 text-xs">{p.plan}</span>
                            <span className="text-green-400 font-semibold">{fmt(p.amount)}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </>
            ) : (
              <div className="text-center text-zinc-500 py-12 font-body">Loading earnings data...</div>
            )}
          </div>
        )}

        {/* Leaderboard Management Tab */}
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
              {(!data.leaderboard?.users?.length) && (
                <div className="text-center text-zinc-500 py-8 font-body text-sm">No users found</div>
              )}
            </div>
          </div>
        )}

        {/* Grade Requests Tab */}
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
                        req.status === 'denied' ? 'bg-red-500/20 text-red-400' :
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
              {(!data['grade-requests']?.requests?.length) && (
                <div className="text-center text-zinc-500 py-8 font-body text-sm">No grade change requests yet</div>
              )}
            </div>
          </div>
        )}

        {/* Feedback Tab */}
        {tab === 'feedback' && (
          <div data-testid="admin-feedback-panel">
            <div className="glass rounded-xl border border-white/5 overflow-hidden divide-y divide-white/5">
              {data.feedback?.feedback?.map((fb) => (
                <div key={fb.feedback_id} className="px-5 py-4">
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full font-body ${
                          fb.type === 'bug' ? 'bg-rose-500/20 text-rose-400' :
                          fb.type === 'suggestion' ? 'bg-amber-500/20 text-amber-400' :
                          'bg-cyan-500/20 text-cyan-400'
                        }`}>
                          {fb.type === 'bug' ? 'Bug' : fb.type === 'suggestion' ? 'Suggestion' : 'General'}
                        </span>
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
              {(!data.feedback?.feedback?.length) && (
                <div className="text-center text-zinc-500 py-10 font-body text-sm">No feedback yet</div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
