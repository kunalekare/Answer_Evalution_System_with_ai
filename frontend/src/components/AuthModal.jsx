/**
 * Authentication Modal Component
 * ================================
 * Professional Sign In / Sign Up modal with role selection.
 * 
 * Features:
 * - Toggle between Sign In and Sign Up
 * - Role selection for registration (Student, Teacher, Admin)
 * - Form validation
 * - Animated transitions
 */

import React, { useState } from 'react';
import {
  Dialog,
  DialogContent,
  Box,
  Typography,
  TextField,
  Button,
  IconButton,
  InputAdornment,
  Divider,
  ToggleButton,
  ToggleButtonGroup,
  Alert,
  Fade,
  useTheme,
  alpha,
  Chip,
} from '@mui/material';
import {
  Close as CloseIcon,
  Visibility,
  VisibilityOff,
  School as StudentIcon,
  Person as TeacherIcon,
  AdminPanelSettings as AdminIcon,
  Email as EmailIcon,
  Lock as LockIcon,
  Person as PersonIcon,
  Login as LoginIcon,
  PersonAdd as SignUpIcon,
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth, ROLES } from '../context/AuthContext';

const MotionBox = motion(Box);

const roleInfo = {
  [ROLES.STUDENT]: {
    icon: <StudentIcon />,
    label: 'Student',
    description: 'View your evaluation scores and results',
    color: '#6366f1',
  },
  [ROLES.TEACHER]: {
    icon: <TeacherIcon />,
    label: 'Teacher',
    description: 'Evaluate student answers and manage assessments',
    color: '#06b6d4',
  },
  [ROLES.ADMIN]: {
    icon: <AdminIcon />,
    label: 'Admin',
    description: 'Full system access and user management',
    color: '#f59e0b',
  },
};

export default function AuthModal({ open, onClose, initialMode = 'signin' }) {
  const theme = useTheme();
  const { signIn, signUp } = useAuth();
  
  const [mode, setMode] = useState(initialMode);
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  
  // Form state
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
    role: ROLES.STUDENT,
  });

  const handleChange = (field) => (e) => {
    setFormData({ ...formData, [field]: e.target.value });
    setError('');
  };

  const handleRoleChange = (e, newRole) => {
    if (newRole) {
      setFormData({ ...formData, role: newRole });
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      if (mode === 'signin') {
        const result = await signIn(formData.email, formData.password);
        if (result.success) {
          onClose();
        } else {
          setError(result.error || 'Login failed');
        }
      } else {
        // Validation for sign up
        if (!formData.name.trim()) {
          setError('Name is required');
          setLoading(false);
          return;
        }
        if (!formData.email.trim()) {
          setError('Email is required');
          setLoading(false);
          return;
        }
        if (formData.password.length < 6) {
          setError('Password must be at least 6 characters');
          setLoading(false);
          return;
        }
        if (formData.password !== formData.confirmPassword) {
          setError('Passwords do not match');
          setLoading(false);
          return;
        }

        const result = await signUp(
          formData.name,
          formData.email,
          formData.password,
          formData.role
        );
        
        if (result.success) {
          onClose();
        } else {
          setError(result.error);
        }
      }
    } catch (err) {
      setError('An error occurred. Please try again.');
    }
    
    setLoading(false);
  };

  const toggleMode = () => {
    setMode(mode === 'signin' ? 'signup' : 'signin');
    setError('');
    setFormData({
      name: '',
      email: '',
      password: '',
      confirmPassword: '',
      role: ROLES.STUDENT,
    });
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="sm"
      fullWidth
      PaperProps={{
        sx: {
          borderRadius: { xs: 0, sm: 4 },
          overflow: 'hidden',
          maxWidth: { xs: '100%', sm: 480 },
          m: { xs: 0, sm: 2 },
          maxHeight: { xs: '100%', sm: 'calc(100% - 64px)' },
        },
      }}
      sx={{
        '& .MuiDialog-container': {
          alignItems: { xs: 'flex-end', sm: 'center' },
        },
      }}
    >
      {/* Header gradient */}
      <Box
        sx={{
          background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
          p: { xs: 2.5, sm: 4 },
          position: 'relative',
        }}
      >
        <IconButton
          onClick={onClose}
          sx={{
            position: 'absolute',
            top: { xs: 8, sm: 12 },
            right: { xs: 8, sm: 12 },
            color: 'white',
          }}
        >
          <CloseIcon />
        </IconButton>
        
        <Box sx={{ textAlign: 'center', color: 'white' }}>
          <Box
            sx={{
              width: { xs: 50, sm: 60 },
              height: { xs: 50, sm: 60 },
              borderRadius: '50%',
              bgcolor: alpha('#fff', 0.2),
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              mx: 'auto',
              mb: { xs: 1.5, sm: 2 },
            }}
          >
            {mode === 'signin' ? <LoginIcon sx={{ fontSize: { xs: 24, sm: 30 } }} /> : <SignUpIcon sx={{ fontSize: { xs: 24, sm: 30 } }} />}
          </Box>
          <Typography variant="h5" fontWeight={700} sx={{ fontSize: { xs: '1.25rem', sm: '1.5rem' } }}>
            {mode === 'signin' ? 'Welcome Back!' : 'Create Account'}
          </Typography>
          <Typography variant="body2" sx={{ opacity: 0.9, mt: 0.5, fontSize: { xs: '0.8rem', sm: '0.875rem' } }}>
            {mode === 'signin' 
              ? 'Sign in to continue to PaperEval' 
              : 'Join PaperEval to get started'}
          </Typography>
        </Box>
      </Box>

      <DialogContent sx={{ p: { xs: 2.5, sm: 4 } }}>
        <AnimatePresence mode="wait">
          <MotionBox
            key={mode}
            initial={{ opacity: 0, x: mode === 'signin' ? -20 : 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: mode === 'signin' ? 20 : -20 }}
            transition={{ duration: 0.3 }}
          >
            <form onSubmit={handleSubmit}>
              {error && (
                <Alert severity="error" sx={{ mb: { xs: 2, sm: 3 }, fontSize: { xs: '0.8rem', sm: '0.875rem' } }}>
                  {error}
                </Alert>
              )}

              {/* Role Selection for Sign Up */}
              {mode === 'signup' && (
                <Box sx={{ mb: { xs: 2, sm: 3 } }}>
                  <Typography variant="subtitle2" fontWeight={600} sx={{ mb: 1.5, fontSize: { xs: '0.8rem', sm: '0.875rem' } }}>
                    I am a...
                  </Typography>
                  <ToggleButtonGroup
                    value={formData.role}
                    exclusive
                    onChange={handleRoleChange}
                    fullWidth
                    sx={{
                      '& .MuiToggleButton-root': {
                        flex: 1,
                        py: { xs: 1, sm: 1.5 },
                        border: '2px solid',
                        borderColor: 'divider',
                        borderRadius: '12px !important',
                        mx: 0.5,
                        '&:first-of-type': { ml: 0 },
                        '&:last-of-type': { mr: 0 },
                        '&.Mui-selected': {
                          borderColor: roleInfo[formData.role].color,
                          bgcolor: alpha(roleInfo[formData.role].color, 0.1),
                          '&:hover': {
                            bgcolor: alpha(roleInfo[formData.role].color, 0.15),
                          },
                        },
                      },
                    }}
                  >
                    {Object.entries(roleInfo).map(([role, info]) => (
                      <ToggleButton key={role} value={role}>
                        <Box sx={{ textAlign: 'center' }}>
                          <Box sx={{ color: info.color, mb: 0.5, '& svg': { fontSize: { xs: 20, sm: 24 } } }}>
                            {info.icon}
                          </Box>
                          <Typography variant="body2" fontWeight={600} sx={{ fontSize: { xs: '0.7rem', sm: '0.8rem' } }}>
                            {info.label}
                          </Typography>
                        </Box>
                      </ToggleButton>
                    ))}
                  </ToggleButtonGroup>
                  <Typography 
                    variant="caption" 
                    color="text.secondary" 
                    sx={{ display: 'block', mt: 1, textAlign: 'center', fontSize: { xs: '0.65rem', sm: '0.75rem' } }}
                  >
                    {roleInfo[formData.role].description}
                  </Typography>
                </Box>
              )}

              {/* Name field for Sign Up */}
              {mode === 'signup' && (
                <TextField
                  fullWidth
                  label="Full Name"
                  value={formData.name}
                  onChange={handleChange('name')}
                  sx={{ mb: 2 }}
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <PersonIcon color="action" />
                      </InputAdornment>
                    ),
                  }}
                />
              )}

              {/* Email field */}
              <TextField
                fullWidth
                label="Email Address"
                type="email"
                value={formData.email}
                onChange={handleChange('email')}
                sx={{ mb: 2 }}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <EmailIcon color="action" />
                    </InputAdornment>
                  ),
                }}
              />

              {/* Password field */}
              <TextField
                fullWidth
                label="Password"
                type={showPassword ? 'text' : 'password'}
                value={formData.password}
                onChange={handleChange('password')}
                sx={{ mb: mode === 'signup' ? 2 : 0 }}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <LockIcon color="action" />
                    </InputAdornment>
                  ),
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton
                        onClick={() => setShowPassword(!showPassword)}
                        edge="end"
                      >
                        {showPassword ? <VisibilityOff /> : <Visibility />}
                      </IconButton>
                    </InputAdornment>
                  ),
                }}
              />

              {/* Confirm Password for Sign Up */}
              {mode === 'signup' && (
                <TextField
                  fullWidth
                  label="Confirm Password"
                  type={showPassword ? 'text' : 'password'}
                  value={formData.confirmPassword}
                  onChange={handleChange('confirmPassword')}
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <LockIcon color="action" />
                      </InputAdornment>
                    ),
                  }}
                />
              )}

              {/* Submit Button */}
              <Button
                type="submit"
                fullWidth
                variant="contained"
                size="large"
                disabled={loading}
                sx={{
                  mt: 3,
                  py: 1.5,
                  fontSize: '1rem',
                  fontWeight: 600,
                  background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
                  '&:hover': {
                    background: 'linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)',
                  },
                }}
              >
                {loading ? 'Please wait...' : mode === 'signin' ? 'Sign In' : 'Create Account'}
              </Button>

              {/* Demo Accounts Info */}
              {mode === 'signin' && (
                <Box sx={{ mt: { xs: 2, sm: 3 }, p: { xs: 1.5, sm: 2 }, bgcolor: alpha('#6366f1', 0.05), borderRadius: 2 }}>
                  <Typography variant="caption" fontWeight={600} color="text.secondary" sx={{ fontSize: { xs: '0.65rem', sm: '0.75rem' } }}>
                    Demo Accounts:
                  </Typography>
                  <Box sx={{ mt: 1, display: 'flex', flexDirection: { xs: 'column', sm: 'row' }, flexWrap: 'wrap', gap: 0.5 }}>
                    <Chip 
                      size="small" 
                      label="admin@papereval.com / admin123"
                      sx={{ fontSize: { xs: '0.6rem', sm: '0.7rem' }, height: { xs: 22, sm: 24 } }}
                    />
                    <Chip 
                      size="small" 
                      label="teacher@papereval.com / teacher123"
                      sx={{ fontSize: { xs: '0.6rem', sm: '0.7rem' }, height: { xs: 22, sm: 24 } }}
                    />
                    <Chip 
                      size="small" 
                      label="student@papereval.com / student123"
                      sx={{ fontSize: { xs: '0.6rem', sm: '0.7rem' }, height: { xs: 22, sm: 24 } }}
                    />
                  </Box>
                </Box>
              )}

              {/* Toggle mode */}
              <Divider sx={{ my: { xs: 2, sm: 3 } }}>
                <Typography variant="body2" color="text.secondary" sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}>
                  or
                </Typography>
              </Divider>

              <Box sx={{ textAlign: 'center' }}>
                <Typography variant="body2" color="text.secondary" sx={{ fontSize: { xs: '0.8rem', sm: '0.875rem' } }}>
                  {mode === 'signin' ? "Don't have an account?" : 'Already have an account?'}
                </Typography>
                <Button
                  onClick={toggleMode}
                  sx={{ mt: 1, fontWeight: 600, fontSize: { xs: '0.8rem', sm: '0.875rem' } }}
                >
                  {mode === 'signin' ? 'Create Account' : 'Sign In'}
                </Button>
              </Box>
            </form>
          </MotionBox>
        </AnimatePresence>
      </DialogContent>
    </Dialog>
  );
}
