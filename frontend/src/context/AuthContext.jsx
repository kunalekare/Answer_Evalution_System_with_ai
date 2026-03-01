/**
 * Authentication Context
 * =======================
 * Provides user authentication state and methods across the app.
 * Connects to the backend API for authentication.
 * 
 * Roles:
 * - student: Can view their scores/results, create grievances
 * - teacher: Full evaluation access, manage students, handle grievances
 * - admin: Full system access including user management
 */

import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// User role permissions
export const ROLES = {
  STUDENT: 'student',
  TEACHER: 'teacher',
  ADMIN: 'admin',
};

// Role-based permissions
export const PERMISSIONS = {
  [ROLES.STUDENT]: {
    canEvaluate: false,
    canViewOwnResults: true,
    canViewAllResults: false,
    canUpload: false,
    canManageUsers: false,
    canViewHistory: false,
    canViewDashboard: false,
    canCreateGrievance: true,
    canCreateCommunity: false,
  },
  [ROLES.TEACHER]: {
    canEvaluate: true,
    canViewOwnResults: true,
    canViewAllResults: true,
    canUpload: true,
    canManageUsers: false,
    canViewHistory: true,
    canViewDashboard: true,
    canCreateGrievance: true,
    canCreateCommunity: true,
  },
  [ROLES.ADMIN]: {
    canEvaluate: true,
    canViewOwnResults: true,
    canViewAllResults: true,
    canUpload: true,
    canManageUsers: true,
    canViewHistory: true,
    canViewDashboard: true,
    canCreateGrievance: true,
    canCreateCommunity: true,
  },
};

const AuthContext = createContext(null);

// Demo/Mock users for testing (used when backend is unavailable)
const DEMO_USERS = [
  { id: 1, email: 'admin@papereval.com', password: 'admin123', name: 'Admin User', role: ROLES.ADMIN },
  { id: 2, email: 'teacher@papereval.com', password: 'teacher123', name: 'Dr. Sarah Johnson', role: ROLES.TEACHER },
  { id: 3, email: 'student@papereval.com', password: 'student123', name: 'John Student', role: ROLES.STUDENT },
];

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState(null);
  const [refreshToken, setRefreshToken] = useState(null);

  // Check for existing session on mount
  useEffect(() => {
    const savedToken = localStorage.getItem('token');
    const savedRefreshToken = localStorage.getItem('refreshToken');
    const savedUser = localStorage.getItem('assessiq_user');
    
    if (savedToken && savedUser) {
      try {
        setToken(savedToken);
        setRefreshToken(savedRefreshToken);
        setUser(JSON.parse(savedUser));
      } catch (e) {
        localStorage.removeItem('token');
        localStorage.removeItem('refreshToken');
        localStorage.removeItem('assessiq_user');
      }
    }
    setLoading(false);
  }, []);

  // Sign in function - tries backend first, falls back to demo mode
  const signIn = async (email, password, role = null) => {
    try {
      // Determine role from email if not specified
      if (!role) {
        if (email.toLowerCase().includes('admin')) role = 'admin';
        else if (email.toLowerCase().includes('teacher')) role = 'teacher';
        else role = 'student';
      }

      // Try backend API first
      const response = await axios.post(`${API_BASE_URL}/api/v1/auth/login`, {
        email,
        password,
        role
      });

      if (response.data.access_token) {
        const user = response.data.user || {};
        const userData = {
          id: user.id,
          email: user.email || email,
          name: user.name || email.split('@')[0],
          role: user.role || role,
          [`${user.role || role}_id`]: user.id
        };
        
        setToken(response.data.access_token);
        setRefreshToken(response.data.refresh_token);
        setUser(userData);
        
        localStorage.setItem('token', response.data.access_token);
        localStorage.setItem('refreshToken', response.data.refresh_token);
        localStorage.setItem('assessiq_user', JSON.stringify(userData));
        
        return { success: true, user: userData };
      }
    } catch (error) {
      console.log('Backend auth failed, trying demo mode:', error.message);
    }

    // Fallback to demo mode
    const foundUser = DEMO_USERS.find(
      u => u.email.toLowerCase() === email.toLowerCase() && u.password === password
    );
    
    if (foundUser) {
      const userWithoutPassword = { ...foundUser };
      delete userWithoutPassword.password;
      userWithoutPassword[`${foundUser.role}_id`] = foundUser.id;
      setUser(userWithoutPassword);
      setToken('demo_token');
      localStorage.setItem('token', 'demo_token');
      localStorage.setItem('assessiq_user', JSON.stringify(userWithoutPassword));
      return { success: true, user: userWithoutPassword, isDemo: true };
    }
    
    return { success: false, error: 'Invalid email or password' };
  };

  // Sign up function
  const signUp = async (name, email, password, role = ROLES.STUDENT) => {
    // For demo purposes, create local user
    const newUser = {
      id: Date.now(),
      email,
      name,
      role,
      [`${role}_id`]: Date.now()
    };
    
    setUser(newUser);
    setToken('demo_token');
    localStorage.setItem('token', 'demo_token');
    localStorage.setItem('assessiq_user', JSON.stringify(newUser));
    
    return { success: true, user: newUser };
  };

  // Sign out function
  const signOut = async () => {
    try {
      if (refreshToken && refreshToken !== 'demo_token') {
        await axios.post(`${API_BASE_URL}/api/v1/auth/logout`, {
          refresh_token: refreshToken
        });
      }
    } catch (error) {
      console.log('Logout API call failed:', error.message);
    }
    
    setUser(null);
    setToken(null);
    setRefreshToken(null);
    localStorage.removeItem('token');
    localStorage.removeItem('refreshToken');
    localStorage.removeItem('assessiq_user');
  };

  // Check if user has permission
  const hasPermission = (permission) => {
    if (!user) return false;
    return PERMISSIONS[user.role]?.[permission] || false;
  };

  // Check if user has specific role
  const hasRole = (role) => {
    if (!user) return false;
    if (Array.isArray(role)) {
      return role.includes(user.role);
    }
    return user.role === role;
  };

  // Get all users (admin only) - needs backend call
  const getAllUsers = async () => {
    if (!hasRole(ROLES.ADMIN)) return [];
    // Return demo users for now
    return DEMO_USERS.map(u => {
      const { password, ...userWithoutPassword } = u;
      return userWithoutPassword;
    });
  };

  const value = {
    user,
    loading,
    token,
    isAuthenticated: !!user,
    signIn,
    signUp,
    signOut,
    hasPermission,
    hasRole,
    getAllUsers,
    ROLES,
    PERMISSIONS,
  };

  return (
    <AuthContext.Provider value={value}>
      {!loading && children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

export default AuthContext;
