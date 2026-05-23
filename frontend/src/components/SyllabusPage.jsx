import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { BookOpen, ChevronRight, Search, X, Sparkles, ArrowRight, GraduationCap } from 'lucide-react';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const SUBJECT_ICONS = {
  Mathematics: '∑', Science: '⚗', Physics: '⚡', Chemistry: '🧪',
  Biology: '🌿', English: '📖', 'Social Science': '🌍', 'Computer Science': '💻'
};

const SUBJECT_COLORS = {
  Mathematics: '#22d3ee', Science: '#8b5cf6', Physics: '#06b6d4',
  Chemistry: '#d946ef', Biology: '#10b981', English: '#f59e0b',
  'Social Science': '#3b82f6', 'Computer Science': '#ef4444'
};

export default function SyllabusPage() {
  const nav = useNavigate();
  const [classes, setClasses] = useState([]);
  const [selectedClass, setSelectedClass] = useState('');
  const [subjects, setSubjects] = useState([]);
  const [selectedSubject, setSelectedSubject] = useState(null);
  const [chapters, setChapters] = useState([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(false);
  const [view, setView] = useState('classes'); // 'classes' | 'subjects' | 'chapters'

  useEffect(() => {
    axios.get(`${API}/syllabus/classes`, { withCredentials: true })
      .then(r => setClasses(r.data));
  }, []);

  const selectClass = async (cls) => {
    setSelectedClass(cls);
    setLoading(true);
    const r = await axios.get(`${API}/syllabus/${cls}/subjects`, { withCredentials: true });
    setSubjects(r.data);
    setView('subjects');
    setLoading(false);
  };

  const selectSubject = async (subj) => {
    setSelectedSubject(subj);
    setLoading(true);
    const r = await axios.get(`${API}/syllabus/${selectedClass}/${encodeURIComponent(subj.name)}/chapters`, { withCredentials: true });
    setChapters(r.data);
    setView('chapters');
    setLoading(false);
  };

  const startChat = (chapter) => {
    nav('/chat', { state: { class_level: selectedClass, subject: selectedSubject?.name, chapter: chapter.name, chapter_id: chapter.id } });
  };

  const filteredChapters = chapters.filter(c => c.name.toLowerCase().includes(search.toLowerCase()));
  const subjectColor = selectedSubject ? (SUBJECT_COLORS[selectedSubject.name] || '#22d3ee') : '#22d3ee';

  return (
    <div className="p-4 sm:p-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-2 text-zinc-600 text-sm font-body mb-2">
          <button onClick={() => { setView('classes'); setSelectedClass(''); }} className="hover:text-zinc-400 transition-colors">Classes</button>
          {selectedClass && <>
            <ChevronRight size={12} />
            <button onClick={() => { setView('subjects'); setSelectedSubject(null); }} className="hover:text-zinc-400 transition-colors">Class {selectedClass}</button>
          </>}
          {selectedSubject && <>
            <ChevronRight size={12} />
            <span className="text-zinc-400">{selectedSubject.name}</span>
          </>}
        </div>
        <h1 className="text-2xl sm:text-3xl font-heading font-black text-white flex items-center gap-3">
          <GraduationCap size={28} className="text-cyan-400" />
          CBSE Syllabus
        </h1>
        <p className="text-zinc-500 text-sm font-body mt-1">Classes 6–12 • All Subjects</p>
      </div>

      {/* Classes View */}
      <AnimatePresence mode="wait">
        {view === 'classes' && (
          <motion.div key="classes" initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 10 }}>
            <div className="grid grid-cols-3 sm:grid-cols-4 lg:grid-cols-7 gap-3">
              {classes.map((cls, i) => (
                <motion.button key={cls.id} initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: i * 0.05 }}
                  onClick={() => selectClass(cls.id)} data-testid={`class-btn-${cls.id}`}
                  className="aspect-square flex flex-col items-center justify-center rounded-2xl glass-surface border border-white/5 hover:border-cyan-500/30 hover:bg-cyan-500/5 transition-all group">
                  <span className="text-2xl font-heading font-black text-white group-hover:text-cyan-400 transition-colors">{cls.id}</span>
                  <span className="text-zinc-600 text-xs font-body group-hover:text-zinc-400 transition-colors">Class</span>
                </motion.button>
              ))}
            </div>

            <div className="mt-8 p-5 rounded-2xl glass border border-cyan-500/15" style={{ background: 'rgba(34,211,238,0.04)' }}>
              <div className="flex items-center gap-2 mb-2">
                <Sparkles size={16} className="text-cyan-400" />
                <span className="text-cyan-400 text-sm font-body font-semibold">AI-Powered Learning</span>
              </div>
              <p className="text-zinc-400 text-sm font-body">Select any class and chapter to start a personalized AI tutoring session. The AI adapts to your pace and learning style.</p>
            </div>
          </motion.div>
        )}

        {view === 'subjects' && (
          <motion.div key="subjects" initial={{ opacity: 0, x: 10 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -10 }}>
            <h2 className="text-white font-heading font-bold mb-4">Class {selectedClass} Subjects</h2>
            {loading ? (
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
                {[...Array(6)].map((_, i) => <div key={i} className="h-32 rounded-2xl shimmer bg-zinc-900" />)}
              </div>
            ) : (
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
                {subjects.map((subj, i) => {
                  const color = SUBJECT_COLORS[subj.name] || '#22d3ee';
                  return (
                    <motion.button key={subj.name} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.06 }}
                      onClick={() => selectSubject(subj)} data-testid={`subject-btn-${subj.name}`}
                      className="p-5 rounded-2xl border text-left transition-all hover:-translate-y-1 card-3d"
                      style={{ background: color + '08', borderColor: color + '25' }}>
                      <div className="text-3xl mb-3">{SUBJECT_ICONS[subj.name] || '📚'}</div>
                      <h3 className="text-white font-heading font-bold text-base leading-tight mb-1">{subj.name}</h3>
                      <p className="text-zinc-500 text-xs font-body">{subj.chapter_count} chapters</p>
                    </motion.button>
                  );
                })}
              </div>
            )}
          </motion.div>
        )}

        {view === 'chapters' && (
          <motion.div key="chapters" initial={{ opacity: 0, x: 10 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -10 }}>
            <div className="flex items-center gap-3 mb-4">
              <h2 className="text-white font-heading font-bold flex-1">{selectedSubject?.name} Chapters</h2>
              <div className="relative">
                <Search size={14} className="absolute left-3 top-2.5 text-zinc-500" />
                <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search..."
                  className="bg-zinc-900 border border-white/10 rounded-xl pl-8 pr-4 py-2 text-sm text-white placeholder-zinc-600 focus:outline-none focus:border-cyan-500/50 w-44 font-body" />
              </div>
            </div>

            <div className="space-y-2">
              {filteredChapters.map((ch, i) => (
                <motion.div key={ch.id} initial={{ opacity: 0, y: 5 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.03 }}
                  className="flex items-center gap-3 p-3.5 rounded-xl glass-surface border border-white/5 hover:border-white/10 transition-all group">
                  <div className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 text-xs font-heading font-bold text-zinc-600"
                    style={{ background: subjectColor + '10', color: subjectColor }}>
                    {i + 1}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-white text-sm font-body font-medium truncate">{ch.name}</p>
                    <p className="text-zinc-600 text-xs font-body mt-0.5">{ch.lessons?.length || 0} lessons</p>
                  </div>
                  <button onClick={() => startChat(ch)} data-testid={`start-chapter-${ch.id}`}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-body font-semibold opacity-0 group-hover:opacity-100 transition-all"
                    style={{ background: subjectColor + '20', color: subjectColor, border: `1px solid ${subjectColor}40` }}>
                    <Sparkles size={12} /> Learn
                  </button>
                </motion.div>
              ))}
            </div>

            {filteredChapters.length === 0 && (
              <div className="text-center py-10 text-zinc-600 font-body">No chapters found</div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
