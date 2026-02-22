/**
 * AssessIQ - Main Application Component
 * ======================================
 * AI-Powered Student Answer Evaluation System
 *
 * Features:
 * - Professional academic dashboard
 * - File upload with drag & drop
 * - Real-time evaluation results
 * - Score visualization
 * - Role-based access (Student, Teacher, Admin)
 */

import React, { useMemo } from "react";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import { ThemeProvider, CssBaseline, createTheme } from "@mui/material";
import { Toaster } from "react-hot-toast";

// Context
import { AuthProvider, useAuth, ROLES } from "./context/AuthContext";
import { ThemeContextProvider, useThemeMode } from "./context/ThemeContext";

// Pages
import LandingPage from "./pages/LandingPage";
import Dashboard from "./pages/Dashboard";
import Evaluate from "./pages/Evaluate";
import Results from "./pages/Results";
import History from "./pages/History";
import StudentDashboard from "./pages/StudentDashboard";
import ChatBot from "./pages/ChatBot";
import ManualChecking from "./pages/ManualChecking";
import Community from "./pages/Community";
import StudentManagement from "./pages/StudentManagement";
import UserManagement from "./pages/UserManagement";
import Profile from "./pages/Profile";

// Components
import Layout from "./components/Layout";

// Protected Route Component
function ProtectedRoute({ children, allowedRoles = [], requireAuth = true }) {
  const { isAuthenticated, hasRole } = useAuth();
  
  if (requireAuth && !isAuthenticated) {
    return <Navigate to="/" replace />;
  }
  
  if (allowedRoles.length > 0 && !hasRole(allowedRoles)) {
    // Redirect students to their dashboard
    if (hasRole(ROLES.STUDENT)) {
      return <Navigate to="/student" replace />;
    }
    return <Navigate to="/dashboard" replace />;
  }
  
  return children;
}

// Role-based dashboard redirect
function DashboardRedirect() {
  const { hasRole, isAuthenticated } = useAuth();
  
  if (!isAuthenticated) {
    return <Navigate to="/" replace />;
  }
  
  if (hasRole(ROLES.STUDENT)) {
    return <Navigate to="/student" replace />;
  }
  
  return <Dashboard />;
}

function AppRoutes() {
  return (
    <Routes>
      {/* Landing page without layout */}
      <Route path="/" element={<LandingPage />} />
      
      {/* Student Dashboard */}
      <Route 
        path="/student" 
        element={
          <ProtectedRoute allowedRoles={[ROLES.STUDENT]}>
            <Layout><StudentDashboard /></Layout>
          </ProtectedRoute>
        } 
      />
      
      {/* Dashboard with role-based redirect */}
      <Route 
        path="/dashboard" 
        element={
          <ProtectedRoute>
            <Layout><DashboardRedirect /></Layout>
          </ProtectedRoute>
        } 
      />
      
      {/* Evaluate - Teachers and Admins only */}
      <Route 
        path="/evaluate" 
        element={
          <ProtectedRoute allowedRoles={[ROLES.TEACHER, ROLES.ADMIN]}>
            <Layout><Evaluate /></Layout>
          </ProtectedRoute>
        } 
      />
      
      {/* Manual Checking - Teachers and Admins only */}
      <Route 
        path="/manual-checking" 
        element={
          <ProtectedRoute allowedRoles={[ROLES.TEACHER, ROLES.ADMIN]}>
            <Layout><ManualChecking /></Layout>
          </ProtectedRoute>
        } 
      />
      
      {/* AI ChatBot - All authenticated users */}
      <Route 
        path="/chatbot" 
        element={
          <ProtectedRoute>
            <Layout><ChatBot /></Layout>
          </ProtectedRoute>
        } 
      />
      
      {/* Community - All authenticated users */}
      <Route 
        path="/community" 
        element={
          <ProtectedRoute>
            <Layout><Community /></Layout>
          </ProtectedRoute>
        } 
      />
      
      {/* Results - All authenticated users */}
      <Route 
        path="/results/:id" 
        element={
          <ProtectedRoute>
            <Layout><Results /></Layout>
          </ProtectedRoute>
        } 
      />
      
      {/* History - Teachers and Admins only */}
      <Route 
        path="/history" 
        element={
          <ProtectedRoute allowedRoles={[ROLES.TEACHER, ROLES.ADMIN]}>
            <Layout><History /></Layout>
          </ProtectedRoute>
        } 
      />
      
      {/* Student Management - Teachers only */}
      <Route 
        path="/students" 
        element={
          <ProtectedRoute allowedRoles={[ROLES.TEACHER]}>
            <Layout><StudentManagement /></Layout>
          </ProtectedRoute>
        } 
      />
      
      {/* User Management - Admins only */}
      <Route 
        path="/admin/users" 
        element={
          <ProtectedRoute allowedRoles={[ROLES.ADMIN]}>
            <Layout><UserManagement /></Layout>
          </ProtectedRoute>
        } 
      />
      
      {/* Profile - Students only */}
      <Route 
        path="/profile" 
        element={
          <ProtectedRoute allowedRoles={[ROLES.STUDENT]}>
            <Layout><Profile /></Layout>
          </ProtectedRoute>
        } 
      />
    </Routes>
  );
}

// Inner app component that uses the theme from context
function ThemedApp() {
  const { mode } = useThemeMode();
  
  return (
    <>
      <CssBaseline />
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: mode === 'dark' ? '#334155' : '#333',
            color: '#fff',
            borderRadius: '10px',
          },
          success: {
            iconTheme: {
              primary: '#4ade80',
              secondary: '#fff',
            },
          },
          error: {
            iconTheme: {
              primary: '#f87171',
              secondary: '#fff',
            },
          },
        }}
      />
      <Router future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <AuthProvider>
          <AppRoutes />
        </AuthProvider>
      </Router>
    </>
  );
}

function App() {
  return (
    <ThemeContextProvider>
      <ThemedAppWrapper />
    </ThemeContextProvider>
  );
}

// Wrapper component that applies the theme
function ThemedAppWrapper() {
  const { mode, isDark } = useThemeMode();
  
  const theme = useMemo(() => {
    const lightPalette = {
      mode: 'light',
      primary: { main: '#6366f1', light: '#818cf8', dark: '#4f46e5' },
      secondary: { main: '#8b5cf6', light: '#a78bfa', dark: '#7c3aed' },
      success: { main: '#22c55e', light: '#4ade80', dark: '#16a34a' },
      warning: { main: '#f59e0b', light: '#fbbf24', dark: '#d97706' },
      error: { main: '#ef4444', light: '#f87171', dark: '#dc2626' },
      info: { main: '#06b6d4', light: '#22d3ee', dark: '#0891b2' },
      background: { default: '#f8fafc', paper: '#ffffff' },
      text: { primary: '#1e293b', secondary: '#64748b' },
      divider: 'rgba(0, 0, 0, 0.08)',
    };
    
    const darkPalette = {
      mode: 'dark',
      primary: { main: '#818cf8', light: '#a5b4fc', dark: '#6366f1' },
      secondary: { main: '#a78bfa', light: '#c4b5fd', dark: '#8b5cf6' },
      success: { main: '#4ade80', light: '#86efac', dark: '#22c55e' },
      warning: { main: '#fbbf24', light: '#fcd34d', dark: '#f59e0b' },
      error: { main: '#f87171', light: '#fca5a5', dark: '#ef4444' },
      info: { main: '#22d3ee', light: '#67e8f9', dark: '#06b6d4' },
      background: { default: '#0f172a', paper: '#1e293b' },
      text: { primary: '#f1f5f9', secondary: '#94a3b8' },
      divider: 'rgba(255, 255, 255, 0.08)',
    };
    
    const palette = isDark ? darkPalette : lightPalette;
    
    return createTheme({
      palette,
      typography: {
        fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
        h1: { fontFamily: '"Poppins", sans-serif', fontWeight: 700 },
        h2: { fontFamily: '"Poppins", sans-serif', fontWeight: 600 },
        h3: { fontFamily: '"Poppins", sans-serif', fontWeight: 600 },
        h4: { fontFamily: '"Poppins", sans-serif', fontWeight: 600 },
        h5: { fontFamily: '"Poppins", sans-serif', fontWeight: 500 },
        h6: { fontFamily: '"Poppins", sans-serif', fontWeight: 500 },
        button: { textTransform: 'none', fontWeight: 500 },
      },
      shape: { borderRadius: 12 },
      components: {
        MuiButton: {
          styleOverrides: {
            root: { borderRadius: 8, padding: '10px 24px', fontSize: '0.95rem' },
            contained: {
              boxShadow: '0 4px 14px 0 rgba(0, 0, 0, 0.1)',
              '&:hover': { boxShadow: '0 6px 20px rgba(0, 0, 0, 0.15)' },
            },
          },
        },
        MuiCard: {
          styleOverrides: {
            root: {
              borderRadius: 16,
              boxShadow: isDark ? '0 4px 20px rgba(0, 0, 0, 0.3)' : '0 4px 20px rgba(0, 0, 0, 0.08)',
            },
          },
        },
        MuiPaper: {
          styleOverrides: { root: { borderRadius: 16, backgroundImage: 'none' } },
        },
        MuiAppBar: {
          styleOverrides: { root: { backgroundImage: 'none' } },
        },
        MuiDrawer: {
          styleOverrides: { paper: { backgroundImage: 'none' } },
        },
      },
    });
  }, [isDark]);
  
  return (
    <ThemeProvider theme={theme}>
      <ThemedApp />
    </ThemeProvider>
  );
}

export default App;
