import { useState, useEffect, useCallback } from 'react';
import {
  BrowserRouter,
  Routes,
  Route,
  Navigate,
  useLocation,
} from 'react-router-dom';

import './App.css';
import './index.css';
import 'katex/dist/katex.min.css';

import { AuthProvider, useAuth } from './contexts/AuthContext';
import { SubscriptionProvider } from './contexts/SubscriptionContext';
import { CreditsProvider } from './contexts/CreditsContext';
import { Toaster } from 'sonner';

import LandingPage from './components/LandingPage';
import IntroScreen from './components/IntroScreen';
import AuthPage from './components/AuthPage';
import AuthCallback from './components/AuthCallback';
import TermsPage from './components/TermsPage';
import PrivacyPage from './components/PrivacyPage';
import EmailVerificationPage from './components/EmailVerificationPage';

import Layout from './components/Layout';
import Dashboard from './components/Dashboard';
import ChatPage from './components/ChatPage';
import SyllabusPage from './components/SyllabusPage';
import ProgressPage from './components/ProgressPage';
import QuizArena from './components/QuizArena';
import ProfilePage from './components/ProfilePage';
import LeaderboardPage from './components/LeaderboardPage';
import MockExamPage from './components/MockExamPage';
import StudyPlanPage from './components/StudyPlanPage';
import PricingPage from './components/PricingPage';

import OnboardingModal from './components/OnboardingModal';
import UpgradePromptModal from './components/UpgradePromptModal';
import GradeAccessGuard from './components/GradeAccessGuard';
import NewUserTutorial from './components/NewUserTutorial';

import AdminDashboard from './components/AdminDashboard';


function LoadingScreen({ message = 'Loading AceIt AI...' }) {
  return (
    <div className="min-h-screen bg-zinc-950 flex items-center justify-center">
      <div className="flex flex-col items-center gap-4">
        <div className="w-12 h-12 rounded-full border-2 border-cyan-400 border-t-transparent animate-spin" />
        <p className="text-zinc-400 text-sm font-body">
          {message}
        </p>
      </div>
    </div>
  );
}


/*
 * Handles authenticated users.
 *
 * IMPORTANT ORDER:
 *
 * 1. No school yet
 *    -> Layout renders SchoolSelectModal
 *
 * 2. School exists but onboarding is incomplete
 *    -> OnboardingModal
 *
 * 3. School + onboarding complete
 *    -> Normal app + tutorial if needed
 */
function ProtectedRoute({ children }) {
  const { user, loading, refresh } = useAuth();
  const [showTutorial, setShowTutorial] = useState(false);

  useEffect(() => {
    /*
     * Tutorial can ONLY appear after:
     *
     * - the user exists
     * - a school has been selected
     * - onboarding is complete
     * - tutorial hasn't been seen
     */
    if (
      user &&
      user.school &&
      user.is_onboarded &&
      user.is_tutorial_seen === false
    ) {
      setShowTutorial(true);
    } else {
      setShowTutorial(false);
    }
  }, [user]);

  if (loading) {
    return <LoadingScreen />;
  }

  /*
   * User signed out.
   *
   * Normally RootGate handles this, but keeping this here
   * makes the protected route itself safe too.
   */
  if (!user) {
    return <Navigate to="/" replace />;
  }

  /*
   * New Google users start with no school.
   *
   * DO NOT show onboarding yet.
   *
   * Layout contains SchoolSelectModal.
   */
  if (!user.school) {
    return (
      <>
        {children}
      </>
    );
  }

  /*
   * School selected, but onboarding isn't complete yet.
   */
  if (!user.is_onboarded) {
    return (
      <>
        {children}

        <OnboardingModal
          onComplete={() => {
            refresh?.();
          }}
        />
      </>
    );
  }

  /*
   * Fully onboarded user.
   */
  return (
    <>
      {children}

      <UpgradePromptModal />

      <GradeAccessGuard />

      {showTutorial && (
        <NewUserTutorial
          onClose={() => setShowTutorial(false)}
        />
      )}
    </>
  );
}


/*
 * ROOT BEHAVIOR
 *
 * This is the important part of the remembering system.
 *
 * If the browser still has a valid authenticated session:
 *     -> show the main app
 *
 * If there is no authenticated session:
 *     -> show the Landing Page
 *
 * There is NO sessionStorage/localStorage decision here.
 * The backend auth cookie is the source of truth.
 */
function RootGate() {
  const { user, loading } = useAuth();
  const [introComplete, setIntroComplete] = useState(false);
  const finishIntro = useCallback(() => setIntroComplete(true), []);

  if (loading) {
    return <LoadingScreen />;
  }

  /*
   * SIGNED OUT / FIRST VISIT
   * -> Landing Page
   */
  if (!user) {
    return introComplete
      ? <LandingPage />
      : <IntroScreen onComplete={finishIntro} />;
  }

  /*
   * SIGNED IN
   * -> Main application
   *
   * ProtectedRoute handles:
   * School Select
   * Onboarding
   * Tutorial
   */
  return (
    <ProtectedRoute>
      <Layout />
    </ProtectedRoute>
  );
}


/*
 * Authentication pages should not be shown to a user
 * who is already logged in.
 */
function PublicAuthRoute({ children }) {
  const { user, loading } = useAuth();

  if (loading) {
    return <LoadingScreen />;
  }

  if (user) {
    return <Navigate to="/" replace />;
  }

  return children;
}


/*
 * Handles OAuth callback.
 */
function AppRouter() {
  const location = useLocation();

  /*
   * Support both:
   *
   * #session_id=...
   * ?session_id=...
   */
  const hasOAuth =
    location.hash?.includes('session_id=') ||
    location.search?.includes('session_id=');

  if (hasOAuth) {
    return <AuthCallback />;
  }

  return (
    <Routes>

      {/* Login / Signup */}
      <Route
        path="/login"
        element={
          <PublicAuthRoute>
            <AuthPage />
          </PublicAuthRoute>
        }
      />

      <Route path="/landing" element={<PublicAuthRoute><LandingPage /></PublicAuthRoute>} />

      {/* Public legal pages */}
      <Route
        path="/terms"
        element={<TermsPage />}
      />

      <Route
        path="/privacy"
        element={<PrivacyPage />}
      />

      <Route
        path="/verify-email"
        element={<EmailVerificationPage />}
      />

      <Route
        path="/resend-verification"
        element={<EmailVerificationPage />}
      />


      {/*
       * ROOT APPLICATION
       *
       * RootGate decides:
       *
       * signed out -> LandingPage
       * signed in  -> ProtectedRoute -> Layout
       */}
      <Route
        path="/"
        element={<RootGate />}
      >
        {/* Main Dashboard */}
        <Route
          index
          element={<Dashboard />}
        />

        <Route
          path="dashboard"
          element={<Dashboard />}
        />

        {/* AI Tutor */}
        <Route
          path="chat"
          element={<ChatPage />}
        />

        <Route
          path="chat/:sessionId"
          element={<ChatPage />}
        />

        {/* Syllabus */}
        <Route
          path="syllabus"
          element={<SyllabusPage />}
        />

        {/* Progress */}
        <Route
          path="progress"
          element={<ProgressPage />}
        />

        {/* Quiz Arena */}
        <Route
          path="quiz"
          element={<QuizArena />}
        />

        {/* Leaderboard */}
        <Route
          path="leaderboard"
          element={<LeaderboardPage />}
        />

        {/* Mock Exams */}
        <Route
          path="mock-exams"
          element={<MockExamPage />}
        />

        {/* Study Plan */}
        <Route
          path="study-plan"
          element={<StudyPlanPage />}
        />

        {/* Upgrade */}
        <Route
          path="upgrade"
          element={<PricingPage />}
        />

        {/* Profile */}
        <Route
          path="profile"
          element={<ProfilePage />}
        />

        {/* Admin */}
        <Route
          path="/admin"
          element={
            <ProtectedRoute>
              <AdminDashboard />
            </ProtectedRoute>
          }
        />

        {/* Unknown app routes */}
        <Route
          path="*"
          element={<Navigate to="/" replace />}
        />
      </Route>

    </Routes>
  );
}


function App() {
  return (
    <div className="App">

      <BrowserRouter>

        <AuthProvider>

          <SubscriptionProvider>

            <CreditsProvider>

              <AppRouter />

              <Toaster
                position="top-center"
                theme="dark"
                closeButton
                richColors
              />

            </CreditsProvider>

          </SubscriptionProvider>

        </AuthProvider>

      </BrowserRouter>

    </div>
  );
}


export default App;