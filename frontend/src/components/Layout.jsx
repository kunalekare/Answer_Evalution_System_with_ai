/**
 * Layout Component
 * =================
 * Main layout wrapper with navigation sidebar and header.
 * Supports role-based navigation for Students, Teachers, and Admins.
 */

import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  Box,
  Drawer,
  AppBar,
  Toolbar,
  List,
  Typography,
  Divider,
  IconButton,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Avatar,
  useTheme,
  useMediaQuery,
  Tooltip,
  Menu,
  MenuItem,
  Chip,
  alpha,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Dashboard as DashboardIcon,
  Assignment as AssignmentIcon,
  History as HistoryIcon,
  Settings as SettingsIcon,
  School as SchoolIcon,
  ChevronLeft as ChevronLeftIcon,
  LightMode as LightModeIcon,
  Notifications as NotificationsIcon,
  Logout as LogoutIcon,
  Person as PersonIcon,
  AdminPanelSettings as AdminIcon,
  Home as HomeIcon,
  Grade as GradeIcon,
  SmartToy as ChatBotIcon,
  FactCheck as ManualCheckIcon,
} from '@mui/icons-material';
import { useAuth, ROLES } from '../context/AuthContext';

const drawerWidth = 280;

// Menu items based on role
const getMenuItems = (role) => {
  const baseItems = [];
  
  if (role === ROLES.STUDENT) {
    return [
      { text: 'My Scores', icon: <GradeIcon />, path: '/student' },
      { text: 'AI Assistant', icon: <ChatBotIcon />, path: '/chatbot' },
    ];
  }
  
  if (role === ROLES.TEACHER || role === ROLES.ADMIN) {
    baseItems.push(
      { text: 'Dashboard', icon: <DashboardIcon />, path: '/dashboard' },
      { text: 'Evaluate Answer', icon: <AssignmentIcon />, path: '/evaluate' },
      { text: 'Manual Checking', icon: <ManualCheckIcon />, path: '/manual-checking' },
      { text: 'AI Assistant', icon: <ChatBotIcon />, path: '/chatbot' },
      { text: 'History', icon: <HistoryIcon />, path: '/history' }
    );
  }
  
  if (role === ROLES.ADMIN) {
    baseItems.push(
      { text: 'User Management', icon: <AdminIcon />, path: '/admin/users' }
    );
  }
  
  return baseItems;
};

const getRoleColor = (role) => {
  if (role === ROLES.ADMIN) return '#f59e0b';
  if (role === ROLES.TEACHER) return '#06b6d4';
  return '#6366f1';
};

const getRoleLabel = (role) => {
  if (role === ROLES.ADMIN) return 'Admin';
  if (role === ROLES.TEACHER) return 'Teacher';
  return 'Student';
};

function Layout({ children }) {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const navigate = useNavigate();
  const location = useLocation();
  const { user, signOut, hasRole } = useAuth();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [collapsed, setCollapsed] = useState(false);
  const [userMenuAnchor, setUserMenuAnchor] = useState(null);
  
  // Get menu items based on user role
  const menuItems = getMenuItems(user?.role);

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const handleNavigation = (path) => {
    navigate(path);
    if (isMobile) {
      setMobileOpen(false);
    }
  };

  const handleUserMenuOpen = (event) => {
    setUserMenuAnchor(event.currentTarget);
  };

  const handleUserMenuClose = () => {
    setUserMenuAnchor(null);
  };

  const handleSignOut = () => {
    signOut();
    handleUserMenuClose();
    navigate('/');
  };

  const handleGoHome = () => {
    navigate('/');
    handleUserMenuClose();
  };

  const drawerContent = (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Logo Section */}
      <Box
        sx={{
          p: 3,
          display: 'flex',
          alignItems: 'center',
          gap: 2,
          cursor: 'pointer',
        }}
        onClick={handleGoHome}
      >
        <Box
          sx={{
            width: 48,
            height: 48,
            borderRadius: 2,
            background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 4px 14px rgba(99, 102, 241, 0.4)',
          }}
        >
          <SchoolIcon sx={{ color: 'white', fontSize: 28 }} />
        </Box>
        {!collapsed && (
          <Box>
            <Typography
              variant="h5"
              sx={{
                fontWeight: 700,
                background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
              }}
            >
              AssessIQ
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Smart Evaluation System
            </Typography>
          </Box>
        )}
      </Box>

      {/* User Info Section */}
      {user && !collapsed && (
        <Box
          sx={{
            mx: 2,
            p: 2,
            borderRadius: 2,
            bgcolor: alpha(getRoleColor(user.role), 0.1),
            mb: 2,
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
            <Avatar
              sx={{
                width: 40,
                height: 40,
                bgcolor: getRoleColor(user.role),
                fontSize: '1rem',
              }}
            >
              {user.name?.charAt(0) || 'U'}
            </Avatar>
            <Box sx={{ flex: 1, minWidth: 0 }}>
              <Typography
                variant="subtitle2"
                fontWeight={600}
                noWrap
                sx={{ maxWidth: 140 }}
              >
                {user.name}
              </Typography>
              <Chip
                size="small"
                label={getRoleLabel(user.role)}
                sx={{
                  height: 18,
                  fontSize: '0.65rem',
                  fontWeight: 600,
                  bgcolor: alpha(getRoleColor(user.role), 0.2),
                  color: getRoleColor(user.role),
                }}
              />
            </Box>
          </Box>
        </Box>
      )}

      <Divider sx={{ mx: 2 }} />

      {/* Navigation Items */}
      <List sx={{ flex: 1, px: 2, py: 2 }}>
        {menuItems.map((item) => {
          const isActive = location.pathname === item.path;
          return (
            <ListItem key={item.text} disablePadding sx={{ mb: 1 }}>
              <ListItemButton
                onClick={() => handleNavigation(item.path)}
                sx={{
                  borderRadius: 2,
                  py: 1.5,
                  backgroundColor: isActive ? 'primary.main' : 'transparent',
                  color: isActive ? 'white' : 'text.primary',
                  '&:hover': {
                    backgroundColor: isActive ? 'primary.dark' : 'action.hover',
                  },
                  transition: 'all 0.2s ease',
                }}
              >
                <ListItemIcon
                  sx={{
                    color: isActive ? 'white' : 'text.secondary',
                    minWidth: 44,
                  }}
                >
                  {item.icon}
                </ListItemIcon>
                {!collapsed && <ListItemText primary={item.text} />}
              </ListItemButton>
            </ListItem>
          );
        })}
      </List>

      {/* Bottom Section */}
      <Box sx={{ p: 2 }}>
        <Divider sx={{ mb: 2 }} />
        <ListItem disablePadding sx={{ mb: 1 }}>
          <ListItemButton
            onClick={handleGoHome}
            sx={{
              borderRadius: 2,
              py: 1.5,
            }}
          >
            <ListItemIcon sx={{ minWidth: 44 }}>
              <HomeIcon />
            </ListItemIcon>
            {!collapsed && <ListItemText primary="Home" />}
          </ListItemButton>
        </ListItem>
        <ListItem disablePadding>
          <ListItemButton
            onClick={handleSignOut}
            sx={{
              borderRadius: 2,
              py: 1.5,
              color: 'error.main',
              '&:hover': {
                bgcolor: alpha('#ef4444', 0.1),
              },
            }}
          >
            <ListItemIcon sx={{ minWidth: 44, color: 'error.main' }}>
              <LogoutIcon />
            </ListItemIcon>
            {!collapsed && <ListItemText primary="Sign Out" />}
          </ListItemButton>
        </ListItem>
      </Box>
    </Box>
  );

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      {/* App Bar */}
      <AppBar
        position="fixed"
        sx={{
          width: { md: `calc(100% - ${collapsed ? 80 : drawerWidth}px)` },
          ml: { md: `${collapsed ? 80 : drawerWidth}px` },
          backgroundColor: 'background.paper',
          color: 'text.primary',
          boxShadow: '0 1px 3px rgba(0, 0, 0, 0.08)',
          borderBottom: '1px solid',
          borderColor: 'divider',
        }}
        elevation={0}
      >
        <Toolbar sx={{ justifyContent: 'space-between' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: { xs: 1, md: 2 } }}>
            <IconButton
              color="inherit"
              aria-label="open drawer"
              edge="start"
              onClick={handleDrawerToggle}
              sx={{ display: { md: 'none' } }}
            >
              <MenuIcon />
            </IconButton>
            <IconButton
              onClick={() => setCollapsed(!collapsed)}
              sx={{ display: { xs: 'none', md: 'flex' } }}
            >
              <ChevronLeftIcon
                sx={{
                  transform: collapsed ? 'rotate(180deg)' : 'rotate(0deg)',
                  transition: 'transform 0.3s ease',
                }}
              />
            </IconButton>
            <Typography 
              variant="h6" 
              noWrap 
              component="div" 
              sx={{ 
                fontWeight: 600,
                fontSize: { xs: '1rem', md: '1.25rem' },
                maxWidth: { xs: 150, sm: 200, md: 'none' },
              }}
            >
              {menuItems.find((item) => item.path === location.pathname)?.text || 'AssessIQ'}
            </Typography>
          </Box>

          <Box sx={{ display: 'flex', alignItems: 'center', gap: { xs: 0.5, md: 1 } }}>
            <Tooltip title="Toggle theme">
              <IconButton size="small" sx={{ display: { xs: 'none', sm: 'flex' } }}>
                <LightModeIcon />
              </IconButton>
            </Tooltip>
            <Tooltip title="Notifications">
              <IconButton size="small">
                <NotificationsIcon />
              </IconButton>
            </Tooltip>
            <Tooltip title={user?.name || 'User'}>
              <Avatar
                onClick={handleUserMenuOpen}
                sx={{
                  ml: { xs: 0.5, md: 1 },
                  width: { xs: 36, md: 40 },
                  height: { xs: 36, md: 40 },
                  bgcolor: getRoleColor(user?.role),
                  cursor: 'pointer',
                  fontWeight: 600,
                  fontSize: { xs: '0.9rem', md: '1rem' },
                }}
              >
                {user?.name?.charAt(0) || 'U'}
              </Avatar>
            </Tooltip>
            <Menu
              anchorEl={userMenuAnchor}
              open={Boolean(userMenuAnchor)}
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
                <Box sx={{ mt: 0.5 }}>
                  <Chip
                    size="small"
                    label={getRoleLabel(user?.role)}
                    sx={{
                      height: 18,
                      fontSize: '0.65rem',
                      fontWeight: 600,
                      bgcolor: alpha(getRoleColor(user?.role), 0.1),
                      color: getRoleColor(user?.role),
                    }}
                  />
                </Box>
              </Box>
              <Divider />
              <MenuItem onClick={handleGoHome}>
                <ListItemIcon>
                  <HomeIcon fontSize="small" />
                </ListItemIcon>
                Home
              </MenuItem>
              <MenuItem onClick={handleSignOut} sx={{ color: 'error.main' }}>
                <ListItemIcon>
                  <LogoutIcon fontSize="small" sx={{ color: 'error.main' }} />
                </ListItemIcon>
                Sign Out
              </MenuItem>
            </Menu>
          </Box>
        </Toolbar>
      </AppBar>

      {/* Sidebar Drawer */}
      <Box
        component="nav"
        sx={{
          width: { md: collapsed ? 80 : drawerWidth },
          flexShrink: { md: 0 },
        }}
      >
        {/* Mobile Drawer */}
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={handleDrawerToggle}
          ModalProps={{ keepMounted: true }}
          sx={{
            display: { xs: 'block', md: 'none' },
            '& .MuiDrawer-paper': {
              boxSizing: 'border-box',
              width: drawerWidth,
              borderRight: 'none',
              boxShadow: '4px 0 24px rgba(0, 0, 0, 0.08)',
            },
          }}
        >
          {drawerContent}
        </Drawer>

        {/* Desktop Drawer */}
        <Drawer
          variant="permanent"
          sx={{
            display: { xs: 'none', md: 'block' },
            '& .MuiDrawer-paper': {
              boxSizing: 'border-box',
              width: collapsed ? 80 : drawerWidth,
              borderRight: 'none',
              boxShadow: '4px 0 24px rgba(0, 0, 0, 0.05)',
              transition: 'width 0.3s ease',
              overflowX: 'hidden',
            },
          }}
          open
        >
          {drawerContent}
        </Drawer>
      </Box>

      {/* Main Content */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: { xs: 2, sm: 2.5, md: 3 },
          width: { md: `calc(100% - ${collapsed ? 80 : drawerWidth}px)` },
          mt: { xs: '56px', md: '64px' },
          backgroundColor: 'background.default',
          minHeight: { xs: 'calc(100vh - 56px)', md: 'calc(100vh - 64px)' },
        }}
      >
        {children}
      </Box>
    </Box>
  );
}

export default Layout;
