import { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import './App.css';
import './index.css';

import { AuthProvider, useAuth } from './contexts/AuthContext';
import IntroScreen from './components/IntroScreen';
import AuthPage from './components/AuthPage';
import AuthCallback from './components/AuthCallback';
import Layout from './components/Layout';
import Dashboard from './components/Dashboard';
import ChatPage from './components/ChatPage';
import SyllabusPage from './components/SyllabusPage';
import ProgressPage from './components/ProgressPage';
import QuizArena from './components/QuizArena';
import ProfilePage from './components/ProfilePage';

function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) return (
    <div className="min-h-screen bg-zinc-950 flex items-center justify-center">
      <div className="flex flex-col items-center gap-4">
        <div className="w-12 h-12 rounded-full border-2 border-cyan-400 border-t-transparent animate-spin" />
        <p className="text-zinc-400 text-sm font-body">Loading NeuraLearn...</p>
      </div>
    </div>
  );
  if (!user) return <Navigate to="/login" replace />;
  return children;
}

function AppRouter() {
  const location = useLocation();

  // Handle OAuth callback synchronously during render (prevents race conditions)
  if (location.hash?.includes('session_id=')) {
    return <AuthCallback />;
  }

  return (
    <Routes>
      <Route path="/login" element={<AuthPage />} />
      <Route path="/" element={
        <ProtectedRoute>
          <Layout />
        </ProtectedRoute>
      }>
        <Route index element={<Dashboard />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="chat" element={<ChatPage />} />
        <Route path="chat/:sessionId" element={<ChatPage />} />
        <Route path="syllabus" element={<SyllabusPage />} />
        <Route path="progress" element={<ProgressPage />} />
        <Route path="quiz" element={<QuizArena />} />
        <Route path="profile" element={<ProfilePage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}

function App() {
  const [showIntro, setShowIntro] = useState(() => {
    // Skip intro for OAuth callback
    if (window.location.hash?.includes('session_id=')) return false;
    return !sessionStorage.getItem('neuralearn_intro_seen');
  });

  const handleIntroComplete = () => {
    sessionStorage.setItem('neuralearn_intro_seen', 'true');
    setShowIntro(false);
  };

  return (
    <div className="App">
      <BrowserRouter>
        <AuthProvider>
          {showIntro ? (
            <IntroScreen onComplete={handleIntroComplete} />
          ) : (
            <AppRouter />
          )}
        </AuthProvider>
      </BrowserRouter>
    </div>
  );
}

export default App;
