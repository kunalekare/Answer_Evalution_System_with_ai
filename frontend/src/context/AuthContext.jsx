/**
 * Authentication Context
 * =======================
 * Provides user authentication state and methods across the app.
 * 
 * Roles:
 * - student: Can only view their scores/results
 * - teacher: Full access to evaluate answers (current functionality)
 * - admin: Full system access including user management
 */

import React, { createContext, useContext, useState, useEffect } from 'react';

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
  },
  [ROLES.TEACHER]: {
    canEvaluate: true,
    canViewOwnResults: true,
    canViewAllResults: true,
    canUpload: true,
    canManageUsers: false,
    canViewHistory: true,
    canViewDashboard: true,
  },
  [ROLES.ADMIN]: {
    canEvaluate: true,
    canViewOwnResults: true,
    canViewAllResults: true,
    canUpload: true,
    canManageUsers: true,
    canViewHistory: true,
    canViewDashboard: true,
  },
};

const AuthContext = createContext(null);

// Mock users database (in production, this would be a backend API)
const MOCK_USERS = [
  { id: 1, email: 'admin@assessiq.com', password: 'admin123', name: 'Admin User', role: ROLES.ADMIN },
  { id: 2, email: 'teacher@assessiq.com', password: 'teacher123', name: 'Dr. Sarah Johnson', role: ROLES.TEACHER },
  { id: 3, email: 'student@assessiq.com', password: 'student123', name: 'John Student', role: ROLES.STUDENT },
];

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [users, setUsers] = useState(MOCK_USERS);

  // Check for existing session on mount
  useEffect(() => {
    const savedUser = localStorage.getItem('assessiq_user');
    if (savedUser) {
      try {
        setUser(JSON.parse(savedUser));
      } catch (e) {
        localStorage.removeItem('assessiq_user');
      }
    }
    setLoading(false);
  }, []);

  // Sign in function
  const signIn = (email, password) => {
    const foundUser = users.find(
      u => u.email.toLowerCase() === email.toLowerCase() && u.password === password
    );
    
    if (foundUser) {
      const userWithoutPassword = { ...foundUser };
      delete userWithoutPassword.password;
      setUser(userWithoutPassword);
      localStorage.setItem('assessiq_user', JSON.stringify(userWithoutPassword));
      return { success: true, user: userWithoutPassword };
    }
    
    return { success: false, error: 'Invalid email or password' };
  };

  // Sign up function
  const signUp = (name, email, password, role = ROLES.STUDENT) => {
    // Check if email already exists
    if (users.find(u => u.email.toLowerCase() === email.toLowerCase())) {
      return { success: false, error: 'Email already registered' };
    }

    const newUser = {
      id: users.length + 1,
      email,
      password,
      name,
      role,
    };

    setUsers([...users, newUser]);
    
    // Auto sign in after registration
    const userWithoutPassword = { ...newUser };
    delete userWithoutPassword.password;
    setUser(userWithoutPassword);
    localStorage.setItem('assessiq_user', JSON.stringify(userWithoutPassword));
    
    return { success: true, user: userWithoutPassword };
  };

  // Sign out function
  const signOut = () => {
    setUser(null);
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

  // Get all users (admin only)
  const getAllUsers = () => {
    if (!hasRole(ROLES.ADMIN)) return [];
    return users.map(u => {
      const { password, ...userWithoutPassword } = u;
      return userWithoutPassword;
    });
  };

  const value = {
    user,
    loading,
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
