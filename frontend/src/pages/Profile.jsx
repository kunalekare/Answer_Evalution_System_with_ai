/**
 * Profile Page
 * =============
 * For students to view and update their profile.
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  TextField,
  Grid,
  Avatar,
  Divider,
  Card,
  CardContent,
  LinearProgress,
  Alert,
  IconButton,
  InputAdornment,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Tabs,
  Tab,
} from '@mui/material';
import {
  Person as PersonIcon,
  Edit as EditIcon,
  Save as SaveIcon,
  Cancel as CancelIcon,
  Email as EmailIcon,
  Phone as PhoneIcon,
  LocationOn as LocationIcon,
  School as SchoolIcon,
  Badge as BadgeIcon,
  CalendarToday as CalendarIcon,
  Wc as GenderIcon,
  History as HistoryIcon,
  Assessment as AssessmentIcon,
  Lock as LockIcon,
  Visibility,
  VisibilityOff,
} from '@mui/icons-material';
import { toast } from 'react-hot-toast';
import { useAuth } from '../context/AuthContext';
import { getStudentProfile, updateStudentProfile, changePassword } from '../services/api';

export default function Profile() {
  const { user, refreshUser } = useAuth();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [activeTab, setActiveTab] = useState(0);
  const [profileData, setProfileData] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    address: '',
    date_of_birth: '',
    gender: '',
  });
  
  // Password change state
  const [passwordData, setPasswordData] = useState({
    current_password: '',
    new_password: '',
    confirm_password: '',
  });
  const [showOldPassword, setShowOldPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);

  useEffect(() => {
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    try {
      setLoading(true);
      const response = await getStudentProfile();
      if (response.success && response.data) {
        setProfileData(response.data);
        setFormData({
          name: response.data.name || '',
          email: response.data.email || '',
          phone: response.data.phone || '',
          address: response.data.address || '',
          date_of_birth: response.data.date_of_birth || '',
          gender: response.data.gender || '',
        });
      }
    } catch (error) {
      console.error('Error fetching profile:', error);
      toast.error('Failed to load profile');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveProfile = async () => {
    try {
      setSaving(true);
      const response = await updateStudentProfile(formData);
      if (response.success) {
        toast.success('Profile updated successfully');
        setIsEditing(false);
        fetchProfile();
        if (refreshUser) refreshUser();
      }
    } catch (error) {
      console.error('Error updating profile:', error);
      toast.error(error.message || 'Failed to update profile');
    } finally {
      setSaving(false);
    }
  };

  const handleChangePassword = async () => {
    if (!passwordData.current_password || !passwordData.new_password) {
      toast.error('Please fill in all password fields');
      return;
    }
    if (passwordData.new_password !== passwordData.confirm_password) {
      toast.error('New passwords do not match');
      return;
    }
    if (passwordData.new_password.length < 6) {
      toast.error('New password must be at least 6 characters');
      return;
    }
    
    try {
      setSaving(true);
      const response = await changePassword({
        current_password: passwordData.current_password,
        new_password: passwordData.new_password,
      });
      if (response.success) {
        toast.success('Password changed successfully');
        setPasswordData({
          current_password: '',
          new_password: '',
          confirm_password: '',
        });
      }
    } catch (error) {
      console.error('Error changing password:', error);
      toast.error(error.message || 'Failed to change password');
    } finally {
      setSaving(false);
    }
  };

  const handleCancelEdit = () => {
    setIsEditing(false);
    if (profileData) {
      setFormData({
        name: profileData.name || '',
        email: profileData.email || '',
        phone: profileData.phone || '',
        address: profileData.address || '',
        date_of_birth: profileData.date_of_birth || '',
        gender: profileData.gender || '',
      });
    }
  };

  if (loading) {
    return (
      <Box sx={{ p: 3 }}>
        <LinearProgress />
        <Typography sx={{ mt: 2, textAlign: 'center' }}>Loading profile...</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3, maxWidth: 1200, mx: 'auto' }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" fontWeight={700} gutterBottom>
            My Profile
          </Typography>
          <Typography variant="body1" color="text.secondary">
            View and manage your profile information
          </Typography>
        </Box>
        {activeTab === 0 && !isEditing && (
          <Button
            variant="contained"
            startIcon={<EditIcon />}
            onClick={() => setIsEditing(true)}
          >
            Edit Profile
          </Button>
        )}
      </Box>

      {/* Profile Header Card */}
      <Card sx={{ mb: 3, background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>
        <CardContent sx={{ py: 4 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 3 }}>
            <Avatar
              src={profileData?.profile_image}
              sx={{
                width: 100,
                height: 100,
                bgcolor: 'rgba(255,255,255,0.2)',
                fontSize: 40,
                border: '4px solid rgba(255,255,255,0.3)',
              }}
            >
              {profileData?.name?.charAt(0) || 'S'}
            </Avatar>
            <Box>
              <Typography variant="h4" sx={{ color: 'white', fontWeight: 700 }}>
                {profileData?.name || 'Student'}
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mt: 1 }}>
                <Chip
                  icon={<BadgeIcon />}
                  label={`Roll No: ${profileData?.roll_no || 'N/A'}`}
                  sx={{ bgcolor: 'rgba(255,255,255,0.2)', color: 'white' }}
                />
                {profileData?.class_name && (
                  <Chip
                    icon={<SchoolIcon />}
                    label={profileData.class_name}
                    sx={{ bgcolor: 'rgba(255,255,255,0.2)', color: 'white' }}
                  />
                )}
                <Chip
                  label={profileData?.status || 'Active'}
                  color={profileData?.status === 'active' ? 'success' : 'default'}
                  sx={{ textTransform: 'capitalize' }}
                />
              </Box>
            </Box>
          </Box>
        </CardContent>
      </Card>

      {/* Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs
          value={activeTab}
          onChange={(_, v) => setActiveTab(v)}
          sx={{ borderBottom: 1, borderColor: 'divider' }}
        >
          <Tab icon={<PersonIcon />} label="Personal Info" iconPosition="start" />
          <Tab icon={<LockIcon />} label="Security" iconPosition="start" />
        </Tabs>
      </Paper>

      {/* Personal Information Tab */}
      {activeTab === 0 && (
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" fontWeight={600} gutterBottom>
            Personal Information
          </Typography>
          <Divider sx={{ mb: 3 }} />

          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Full Name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                disabled={!isEditing}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <PersonIcon color="action" />
                    </InputAdornment>
                  ),
                }}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Email"
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                disabled={!isEditing}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <EmailIcon color="action" />
                    </InputAdornment>
                  ),
                }}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Phone"
                value={formData.phone}
                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                disabled={!isEditing}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <PhoneIcon color="action" />
                    </InputAdornment>
                  ),
                }}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth disabled={!isEditing}>
                <InputLabel>Gender</InputLabel>
                <Select
                  value={formData.gender}
                  onChange={(e) => setFormData({ ...formData, gender: e.target.value })}
                  label="Gender"
                  startAdornment={
                    <InputAdornment position="start">
                      <GenderIcon color="action" />
                    </InputAdornment>
                  }
                >
                  <MenuItem value="">Select</MenuItem>
                  <MenuItem value="Male">Male</MenuItem>
                  <MenuItem value="Female">Female</MenuItem>
                  <MenuItem value="Other">Other</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Date of Birth"
                type="date"
                value={formData.date_of_birth}
                onChange={(e) => setFormData({ ...formData, date_of_birth: e.target.value })}
                disabled={!isEditing}
                InputLabelProps={{ shrink: true }}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <CalendarIcon color="action" />
                    </InputAdornment>
                  ),
                }}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Address"
                value={formData.address}
                onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                disabled={!isEditing}
                multiline
                rows={2}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <LocationIcon color="action" />
                    </InputAdornment>
                  ),
                }}
              />
            </Grid>
          </Grid>

          {/* Academic Information (Read-only) */}
          <Typography variant="h6" fontWeight={600} sx={{ mt: 4 }} gutterBottom>
            Academic Information
          </Typography>
          <Divider sx={{ mb: 3 }} />

          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Roll Number"
                value={profileData?.roll_no || ''}
                disabled
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <BadgeIcon color="action" />
                    </InputAdornment>
                  ),
                }}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Enrollment Number"
                value={profileData?.enrollment_no || ''}
                disabled
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <BadgeIcon color="action" />
                    </InputAdornment>
                  ),
                }}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Class"
                value={profileData?.class_name || ''}
                disabled
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <SchoolIcon color="action" />
                    </InputAdornment>
                  ),
                }}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Academic Year"
                value={profileData?.academic_year || ''}
                disabled
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <CalendarIcon color="action" />
                    </InputAdornment>
                  ),
                }}
              />
            </Grid>
          </Grid>

          {/* Action Buttons */}
          {isEditing && (
            <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 2, mt: 4 }}>
              <Button
                variant="outlined"
                startIcon={<CancelIcon />}
                onClick={handleCancelEdit}
                disabled={saving}
              >
                Cancel
              </Button>
              <Button
                variant="contained"
                startIcon={saving ? null : <SaveIcon />}
                onClick={handleSaveProfile}
                disabled={saving}
              >
                {saving ? 'Saving...' : 'Save Changes'}
              </Button>
            </Box>
          )}
        </Paper>
      )}

      {/* Security Tab */}
      {activeTab === 1 && (
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" fontWeight={600} gutterBottom>
            Change Password
          </Typography>
          <Divider sx={{ mb: 3 }} />

          <Grid container spacing={3} sx={{ maxWidth: 500 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Current Password"
                type={showOldPassword ? 'text' : 'password'}
                value={passwordData.current_password}
                onChange={(e) =>
                  setPasswordData({ ...passwordData, current_password: e.target.value })
                }
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <LockIcon color="action" />
                    </InputAdornment>
                  ),
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton
                        onClick={() => setShowOldPassword(!showOldPassword)}
                        edge="end"
                      >
                        {showOldPassword ? <VisibilityOff /> : <Visibility />}
                      </IconButton>
                    </InputAdornment>
                  ),
                }}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="New Password"
                type={showNewPassword ? 'text' : 'password'}
                value={passwordData.new_password}
                onChange={(e) =>
                  setPasswordData({ ...passwordData, new_password: e.target.value })
                }
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <LockIcon color="action" />
                    </InputAdornment>
                  ),
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton
                        onClick={() => setShowNewPassword(!showNewPassword)}
                        edge="end"
                      >
                        {showNewPassword ? <VisibilityOff /> : <Visibility />}
                      </IconButton>
                    </InputAdornment>
                  ),
                }}
                helperText="Minimum 6 characters"
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Confirm New Password"
                type="password"
                value={passwordData.confirm_password}
                onChange={(e) =>
                  setPasswordData({ ...passwordData, confirm_password: e.target.value })
                }
                error={
                  passwordData.confirm_password &&
                  passwordData.new_password !== passwordData.confirm_password
                }
                helperText={
                  passwordData.confirm_password &&
                  passwordData.new_password !== passwordData.confirm_password
                    ? 'Passwords do not match'
                    : ''
                }
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <LockIcon color="action" />
                    </InputAdornment>
                  ),
                }}
              />
            </Grid>
            <Grid item xs={12}>
              <Button
                variant="contained"
                onClick={handleChangePassword}
                disabled={saving}
              >
                {saving ? 'Changing...' : 'Change Password'}
              </Button>
            </Grid>
          </Grid>

          <Alert severity="info" sx={{ mt: 4 }}>
            Make sure to choose a strong password that you don't use elsewhere. A good password
            includes a mix of letters, numbers, and special characters.
          </Alert>
        </Paper>
      )}
    </Box>
  );
}
