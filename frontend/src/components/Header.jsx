/**
 * Professional Header Component
 * ==============================
 * A sleek, animated header for the landing page with:
 * - Logo and branding
 * - Navigation links
 * - Sign In / Sign Up buttons
 * - Scroll-based transparency
 */

import React, { useState, useEffect } from 'react';
import {
  AppBar,
  Toolbar,
  Box,
  Typography,
  Button,
  Container,
  useTheme,
  alpha,
  IconButton,
  Drawer,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  Avatar,
  Menu,
  MenuItem,
  Chip,
  Tooltip,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Close as CloseIcon,
  Psychology as AIIcon,
  Login as LoginIcon,
  PersonAdd as SignUpIcon,
  Dashboard as DashboardIcon,
  School as SchoolIcon,
  History as HistoryIcon,
  Logout as LogoutIcon,
  Person as PersonIcon,
  AdminPanelSettings as AdminIcon,
  LightMode as LightModeIcon,
  DarkMode as DarkModeIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useAuth, ROLES } from '../context/AuthContext';
import { useThemeMode } from '../context/ThemeContext';
import AuthModal from './AuthModal';

const MotionAppBar = motion(AppBar);

const navLinks = [
  { label: 'Features', href: '#features' },
  { label: 'How It Works', href: '#how-it-works' },
  { label: 'Testimonials', href: '#testimonials' },
];

export default function Header() {
  const theme = useTheme();
  const navigate = useNavigate();
  const { user, isAuthenticated, signOut, hasRole } = useAuth();
  const { mode, isDark, toggleTheme } = useThemeMode();
  
  const [scrolled, setScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [authModal, setAuthModal] = useState({ open: false, mode: 'signin' });
  const [userMenu, setUserMenu] = useState(null);

  // Handle scroll
  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 50);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const handleNavClick = (href) => {
    if (href.startsWith('#')) {
      const element = document.querySelector(href);
      if (element) {
        element.scrollIntoView({ behavior: 'smooth' });
      }
    }
    setMobileMenuOpen(false);
  };

  const handleOpenAuth = (mode) => {
    setAuthModal({ open: true, mode });
    setMobileMenuOpen(false);
  };

  const handleCloseAuth = () => {
    setAuthModal({ open: false, mode: 'signin' });
  };

  const handleUserMenuOpen = (event) => {
    setUserMenu(event.currentTarget);
  };

  const handleUserMenuClose = () => {
    setUserMenu(null);
  };

  const handleSignOut = () => {
    signOut();
    handleUserMenuClose();
  };

  const handleGoToDashboard = () => {
    navigate('/dashboard');
    handleUserMenuClose();
  };

  const getRoleColor = () => {
    if (hasRole(ROLES.ADMIN)) return '#f59e0b';
    if (hasRole(ROLES.TEACHER)) return '#06b6d4';
    return '#6366f1';
  };

  const getRoleLabel = () => {
    if (hasRole(ROLES.ADMIN)) return 'Admin';
    if (hasRole(ROLES.TEACHER)) return 'Teacher';
    return 'Student';
  };

  return (
    <>
      <MotionAppBar
        position="fixed"
        elevation={scrolled ? 2 : 0}
        initial={{ y: -100 }}
        animate={{ y: 0 }}
        transition={{ duration: 0.5 }}
        sx={{
          bgcolor: scrolled 
            ? alpha(theme.palette.background.paper, 0.95)
            : 'transparent',
          backdropFilter: scrolled ? 'blur(20px)' : 'none',
          borderBottom: scrolled 
            ? `1px solid ${alpha('#000', 0.1)}`
            : 'none',
          transition: 'all 0.3s ease',
        }}
      >
        <Container maxWidth="lg" sx={{ px: { xs: 2, sm: 3 } }}>
          <Toolbar sx={{ py: { xs: 0.5, md: 1 }, px: 0, minHeight: { xs: 56, md: 64 } }}>
            {/* Logo */}
            <Box 
              sx={{ 
                display: 'flex', 
                alignItems: 'center', 
                cursor: 'pointer',
                mr: { xs: 2, md: 4 },
              }}
              onClick={() => navigate('/')}
            >
              <Box
                sx={{
                  width: { xs: 36, md: 42 },
                  height: { xs: 36, md: 42 },
                  borderRadius: { xs: 1.5, md: 2 },
                  background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  mr: { xs: 1, md: 1.5 },
                }}
              >
                <AIIcon sx={{ color: 'white', fontSize: { xs: 22, md: 26 } }} />
              </Box>
              <Typography
                variant="h5"
                fontWeight={700}
                sx={{
                  fontSize: { xs: '1.25rem', md: '1.5rem' },
                  background: scrolled 
                    ? 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)'
                    : 'linear-gradient(135deg, #fff 0%, #e0e0e0 100%)',
                  backgroundClip: 'text',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                }}
              >
                AssessIQ
              </Typography>
            </Box>

            {/* Desktop Navigation */}
            <Box sx={{ display: { xs: 'none', md: 'flex' }, gap: 1, flexGrow: 1 }}>
              {navLinks.map((link) => (
                <Button
                  key={link.label}
                  onClick={() => handleNavClick(link.href)}
                  sx={{
                    color: scrolled ? 'text.primary' : 'white',
                    fontWeight: 500,
                    px: 2,
                    '&:hover': {
                      bgcolor: scrolled 
                        ? alpha('#6366f1', 0.1)
                        : alpha('#fff', 0.1),
                    },
                  }}
                >
                  {link.label}
                </Button>
              ))}
            </Box>

            {/* Desktop Auth Buttons */}
            <Box sx={{ display: { xs: 'none', md: 'flex' }, gap: 2, alignItems: 'center' }}>
              {/* Theme Toggle */}
              <Tooltip title={isDark ? 'Switch to light mode' : 'Switch to dark mode'}>
                <IconButton
                  onClick={toggleTheme}
                  sx={{
                    width: 40,
                    height: 40,
                    borderRadius: 2,
                    bgcolor: scrolled 
                      ? alpha(isDark ? '#fbbf24' : '#6366f1', 0.1)
                      : alpha('#fff', 0.15),
                    color: scrolled 
                      ? (isDark ? '#fbbf24' : '#6366f1')
                      : 'white',
                    backdropFilter: scrolled ? 'none' : 'blur(8px)',
                    transition: 'all 0.3s ease',
                    '&:hover': {
                      bgcolor: scrolled 
                        ? alpha(isDark ? '#fbbf24' : '#6366f1', 0.2)
                        : alpha('#fff', 0.25),
                      transform: 'rotate(30deg)',
                    },
                  }}
                >
                  {isDark ? <LightModeIcon /> : <DarkModeIcon />}
                </IconButton>
              </Tooltip>
              
              {isAuthenticated ? (
                <>
                  <Button
                    variant="outlined"
                    startIcon={<DashboardIcon />}
                    onClick={handleGoToDashboard}
                    sx={{
                      color: scrolled ? '#6366f1' : 'white',
                      borderColor: scrolled ? '#6366f1' : alpha('#fff', 0.5),
                      '&:hover': {
                        borderColor: scrolled ? '#4f46e5' : 'white',
                        bgcolor: scrolled ? alpha('#6366f1', 0.1) : alpha('#fff', 0.1),
                      },
                    }}
                  >
                    Dashboard
                  </Button>
                  <Box 
                    onClick={handleUserMenuOpen}
                    sx={{ 
                      display: 'flex', 
                      alignItems: 'center', 
                      gap: 1.5,
                      cursor: 'pointer',
                      p: 1,
                      borderRadius: 2,
                      '&:hover': {
                        bgcolor: scrolled ? alpha('#6366f1', 0.1) : alpha('#fff', 0.1),
                      },
                    }}
                  >
                    <Avatar
                      sx={{
                        width: 36,
                        height: 36,
                        bgcolor: getRoleColor(),
                        fontSize: '0.9rem',
                        fontWeight: 600,
                      }}
                    >
                      {user?.name?.charAt(0) || 'U'}
                    </Avatar>
                    <Box sx={{ display: { xs: 'none', lg: 'block' } }}>
                      <Typography
                        variant="body2"
                        fontWeight={600}
                        sx={{ color: scrolled ? 'text.primary' : 'white', lineHeight: 1.2 }}
                      >
                        {user?.name}
                      </Typography>
                      <Chip
                        size="small"
                        label={getRoleLabel()}
                        sx={{
                          height: 18,
                          fontSize: '0.65rem',
                          fontWeight: 600,
                          bgcolor: alpha(getRoleColor(), 0.2),
                          color: getRoleColor(),
                        }}
                      />
                    </Box>
                  </Box>
                  <Menu
                    anchorEl={userMenu}
                    open={Boolean(userMenu)}
                    onClose={handleUserMenuClose}
                    PaperProps={{
                      sx: {
                        mt: 1,
                        minWidth: 200,
                        borderRadius: 2,
                        boxShadow: '0 10px 40px rgba(0,0,0,0.15)',
                      },
                    }}
                  >
                    <Box sx={{ px: 2, py: 1.5 }}>
                      <Typography variant="subtitle2" fontWeight={600}>
                        {user?.name}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {user?.email}
                      </Typography>
                    </Box>
                    <Divider />
                    <MenuItem onClick={handleGoToDashboard}>
                      <ListItemIcon>
                        <DashboardIcon fontSize="small" />
                      </ListItemIcon>
                      Dashboard
                    </MenuItem>
                    <MenuItem onClick={handleSignOut}>
                      <ListItemIcon>
                        <LogoutIcon fontSize="small" />
                      </ListItemIcon>
                      Sign Out
                    </MenuItem>
                  </Menu>
                </>
              ) : (
                <>
                  <Button
                    startIcon={<LoginIcon />}
                    onClick={() => handleOpenAuth('signin')}
                    sx={{
                      color: scrolled ? 'text.primary' : 'white',
                      fontWeight: 500,
                      '&:hover': {
                        bgcolor: scrolled 
                          ? alpha('#6366f1', 0.1)
                          : alpha('#fff', 0.1),
                      },
                    }}
                  >
                    Sign In
                  </Button>
                  <Button
                    variant="contained"
                    startIcon={<SignUpIcon />}
                    onClick={() => handleOpenAuth('signup')}
                    sx={{
                      fontWeight: 600,
                      background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
                      boxShadow: `0 4px 15px ${alpha('#6366f1', 0.4)}`,
                      '&:hover': {
                        background: 'linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)',
                      },
                    }}
                  >
                    Sign Up
                  </Button>
                </>
              )}
            </Box>

            {/* Mobile Menu Button */}
            <IconButton
              sx={{
                display: { xs: 'flex', md: 'none' },
                color: scrolled ? 'text.primary' : 'white',
                ml: 'auto',
              }}
              onClick={() => setMobileMenuOpen(true)}
            >
              <MenuIcon />
            </IconButton>
          </Toolbar>
        </Container>
      </MotionAppBar>

      {/* Mobile Drawer */}
      <Drawer
        anchor="right"
        open={mobileMenuOpen}
        onClose={() => setMobileMenuOpen(false)}
        PaperProps={{
          sx: {
            width: { xs: '85%', sm: 300 },
            maxWidth: 320,
            borderRadius: '16px 0 0 16px',
          },
        }}
      >
        <Box sx={{ p: 2.5, height: '100%', display: 'flex', flexDirection: 'column' }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Box
                sx={{
                  width: 32,
                  height: 32,
                  borderRadius: 1.5,
                  background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <AIIcon sx={{ color: 'white', fontSize: 20 }} />
              </Box>
              <Typography variant="h6" fontWeight={700} sx={{ 
                background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
                backgroundClip: 'text',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
              }}>
                AssessIQ
              </Typography>
            </Box>
            <IconButton onClick={() => setMobileMenuOpen(false)} size="small">
              <CloseIcon />
            </IconButton>
          </Box>

          {isAuthenticated && (
            <Box 
              sx={{ 
                p: 2, 
                bgcolor: alpha('#6366f1', 0.1), 
                borderRadius: 2, 
                mb: 2 
              }}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                <Avatar sx={{ bgcolor: getRoleColor(), width: 44, height: 44 }}>
                  {user?.name?.charAt(0)}
                </Avatar>
                <Box sx={{ flex: 1, minWidth: 0 }}>
                  <Typography variant="subtitle2" fontWeight={600} noWrap>
                    {user?.name}
                  </Typography>
                  <Chip
                    size="small"
                    label={getRoleLabel()}
                    sx={{
                      height: 20,
                      fontSize: '0.7rem',
                      fontWeight: 600,
                      bgcolor: alpha(getRoleColor(), 0.2),
                      color: getRoleColor(),
                    }}
                  />
                </Box>
              </Box>
            </Box>
          )}

          <Divider sx={{ my: 2 }} />

          <List sx={{ flex: 1 }}>
            {navLinks.map((link) => (
              <ListItem 
                button 
                key={link.label}
                onClick={() => handleNavClick(link.href)}
                sx={{
                  borderRadius: 2,
                  mb: 0.5,
                  '&:hover': { bgcolor: alpha('#6366f1', 0.08) },
                }}
              >
                <ListItemText 
                  primary={link.label} 
                  primaryTypographyProps={{ fontWeight: 500 }}
                />
              </ListItem>
            ))}
            {/* Theme Toggle in Mobile Menu */}
            <ListItem 
              button 
              onClick={toggleTheme}
              sx={{
                borderRadius: 2,
                mb: 0.5,
                bgcolor: alpha(isDark ? '#fbbf24' : '#6366f1', 0.08),
                '&:hover': { bgcolor: alpha(isDark ? '#fbbf24' : '#6366f1', 0.15) },
              }}
            >
              <ListItemIcon sx={{ minWidth: 40, color: isDark ? '#fbbf24' : '#6366f1' }}>
                {isDark ? <LightModeIcon /> : <DarkModeIcon />}
              </ListItemIcon>
              <ListItemText 
                primary={isDark ? 'Light Mode' : 'Dark Mode'}
                primaryTypographyProps={{ fontWeight: 500 }}
              />
            </ListItem>
          </List>

          <Divider sx={{ my: 2 }} />

          {isAuthenticated ? (
            <List>
              <ListItem 
                button 
                onClick={handleGoToDashboard}
                sx={{
                  borderRadius: 2,
                  mb: 0.5,
                  bgcolor: alpha('#6366f1', 0.08),
                  '&:hover': { bgcolor: alpha('#6366f1', 0.15) },
                }}
              >
                <ListItemIcon sx={{ minWidth: 40 }}>
                  <DashboardIcon color="primary" />
                </ListItemIcon>
                <ListItemText 
                  primary="Dashboard" 
                  primaryTypographyProps={{ fontWeight: 600, color: 'primary.main' }}
                />
              </ListItem>
              <ListItem 
                button 
                onClick={handleSignOut}
                sx={{
                  borderRadius: 2,
                  '&:hover': { bgcolor: alpha('#ef4444', 0.08) },
                }}
              >
                <ListItemIcon sx={{ minWidth: 40 }}>
                  <LogoutIcon color="error" />
                </ListItemIcon>
                <ListItemText 
                  primary="Sign Out"
                  primaryTypographyProps={{ color: 'error.main' }}
                />
              </ListItem>
            </List>
          ) : (
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
              <Button
                fullWidth
                variant="outlined"
                size="large"
                startIcon={<LoginIcon />}
                onClick={() => handleOpenAuth('signin')}
                sx={{ py: 1.25 }}
              >
                Sign In
              </Button>
              <Button
                fullWidth
                variant="contained"
                size="large"
                startIcon={<SignUpIcon />}
                onClick={() => handleOpenAuth('signup')}
                sx={{
                  py: 1.25,
                  background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
                }}
              >
                Sign Up
              </Button>
            </Box>
          )}
        </Box>
      </Drawer>

      {/* Auth Modal */}
      <AuthModal
        open={authModal.open}
        onClose={handleCloseAuth}
        initialMode={authModal.mode}
      />
    </>
  );
}
