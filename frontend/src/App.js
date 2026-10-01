import { useState, useEffect } from 'react';
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
import SchoolSelectModal from './components/SchoolSelectModal';
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

function ProtectedRoute({ children }) {
  const { user, loading, refresh } = useAuth();
  const [showTutorial, setShowTutorial] = useState(false);

  useEffect(() => {
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

  if (!user) {
    return <Navigate to="/" replace />;
  }

  // Reuse the existing school modal before mounting app pages.
  if (!user.school) {
    return (
      <div className="min-h-screen bg-zinc-950">
        <SchoolSelectModal />
      </div>
    );
  }

  // Complete onboarding before curriculum pages initialise.
  if (!user.is_onboarded) {
    return (
      <div className="min-h-screen bg-zinc-950">
        <OnboardingModal
          onComplete={() => {
            refresh?.();
          }}
        />
      </div>
    );
  }

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

function RootGate() {
  const { user, loading } = useAuth();

  if (loading) {
    return <LoadingScreen />;
  }

  if (!user) {
    return <LandingPage />;
  }

  return (
    <ProtectedRoute>
      <Layout />
    </ProtectedRoute>
  );
}

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

function AppRouter() {
  const location = useLocation();

  const hasOAuth =
    location.hash?.includes('session_id=') ||
    location.search?.includes('session_id=');

  if (hasOAuth) {
    return <AuthCallback />;
  }

  return (
    <Routes>
      <Route
        path="/login"
        element={
          <PublicAuthRoute>
            <AuthPage />
          </PublicAuthRoute>
        }
      />

      <Route path="/terms" element={<TermsPage />} />
      <Route path="/privacy" element={<PrivacyPage />} />

      <Route
        path="/verify-email"
        element={<EmailVerificationPage />}
      />

      <Route
        path="/resend-verification"
        element={<EmailVerificationPage />}
      />

      <Route path="/" element={<RootGate />}>
        <Route index element={<Dashboard />} />

        <Route
          path="dashboard"
          element={<Dashboard />}
        />

        <Route
          path="chat"
          element={<ChatPage />}
        />

        <Route
          path="chat/:sessionId"
          element={<ChatPage />}
        />

        <Route
          path="syllabus"
          element={<SyllabusPage />}
        />

        <Route
          path="progress"
          element={<ProgressPage />}
        />

        <Route
          path="quiz"
          element={<QuizArena />}
        />

        <Route
          path="leaderboard"
          element={<LeaderboardPage />}
        />

        <Route
          path="mock-exams"
          element={<MockExamPage />}
        />

        <Route
          path="study-plan"
          element={<StudyPlanPage />}
        />

        <Route
          path="upgrade"
          element={<PricingPage />}
        />

        <Route
          path="profile"
          element={<ProfilePage />}
        />

        <Route
          path="/admin"
          element={
            <ProtectedRoute>
              <AdminDashboard />
            </ProtectedRoute>
          }
        />

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