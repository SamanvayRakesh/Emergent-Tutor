import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  BookOpen,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
} from 'lucide-react';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function SchoolSelectModal() {
  const { user, login } = useAuth();

  const [schools, setSchools] = useState([]);
  const [selected, setSelected] = useState('');
  const [loadingSchools, setLoadingSchools] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [retry, setRetry] = useState(0);

  const needsSchool = Boolean(user && !user.school);

  useEffect(() => {
    if (!needsSchool) return;

    let active = true;

    setLoadingSchools(true);
    setError('');

    axios
      .get(`${API}/auth/schools`, {
        withCredentials: true,
      })
      .then(({ data }) => {
        if (active) {
          setSchools(data.schools || []);
        }
      })
      .catch(() => {
        if (active) {
          setError('Could not load schools. Please try again.');
        }
      })
      .finally(() => {
        if (active) {
          setLoadingSchools(false);
        }
      });

    return () => {
      active = false;
    };
  }, [needsSchool, retry]);

  if (!needsSchool) return null;

  const canSave = schools.some(
    school => school.id === selected && school.available
  );

  const handleSave = async () => {
    if (!canSave || saving) return;

    setSaving(true);
    setError('');

    try {
      // Use the existing school-saving logic.
      await axios.put(
        `${API}/users/school`,
        { school: selected },
        { withCredentials: true }
      );

      // Refresh the complete account before app pages load.
      const { data } = await axios.get(
        `${API}/auth/me`,
        { withCredentials: true }
      );

      if (data.school !== selected) {
        throw new Error(
          'Your school was not confirmed. Please try again.'
        );
      }

      login(data);
    } catch (e) {
      const detail = e.response?.data?.detail;

      setError(
        typeof detail === 'string'
          ? detail
          : e.message || 'Could not save your school. Please try again.'
      );
    } finally {
      setSaving(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-[110] flex items-center justify-center bg-black/80 backdrop-blur-sm px-4"
      data-testid="school-select-modal"
    >
      <motion.div
        role="dialog"
        aria-modal="true"
        aria-labelledby="school-modal-title"
        initial={{ opacity: 0, scale: 0.95, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        transition={{
          type: 'spring',
          stiffness: 300,
          damping: 30,
        }}
        className="w-full max-w-md max-h-[90vh] overflow-y-auto"
      >
        <div className="glass rounded-2xl p-8 shadow-2xl border border-white/10">
          <div className="flex flex-col items-center text-center mb-6">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-cyan-500 to-cyan-600 flex items-center justify-center mb-4 shadow-lg shadow-cyan-500/30">
              <BookOpen size={26} className="text-white" />
            </div>

            <h2
              id="school-modal-title"
              className="text-white text-xl font-heading font-black mb-1"
            >
              Choose your school,{' '}
              {user?.name?.split(' ')[0] || 'there'}
            </h2>

            <p className="text-zinc-400 text-sm font-body leading-relaxed">
              We will load your school's syllabus, AI tutor and practice.
            </p>
          </div>

          {loadingSchools && (
            <p className="text-zinc-400 text-sm mb-4">
              Loading schools…
            </p>
          )}

          <div className="space-y-3 mb-5">
            {schools.map(school => (
              <button aria-pressed={selected === school.id}
                key={school.id}
                type="button"
                data-testid={`school-option-${school.id}`}
                disabled={!school.available || saving}
                onClick={() => {
                  setSelected(school.id);
                  setError('');
                }}
                className={`w-full text-left px-4 py-3.5 rounded-xl border text-sm font-body transition-all relative ${
                  !school.available
                    ? 'border-white/5 bg-zinc-900/50 text-zinc-600 cursor-not-allowed'
                    : selected === school.id
                      ? 'border-cyan-500/70 bg-cyan-500/10 text-white'
                      : 'border-white/10 bg-zinc-900 text-zinc-300 hover:border-white/20'
                } disabled:cursor-not-allowed`}
              >
                <span className="font-semibold pr-5 block">
                  {school.name}
                </span>

                {!school.available && (
                  <span className="text-[10px] text-zinc-500">
                    Coming Soon
                  </span>
                )}

                {selected === school.id && (
                  <CheckCircle2
                    size={16}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-cyan-400"
                  />
                )}
              </button>
            ))}
          </div>

          {error && (
            <div
              role="alert"
              className="flex items-start gap-2 p-3 mb-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-xs font-body"
            >
              <AlertTriangle
                size={14}
                className="shrink-0 mt-0.5"
              />
              <p>{error}</p>
            </div>
          )}

          {!loadingSchools && schools.length === 0 && (
            <button
              type="button"
              onClick={() => setRetry(value => value + 1)}
              className="text-cyan-400 text-sm mb-4"
            >
              Reload school options
            </button>
          )}

          <button data-ace-primary="true"
            type="button"
            data-testid="school-modal-confirm"
            onClick={handleSave}
            disabled={saving || loadingSchools || !canSave}
            className="w-full flex items-center justify-center gap-2 py-3 rounded-xl font-heading font-bold text-sm bg-gradient-to-r from-cyan-500 to-cyan-600 text-black hover:from-cyan-400 hover:to-cyan-500 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {saving ? (
              'Saving…'
            ) : (
              <>
                Confirm & Continue
                <ArrowRight size={16} />
              </>
            )}
          </button>

          <p className="text-zinc-600 text-[11px] text-center mt-3 font-body">
            Select the school whose curriculum you study.
          </p>
        </div>
      </motion.div>
    </div>
  );
}