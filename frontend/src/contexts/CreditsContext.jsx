import { createContext, useContext, useEffect, useState, useCallback, useRef } from 'react';
import axios from 'axios';
import { toast } from 'sonner';
import { useAuth } from './AuthContext';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const CreditsContext = createContext({});

// Map server routes → cost (so we know which client calls debit credits)
const ROUTE_COST = [
  { match: /\/api\/chat\/sessions\/.+\/message$/, kind: 'ai_message',         cost: 1  },
  { match: /\/api\/quiz\/generate$/,              kind: 'quiz_generate',      cost: 15 },
  { match: /\/api\/mock-exam\/generate$/,         kind: 'mock_exam_generate', cost: 30 },
];

function routeMeta(url, method) {
  if (!url || method?.toLowerCase() !== 'post') return null;
  return ROUTE_COST.find(r => r.match.test(url)) || null;
}

export function CreditsProvider({ children }) {
  const { user } = useAuth();
  const [credits, setCredits] = useState(null);
  const [lowThreshold, setLowThreshold] = useState(10);
  const lowToastShown = useRef(false);

  const refresh = useCallback(async () => {
    if (!user) { setCredits(null); return; }
    try {
      const { data } = await axios.get(`${API}/credits`, { withCredentials: true });
      setCredits(data.credits);
      setLowThreshold(data.low_threshold || 10);
    } catch (e) { console.warn('Credits refresh failed:', e); }
  }, [user]);

  useEffect(() => { refresh(); }, [refresh]);

  // Optimistic + toast hook on success/failure for credit-spending routes
  useEffect(() => {
    const reqI = axios.interceptors.request.use(cfg => cfg);
    const resI = axios.interceptors.response.use(
      (response) => {
        const meta = routeMeta(response.config?.url, response.config?.method);
        if (meta) {
          setCredits(prev => {
            if (prev == null) return prev;
            const next = Math.max(0, prev - meta.cost);
            toast.success(`−${meta.cost} credit${meta.cost > 1 ? 's' : ''} used`, {
              id: 'credit-deduct', duration: 1800,
              style: { background: 'rgba(30,27,75,0.85)', color: '#fcd34d', border: '1px solid rgba(251,191,36,0.4)', backdropFilter: 'blur(14px)' },
            });
            if (next <= lowThreshold && !lowToastShown.current) {
              lowToastShown.current = true;
              toast(`⚡ Low credits remaining: ${next} left`, {
                id: 'low-credits', duration: 4500,
                style: { background: 'rgba(76,5,25,0.9)', color: '#fecaca', border: '1px solid rgba(244,63,94,0.5)' },
              });
              setTimeout(() => { lowToastShown.current = false; }, 60_000);
            }
            refresh();
            return next;
          });
        }
        return response;
      },
      (err) => {
        if (err?.response?.status === 402) {
          const detail = err.response.data?.detail;
          const msg = typeof detail === 'string' ? detail : (detail?.message || 'Not enough credits');
          if (detail?.code === 'INSUFFICIENT_CREDITS') {
            toast.error(msg, {
              id: 'no-credits', duration: 5000,
              style: { background: 'rgba(76,5,25,0.92)', color: '#fee2e2', border: '1px solid rgba(244,63,94,0.6)', backdropFilter: 'blur(14px)' },
            });
            refresh();
          }
        }
        return Promise.reject(err);
      },
    );
    return () => { axios.interceptors.request.eject(reqI); axios.interceptors.response.eject(resI); };
  }, [refresh, lowThreshold]);

  return (
    <CreditsContext.Provider value={{ credits, lowThreshold, refresh }}>
      {children}
    </CreditsContext.Provider>
  );
}

export function useCredits() { return useContext(CreditsContext); }
