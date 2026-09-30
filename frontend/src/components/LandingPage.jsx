import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowRight, Sparkles, Rocket } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import * as THREE from 'three';

const FEATURES = [
  {
    icon: '🧠',
    title: 'Adaptive Learning AI',
    description:
      'Our AI adapts in real-time to your learning pace, style, and gaps. It personalizes every explanation, example, and quiz.',
    color: '#67e8f9',
    gradient: 'from-cyan-300 to-blue-400',
  },
  {
    icon: '💬',
    title: 'Chat with Your AI Tutor',
    description:
      'Ask any question anytime. Get instant explanations with step-by-step breakdowns tailored just for you.',
    color: '#d8b4fe',
    gradient: 'from-violet-300 to-purple-400',
  },
  {
    icon: '🎯',
    title: 'Smart Quizzes & Exams',
    description:
      'AI-generated practice questions that adapt to your performance. Mock exams that mirror real board patterns.',
    color: '#f472b6',
    gradient: 'from-pink-300 to-rose-400',
  },
  {
    icon: '📈',
    title: 'Real-Time Analytics',
    description:
      'Track every milestone. See weak topics instantly. Get actionable insights to accelerate your progress.',
    color: '#6ee7b7',
    gradient: 'from-emerald-300 to-green-400',
  },
  {
    icon: '🗺️',
    title: 'AI Study Roadmap',
    description:
      'Personalized study plans that account for your exam date, available time, and target score.',
    color: '#fcd34d',
    gradient: 'from-amber-300 to-orange-400',
  },
  {
    icon: '📚',
    title: 'Complete Curriculum',
    description:
      'All chapters, all topics covered. Structured learning without distractions or gaps in knowledge.',
    color: '#a5b4fc',
    gradient: 'from-indigo-300 to-blue-400',
  },
];

// Animated background with 3D particles
function AnimatedBackground() {
  const canvasRef = useRef(null);
  const mousePos = useRef({ x: 0, y: 0 });

  useEffect(() => {
    if (!canvasRef.current) return;

    const scene = new THREE.Scene();

    const camera = new THREE.PerspectiveCamera(
      65,
      window.innerWidth / window.innerHeight,
      0.1,
      100
    );

    camera.position.z = 20;

    const renderer = new THREE.WebGLRenderer({
      canvas: canvasRef.current,
      alpha: true,
      antialias: true,
    });

    renderer.setPixelRatio(
      Math.min(window.devicePixelRatio, 2)
    );

    renderer.setSize(
      window.innerWidth,
      window.innerHeight
    );

    const particleCount = 1500;

    const positions = new Float32Array(
      particleCount * 3
    );

    const colors = new Float32Array(
      particleCount * 3
    );

    const sizes = new Float32Array(
      particleCount
    );

    const palette = [
      new THREE.Color('#67e8f9'),
      new THREE.Color('#d8b4fe'),
      new THREE.Color('#f472b6'),
      new THREE.Color('#6ee7b7'),
      new THREE.Color('#fcd34d'),
      new THREE.Color('#a5b4fc'),
    ];

    for (let i = 0; i < particleCount; i++) {
      const index = i * 3;

      const color =
        palette[
          Math.floor(
            Math.random() * palette.length
          )
        ];

      positions[index] =
        (Math.random() - 0.5) * 70;

      positions[index + 1] =
        (Math.random() - 0.5) * 60;

      positions[index + 2] =
        (Math.random() - 0.5) * 50;

      colors[index] = color.r;
      colors[index + 1] = color.g;
      colors[index + 2] = color.b;

      sizes[i] =
        Math.random() * 0.2 + 0.05;
    }

    const geometry =
      new THREE.BufferGeometry();

    geometry.setAttribute(
      'position',
      new THREE.BufferAttribute(
        positions,
        3
      )
    );

    geometry.setAttribute(
      'color',
      new THREE.BufferAttribute(
        colors,
        3
      )
    );

    geometry.setAttribute(
      'size',
      new THREE.BufferAttribute(
        sizes,
        1
      )
    );

    const material =
      new THREE.PointsMaterial({
        size: 0.1,
        vertexColors: true,
        transparent: true,
        opacity: 0.6,
        sizeAttenuation: true,
        blending: THREE.AdditiveBlending,
      });

    const particles =
      new THREE.Points(
        geometry,
        material
      );

    scene.add(particles);

    const createKnot = (
      scale,
      z,
      color,
      opacity
    ) => {
      const geo =
        new THREE.TorusKnotGeometry(
          scale,
          scale * 0.4,
          120,
          16
        );

      const mat =
        new THREE.MeshBasicMaterial({
          color,
          wireframe: true,
          transparent: true,
          opacity,
        });

      const mesh =
        new THREE.Mesh(
          geo,
          mat
        );

      mesh.position.z = z;

      scene.add(mesh);

      return mesh;
    };

    const knot1 = createKnot(
      8,
      -28,
      0x67e8f9,
      0.05
    );

    const knot2 = createKnot(
      6,
      -18,
      0xd8b4fe,
      0.07
    );

    const knot3 = createKnot(
      7,
      -38,
      0x6ee7b7,
      0.04
    );

    const handleMouseMove = (e) => {
      mousePos.current.x =
        (e.clientX / window.innerWidth) * 2 - 1;

      mousePos.current.y =
        -(e.clientY / window.innerHeight) * 2 + 1;
    };

    window.addEventListener(
      'mousemove',
      handleMouseMove
    );

    let animationFrame;

    const animate = () => {
      animationFrame =
        requestAnimationFrame(
          animate
        );

      particles.rotation.y +=
        0.0002;

      particles.rotation.x +=
        0.00006;

      particles.position.x =
        mousePos.current.x * 1.5;

      particles.position.y =
        mousePos.current.y * 1.5;

      knot1.rotation.x +=
        0.0007;

      knot1.rotation.y +=
        0.001;

      knot2.rotation.x -=
        0.0005;

      knot2.rotation.y +=
        0.0012;

      knot3.rotation.x +=
        0.0004;

      knot3.rotation.y -=
        0.0008;

      renderer.render(
        scene,
        camera
      );
    };

    animate();

    const handleResize = () => {
      camera.aspect =
        window.innerWidth /
        window.innerHeight;

      camera.updateProjectionMatrix();

      renderer.setSize(
        window.innerWidth,
        window.innerHeight
      );
    };

    window.addEventListener(
      'resize',
      handleResize
    );

    return () => {
      cancelAnimationFrame(
        animationFrame
      );

      window.removeEventListener(
        'resize',
        handleResize
      );

      window.removeEventListener(
        'mousemove',
        handleMouseMove
      );

      geometry.dispose();
      material.dispose();
      renderer.dispose();
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="fixed inset-0 w-full h-full pointer-events-none"
    />
  );
}

// Animated glowing orbs
function GlowOrb({
  className,
  color,
  delay = 0,
}) {
  return (
    <motion.div
      className={`absolute rounded-full blur-3xl pointer-events-none ${className}`}
      style={{
        background: color,
      }}
      animate={{
        scale: [1, 1.4, 1],
        opacity: [0.1, 0.3, 0.1],
        y: [0, 50, 0],
        x: [0, 30, 0],
      }}
      transition={{
        duration: 10,
        repeat: Infinity,
        ease: 'easeInOut',
        delay,
      }}
    />
  );
}

// Feature card with enhanced animations
function FeatureCard({
  feature,
  index,
}) {
  const [isHovered, setIsHovered] =
    useState(false);

  return (
    <motion.div
      initial={{
        opacity: 0,
        y: 60,
        scale: 0.9,
      }}
      whileInView={{
        opacity: 1,
        y: 0,
        scale: 1,
      }}
      viewport={{
        once: true,
        amount: 0.2,
      }}
      transition={{
        duration: 0.7,
        delay: index * 0.15,
        type: 'spring',
      }}
      whileHover={{
        y: -15,
        scale: 1.03,
      }}
      onHoverStart={() =>
        setIsHovered(true)
      }
      onHoverEnd={() =>
        setIsHovered(false)
      }
      className="relative group cursor-default"
    >
      <motion.div
        className={`absolute -inset-1 rounded-3xl opacity-0 blur-2xl transition-all duration-700 bg-gradient-to-br ${feature.gradient}`}
        animate={{
          opacity: isHovered ? 0.4 : 0,
          scale: isHovered ? 1.1 : 0.95,
        }}
      />

      <div className="relative h-full rounded-3xl border border-white/20 bg-white/[0.08] backdrop-blur-2xl p-8 transition-all duration-500 group-hover:border-white/40 group-hover:bg-white/[0.12] shadow-2xl hover:shadow-xl">
        <motion.div
          className={`mb-6 flex h-16 w-16 items-center justify-center rounded-2xl border text-4xl bg-gradient-to-br ${feature.gradient}`}
          style={{
            borderColor:
              `${feature.color}60`,

            background:
              `linear-gradient(135deg, ${feature.color}25 0%, ${feature.color}08 100%)`,
          }}
          animate={{
            scale: isHovered ? 1.2 : 1,
            rotate: isHovered ? 12 : 0,
          }}
          transition={{
            duration: 0.4,
          }}
        >
          {feature.icon}
        </motion.div>

        <h3
          className="mb-3 text-xl font-black leading-tight"
          style={{
            fontFamily:
              '"Syne", sans-serif',
            color: '#ffffff',
          }}
        >
          {feature.title}
        </h3>

        <p
          className="text-sm leading-7 text-white/60 mb-5"
          style={{
            fontFamily:
              '"Inter", sans-serif',
            fontWeight: 400,
          }}
        >
          {feature.description}
        </p>

        <motion.div
          className="h-1.5 rounded-full w-0 bg-gradient-to-r"
          style={{
            backgroundImage:
              `linear-gradient(90deg, ${feature.color}, transparent)`,
          }}
          animate={{
            width: isHovered
              ? '80px'
              : 0,
          }}
          transition={{
            duration: 0.5,
          }}
        />
      </div>
    </motion.div>
  );
}

// Floating elements animation
function FloatingElements() {
  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none">
      {[...Array(8)].map(
        (_, i) => (
          <motion.div
            key={i}
            className="absolute w-32 h-32 rounded-full"
            style={{
              background: [
                'radial-gradient(circle, rgba(103, 232, 249, 0.15) 0%, transparent 70%)',
                'radial-gradient(circle, rgba(216, 180, 254, 0.15) 0%, transparent 70%)',
                'radial-gradient(circle, rgba(110, 231, 183, 0.15) 0%, transparent 70%)',
              ][i % 3],

              left:
                `${Math.random() * 100}%`,

              top:
                `${Math.random() * 100}%`,
            }}
            animate={{
              y: [0, -100, 0],
              x: [
                0,
                Math.random() * 100 - 50,
                0,
              ],
              scale: [1, 1.5, 1],
              opacity: [
                0.3,
                0.6,
                0.3,
              ],
            }}
            transition={{
              duration:
                8 + Math.random() * 4,

              repeat: Infinity,

              delay:
                i * 0.5,
            }}
          />
        )
      )}
    </div>
  );
}

// Transition animation component
function TransitionOverlay({
  isActive,
}) {
  return (
    <AnimatePresence>
      {isActive && (
        <motion.div
          className="fixed inset-0 z-50 bg-gradient-to-r from-cyan-400 via-violet-400 to-fuchsia-400"
          initial={{
            clipPath:
              'inset(0% 100% 0% 0%)',
          }}
          animate={{
            clipPath:
              'inset(0% 0% 0% 0%)',
          }}
          exit={{
            clipPath:
              'inset(0% 0% 0% 100%)',
          }}
          transition={{
            duration: 0.8,
            ease: 'easeInOut',
          }}
        />
      )}
    </AnimatePresence>
  );
}

export default function LandingPage() {
  const navigate = useNavigate();

  /*
   * We only use logout here to allow the remembered-login
   * state to be manually cleared from the landing page.
   */
  const {
    loading,
    logout,
  } = useAuth();

  const [activeTab, setActiveTab] =
    useState('value');

  const [transitioning, setTransitioning] =
    useState(false);

  /*
   * This does NOT mean the user is currently logged in.
   *
   * It means:
   * "Has this browser successfully logged in before?"
   *
   * localStorage means a normal close/reopen keeps this value.
   * A completely new browser will not have it.
   */
  const [
    hasLoggedInBefore,
    setHasLoggedInBefore,
  ] = useState(
    () =>
      localStorage.getItem(
        'aceit_has_logged_in'
      ) === 'true'
  );

  if (loading) {
    return (
      <div className="min-h-screen bg-zinc-950 flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 rounded-full border-2 border-cyan-400 border-t-transparent animate-spin" />

          <p className="text-zinc-400 text-sm">
            Loading AceIt...
          </p>
        </div>
      </div>
    );
  }

  /*
   * Animated navigation.
   */
  const handleNavigation = (
    path
  ) => {
    setTransitioning(true);

    setTimeout(() => {
      navigate(path);
    }, 800);
  };

  const openSignIn = () => {
    handleNavigation(
      '/login?tab=login'
    );
  };

  const openSignUp = () => {
    handleNavigation(
      '/login?tab=register'
    );
  };

  /*
   * "Continue to Ace-It" sends them to the normal
   * sign-in screen because they have signed out.
   */
  const openContinue = () => {
    handleNavigation(
      '/login?tab=login'
    );
  };

  /*
   * This button is shown after the browser has
   * previously had a successful login.
   *
   * It clears the browser's "logged in before" marker,
   * so the next landing-page visit goes back to:
   *
   * Sign In + Get Started
   */
  const handleLandingSignOut =
    async () => {
      await logout();

      try {
        localStorage.removeItem(
          'aceit_has_logged_in'
        );
      } catch (e) {
        console.warn(
          'Could not clear remembered login:',
          e
        );
      }

      setHasLoggedInBefore(false);
    };

  return (
    <main className="relative min-h-screen bg-gradient-to-b from-slate-950 via-zinc-950 to-slate-950 text-white">
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=Space+Grotesk:wght@400;500;600;700&family=DM+Sans:wght@400;500;700&family=Inter:wght@300;400;500;600;700&display=swap');

        * {
          box-sizing: border-box;
        }
      `}</style>

      <TransitionOverlay
        isActive={transitioning}
      />

      <AnimatedBackground />

      <FloatingElements />

      <GlowOrb
        className="left-[-15rem] top-[-8rem] h-[40rem] w-[40rem]"
        color="rgba(103, 232, 249, 0.2)"
        delay={0}
      />

      <GlowOrb
        className="right-[-10rem] top-[25%] h-[38rem] w-[38rem]"
        color="rgba(216, 180, 254, 0.2)"
        delay={1}
      />

      <GlowOrb
        className="bottom-[-12rem] left-[25%] h-[36rem] w-[36rem]"
        color="rgba(110, 231, 183, 0.18)"
        delay={2}
      />

      <GlowOrb
        className="right-[10%] bottom-[10%] h-[32rem] w-[32rem]"
        color="rgba(103, 232, 249, 0.18)"
        delay={1.5}
      />

      <nav className="relative z-20 mx-auto flex max-w-7xl items-center justify-between px-4 py-6 sm:px-6 md:px-8">
        <motion.button
          onClick={() =>
            window.scrollTo({
              top: 0,
              behavior: 'smooth',
            })
          }
          whileHover={{
            scale: 1.05,
          }}
          className="group flex items-center gap-3"
        >
          <div className="relative">
            <motion.div
              className="absolute inset-0 rounded-full bg-gradient-to-r from-cyan-300 to-violet-300 blur-xl"
              animate={{
                opacity: [
                  0.3,
                  0.6,
                  0.3,
                ],
                scale: [
                  1,
                  1.15,
                  1,
                ],
              }}
              transition={{
                duration: 3,
                repeat: Infinity,
              }}
            />

            <img
              src="/aceit-logo.png"
              alt="AceIt"
              className="relative h-16 w-auto object-contain"
            />
          </div>
        </motion.button>

        <div
          className="hidden items-center gap-8 text-sm text-white/60 md:flex"
          style={{
            fontFamily:
              '"Inter", sans-serif',
          }}
        >
          <a
            href="#features"
            className="transition hover:text-cyan-300"
          >
            Features
          </a>

          <a
            href="#why"
            className="transition hover:text-cyan-300"
          >
            Why AceIt
          </a>
        </div>

        <div className="flex items-center gap-3">
          {hasLoggedInBefore ? (
            <>
              <motion.button
                onClick={
                  openContinue
                }
                whileHover={{
                  scale: 1.05,
                }}
                whileTap={{
                  scale: 0.95,
                }}
                className="rounded-full border border-cyan-300/40 bg-cyan-300/10 px-4 py-2.5 text-sm font-semibold text-cyan-200 transition hover:border-cyan-200 hover:bg-cyan-300/15 hover:text-white sm:px-5"
                style={{
                  fontFamily:
                    '"DM Sans", sans-serif',
                }}
              >
                Continue to Ace-It
              </motion.button>

              <motion.button
                onClick={
                  handleLandingSignOut
                }
                whileHover={{
                  scale: 1.05,
                }}
                whileTap={{
                  scale: 0.95,
                }}
                className="rounded-full border border-white/20 px-4 py-2.5 text-sm font-medium text-white/70 transition hover:border-red-300/60 hover:bg-red-300/10 hover:text-red-200 sm:px-5"
                style={{
                  fontFamily:
                    '"DM Sans", sans-serif',
                }}
              >
                Sign Out
              </motion.button>
            </>
          ) : (
            <>
              <motion.button
                onClick={openSignIn}
                whileHover={{
                  scale: 1.05,
                }}
                whileTap={{
                  scale: 0.95,
                }}
                className="rounded-full border border-white/30 px-4 py-2.5 text-sm font-medium text-white/80 transition hover:border-cyan-300 hover:text-cyan-300 hover:bg-white/5 sm:px-5"
                style={{
                  fontFamily:
                    '"DM Sans", sans-serif',
                }}
              >
                Sign In
              </motion.button>

              <motion.button
                onClick={openSignUp}
                whileHover={{
                  scale: 1.06,
                }}
                whileTap={{
                  scale: 0.92,
                }}
                className="rounded-full bg-gradient-to-r from-cyan-400 to-blue-500 px-4 py-2.5 text-sm font-bold text-white shadow-lg hover:shadow-cyan-400/50 transition sm:px-5"
                style={{
                  fontFamily:
                    '"Syne", sans-serif',
                }}
              >
                Get Started
              </motion.button>
            </>
          )}
        </div>
      </nav>

      <section
        id="hero"
        className="relative z-10 min-h-[calc(100vh-100px)] flex items-center px-4 py-20 sm:px-6 md:px-8"
      >
        <div className="mx-auto grid w-full max-w-7xl items-center gap-12 lg:gap-20 lg:grid-cols-[1.3fr_0.7fr]">
          <motion.div
            initial={{
              opacity: 0,
              y: 50,
            }}
            animate={{
              opacity: 1,
              y: 0,
            }}
            transition={{
              duration: 1.2,
            }}
          >
            <motion.div
              className="mb-8 inline-flex items-center gap-2 rounded-full border border-cyan-300/40 bg-cyan-300/10 px-5 py-3 text-sm text-cyan-200"
              whileHover={{
                scale: 1.05,
                borderColor:
                  'rgba(103, 232, 249, 0.8)',
              }}
              style={{
                fontFamily:
                  '"Inter", sans-serif',
              }}
            >
              <motion.div className="h-2 w-2 rounded-full bg-cyan-300 animate-pulse" />

              <span>
                Learning reimagined with AI
              </span>
            </motion.div>

            <h1
              className="max-w-4xl text-5xl leading-[1.1] tracking-tight sm:text-7xl lg:text-8xl text-white"
              style={{
                fontFamily:
                  '"Syne", sans-serif',
                fontWeight: 800,
              }}
            >
              Your{' '}
              <span className="bg-gradient-to-r from-cyan-300 via-violet-300 to-emerald-300 bg-clip-text text-transparent animate-pulse">
                personalized
              </span>{' '}
              AI-tutor for learning.
            </h1>

            <p
              className="mt-8 max-w-2xl text-lg leading-8 text-white/70 sm:text-xl"
              style={{
                fontFamily:
                  '"Inter", sans-serif',
                fontWeight: 400,
              }}
            >
              AceIt does everything better than traditional tutoring.{' '}
              <span className="text-cyan-300 font-semibold">
                At just 10% of the cost.
              </span>
            </p>

            <div className="mt-10 flex flex-col gap-4 sm:flex-row">
              <motion.button
                onClick={openSignUp}
                whileHover={{
                  scale: 1.07,
                  boxShadow:
                    '0 0 50px rgba(103, 232, 249, 0.5)',
                }}
                whileTap={{
                  scale: 0.92,
                }}
                className="flex items-center justify-center gap-3 rounded-2xl bg-gradient-to-r from-cyan-400 to-blue-500 px-8 py-5 text-lg font-bold text-white shadow-xl hover:shadow-cyan-400/50 transition"
                style={{
                  fontFamily:
                    '"Syne", sans-serif',
                }}
              >
                <Sparkles size={20} />

                Start learning free

                <ArrowRight size={20} />
              </motion.button>

              <motion.button
                onClick={openSignIn}
                whileHover={{
                  scale: 1.05,
                  borderColor:
                    'rgba(103, 232, 249, 0.8)',
                }}
                whileTap={{
                  scale: 0.92,
                }}
                className="flex items-center justify-center gap-2 rounded-2xl border-2 border-white/20 bg-white/[0.06] px-8 py-5 text-lg font-bold text-white/90 backdrop-blur-xl transition hover:bg-white/[0.12]"
                style={{
                  fontFamily:
                    '"DM Sans", sans-serif',
                }}
              >
                Sign in
              </motion.button>
            </div>

            <motion.div
              className="mt-14 flex flex-wrap gap-10"
              initial={{
                opacity: 0,
              }}
              animate={{
                opacity: 1,
              }}
              transition={{
                delay: 0.6,
              }}
            >
              {[
                {
                  value: '10x',
                  label: 'Better learning',
                },
                {
                  value: '24/7',
                  label: 'AI support',
                },
                {
                  value: '100%',
                  label: 'Personalized',
                },
              ].map(
                (stat, i) => (
                  <motion.div
                    key={i}
                    className="flex items-center gap-4"
                    whileHover={{
                      scale: 1.05,
                    }}
                  >
                    <div className="rounded-lg bg-white/10 border border-white/20 p-3">
                      <Sparkles
                        size={20}
                        className="text-cyan-300"
                      />
                    </div>

                    <div>
                      <p
                        className="text-xl text-white/95"
                        style={{
                          fontFamily:
                            '"Syne", sans-serif',
                          fontWeight: 700,
                        }}
                      >
                        {stat.value}
                      </p>

                      <p
                        className="text-xs text-white/50"
                        style={{
                          fontFamily:
                            '"Inter", sans-serif',
                        }}
                      >
                        {stat.label}
                      </p>
                    </div>
                  </motion.div>
                )
              )}
            </motion.div>
          </motion.div>

          <motion.div
            initial={{
              opacity: 0,
              scale: 0.85,
              rotate: 8,
            }}
            animate={{
              opacity: 1,
              scale: 1,
              rotate: 0,
            }}
            transition={{
              duration: 1.3,
              delay: 0.3,
            }}
            className="relative"
          >
            <div className="absolute inset-0 rounded-[3rem] bg-gradient-to-br from-cyan-400/25 via-violet-300/20 to-emerald-300/15 blur-3xl" />

            <motion.div
              className="relative overflow-hidden rounded-[3rem] border border-white/20 bg-white/[0.08] backdrop-blur-3xl p-8 shadow-2xl"
              animate={{
                borderColor: [
                  'rgba(255,255,255,0.15)',
                  'rgba(103,232,249,0.4)',
                  'rgba(255,255,255,0.15)',
                ],
              }}
              transition={{
                duration: 5,
                repeat: Infinity,
              }}
            >
              <motion.div
                className="mb-8 inline-flex items-center gap-3 rounded-full bg-gradient-to-r from-cyan-400/20 to-violet-300/20 px-4 py-2"
                animate={{
                  scale: [
                    1,
                    1.05,
                    1,
                  ],
                }}
                transition={{
                  duration: 2.5,
                  repeat: Infinity,
                }}
              >
                <div className="h-2 w-2 rounded-full bg-cyan-300 animate-pulse" />

                <span
                  className="text-xs text-cyan-200"
                  style={{
                    fontFamily:
                      '"Inter", sans-serif',
                  }}
                >
                  Adaptive AI learning
                </span>
              </motion.div>

              <h2
                className="text-2xl text-white/95 mb-8"
                style={{
                  fontFamily:
                    '"Syne", sans-serif',
                  fontWeight: 700,
                }}
              >
                Personalized just for you
              </h2>

              <div className="space-y-6">
                {[
                  {
                    label:
                      'Personalization',
                    value: 100,
                    color:
                      'from-cyan-400 to-blue-500',
                  },
                  {
                    label:
                      'Effectiveness',
                    value: 98,
                    color:
                      'from-violet-400 to-purple-500',
                  },
                  {
                    label:
                      'Availability',
                    value: 100,
                    color:
                      'from-emerald-400 to-green-500',
                  },
                ].map(
                  (metric, i) => (
                    <motion.div
                      key={i}
                      initial={{
                        opacity: 0,
                        x: -20,
                      }}
                      animate={{
                        opacity: 1,
                        x: 0,
                      }}
                      transition={{
                        delay:
                          0.8 +
                          i * 0.12,
                      }}
                    >
                      <div className="mb-2 flex items-center justify-between text-sm">
                        <span
                          className="text-white/70"
                          style={{
                            fontFamily:
                              '"Inter", sans-serif',
                          }}
                        >
                          {metric.label}
                        </span>

                        <motion.span
                          className="text-cyan-300"
                          animate={{
                            scale: [
                              1,
                              1.15,
                              1,
                            ],
                          }}
                          transition={{
                            delay:
                              1 +
                              i *
                                0.15,
                          }}
                          style={{
                            fontFamily:
                              '"Syne", sans-serif',
                            fontWeight: 700,
                          }}
                        >
                          {metric.value}%
                        </motion.span>
                      </div>

                      <div className="h-2.5 overflow-hidden rounded-full bg-white/10">
                        <motion.div
                          initial={{
                            width: 0,
                          }}
                          animate={{
                            width: `${metric.value}%`,
                          }}
                          transition={{
                            duration: 1.8,
                            delay:
                              0.9 +
                              i *
                                0.15,
                            ease: 'easeOut',
                          }}
                          className={`h-full rounded-full bg-gradient-to-r ${metric.color}`}
                        />
                      </div>
                    </motion.div>
                  )
                )}
              </div>

              <motion.div
                className="mt-8 rounded-2xl border border-cyan-300/30 bg-gradient-to-r from-cyan-400/10 to-violet-300/10 p-5"
                whileHover={{
                  borderColor:
                    'rgba(103, 232, 249, 0.7)',
                }}
              >
                <p
                  className="text-sm leading-6 text-white/70"
                  style={{
                    fontFamily:
                      '"Inter", sans-serif',
                  }}
                >
                  <span
                    className="text-cyan-300"
                    style={{
                      fontWeight: 600,
                    }}
                  >
                    Real-time adaptive:
                  </span>{' '}
                  Learns your pace and style instantly. Personalizes every interaction.
                </p>
              </motion.div>
            </motion.div>
          </motion.div>
        </div>
      </section>

      <section
        id="features"
        className="relative z-10 px-4 py-40 sm:px-6 md:px-8"
      >
        <div className="mx-auto max-w-7xl">
          <motion.div
            initial={{
              opacity: 0,
              y: 40,
            }}
            whileInView={{
              opacity: 1,
              y: 0,
            }}
            viewport={{
              once: true,
            }}
            className="mx-auto mb-24 max-w-3xl text-center"
          >
            <p
              className="mb-4 text-sm font-semibold uppercase tracking-[0.3em] text-cyan-300"
              style={{
                fontFamily:
                  '"Space Grotesk", sans-serif',
              }}
            >
              Powerful Features
            </p>

            <h2
              className="text-5xl sm:text-6xl text-white"
              style={{
                fontFamily:
                  '"Syne", sans-serif',
                fontWeight: 800,
              }}
            >
              Everything you need to{' '}
              <span className="bg-gradient-to-r from-cyan-300 to-violet-300 bg-clip-text text-transparent">
                excel
              </span>
            </h2>

            <p
              className="mt-8 text-lg leading-8 text-white/60"
              style={{
                fontFamily:
                  '"Inter", sans-serif',
              }}
            >
              Comprehensive tools built specifically for student success and exam mastery
            </p>
          </motion.div>

          <div className="grid gap-7 md:grid-cols-2 lg:grid-cols-3">
            {FEATURES.map(
              (
                feature,
                index
              ) => (
                <FeatureCard
                  key={
                    feature.title
                  }
                  feature={
                    feature
                  }
                  index={
                    index
                  }
                />
              )
            )}
          </div>
        </div>
      </section>

      <section
        id="why"
        className="relative z-10 px-4 py-40 sm:px-6 md:px-8"
      >
        <div className="mx-auto max-w-7xl">
          <div className="grid items-center gap-20 lg:grid-cols-2">
            <motion.div
              initial={{
                opacity: 0,
                x: -50,
              }}
              whileInView={{
                opacity: 1,
                x: 0,
              }}
              viewport={{
                once: true,
              }}
            >
              <p
                className="mb-4 text-sm font-semibold uppercase tracking-[0.3em] text-violet-300"
                style={{
                  fontFamily:
                    '"Space Grotesk", sans-serif',
                }}
              >
                The Choice is Clear
              </p>

              <h2
                className="text-5xl sm:text-6xl leading-tight mb-8 text-white"
                style={{
                  fontFamily:
                    '"Syne", sans-serif',
                  fontWeight: 800,
                }}
              >
                AceIt does everything better.
                <br />
                <span className="text-cyan-300">
                  At 10% the cost.
                </span>
              </h2>

              <p
                className="text-lg text-white/60 mb-10 leading-relaxed max-w-2xl"
                style={{
                  fontFamily:
                    '"Inter", sans-serif',
                }}
              >
                Traditional tutoring charges ₹500–1000/hour but teaches one way. AceIt adapts to every student uniquely and costs just 10% as much while delivering superior results.
              </p>

              <div className="space-y-5 mb-12">
                {[
                  'Personalized to every student',
                  'Available 24/7 for instant help',
                  'Adaptive quizzes that evolve',
                  'Complete curriculum coverage',
                  'Real-time progress tracking',
                  '10% of traditional tutoring cost',
                ].map(
                  (
                    item,
                    i
                  ) => (
                    <motion.div
                      key={i}
                      initial={{
                        opacity: 0,
                        x: -20,
                      }}
                      whileInView={{
                        opacity: 1,
                        x: 0,
                      }}
                      transition={{
                        delay:
                          i *
                          0.08,
                      }}
                      className="flex items-center gap-4 group cursor-default"
                    >
                      <div className="rounded-lg bg-gradient-to-br from-cyan-300/20 to-violet-300/20 p-2 group-hover:scale-110 transition-transform">
                        <span className="text-xl">
                          ✓
                        </span>
                      </div>

                      <span
                        className="text-white/75 text-sm"
                        style={{
                          fontFamily:
                            '"Inter", sans-serif',
                        }}
                      >
                        {item}
                      </span>
                    </motion.div>
                  )
                )}
              </div>
            </motion.div>

            <motion.div
              initial={{
                opacity: 0,
                x: 50,
              }}
              whileInView={{
                opacity: 1,
                x: 0,
              }}
              viewport={{
                once: true,
              }}
            >
              <div className="rounded-3xl border border-white/15 bg-white/[0.07] backdrop-blur-xl overflow-hidden">
                <div className="flex border-b border-white/10 bg-white/[0.05]">
                  {[
                    {
                      id: 'value',
                      label:
                        'Value Proposition',
                    },
                    {
                      id: 'quality',
                      label:
                        'Quality Metrics',
                    },
                  ].map(
                    (tab) => (
                      <button
                        key={
                          tab.id
                        }
                        onClick={() =>
                          setActiveTab(
                            tab.id
                          )
                        }
                        className={`flex-1 py-4 px-4 text-sm transition relative ${
                          activeTab ===
                          tab.id
                            ? 'text-cyan-300'
                            : 'text-white/50 hover:text-white/70'
                        }`}
                        style={{
                          fontFamily:
                            '"Syne", sans-serif',
                          fontWeight:
                            activeTab ===
                            tab.id
                              ? 700
                              : 600,
                        }}
                      >
                        {
                          tab.label
                        }

                        {activeTab ===
                          tab.id && (
                          <motion.div
                            layoutId="underline"
                            className="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-cyan-400 to-violet-400"
                          />
                        )}
                      </button>
                    )
                  )}
                </div>

                <div className="p-10">
                  <AnimatePresence mode="wait">
                    {activeTab ===
                      'value' && (
                      <motion.div
                        key="value"
                        initial={{
                          opacity: 0,
                          y: 20,
                        }}
                        animate={{
                          opacity: 1,
                          y: 0,
                        }}
                        exit={{
                          opacity: 0,
                          y: -20,
                        }}
                        transition={{
                          duration:
                            0.4,
                        }}
                        className="space-y-6"
                      >
                        <div className="rounded-2xl bg-gradient-to-br from-cyan-400/15 to-blue-400/10 border border-cyan-300/30 p-6">
                          <h3
                            className="text-lg mb-3 text-cyan-300"
                            style={{
                              fontFamily:
                                '"Syne", sans-serif',
                              fontWeight: 700,
                            }}
                          >
                            Why Choose AceIt
                          </h3>

                          <ul className="space-y-3">
                            {[
                              'Better results at fraction of cost',
                              'AI learns your unique style',
                              'Adapts faster than tutors',
                              'Available when you need it',
                              'Personalized explanations',
                              'Proven effectiveness',
                            ].map(
                              (
                                item
                              ) => (
                                <li
                                  key={
                                    item
                                  }
                                  className="flex items-center gap-3 text-white/70 text-sm"
                                  style={{
                                    fontFamily:
                                      '"Inter", sans-serif',
                                  }}
                                >
                                  <motion.div
                                    className="h-1.5 w-1.5 rounded-full bg-cyan-300"
                                    animate={{
                                      scale: [
                                        1,
                                        1.3,
                                        1,
                                      ],
                                    }}
                                    transition={{
                                      duration:
                                        2,
                                      repeat:
                                        Infinity,
                                    }}
                                  />

                                  {
                                    item
                                  }
                                </li>
                              )
                            )}
                          </ul>
                        </div>

                        <div className="text-center pt-4">
                          <p
                            className="text-white/50 text-sm"
                            style={{
                              fontFamily:
                                '"Inter", sans-serif',
                            }}
                          >
                            🎯 Save time. Save money. Get better results.
                          </p>
                        </div>
                      </motion.div>
                    )}

                    {activeTab ===
                      'quality' && (
                      <motion.div
                        key="quality"
                        initial={{
                          opacity: 0,
                          y: 20,
                        }}
                        animate={{
                          opacity: 1,
                          y: 0,
                        }}
                        exit={{
                          opacity: 0,
                          y: -20,
                        }}
                        transition={{
                          duration:
                            0.4,
                        }}
                        className="space-y-7"
                      >
                        {[
                          {
                            label:
                              'Learning Effectiveness',
                            aceit: 98,
                            trad: 65,
                          },
                          {
                            label:
                              'Personalization Level',
                            aceit: 100,
                            trad: 30,
                          },
                          {
                            label:
                              'Availability',
                            aceit: 100,
                            trad: 25,
                          },
                          {
                            label:
                              'Adaptability',
                            aceit: 95,
                            trad: 40,
                          },
                        ].map(
                          (
                            metric,
                            i
                          ) => (
                            <div
                              key={
                                metric.label
                              }
                            >
                              <div className="mb-3 flex justify-between">
                                <span
                                  className="text-white/75 text-sm font-semibold"
                                  style={{
                                    fontFamily:
                                      '"Inter", sans-serif',
                                  }}
                                >
                                  {
                                    metric.label
                                  }
                                </span>

                                <span
                                  className="text-cyan-300 text-sm"
                                  style={{
                                    fontFamily:
                                      '"Syne", sans-serif',
                                    fontWeight: 700,
                                  }}
                                >
                                  AceIt{' '}
                                  {
                                    metric.aceit
                                  }
                                  %
                                </span>
                              </div>

                              <div className="flex gap-4">
                                <div className="flex-1">
                                  <p
                                    className="text-xs text-white/50 mb-2"
                                    style={{
                                      fontFamily:
                                        '"Inter", sans-serif',
                                    }}
                                  >
                                    Traditional
                                  </p>

                                  <div className="h-2.5 rounded-full bg-white/10 overflow-hidden">
                                    <motion.div
                                      initial={{
                                        width: 0,
                                      }}
                                      whileInView={{
                                        width: `${metric.trad}%`,
                                      }}
                                      transition={{
                                        duration:
                                          1.5,
                                        delay:
                                          i *
                                          0.1,
                                      }}
                                      className="h-full bg-white/40 rounded-full"
                                    />
                                  </div>
                                </div>

                                <div className="flex-1">
                                  <p
                                    className="text-xs text-cyan-400 mb-2"
                                    style={{
                                      fontFamily:
                                        '"Inter", sans-serif',
                                    }}
                                  >
                                    AceIt
                                  </p>

                                  <div className="h-2.5 rounded-full bg-white/10 overflow-hidden">
                                    <motion.div
                                      initial={{
                                        width: 0,
                                      }}
                                      whileInView={{
                                        width: `${metric.aceit}%`,
                                      }}
                                      transition={{
                                        duration:
                                          1.5,
                                        delay:
                                          i *
                                            0.1 +
                                          0.2,
                                      }}
                                      className="h-full bg-gradient-to-r from-cyan-400 to-violet-400 rounded-full"
                                    />
                                  </div>
                                </div>
                              </div>
                            </div>
                          )
                        )}
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      <section className="relative z-10 px-4 py-40 sm:px-6 md:px-8 text-center">
        <div className="mx-auto max-w-4xl">
          <motion.div
            initial={{
              opacity: 0,
              y: 50,
            }}
            whileInView={{
              opacity: 1,
              y: 0,
            }}
            viewport={{
              once: true,
            }}
          >
            <motion.div
              animate={{
                scale: [
                  1,
                  1.1,
                  1,
                ],
                rotate: [
                  0,
                  5,
                  -5,
                  0,
                ],
              }}
              transition={{
                duration: 4,
                repeat: Infinity,
              }}
              className="mb-8"
            >
              <Rocket
                className="mx-auto text-cyan-300"
                size={48}
              />
            </motion.div>

            <h2
              className="text-5xl sm:text-6xl mb-6 text-white"
              style={{
                fontFamily:
                  '"Syne", sans-serif',
                fontWeight: 800,
              }}
            >
              Ready to transform your learning?
            </h2>

            <p
              className="text-lg text-white/60 mb-12 max-w-2xl mx-auto leading-relaxed"
              style={{
                fontFamily:
                  '"Inter", sans-serif',
              }}
            >
              Join thousands of students who are acing their exams with personalized AI tutoring. Start free today—no credit card needed.
            </p>

            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <motion.button
                onClick={openSignUp}
                whileHover={{
                  scale: 1.08,
                  boxShadow:
                    '0 0 60px rgba(103, 232, 249, 0.6)',
                }}
                whileTap={{
                  scale: 0.92,
                }}
                className="inline-flex items-center gap-3 rounded-2xl bg-gradient-to-r from-cyan-400 via-violet-400 to-emerald-400 px-10 py-6 text-lg font-bold text-white shadow-2xl transition"
                style={{
                  fontFamily:
                    '"Syne", sans-serif',
                }}
              >
                <Sparkles
                  size={24}
                />

                Create free account

                <ArrowRight
                  size={24}
                />
              </motion.button>

              <motion.button
                onClick={openSignIn}
                whileHover={{
                  scale: 1.05,
                }}
                className="inline-flex items-center gap-2 rounded-2xl border-2 border-white/30 px-10 py-6 text-lg font-bold text-white/80 transition hover:border-cyan-300 hover:text-cyan-300"
                style={{
                  fontFamily:
                    '"DM Sans", sans-serif',
                }}
              >
                Sign in
              </motion.button>
            </div>

            <p
              className="mt-10 text-sm text-white/50"
              style={{
                fontFamily:
                  '"Inter", sans-serif',
              }}
            >
              Get 100 AI credits free. Start learning immediately.
            </p>
          </motion.div>
        </div>
      </section>

      <footer className="relative z-10 border-t border-white/10 px-4 py-8 sm:px-6 md:px-8">
        <div className="mx-auto max-w-7xl text-center">
          <img
            src="/aceit-logo.png"
            alt="AceIt"
            className="mx-auto mb-4 h-12 w-auto object-contain opacity-70"
          />

          <p
            className="text-xs text-white/40"
            style={{
              fontFamily:
                '"Inter", sans-serif',
            }}
          >
            © 2026 AceIt AI. This property belongs to Codegeeko Academy Private Limited.
          </p>
        </div>
      </footer>
    </main>
  );
}