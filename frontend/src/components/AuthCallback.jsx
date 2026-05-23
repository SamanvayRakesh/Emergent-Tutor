import { useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function AuthCallback() {
  const hasProcessed = useRef(false);
  const nav = useNavigate();
  const { login } = useAuth();

  useEffect(() => {
    if (hasProcessed.current) return;
    hasProcessed.current = true;

    const hash = window.location.hash;
    const match = hash.match(/session_id=([^&]+)/);
    if (!match) {
      nav('/login', { replace: true });
      return;
    }

    const session_id = match[1];

    const processSession = async () => {
      try {
        const { data } = await axios.post(
          `${API}/google-auth/session`,
          { session_id },
          { withCredentials: true }
        );
        login(data);
        window.history.replaceState(null, '', '/');
        nav('/', { replace: true });
      } catch (err) {
        console.error('Auth callback error:', err);
        nav('/login', { replace: true });
      }
    };

    processSession();
  }, [nav, login]);

  return (
    <div className="min-h-screen bg-zinc-950 flex items-center justify-center">
      <div className="flex flex-col items-center gap-4">
        <div className="w-12 h-12 rounded-full border-2 border-cyan-400 border-t-transparent animate-spin" />
        <p className="text-zinc-400 font-body text-sm">Completing sign in...</p>
      </div>
    </div>
  );
}
