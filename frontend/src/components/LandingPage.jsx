import { useEffect, useRef, useState } from 'react';
import { Navigate, useNavigate } from 'react-router-dom';
import {
  ArrowRight,
  ArrowDown,
  Sparkles,
  Brain,
  MessageSquare,
  Target,
  BarChart3,
  BookOpen,
  CalendarDays,
  Check,
  X,
  Zap,
  ChevronRight,
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

const SUBJECTS = [
  { name: 'MATHEMATICS', color: '#75e8ff' },
  { name: 'PHYSICS', color: '#bca7ff' },
  { name: 'CHEMISTRY', color: '#ffb6a0' },
  { name: 'BIOLOGY', color: '#94f0cb' },
  { name: 'ENGLISH', color: '#f7b7e3' },
  { name: 'HISTORY', color: '#ffd591' },
  { name: 'GEOGRAPHY', color: '#94f0cb' },
  { name: 'ALGEBRA', color: '#75e8ff' },
  { name: 'GEOMETRY', color: '#bca7ff' },
  { name: 'SOCIAL SCIENCE', color: '#ffb6a0' },
];

const FEATURES = [
  {
    icon: Brain,
    title: 'Teaching that adapts.',
    copy: 'Explanations shaped around your progress and the topics that need more attention.',
    color: '#bca7ff',
  },
  {
    icon: MessageSquare,
    title: 'Questions welcome.',
    copy: 'Ask again, request an example or break a difficult idea into smaller steps.',
    color: '#75e8ff',
  },
  {
    icon: Target,
    title: 'Practice with purpose.',
    copy: 'Use quizzes and mock exams to put your understanding into practice.',
    color: '#ffb6a0',
  },
  {
    icon: BarChart3,
    title: 'Progress you can see.',
    copy: 'Review quiz performance, spot weak topics and track your learning.',
    color: '#94f0cb',
  },
  {
    icon: BookOpen,
    title: 'Your chapters, together.',
    copy: 'Explore supported CBSE, NIOS and school-specific curriculum options.',
    color: '#ffd591',
  },
  {
    icon: CalendarDays,
    title: 'A clearer study plan.',
    copy: 'Organise preparation with study plans on eligible subscription plans.',
    color: '#f7b7e3',
  },
];

const LESSONS = {
  simple: {
    title: 'The simple version',
    text: 'Friction is a force that resists movement when two surfaces touch. It helps your shoes grip the ground.',
  },
  example: {
    title: 'Make it relatable',
    text: 'Imagine sliding a book across a table. It slows down because friction between the book and table resists its motion.',
  },
  deeper: {
    title: 'A little more detail',
    text: 'Friction acts against relative motion, or the tendency to move, between surfaces in contact. It can also transfer energy into heat.',
  },
};

const CSS = `
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600;700;800&family=Inter:wght@400;500;600;700;800&display=swap');

.al {
  --bg:#090c18;
  --ink:#f6f5ff;
  --muted:#a6acc2;
  --cyan:#75e8ff;
  --lav:#bca7ff;
  --mint:#94f0cb;
  --peach:#ffb6a0;
  background:var(--bg);
  color:var(--ink);
  font-family:Inter,sans-serif;
  overflow-x:clip;
}
.al,.al *{box-sizing:border-box}
.al a{text-decoration:none;color:inherit}
.al button,.al input{font:inherit}
.al button{cursor:pointer}
.al button:disabled{cursor:default}
.al a:focus-visible,.al button:focus-visible,.al input:focus-visible,.al summary:focus-visible{
  outline:2px solid var(--cyan);outline-offset:5px
}
.al-wrap{width:min(1200px,calc(100% - 64px));margin:auto}
.al-header{position:relative;z-index:5;background:#0d1121;border-bottom:1px solid #ffffff12}
.al-nav{min-height:86px;display:flex;align-items:center;justify-content:space-between;gap:24px}
.al-logo{height:54px;width:auto;object-fit:contain}
.al-links,.al-actions{display:flex;align-items:center;gap:26px}
.al-links a,.al-signin{font-size:12px;font-weight:600;color:#c1c6dc}
.al-links a:hover,.al-signin:hover{color:var(--cyan)}
.al-btn{
  border:0;border-radius:9px;padding:15px 21px;display:inline-flex;
  align-items:center;justify-content:center;gap:10px;font-size:13px;font-weight:800;
  color:#131529!important;background:linear-gradient(110deg,#75e8ff,#bca7ff);
  transition:transform .2s,box-shadow .2s
}
.al-btn:hover{transform:translateY(-3px);box-shadow:0 10px 35px #75e8ff25}
.al-btn:disabled{opacity:.65;transform:none}
.al-btn-outline{background:transparent;border:1px solid #ffffff30;color:#f6f5ff!important}
.al-hero{
  position:relative;isolation:isolate;
  background:
    radial-gradient(ellipse at 82% 25%,#8a6eff19,transparent 48%),
    radial-gradient(ellipse at 70% 90%,#75e8ff0d,transparent 45%),#090c18
}
.al-hero::before{
  content:'';position:absolute;inset:0;z-index:-1;
  background-image:linear-gradient(#ffffff03 1px,transparent 1px),
  linear-gradient(90deg,#ffffff03 1px,transparent 1px);
  background-size:64px 64px;mask-image:linear-gradient(90deg,transparent,black)
}
.al-hero-grid{
  min-height:730px;display:grid;grid-template-columns:1.05fr 1fr;
  align-items:center;gap:48px;padding:75px 0 100px
}
.al-eyebrow{
  margin:0;display:flex;align-items:center;gap:9px;color:var(--cyan);
  font-size:10px;font-weight:700;letter-spacing:.18em;text-transform:uppercase;line-height:1.8
}
.al-dot{width:6px;height:6px;border-radius:50%;background:var(--mint);box-shadow:0 0 14px #94f0cb80}
.al h1{
  font-family:'Barlow Condensed',Impact,sans-serif;font-weight:700;
  font-size:clamp(64px,7.5vw,103px);line-height:.98;letter-spacing:-.02em;margin:27px 0
}
.al h1>span{display:block}
.al-word-slot{height:2em;display:flex;align-items:flex-start}
.al-word{display:block;animation:al-word .6s cubic-bezier(.2,.8,.2,1) both}
.al-copy{color:var(--muted);font-size:14px;line-height:1.9;max-width:470px}
.al-hero-cta{display:flex;gap:12px;flex-wrap:wrap;margin-top:26px}
.al-note{font-size:11px;color:#7e88a6;line-height:1.8}
.al-hero-note{display:flex;align-items:center;gap:8px;margin-top:18px}
.al-stage{position:relative;min-width:0;height:485px;perspective:1200px}
.al-stage-glow{
  position:absolute;inset:60px 5px;background:linear-gradient(140deg,#75e8ff18,#bca7ff25,#ffb6a012);
  filter:blur(45px);border-radius:30px
}
.al-workspace{
  position:absolute;inset:45px 8px 38px;transform:rotateY(-8deg) rotateZ(2deg);
  border:1px solid #ffffff25;border-radius:15px;background:#14182a;
  box-shadow:0 35px 85px #00000060;overflow:hidden;animation:al-hover 8s ease-in-out infinite
}
.al-window-bar{
  padding:15px 18px;background:#1a1e33;border-bottom:1px solid #ffffff10;
  display:flex;align-items:center;gap:6px
}
.al-window-dot{width:6px;height:6px;border-radius:50%;background:#ffb6a0}
.al-window-dot:nth-child(2){background:#ffd591}
.al-window-dot:nth-child(3){background:#94f0cb}
.al-window-title{margin-left:10px;color:#a0a8c5;font-size:10px}
.al-workspace-body{padding:25px}
.al-chapter{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:23px}
.al-chapter h3{margin:0;font-size:17px}
.al-pill{padding:6px 9px;background:#94f0cb13;color:var(--mint);border:1px solid #94f0cb25;border-radius:5px;font-size:9px}
.al-student-msg{margin-left:35px;padding:13px 16px;background:#bca7ff13;border:1px solid #bca7ff28;border-radius:10px;color:#ded5ff;font-size:12px;line-height:1.7}
.al-tutor-msg{margin-top:16px;border-left:2px solid var(--cyan);padding-left:16px}
.al-tutor-label{display:flex;gap:7px;align-items:center;color:var(--cyan);font-size:10px;font-weight:700}
.al-tutor-msg p{font-size:12px;color:#c1c8de;line-height:1.9;margin:11px 0}
.al-equation{
  padding:12px 16px;border:1px solid #ffffff10;background:#090c1840;
  border-radius:7px;color:#f5f0ff;font-size:22px;font-weight:600;letter-spacing:.03em
}
.al-mini-actions{display:flex;gap:8px;margin-top:17px}
.al-mini-actions span{font-size:9px;padding:7px 9px;border-radius:5px;background:#ffffff06;color:#acb5cf;border:1px solid #ffffff10}
.al-float{
  position:absolute;padding:14px 17px;border-radius:10px;border:1px solid #ffffff24;
  background:#191d32;box-shadow:0 15px 40px #00000035;
  display:flex;align-items:center;gap:10px;font-size:11px;animation:al-hover 7s ease-in-out infinite
}
.al-float-top{right:-10px;top:10px;color:var(--mint);animation-delay:-2s}
.al-float-bottom{left:-22px;bottom:12px;color:var(--peach);animation-delay:-4s}
.al-stage-caption{position:absolute;bottom:-25px;right:8px;font-size:9px;color:#727e9e;letter-spacing:.16em}
.al-scroll{
  position:absolute;bottom:23px;left:calc(50% - 18px);width:36px;height:36px;
  border:1px solid #ffffff25;border-radius:50%;display:grid;place-items:center;color:#b9c0d9!important
}
.al-strip{border-top:1px solid #ffffff10;border-bottom:1px solid #ffffff10;background:#101425}
.al-strip-inner{padding:24px 0;display:flex;justify-content:space-between;flex-wrap:wrap;gap:18px}
.al-strip span{color:#a1aac6;font-size:10px;letter-spacing:.12em;text-transform:uppercase}
.al-section{padding:100px 0;scroll-margin-top:24px}
.al-heading{display:grid;grid-template-columns:1.2fr 1fr;gap:60px;align-items:end;margin-bottom:42px}
.al-title{
  margin:16px 0 0;font-family:'Barlow Condensed',Impact,sans-serif;
  font-size:clamp(44px,5vw,68px);line-height:1.03;font-weight:700;text-transform:uppercase
}
.al-title em{font-style:normal;color:var(--lav)}
.al-demo-shell{border:1px solid #ffffff20;border-radius:15px;background:#111527;overflow:hidden}
.al-demo-tabs{display:flex;gap:6px;padding:12px;background:#171b2e;border-bottom:1px solid #ffffff10}
.al-demo-tab{
  display:flex;align-items:center;justify-content:center;gap:8px;flex:1;
  border:1px solid transparent;border-radius:7px;background:transparent;color:#969fbc;
  padding:12px;font-size:12px;font-weight:600
}
.al-demo-tab[aria-selected=true]{background:#bca7ff14;border-color:#bca7ff35;color:#e3d9ff}
.al-demo-panel{padding:35px;min-height:350px;animation:al-word .35s ease both}
.al-demo-label{display:flex;align-items:center;gap:8px;color:var(--mint);font-size:10px;letter-spacing:.08em;margin-bottom:22px}
.al-demo-panel h3{font-size:22px;margin:12px 0 17px;line-height:1.4}
.al-demo-panel p{color:#a8b1cb;line-height:1.9;font-size:13px}
.al-example-question{font-size:13px;color:#e0d9ff;background:#bca7ff0d;border:1px solid #bca7ff24;border-radius:9px;padding:14px 18px;margin-bottom:23px}
.al-choice-row{display:flex;flex-wrap:wrap;gap:9px;margin-top:25px}
.al-choice{
  padding:10px 14px;border:1px solid #ffffff20;background:#ffffff04;
  color:#bcc4dc;border-radius:7px;font-size:11px
}
.al-choice[aria-pressed=true]{border-color:#75e8ff80;background:#75e8ff10;color:var(--cyan)}
.al-quiz-options{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-top:24px}
.al-quiz-option{
  border:1px solid #ffffff20;border-radius:8px;padding:20px;
  font-size:20px;color:#dedff0;background:#ffffff04
}
.al-quiz-option:hover{border-color:#bca7ff80}
.al-quiz-option.is-selected{border-color:var(--lav);background:#bca7ff18}
.al-feedback{padding:14px 17px;border-radius:8px;margin-top:18px;font-size:12px;line-height:1.8;background:#94f0cb0d;color:var(--mint);border:1px solid #94f0cb30}
.al-feedback.is-wrong{background:#ffb6a00d;color:var(--peach);border-color:#ffb6a030}
.al-demo-bottom{
  padding:18px 25px;border-top:1px solid #ffffff10;display:flex;justify-content:space-between;
  align-items:center;gap:20px;background:#0c1020
}
.al-text-btn{display:inline-flex;align-items:center;gap:8px;color:var(--cyan);border:0;background:none;font-size:12px;font-weight:700;padding:5px 0}
.al-progress-row{display:grid;grid-template-columns:110px 1fr 35px;align-items:center;gap:15px;margin:20px 0;font-size:12px;color:#c7cde2}
.al-track{height:7px;background:#ffffff08;border-radius:10px;overflow:hidden}
.al-fill{height:100%;border-radius:10px;animation:al-grow 1s ease both;transform-origin:left}
.al-progress-note{margin-top:24px;padding:16px;border:1px solid #ffd59130;background:#ffd5910b;border-radius:8px;color:#ffd591;font-size:12px;line-height:1.8}
.al-features{display:grid;grid-template-columns:repeat(3,1fr);gap:1px;background:#ffffff12;border:1px solid #ffffff12}
.al-feature{padding:30px;background:#090c18;transition:background .2s}
.al-feature:hover{background:#111628}
.al-feature h3{margin:25px 0 12px;font-size:17px;line-height:1.5}
.al-feature p{margin:0;color:#9da7c2;font-size:12px;line-height:1.9}
.al-band{background:#111527;border-top:1px solid #ffffff10;border-bottom:1px solid #ffffff10}
.al-how{display:grid;grid-template-columns:1fr 1fr;gap:80px;align-items:center}
.al-step{display:flex;gap:22px;padding:25px 0;border-bottom:1px solid #ffffff15}
.al-step-num{font-family:'Barlow Condensed',sans-serif;font-size:32px;color:var(--peach)}
.al-step h3{font-size:16px;margin:0 0 10px}
.al-step p{font-size:12px;line-height:1.9;color:#a0aac5;margin:0}
.al-final{text-align:center;padding:100px 24px;background:radial-gradient(ellipse at 50% 120%,#bca7ff20,transparent 65%),#090c18}
.al-final .al-eyebrow{justify-content:center}
.al-final .al-title{margin-bottom:24px}
.al-final p{color:var(--muted);font-size:14px;line-height:1.9}
.al-final-actions{display:flex;justify-content:center;gap:12px;flex-wrap:wrap;margin:28px 0 20px}
.al-footer{padding:30px 0;border-top:1px solid #ffffff12}
.al-footer-inner{display:flex;align-items:center;justify-content:space-between;gap:25px;flex-wrap:wrap}
.al-footer p{font-size:10px;color:#7a85a4;line-height:1.9;margin:0}
.al-footer-links{display:flex;gap:22px;font-size:11px;color:#a6b0ca}
.al-transition{
  position:fixed;inset:0;z-index:9999;background:#090c18;
  display:flex;align-items:center;justify-content:center;
  animation:al-transition-in .38s ease both
}
.al-transition::before,.al-transition::after{
  content:'';position:absolute;height:140vh;width:33vw;top:-20vh;
  background:linear-gradient(180deg,#75e8ff18,#bca7ff30,#ffb6a014);
  transform:rotate(25deg);animation:al-beam .85s cubic-bezier(.2,.8,.2,1) both
}
.al-transition::before{left:5%;animation-delay:.05s}
.al-transition::after{right:5%;animation-delay:.12s}
.al-transition-content{position:relative;z-index:1;text-align:center;padding:24px}
.al-transition-mark{
  width:75px;height:75px;margin:0 auto 25px;display:grid;place-items:center;
  border:1px solid #75e8ff70;border-radius:20px;color:var(--cyan);
  background:#75e8ff10;animation:al-mark .8s ease both
}
.al-transition-content h2{font-family:'Barlow Condensed',sans-serif;font-size:48px;line-height:1.05;margin:0}
.al-transition-content p{font-size:12px;color:#aab4d0;letter-spacing:.04em}
.al-transition-line{height:2px;width:180px;margin:25px auto;background:#ffffff10;overflow:hidden}
.al-transition-line span{display:block;height:100%;background:linear-gradient(90deg,var(--cyan),var(--lav),var(--peach));animation:al-grow .85s ease both;transform-origin:left}
@keyframes al-word{from{opacity:0;transform:translateY(12px);filter:blur(5px)}to{opacity:1;transform:translateY(0);filter:blur(0)}}
@keyframes al-hover{0%,100%{translate:0 0}50%{translate:0 -12px}}
@keyframes al-grow{from{transform:scaleX(0)}to{transform:scaleX(1)}}
@keyframes al-transition-in{from{opacity:0;clip-path:inset(100% 0 0 0)}to{opacity:1;clip-path:inset(0 0 0 0)}}
@keyframes al-beam{from{opacity:0;translate:0 70vh}to{opacity:1;translate:0 0}}
@keyframes al-mark{from{opacity:0;transform:scale(.4) rotate(-45deg)}to{opacity:1;transform:scale(1) rotate(0)}}
@media(min-width:1150px){.al-word-slot{height:1.05em}}
@media(max-width:950px){
  .al-links{display:none}.al-hero-grid{gap:25px}
  .al h1{font-size:72px}.al-stage{scale:.9}
  .al-heading{gap:30px}.al-how{gap:40px}
}
@media(max-width:700px){
  .al-wrap{width:calc(100% - 36px)}
  .al-nav{min-height:76px;gap:12px}.al-logo{height:43px}
  .al-actions{gap:14px}.al-actions .al-btn{padding:11px 13px;font-size:11px}
  .al-hero-grid{grid-template-columns:1fr;min-height:auto;padding:55px 0 80px;gap:25px}
  .al h1{font-size:clamp(62px,14vw,86px)}
  .al-stage{height:420px;scale:.95}
  .al-float-top{right:0}.al-float-bottom{left:0}
  .al-strip-inner{justify-content:center;gap:15px 24px}.al-strip span{font-size:9px}
  .al-section{padding:65px 0}
  .al-heading,.al-how{grid-template-columns:1fr;gap:25px}
  .al-features{grid-template-columns:1fr}
  .al-demo-panel{padding:22px;min-height:390px}
  .al-demo-tab{padding:10px 5px;font-size:10px;gap:5px}
  .al-demo-bottom{align-items:flex-start;flex-direction:column;gap:9px}
  .al-progress-row{grid-template-columns:90px 1fr 35px;gap:10px}
  .al-final{padding:70px 18px}.al-footer-inner{align-items:flex-start;flex-direction:column}
}
@media(max-width:380px){
  .al-stage{height:445px}.al-workspace-body{padding:18px}
  .al-quiz-option{padding:17px 10px}
}
@media(prefers-reduced-motion:reduce){
  .al *,.al *::before,.al *::after{animation:none!important;transition:none!important}
}
`;

export default function LandingPage() {
  const { user, loading } = useAuth();
  const navigate = useNavigate();

  const [subjectIndex, setSubjectIndex] = useState(0);
  const [demo, setDemo] = useState('tutor');
  const [explanation, setExplanation] = useState('simple');
  const [answer, setAnswer] = useState(null);
  const [transitioning, setTransitioning] = useState(false);
  const [reducedMotion, setReducedMotion] = useState(false);

  const navigationTimer = useRef(null);
  const navigationPending = useRef(false);

  useEffect(() => {
    const media = window.matchMedia(
      '(prefers-reduced-motion: reduce)'
    );

    const update = () => setReducedMotion(media.matches);
    update();
    media.addEventListener('change', update);

    return () => media.removeEventListener('change', update);
  }, []);

  useEffect(() => {
    if (reducedMotion) return undefined;

    const interval = window.setInterval(() => {
      setSubjectIndex((index) => (index + 1) % SUBJECTS.length);
    }, 3000);

    return () => window.clearInterval(interval);
  }, [reducedMotion]);

  useEffect(() => {
    return () => {
      if (navigationTimer.current !== null) {
        window.clearTimeout(navigationTimer.current);
      }
    };
  }, []);

  const openAuth = (tab = 'register') => {
    if (navigationPending.current) return;

    navigationPending.current = true;

    const destination = `/login?tab=${tab}`;

    if (reducedMotion) {
      navigate(destination);
      return;
    }

    setTransitioning(true);

    navigationTimer.current = window.setTimeout(() => {
      navigate(destination);
    }, 950);
  };

  const subject = SUBJECTS[subjectIndex];
  const lesson = LESSONS[explanation];

  if (loading) {
    return (
      <div className="min-h-screen bg-zinc-950 flex items-center justify-center">
        <p className="text-zinc-400 text-sm">Loading Ace-it...</p>
      </div>
    );
  }

  if (user) {
    return <Navigate to="/" replace />;
  }

  return (
    <main className="al">
      <style>{CSS}</style>

      {transitioning && (
        <div
          className="al-transition"
          role="status"
          aria-live="polite"
          aria-label="Opening your account page"
        >
          <div className="al-transition-content">
            <div className="al-transition-mark">
              <Sparkles size={32} />
            </div>
            <h2>YOUR NEXT CHAPTER.</h2>
            <p>Opening your Ace-it account page...</p>
            <div className="al-transition-line">
              <span />
            </div>
          </div>
        </div>
      )}

      <div inert={transitioning ? true : undefined}>
        <header className="al-header">
          <nav className="al-wrap al-nav" aria-label="Main navigation">
            <a href="#top" aria-label="Ace-it home">
              <img
                src="/aceit-logo.png"
                alt="Ace-it"
                className="al-logo"
              />
            </a>

            <div className="al-links">
              <a href="#demo">Try the experience</a>
              <a href="#features">The platform</a>
              <a href="#how">How it works</a>
            </div>

            <div className="al-actions">
              <button
                type="button"
                className="al-text-btn al-signin"
                onClick={() => openAuth('login')}
              >
                Sign in
              </button>

              <button
                type="button"
                className="al-btn"
                onClick={() => openAuth('register')}
              >
                Sign up <ArrowRight size={14} />
              </button>
            </div>
          </nav>
        </header>

        <section className="al-hero" id="top">
          <div className="al-wrap al-hero-grid">
            <div>
              <p className="al-eyebrow">
                <span className="al-dot" />
                Curiosity looks good on you
              </p>

              <h1>
                <span>BIG QUESTIONS.</span>
                <span>BETTER AT</span>

                <span className="al-word-slot">
                  <span
                    key={subject.name}
                    className="al-word"
                    style={{ color: subject.color }}
                  >
                    {subject.name}
                  </span>
                </span>
              </h1>

              <p className="al-copy">
                That moment when a difficult idea finally clicks?
                Let’s get you there. Ace-it brings adaptive tutoring,
                practice and progress into one study space.
              </p>

              <div className="al-hero-cta">
                <button
                  type="button"
                  className="al-btn"
                  onClick={() => openAuth('register')}
                >
                  Create a free account <ArrowRight size={16} />
                </button>

                <a href="#demo" className="al-btn al-btn-outline">
                  Try the demos <ChevronRight size={16} />
                </a>
              </div>

              <p className="al-note al-hero-note">
                <Check size={12} />
                Start free. Explore at your own pace.
              </p>
            </div>

            <div className="al-stage" aria-label="Illustrative Ace-it tutor preview">
              <div className="al-stage-glow" aria-hidden="true" />

              <div className="al-workspace">
                <div className="al-window-bar">
                  <span className="al-window-dot" />
                  <span className="al-window-dot" />
                  <span className="al-window-dot" />
                  <span className="al-window-title">
                    Ace-it / Your learning space
                  </span>
                </div>

                <div className="al-workspace-body">
                  <div className="al-chapter">
                    <h3>A little less confusing.</h3>
                    <span className="al-pill">TUTOR PREVIEW</span>
                  </div>

                  <div className="al-student-msg">
                    Wait, why does a negative exponent make a fraction?
                  </div>

                  <div className="al-tutor-msg">
                    <span className="al-tutor-label">
                      <Sparkles size={13} /> ACE-IT TUTOR
                    </span>

                    <p>
                      It tells you to take the reciprocal.
                      The base stays the same; the power becomes positive.
                    </p>

                    <div className="al-equation">
                      2⁻³ = 1 / 2³ = 1 / 8
                    </div>
                  </div>

                  <div className="al-mini-actions" aria-hidden="true">
                    <span>Another example</span>
                    <span>Practice this</span>
                  </div>
                </div>
              </div>

              <div className="al-float al-float-top" aria-hidden="true">
                <Brain size={18} />
                Built around your learning
              </div>

              <div className="al-float al-float-bottom" aria-hidden="true">
                <Zap size={18} />
                Small steps. Bigger understanding.
              </div>

              <span className="al-stage-caption">
                A PREVIEW OF WHAT’S POSSIBLE
              </span>
            </div>
          </div>

          <a
            href="#demo"
            className="al-scroll"
            aria-label="Scroll to interactive demos"
          >
            <ArrowDown size={17} />
          </a>
        </section>

        <div className="al-strip">
          <div className="al-wrap al-strip-inner">
            <span>Adaptive tutoring</span>
            <span>Quizzes & mock exams</span>
            <span>Supported curricula</span>
            <span>Your progress, visible</span>
          </div>
        </div>

        <section id="demo" className="al-section">
          <div className="al-wrap">
            <div className="al-heading">
              <div>
                <p className="al-eyebrow">A little test drive</p>
                <h2 className="al-title">
                  DON’T JUST READ IT.
                  <br />
                  <em>GET A FEEL FOR IT.</em>
                </h2>
              </div>

              <p className="al-copy">
                Explore three interactive previews of Ace-it’s
                tutoring, quizzes and progress tools. These examples
                use sample content; your full learning space starts
                after signup.
              </p>
            </div>

            <div className="al-demo-shell">
              <div
                className="al-demo-tabs"
                role="tablist"
                aria-label="Feature previews"
              >
                {[
                  { id: 'tutor', label: 'AI Tutor', icon: MessageSquare },
                  { id: 'quiz', label: 'Quick Quiz', icon: Target },
                  { id: 'progress', label: 'Progress', icon: BarChart3 },
                ].map((item) => {
                  const Icon = item.icon;

                  return (
                    <button
                      type="button"
                      key={item.id}
                      id={`demo-tab-${item.id}`}
                      role="tab"
                      aria-selected={demo === item.id}
                      aria-controls={`demo-panel-${item.id}`}
                      className="al-demo-tab"
                      onClick={() => setDemo(item.id)}
                    >
                      <Icon size={15} />
                      {item.label}
                    </button>
                  );
                })}
              </div>

              <div
                key={demo}
                id={`demo-panel-${demo}`}
                role="tabpanel"
                aria-labelledby={`demo-tab-${demo}`}
                className="al-demo-panel"
                tabIndex={0}
              >
                {demo === 'tutor' && (
                  <>
                    <div className="al-demo-label">
                      <Sparkles size={13} />
                      INTERACTIVE EXPLANATION PREVIEW
                    </div>

                    <div className="al-example-question">
                      “What is friction? Explain it in a way I understand.”
                    </div>

                    <h3>{lesson.title}</h3>
                    <p aria-live="polite">{lesson.text}</p>

                    <div className="al-choice-row">
                      {[
                        ['simple', 'Keep it simple'],
                        ['example', 'Give me an example'],
                        ['deeper', 'Go a little deeper'],
                      ].map(([id, label]) => (
                        <button
                          type="button"
                          key={id}
                          className="al-choice"
                          aria-pressed={explanation === id}
                          onClick={() => setExplanation(id)}
                        >
                          {label}
                        </button>
                      ))}
                    </div>
                  </>
                )}

                {demo === 'quiz' && (
                  <>
                    <div className="al-demo-label">
                      <Target size={13} />
                      ONE QUESTION. TRY IT.
                    </div>

                    <h3>What is 2⁻³?</h3>

                    <p>
                      Pick an answer to see the explanation.
                    </p>

                    <div className="al-quiz-options">
                      {['−8', '1/8', '8'].map((option) => (
                        <button
                          type="button"
                          key={option}
                          className={`al-quiz-option ${
                            answer === option ? 'is-selected' : ''
                          }`}
                          aria-pressed={answer === option}
                          onClick={() => setAnswer(option)}
                        >
                          {option}
                        </button>
                      ))}
                    </div>

                    {answer !== null && (
                      <div
                        role="status"
                        className={`al-feedback ${
                          answer !== '1/8' ? 'is-wrong' : ''
                        }`}
                      >
                        {answer === '1/8' ? (
                          <Check size={14} />
                        ) : (
                          <X size={14} />
                        )}
                        {' '}
                        {answer === '1/8'
                          ? 'You got it! '
                          : 'A useful mistake to learn from. '}
                        A negative exponent means reciprocal:
                        2⁻³ = 1 / 2³ = 1/8.
                      </div>
                    )}

                    {answer !== null && (
                      <button
                        type="button"
                        className="al-text-btn"
                        style={{ marginTop: 14 }}
                        onClick={() => setAnswer(null)}
                      >
                        Reset question <ArrowRight size={13} />
                      </button>
                    )}
                  </>
                )}

                {demo === 'progress' && (
                  <>
                    <div className="al-demo-label">
                      <BarChart3 size={13} />
                      SAMPLE PROGRESS VIEW
                    </div>

                    <h3>Know what needs your attention.</h3>
                    <p>
                      An illustrative view of quiz accuracy by topic.
                      These are sample scores, not your account data.
                    </p>

                    {[
                      { name: 'Exponents', value: 80, color: '#75e8ff' },
                      { name: 'Fractions', value: 65, color: '#bca7ff' },
                      { name: 'Geometry', value: 45, color: '#ffb6a0' },
                    ].map((topic) => (
                      <div className="al-progress-row" key={topic.name}>
                        <span>{topic.name}</span>

                        <div
                          className="al-track"
                          role="meter"
                          aria-label={`${topic.name} sample accuracy`}
                          aria-valuemin={0}
                          aria-valuemax={100}
                          aria-valuenow={topic.value}
                        >
                          <div
                            className="al-fill"
                            style={{
                              width: `${topic.value}%`,
                              background: topic.color,
                            }}
                          />
                        </div>

                        <span>{topic.value}%</span>
                      </div>
                    ))}

                    <div className="al-progress-note">
                      In this example, geometry needs the most practice.
                      A clearer next step beats guessing what to study.
                    </div>
                  </>
                )}
              </div>

              <div className="al-demo-bottom">
                <span className="al-note">
                  Sample previews • No account needed to explore
                </span>

                <button
                  type="button"
                  className="al-text-btn"
                  onClick={() => openAuth('register')}
                >
                  Open your learning space <ArrowRight size={15} />
                </button>
              </div>
            </div>
          </div>
        </section>

        <section id="features" className="al-section al-band">
          <div className="al-wrap">
            <div className="al-heading">
              <div>
                <p className="al-eyebrow">One space. More possibilities.</p>
                <h2 className="al-title">
                  BUILT FOR YOUR
                  <br />
                  <em>“NOW I GET IT.”</em>
                </h2>
              </div>

              <p className="al-copy">
                A chapter to understand. A quiz to practise.
                A little progress to build on. Your study tools
                should work together.
              </p>
            </div>

            <div className="al-features">
              {FEATURES.map((feature) => {
                const Icon = feature.icon;

                return (
                  <article className="al-feature" key={feature.title}>
                    <Icon
                      size={25}
                      strokeWidth={1.5}
                      style={{ color: feature.color }}
                    />
                    <h3>{feature.title}</h3>
                    <p>{feature.copy}</p>
                  </article>
                );
              })}
            </div>
          </div>
        </section>

        <section id="how" className="al-section">
          <div className="al-wrap al-how">
            <div>
              <p className="al-eyebrow">Begin with curiosity</p>

              <h2 className="al-title">
                ONE QUESTION.
                <br />
                ONE SMALL STEP.
                <br />
                <em>THEN ANOTHER.</em>
              </h2>

              <p className="al-copy">
                You don’t need to have everything figured out.
                Start with the part that feels confusing.
              </p>

              <button
                type="button"
                className="al-btn"
                style={{ marginTop: 15 }}
                onClick={() => openAuth('register')}
              >
                Start learning free <ArrowRight size={16} />
              </button>
            </div>

            <div>
              {[
                {
                  number: '01',
                  title: 'Find your chapter.',
                  copy: 'Choose your supported school or curriculum and explore the chapters available for your grade.',
                },
                {
                  number: '02',
                  title: 'Make the difficult part smaller.',
                  copy: 'Ask your tutor for an explanation, another example or help with a specific step.',
                },
                {
                  number: '03',
                  title: 'Turn understanding into practice.',
                  copy: 'Try quizzes, review your results and return to the topics that need more attention.',
                },
              ].map((step) => (
                <article className="al-step" key={step.number}>
                  <span className="al-step-num">{step.number}</span>
                  <div>
                    <h3>{step.title}</h3>
                    <p>{step.copy}</p>
                  </div>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section className="al-final">
          <p className="al-eyebrow">
            <Sparkles size={14} />
            Your next chapter starts here
          </p>

          <h2 className="al-title">
            STAY CURIOUS.
            <br />
            <em>MAKE IT CLICK.</em>
          </h2>

          <p>
            Your pace. Your questions. A more personal way to learn.
          </p>

          <div className="al-final-actions">
            <button
              type="button"
              className="al-btn"
              onClick={() => openAuth('register')}
            >
              Create a free account <ArrowRight size={16} />
            </button>

            <button
              type="button"
              className="al-btn al-btn-outline"
              onClick={() => openAuth('login')}
            >
              Sign in
            </button>
          </div>

          <span className="al-note">
            AI features use credits. Availability depends on your plan
            and supported curriculum.
          </span>
        </section>

        <footer className="al-footer">
          <div className="al-wrap al-footer-inner">
            <p>
              © {new Date().getFullYear()} Ace-it AI.
              <br />
              This property belongs to Codegeeko Academy Private Limited.
            </p>

            <div className="al-footer-links">
              <a href="/terms">Terms</a>
              <a href="/privacy">Privacy</a>
              <button
                type="button"
                className="al-text-btn"
                onClick={() => openAuth('login')}
              >
                Sign in
              </button>
            </div>
          </div>
        </footer>
      </div>
    </main>
  );
}