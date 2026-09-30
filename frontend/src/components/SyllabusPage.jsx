import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

import {
  BookOpen,
  ChevronRight,
  Search,
  Sparkles,
  GraduationCap,
  ShieldCheck,
} from 'lucide-react';

import {
  motion,
  AnimatePresence,
} from 'framer-motion';

import axios from 'axios';

import { useAuth } from '../contexts/AuthContext';

const API =
  `${process.env.REACT_APP_BACKEND_URL}/api`;

const SUBJECT_ICONS = {
  Mathematics: '∑',
  Science: '⚗',
  Physics: '⚡',
  Chemistry: '🧪',
  Biology: '🌿',
  English: '📖',
  'Social Science': '🌍',
  'Computer Science': '💻',
  Accountancy: '📊',
  'Business Studies': '💼',
  'Data Entry Operations': '💻',
  Economics: '📈',
  Entrepreneurship: '🚀',
  'Folk Art': '🎨',
};

const SUBJECT_COLORS = {
  Mathematics: '#22d3ee',
  Science: '#8b5cf6',
  Physics: '#06b6d4',
  Chemistry: '#d946ef',
  Biology: '#10b981',
  English: '#f59e0b',
  'Social Science': '#3b82f6',
  'Computer Science': '#ef4444',
  Accountancy: '#f59e0b',
  'Business Studies': '#8b5cf6',
  'Data Entry Operations': '#22d3ee',
  Economics: '#10b981',
  Entrepreneurship: '#f472b6',
  'Folk Art': '#fcd34d',
};

export default function SyllabusPage() {
  const nav = useNavigate();

  const { user } =
    useAuth();

  /*
   * NIOS is ALWAYS Class 10.
   *
   * This also protects older Google accounts
   * that were accidentally left with class_level=9.
   */
  const isNios =
    user?.school === 'nios';

  const isBNPS =
    user?.school ===
    'brooklyn_national';

  const userClass =
    isNios
      ? '10'
      : user?.class_level ||
        '9';

  /*
   * NIOS uses its own curriculum,
   * not CBSE/NCERT badges.
   */
  const showVerifiedBadge =
    !isNios;

  const verifiedLabel =
    isBNPS
      ? 'BNPS'
      : 'NCERT';

  const verifiedTitle =
    isBNPS
      ? 'Chapters verified against Brooklyn National Public School curriculum'
      : 'Chapters verified against official NCERT textbooks';

  const [subjects, setSubjects] =
    useState([]);

  const [
    selectedSubject,
    setSelectedSubject,
  ] = useState(null);

  const [chapters, setChapters] =
    useState([]);

  const [search, setSearch] =
    useState('');

  const [loading, setLoading] =
    useState(true);

  const [view, setView] =
    useState('subjects');

  /*
   * Load the curriculum for the
   * user's active class.
   */
  useEffect(() => {
    setLoading(true);

    axios
      .get(
        `${API}/syllabus/${userClass}/subjects`,
        {
          withCredentials: true,
        }
      )
      .then((r) => {
        setSubjects(
          r.data || []
        );
      })
      .catch(() => {
        setSubjects([]);
      })
      .finally(() => {
        setLoading(false);
      });
  }, [userClass]);

  const selectSubject = async (
    subject
  ) => {
    setSelectedSubject(
      subject
    );

    setLoading(true);

    try {
      const r =
        await axios.get(
          `${API}/syllabus/${userClass}/${encodeURIComponent(subject.name)}/chapters`,
          {
            withCredentials: true,
          }
        );

      setChapters(
        r.data || []
      );

      setView(
        'chapters'
      );
    } catch {
      setChapters([]);
    } finally {
      setLoading(false);
    }
  };

  const startChat = (
    chapter
  ) => {
    /*
     * Pass the same effective class
     * that was used to load the syllabus.
     *
     * For NIOS this is always 10.
     */
    nav('/chat', {
      state: {
        class_level:
          userClass,
        subject:
          selectedSubject?.name,
        chapter:
          chapter.name,
        chapter_id:
          chapter.id,
      },
    });
  };

  const filteredChapters =
    chapters.filter(
      (chapter) =>
        chapter.name
          .toLowerCase()
          .includes(
            search.toLowerCase()
          )
    );

  const subjectColor =
    selectedSubject
      ? (
          SUBJECT_COLORS[
            selectedSubject.name
          ] ||
          '#22d3ee'
        )
      : '#22d3ee';

  const syllabusTitle =
    isNios
      ? 'NIOS Secondary Syllabus'
      : `Class ${userClass} Syllabus`;

  const subjectTitle =
    isNios
      ? 'NIOS Secondary Subjects'
      : `Class ${userClass} Subjects`;

  return (
    <div className="p-4 sm:p-6 max-w-4xl mx-auto">

      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-2 text-zinc-600 text-sm font-body mb-2">
          <button
            onClick={() => {
              setView(
                'subjects'
              );

              setSelectedSubject(
                null
              );

              setSearch('');
            }}
            className="hover:text-zinc-400 transition-colors"
          >
            {syllabusTitle}
          </button>

          {selectedSubject && (
            <>
              <ChevronRight
                size={12}
              />

              <span className="text-zinc-400">
                {selectedSubject.name}
              </span>
            </>
          )}
        </div>

        <h1 className="text-2xl sm:text-3xl font-heading font-black text-white flex items-center gap-3">
          <GraduationCap
            size={28}
            className="text-cyan-400"
          />

          {syllabusTitle}
        </h1>

        <p className="text-zinc-500 text-sm font-body mt-1">
          {isNios
            ? 'NIOS Secondary Course • Class 10 curriculum'
            : `Your locked grade • Class ${userClass}`}
        </p>
      </div>

      <AnimatePresence mode="wait">

        {/* SUBJECTS */}
        {view ===
          'subjects' && (
          <motion.div
            key="subjects"
            initial={{
              opacity: 0,
              x: 10,
            }}
            animate={{
              opacity: 1,
              x: 0,
            }}
            exit={{
              opacity: 0,
              x: -10,
            }}
          >
            <h2 className="text-white font-heading font-bold mb-4">
              {subjectTitle}
            </h2>

            {loading ? (
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
                {[
                  ...Array(6),
                ].map(
                  (_, i) => (
                    <div
                      key={i}
                      className="h-32 rounded-2xl shimmer bg-zinc-900"
                    />
                  )
                )}
              </div>
            ) : (
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
                {subjects.map(
                  (
                    subject,
                    i
                  ) => {
                    const color =
                      SUBJECT_COLORS[
                        subject.name
                      ] ||
                      '#22d3ee';

                    return (
                      <motion.button
                        key={
                          subject.name
                        }
                        initial={{
                          opacity: 0,
                          y: 10,
                        }}
                        animate={{
                          opacity: 1,
                          y: 0,
                        }}
                        transition={{
                          delay:
                            i * 0.06,
                        }}
                        onClick={() =>
                          selectSubject(
                            subject
                          )
                        }
                        data-testid={`subject-btn-${subject.name}`}
                        className="p-5 rounded-2xl border text-left transition-all hover:-translate-y-1 card-3d"
                        style={{
                          background:
                            color +
                            '08',
                          borderColor:
                            color +
                            '25',
                        }}
                      >
                        <div className="text-3xl mb-3">
                          {SUBJECT_ICONS[
                            subject.name
                          ] ||
                            '📚'}
                        </div>

                        <h3 className="text-white font-heading font-bold text-base leading-tight mb-1">
                          {
                            subject.name
                          }
                        </h3>

                        <div className="flex items-center gap-2">
                          <p className="text-zinc-500 text-xs font-body">
                            {
                              subject.chapter_count
                            }{' '}
                            chapters
                          </p>

                          {subject.verified &&
                            showVerifiedBadge && (
                              <span
                                className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded-full text-[10px] font-body font-semibold"
                                style={{
                                  background:
                                    '#10b98122',
                                  color:
                                    '#10b981',
                                  border:
                                    '1px solid #10b98155',
                                }}
                                data-testid={`verified-${subject.name}`}
                                title={
                                  verifiedTitle
                                }
                              >
                                <ShieldCheck
                                  size={
                                    10
                                  }
                                />

                                {
                                  verifiedLabel
                                }
                              </span>
                            )}
                        </div>
                      </motion.button>
                    );
                  }
                )}
              </div>
            )}
          </motion.div>
        )}

        {/* CHAPTERS */}
        {view ===
          'chapters' && (
          <motion.div
            key="chapters"
            initial={{
              opacity: 0,
              x: 10,
            }}
            animate={{
              opacity: 1,
              x: 0,
            }}
            exit={{
              opacity: 0,
              x: -10,
            }}
          >
            <div className="flex items-center gap-3 mb-4">
              <button
                onClick={() => {
                  setView(
                    'subjects'
                  );

                  setSelectedSubject(
                    null
                  );

                  setSearch('');
                }}
                data-testid="back-to-subjects-btn"
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-white/10 bg-white/5 text-zinc-400 hover:text-white hover:border-white/20 text-xs font-body transition-all"
              >
                ← Back
              </button>

              <h2 className="text-white font-heading font-bold flex-1">
                {
                  selectedSubject?.name
                }{' '}
                Chapters
              </h2>

              <div className="relative">
                <Search
                  size={14}
                  className="absolute left-3 top-2.5 text-zinc-500"
                />

                <input
                  value={search}
                  onChange={(e) =>
                    setSearch(
                      e.target.value
                    )
                  }
                  placeholder="Search..."
                  className="bg-zinc-900 border border-white/10 rounded-xl pl-8 pr-4 py-2 text-sm text-white placeholder-zinc-600 focus:outline-none focus:border-cyan-500/50 w-44 font-body"
                />
              </div>
            </div>

            <div className="space-y-2">
              {filteredChapters.map(
                (
                  chapter,
                  i
                ) => (
                  <motion.div
                    key={
                      chapter.id
                    }
                    initial={{
                      opacity: 0,
                      y: 5,
                    }}
                    animate={{
                      opacity: 1,
                      y: 0,
                    }}
                    transition={{
                      delay:
                        i * 0.03,
                    }}
                    className="flex items-center gap-3 p-3.5 rounded-xl glass-surface border border-white/5 hover:border-white/10 transition-all group"
                  >
                    <div
                      className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
                      style={{
                        background:
                          subjectColor +
                          '10',
                      }}
                    >
                      <BookOpen
                        size={14}
                        style={{
                          color:
                            subjectColor,
                        }}
                      />
                    </div>

                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <p className="text-white text-sm font-body font-medium truncate flex-1">
                          {
                            chapter.name
                          }
                        </p>

                        {chapter.verified &&
                          showVerifiedBadge && (
                            <span
                              className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded-full text-[10px] font-body font-semibold flex-shrink-0"
                              style={{
                                background:
                                  '#10b98122',
                                color:
                                  '#10b981',
                                border:
                                  '1px solid #10b98155',
                              }}
                              title={
                                verifiedTitle
                              }
                            >
                              <ShieldCheck
                                size={
                                  10
                                }
                              />

                              {
                                verifiedLabel
                              }
                            </span>
                          )}
                      </div>

                      <p className="text-zinc-600 text-xs font-body mt-0.5">
                        {chapter.book_title ||
                          (
                            isNios
                              ? 'NIOS Secondary Textbook'
                              : isBNPS
                                ? 'BNPS Textbook'
                                : 'NCERT Textbook'
                          )}
                      </p>
                    </div>

                    <button
                      onClick={() =>
                        startChat(
                          chapter
                        )
                      }
                      data-testid={`start-chapter-${chapter.id}`}
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-body font-semibold opacity-0 group-hover:opacity-100 transition-all"
                      style={{
                        background:
                          subjectColor +
                          '20',
                        color:
                          subjectColor,
                        border:
                          `1px solid ${subjectColor}40`,
                      }}
                    >
                      <Sparkles
                        size={12}
                      />

                      Learn
                    </button>
                  </motion.div>
                )
              )}
            </div>

            {filteredChapters.length ===
              0 && (
              <div className="text-center py-10 text-zinc-600 font-body">
                No chapters found
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}