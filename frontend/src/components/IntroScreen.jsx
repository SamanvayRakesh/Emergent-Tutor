import { useEffect, useRef, useCallback, useState } from 'react';
import { motion } from 'framer-motion';
import { gsap } from 'gsap';
import * as THREE from 'three';

const SUBJECTS = ['Mathematics', 'Science', 'English', 'Social Science'];
const SUBJECT_COLORS = ['#22d3ee', '#10b981', '#f59e0b', '#8b5cf6'];

export default function IntroScreen({ onComplete }) {
  const canvasRef = useRef(null);
  const completedRef = useRef(false);
  const [currentSubject, setCurrentSubject] = useState(0);

  const handleComplete = useCallback(() => {
    if (completedRef.current) return;
    completedRef.current = true;
    gsap.to('.intro-wrapper', { opacity: 0, duration: 0.7, onComplete: onComplete });
  }, [onComplete]);

  useEffect(() => {
    if (!canvasRef.current) return;
    const scene = new THREE.Scene();
    const w = window.innerWidth, h = window.innerHeight;
    const camera = new THREE.PerspectiveCamera(60, w / h, 0.1, 100);
    camera.position.z = 15;

    const renderer = new THREE.WebGLRenderer({ canvas: canvasRef.current, alpha: true, antialias: true });
    renderer.setSize(w, h);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

    const count = 2500;
    const pos = new Float32Array(count * 3);
    const col = new Float32Array(count * 3);
    const palette = [new THREE.Color('#22d3ee'), new THREE.Color('#8b5cf6'), new THREE.Color('#d946ef'), new THREE.Color('#ffffff')];

    for (let i = 0; i < count; i++) {
      pos[i * 3] = (Math.random() - 0.5) * 45;
      pos[i * 3 + 1] = (Math.random() - 0.5) * 45;
      pos[i * 3 + 2] = (Math.random() - 0.5) * 25;
      const c = palette[Math.floor(Math.random() * palette.length)];
      col[i * 3] = c.r; col[i * 3 + 1] = c.g; col[i * 3 + 2] = c.b;
    }

    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    geo.setAttribute('color', new THREE.BufferAttribute(col, 3));
    const mat = new THREE.PointsMaterial({ size: 0.07, vertexColors: true, transparent: true, opacity: 0 });
    const points = new THREE.Points(geo, mat);
    scene.add(points);
    gsap.to(mat, { opacity: 0.75, duration: 2 });

    let mx = 0, my = 0;
    const onMouse = (e) => { mx = (e.clientX / w - 0.5) * 2; my = -(e.clientY / h - 0.5) * 2; };
    window.addEventListener('mousemove', onMouse);

    let id;
    const animate = () => {
      id = requestAnimationFrame(animate);
      points.rotation.y += 0.0004 + mx * 0.001;
      points.rotation.x += 0.0002 + my * 0.0005;
      renderer.render(scene, camera);
    };
    animate();

    const onResize = () => {
      camera.aspect = window.innerWidth / window.innerHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(window.innerWidth, window.innerHeight);
    };
    window.addEventListener('resize', onResize);

    return () => {
      cancelAnimationFrame(id);
      window.removeEventListener('mousemove', onMouse);
      window.removeEventListener('resize', onResize);
      renderer.dispose(); geo.dispose(); mat.dispose();
    };
  }, []);

  useEffect(() => {
    const tl = gsap.timeline({ defaults: { ease: 'power3.out' } });
    tl.to('.i-orb', { opacity: 1, scale: 1, duration: 1.2 }, 0.4)
      .to('.i-logo', { opacity: 1, y: 0, duration: 1 }, 1.3)
      .to('.i-tag', { opacity: 1, y: 0, duration: 0.8 }, 2)
      .to('.i-subj', { opacity: 1, y: 0, stagger: 0.06, duration: 0.4 }, 2.5)
      .to('.i-prog', { opacity: 1, duration: 0.5 }, 3.2)
      .to('.i-fill', { width: '100%', duration: 1.3, ease: 'none' }, 3.4)
      .to('.i-skip', { opacity: 1, duration: 0.3 }, 1.2);

    const t = setTimeout(handleComplete, 5500);
    return () => clearTimeout(t);
  }, [handleComplete]);

  return (
    <div className="intro-wrapper fixed inset-0 bg-zinc-950 z-50">
      <canvas ref={canvasRef} className="absolute inset-0 w-full h-full" />

      {/* Ambient glows */}
      <div className="absolute top-1/3 left-1/4 w-96 h-96 bg-violet-600/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />

      <div className="absolute inset-0 flex flex-col items-center justify-center z-10 px-4">
        {/* Orb */}
        <div className="i-orb opacity-0 scale-50 mb-4 relative">
          <img
            src="/aceit-logo.png"
            alt="Ace It"
            className="w-72 h-auto object-contain"
          />
        </div>

        {/* Logo title */}
        <div className="i-logo opacity-0 translate-y-8 text-center mb-2">
          <p className="text-zinc-400 text-sm font-body tracking-widest uppercase">Always Crush Exams</p>
        </div>

        <p className="i-tag opacity-0 translate-y-4 text-zinc-400 text-base sm:text-lg font-body mb-8 text-center max-w-sm">
          Your AI-powered exam prep tutor
          <br /><span className="text-cyan-400 font-semibold">Learn. Think. Master.</span>
        </p>

        {/* Subject pills */}
        <div className="flex flex-wrap gap-2 justify-center max-w-md mb-10">
          {SUBJECTS.map((s, i) => (
            <div key={s} className="i-subj opacity-0 translate-y-3 px-3 py-1 rounded-full text-xs font-body font-semibold glass"
              style={{ color: SUBJECT_COLORS[i], borderColor: SUBJECT_COLORS[i] + '50', border: `1px solid ${SUBJECT_COLORS[i]}50` }}>
              {s}
            </div>
          ))}
        </div>

        {/* Progress bar */}
        <div className="i-prog opacity-0 w-56">
          <div className="h-1 bg-zinc-800 rounded-full overflow-hidden">
            <div className="i-fill h-full w-0 rounded-full"
              style={{ background: 'linear-gradient(90deg, #22d3ee, #8b5cf6, #d946ef)', boxShadow: '0 0 8px rgba(34,211,238,0.6)' }} />
          </div>
          <p className="text-zinc-600 text-xs text-center mt-2 font-body">Initializing AI Tutor...</p>
        </div>
      </div>

      <button onClick={handleComplete} data-testid="intro-skip-btn"
        className="i-skip opacity-0 absolute bottom-6 right-6 text-zinc-500 hover:text-zinc-300 text-sm font-body border border-zinc-800 hover:border-zinc-600 rounded-full px-4 py-2 transition-all">
        Skip
      </button>
    </div>
  );
}
