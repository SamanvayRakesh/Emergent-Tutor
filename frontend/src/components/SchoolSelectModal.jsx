import { useState, useEffect } from 'react';
import {
  motion,
  AnimatePresence,
} from 'framer-motion';

import {
  BookOpen,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
} from 'lucide-react';

import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';

const API =
  `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function SchoolSelectModal() {
  const {
    user,
    login,
  } = useAuth();

  const [schools, setSchools] =
    useState([]);

  const [selected, setSelected] =
    useState('');

  const [saving, setSaving] =
    useState(false);

  const [error, setError] =
    useState('');

  /*
   * Only show this modal when the
   * authenticated user has no school.
   */
  const needsSchool =
    Boolean(user && !user.school);

  useEffect(() => {
    if (!needsSchool) {
      return;
    }

    axios
      .get(
        `${API}/auth/schools`,
        {
          withCredentials: true,
        }
      )
      .then((r) => {
        setSchools(
          r.data?.schools || []
        );
      })
      .catch(() => {
        setError(
          'Could not load school options. Please refresh and try again.'
        );
      });
  }, [needsSchool]);

  if (!needsSchool) {
    return null;
  }

  const handleSave = async () => {
    if (!selected) {
      setError(
        'Please select your school to continue.'
      );
      return;
    }

    setSaving(true);
    setError('');

    try {
      /*
       * IMPORTANT:
       * The backend now updates BOTH:
       *
       * school
       * class_level
       *
       * Example:
       * NIOS -> class 10
       * BNPS -> class 8
       */
      await axios.put(
        `${API}/users/school`,
        {
          school: selected,
        },
        {
          withCredentials: true,
        }
      );

      /*
       * Get the complete updated user.
       *
       * This is important because SyllabusPage,
       * ChatPage, QuizPage, etc. all need the
       * new class_level.
       */
      const { data } =
        await axios.get(
          `${API}/auth/me`,
          {
            withCredentials: true,
          }
        );

      /*
       * Update AuthContext immediately.
       */
      login(data);

    } catch (e) {
      setError(
        e?.response?.data?.detail ||
        'Failed to save. Please try again.'
      );

      setSaving(false);
      return;
    }

    setSaving(false);
  };

  return (
    <AnimatePresence>
      <motion.div
        initial={{
          opacity: 0,
        }}
        animate={{
          opacity: 1,
        }}
        className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm px-4"
        data-testid="school-select-modal"
      >
        <motion.div
          initial={{
            opacity: 0,
            scale: 0.95,
            y: 20,
          }}
          animate={{
            opacity: 1,
            scale: 1,
            y: 0,
          }}
          transition={{
            type: 'spring',
            stiffness: 300,
            damping: 30,
          }}
          className="w-full max-w-md"
        >
          <div className="glass rounded-2xl p-8 shadow-2xl border border-white/10">

            {/* Heading */}
            <div className="flex flex-col items-center text-center mb-6">
              <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-cyan-500 to-cyan-600 flex items-center justify-center mb-4 shadow-lg shadow-cyan-500/30">
                <BookOpen
                  size={26}
                  className="text-white"
                />
              </div>

              <h2 className="text-white text-xl font-heading font-black mb-1">
                One quick thing,{' '}
                {user?.name?.split(' ')[0] ||
                  'there'}
                !
              </h2>

              <p className="text-zinc-400 text-sm font-body leading-relaxed">
                We need to know your school so we can load your exact syllabus, quizzes, and study plans.
              </p>
            </div>

            {/* School options */}
            <div className="space-y-3 mb-5">
              {schools.map(
                (school) => (
                  <button
                    key={school.id}
                    type="button"
                    data-testid={`school-option-${school.id}`}
                    disabled={
                      !school.available
                    }
                    onClick={() => {
                      if (
                        school.available
                      ) {
                        setSelected(
                          school.id
                        );

                        setError('');
                      }
                    }}
                    className={`w-full text-left px-4 py-3.5 rounded-xl border text-sm font-body transition-all relative ${
                      !school.available
                        ? 'border-white/5 bg-zinc-900/50 text-zinc-600 cursor-not-allowed'
                        : selected === school.id
                          ? 'border-cyan-500/70 bg-cyan-500/10 text-white shadow-md shadow-cyan-500/10'
                          : 'border-white/10 bg-zinc-900 text-zinc-300 hover:border-white/20 hover:text-white'
                    }`}
                  >
                    <span className="font-semibold">
                      {school.name}
                    </span>

                    {!school.available && (
                      <span className="ml-2 text-[10px] bg-zinc-800 text-zinc-500 px-2 py-0.5 rounded-full">
                        Coming Soon
                      </span>
                    )}

                    {selected ===
                      school.id && (
                      <CheckCircle2
                        size={16}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-cyan-400"
                      />
                    )}
                  </button>
                )
              )}
            </div>

            {/* Error */}
            {error && (
              <div className="flex items-start gap-2 p-3 mb-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-xs font-body">
                <AlertTriangle
                  size={14}
                  className="shrink-0 mt-0.5"
                />

                <p>
                  {error}
                </p>
              </div>
            )}

            {/* Confirm */}
            <button
              data-testid="school-modal-confirm"
              onClick={handleSave}
              disabled={
                saving ||
                !selected
              }
              className="w-full flex items-center justify-center gap-2 py-3 rounded-xl font-heading font-bold text-sm transition-all
                bg-gradient-to-r from-cyan-500 to-cyan-600 text-black hover:from-cyan-400 hover:to-cyan-500
                disabled:opacity-40 disabled:cursor-not-allowed shadow-lg shadow-cyan-500/20"
            >
              {saving ? (
                'Saving…'
              ) : (
                <>
                  Confirm & Continue
                  <ArrowRight
                    size={16}
                  />
                </>
              )}
            </button>

            <p className="text-zinc-600 text-[11px] text-center mt-3 font-body">
              Your school determines the syllabus loaded for your account.
            </p>

          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}