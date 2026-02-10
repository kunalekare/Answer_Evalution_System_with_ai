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

import React from "react";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import { ThemeProvider, createTheme, CssBaseline } from "@mui/material";
import { Toaster } from "react-hot-toast";

// Context
import { AuthProvider, useAuth, ROLES } from "./context/AuthContext";

// Pages
import LandingPage from "./pages/LandingPage";
import Dashboard from "./pages/Dashboard";
import Evaluate from "./pages/Evaluate";
import Results from "./pages/Results";
import History from "./pages/History";
import StudentDashboard from "./pages/StudentDashboard";
import ChatBot from "./pages/ChatBot";

// Components
import Layout from "./components/Layout";

// Create professional academic theme
const theme = createTheme({
  palette: {
    mode: "light",
    primary: {
      main: "#1565c0",
      light: "#5e92f3",
      dark: "#003c8f",
      contrastText: "#ffffff",
    },
    secondary: {
      main: "#00897b",
      light: "#4ebaaa",
      dark: "#005b4f",
    },
    success: {
      main: "#2e7d32",
      light: "#60ad5e",
      dark: "#005005",
    },
    warning: {
      main: "#f9a825",
      light: "#ffd95a",
      dark: "#c17900",
    },
    error: {
      main: "#c62828",
      light: "#ff5f52",
      dark: "#8e0000",
    },
    background: {
      default: "#f5f7fa",
      paper: "#ffffff",
    },
    text: {
      primary: "#1a1a2e",
      secondary: "#4a4a68",
    },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    h1: {
      fontFamily: '"Poppins", sans-serif',
      fontWeight: 700,
    },
    h2: {
      fontFamily: '"Poppins", sans-serif',
      fontWeight: 600,
    },
    h3: {
      fontFamily: '"Poppins", sans-serif',
      fontWeight: 600,
    },
    h4: {
      fontFamily: '"Poppins", sans-serif',
      fontWeight: 600,
    },
    h5: {
      fontFamily: '"Poppins", sans-serif',
      fontWeight: 500,
    },
    h6: {
      fontFamily: '"Poppins", sans-serif',
      fontWeight: 500,
    },
    button: {
      textTransform: "none",
      fontWeight: 500,
    },
  },
  shape: {
    borderRadius: 12,
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          padding: "10px 24px",
          fontSize: "0.95rem",
        },
        contained: {
          boxShadow: "0 4px 14px 0 rgba(0, 0, 0, 0.1)",
          "&:hover": {
            boxShadow: "0 6px 20px rgba(0, 0, 0, 0.15)",
          },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 16,
          boxShadow: "0 4px 20px rgba(0, 0, 0, 0.08)",
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          borderRadius: 16,
        },
      },
    },
  },
});

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
      
      {/* AI ChatBot - All authenticated users */}
      <Route 
        path="/chatbot" 
        element={
          <ProtectedRoute>
            <Layout><ChatBot /></Layout>
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
    </Routes>
  );
}

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: "#333",
            color: "#fff",
            borderRadius: "10px",
          },
          success: {
            iconTheme: {
              primary: "#4caf50",
              secondary: "#fff",
            },
          },
          error: {
            iconTheme: {
              primary: "#f44336",
              secondary: "#fff",
            },
          },
        }}
      />
      <Router future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <AuthProvider>
          <AppRoutes />
        </AuthProvider>
      </Router>
    </ThemeProvider>
  );
}

export default App;
