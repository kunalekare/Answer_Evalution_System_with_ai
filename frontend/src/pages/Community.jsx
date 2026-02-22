/**
 * Community Page - AssessIQ
 * ==========================
 * Professional WhatsApp-like community management with grievance system.
 * 
 * Role-based features:
 * - Admin: Create admin-teacher communities, manage all grievances
 * - Teacher: Create teacher-student communities, handle student grievances
 * - Student: Join communities, submit grievances
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Box,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
  Button,
  IconButton,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  ListItemSecondaryAction,
  Avatar,
  Chip,
  Badge,
  Tabs,
  Tab,
  Divider,
  MenuItem,
  InputAdornment,
  CircularProgress,
  Alert,
  Tooltip,
  FormControl,
  InputLabel,
  Select,
  Checkbox,
  ListItemButton,
  Skeleton,
} from '@mui/material';
import {
  Add as AddIcon,
  Send as SendIcon,
  Groups as GroupsIcon,
  Person as PersonIcon,
  Search as SearchIcon,
  MoreVert as MoreVertIcon,
  AttachFile as AttachFileIcon,
  Delete as DeleteIcon,
  Report as ReportIcon,
  CheckCircle as ResolvedIcon,
  Pending as PendingIcon,
  Warning as WarningIcon,
  School as SchoolIcon,
  AdminPanelSettings as AdminIcon,
  Close as CloseIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { useAuth } from '../context/AuthContext';
import {
  getCommunities,
  createCommunity,
  getCommunity,
  deleteCommunity,
  addCommunityMembers,
  removeCommunityMember,
  getCommunityMessages,
  sendCommunityMessage,
  getAvailableMembers,
  getGrievances,
  createGrievance,
  getGrievance,
  updateGrievanceStatus,
  addGrievanceResponse,
  getGrievanceStats,
} from '../services/api';
import toast from 'react-hot-toast';

// ========== Constants ==========
const ROLES = { ADMIN: 'admin', TEACHER: 'teacher', STUDENT: 'student' };
const GRIEVANCE_CATEGORIES = ['Academic', 'Behavioral', 'Technical', 'Administrative', 'Other'];
const GRIEVANCE_PRIORITIES = [
  { value: 'low', label: 'Low', color: 'success' },
  { value: 'medium', label: 'Medium', color: 'info' },
  { value: 'high', label: 'High', color: 'warning' },
  { value: 'urgent', label: 'Urgent', color: 'error' },
];
const GRIEVANCE_STATUSES = [
  { value: 'pending', label: 'Pending', color: 'warning', icon: PendingIcon },
  { value: 'in_review', label: 'In Review', color: 'info', icon: SearchIcon },
  { value: 'resolved', label: 'Resolved', color: 'success', icon: ResolvedIcon },
  { value: 'rejected', label: 'Rejected', color: 'error', icon: CloseIcon },
  { value: 'escalated', label: 'Escalated', color: 'warning', icon: WarningIcon },
];

// ========== Helper Components ==========
const StatusChip = ({ status }) => {
  const statusInfo = GRIEVANCE_STATUSES.find(s => s.value === status) || GRIEVANCE_STATUSES[0];
  const IconComp = statusInfo.icon;
  return (
    <Chip
      size="small"
      label={statusInfo.label}
      color={statusInfo.color}
      icon={<IconComp fontSize="small" />}
      sx={{ fontWeight: 500 }}
    />
  );
};

const PriorityChip = ({ priority }) => {
  const priorityInfo = GRIEVANCE_PRIORITIES.find(p => p.value === priority) || GRIEVANCE_PRIORITIES[1];
  return (
    <Chip
      size="small"
      label={priorityInfo.label}
      color={priorityInfo.color}
      variant="outlined"
      sx={{ fontWeight: 500 }}
    />
  );
};

// ========== Main Community Component ==========
export default function Community() {
  const { user, hasRole } = useAuth();
  const [activeTab, setActiveTab] = useState(0);
  const [loading, setLoading] = useState(true);
  
  // Communities state
  const [communities, setCommunities] = useState([]);
  const [selectedCommunity, setSelectedCommunity] = useState(null);
  const [communityDetails, setCommunityDetails] = useState(null);
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [loadingMessages, setLoadingMessages] = useState(false);
  
  // Grievances state
  const [grievances, setGrievances] = useState([]);
  const [selectedGrievance, setSelectedGrievance] = useState(null);
  const [grievanceStats, setGrievanceStats] = useState(null);
  
  // Dialogs
  const [createCommunityDialog, setCreateCommunityDialog] = useState(false);
  const [createGrievanceDialog, setCreateGrievanceDialog] = useState(false);
  const [addMembersDialog, setAddMembersDialog] = useState(false);
  const [grievanceDetailDialog, setGrievanceDetailDialog] = useState(false);
  const [communityInfoDialog, setCommunityInfoDialog] = useState(false);
  
  // Form states
  const [communityForm, setCommunityForm] = useState({
    name: '',
    description: '',
    community_type: hasRole(ROLES.ADMIN) ? 'admin_teacher' : 'teacher_student',
    allow_member_posts: true,
    allow_file_sharing: true,
  });
  const [grievanceForm, setGrievanceForm] = useState({
    subject: '',
    description: '',
    category: '',
    priority: 'medium',
    community_id: null,
  });
  
  // Available members for adding
  const [availableMembers, setAvailableMembers] = useState([]);
  const [selectedMembers, setSelectedMembers] = useState([]);
  const [memberSearch, setMemberSearch] = useState('');
  
  // Refs
  const messagesEndRef = useRef(null);
  const messageInputRef = useRef(null);

  // ========== Data Fetching ==========
  const fetchCommunities = useCallback(async () => {
    try {
      setLoading(true);
      const response = await getCommunities();
      if (response.success) {
        setCommunities(response.data || []);
      }
    } catch (error) {
      console.error('Error fetching communities:', error);
      toast.error('Failed to load communities');
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchGrievances = useCallback(async () => {
    try {
      const response = await getGrievances(1, 50, {});
      if (response.success) {
        setGrievances(response.data || []);
      }
    } catch (error) {
      console.error('Error fetching grievances:', error);
    }
  }, []);

  const fetchGrievanceStats = useCallback(async () => {
    try {
      const response = await getGrievanceStats();
      if (response.success) {
        setGrievanceStats(response.data);
      }
    } catch (error) {
      console.error('Error fetching grievance stats:', error);
    }
  }, []);

  const fetchCommunityDetails = useCallback(async (communityId) => {
    try {
      const response = await getCommunity(communityId);
      if (response.success) {
        setCommunityDetails(response.data);
      }
    } catch (error) {
      console.error('Error fetching community details:', error);
    }
  }, []);

  const fetchMessages = useCallback(async (communityId) => {
    if (!communityId) return;
    try {
      setLoadingMessages(true);
      const response = await getCommunityMessages(communityId);
      if (response.success) {
        setMessages(response.data || []);
        setTimeout(() => scrollToBottom(), 100);
      }
    } catch (error) {
      console.error('Error fetching messages:', error);
    } finally {
      setLoadingMessages(false);
    }
  }, []);

  const fetchAvailableMembers = useCallback(async (communityId, search = '') => {
    try {
      const response = await getAvailableMembers(communityId, search);
      if (response.success) {
        setAvailableMembers(response.data || []);
      }
    } catch (error) {
      console.error('Error fetching available members:', error);
    }
  }, []);

  // ========== Effects ==========
  useEffect(() => {
    fetchCommunities();
    fetchGrievances();
    if (hasRole(ROLES.ADMIN) || hasRole(ROLES.TEACHER)) {
      fetchGrievanceStats();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (selectedCommunity) {
      fetchCommunityDetails(selectedCommunity.community_id);
      fetchMessages(selectedCommunity.community_id);
    }
  }, [selectedCommunity, fetchCommunityDetails, fetchMessages]);

  // ========== Handlers ==========
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSelectCommunity = (community) => {
    setSelectedCommunity(community);
  };

  const handleCreateCommunity = async () => {
    if (!communityForm.name.trim()) {
      toast.error('Community name is required');
      return;
    }
    try {
      const response = await createCommunity(communityForm);
      if (response.success) {
        toast.success('Community created successfully');
        setCreateCommunityDialog(false);
        setCommunityForm({
          name: '',
          description: '',
          community_type: hasRole(ROLES.ADMIN) ? 'admin_teacher' : 'teacher_student',
          allow_member_posts: true,
          allow_file_sharing: true,
        });
        fetchCommunities();
      }
    } catch (error) {
      console.error('Error creating community:', error);
      toast.error(error.message || 'Failed to create community');
    }
  };

  const handleSendMessage = async () => {
    if (!newMessage.trim() || !selectedCommunity) return;
    try {
      const response = await sendCommunityMessage(selectedCommunity.community_id, newMessage);
      if (response.success) {
        setNewMessage('');
        fetchMessages(selectedCommunity.community_id);
      }
    } catch (error) {
      console.error('Error sending message:', error);
      toast.error('Failed to send message');
    }
  };

  const handleAddMembers = async () => {
    if (selectedMembers.length === 0) {
      toast.error('Please select at least one member');
      return;
    }
    try {
      const response = await addCommunityMembers(selectedCommunity.community_id, selectedMembers);
      if (response.success) {
        toast.success('Members added successfully');
        setAddMembersDialog(false);
        setSelectedMembers([]);
        fetchCommunityDetails(selectedCommunity.community_id);
      }
    } catch (error) {
      console.error('Error adding members:', error);
      toast.error(error.message || 'Failed to add members');
    }
  };

  const handleRemoveMember = async (memberId) => {
    if (!window.confirm('Are you sure you want to remove this member?')) return;
    try {
      const response = await removeCommunityMember(selectedCommunity.community_id, memberId);
      if (response.success) {
        toast.success('Member removed');
        fetchCommunityDetails(selectedCommunity.community_id);
      }
    } catch (error) {
      console.error('Error removing member:', error);
      toast.error('Failed to remove member');
    }
  };

  const handleDeleteCommunity = async () => {
    if (!window.confirm('Are you sure you want to delete this community? This action cannot be undone.')) return;
    try {
      const response = await deleteCommunity(selectedCommunity.community_id);
      if (response.success) {
        toast.success('Community deleted');
        setSelectedCommunity(null);
        setCommunityDetails(null);
        fetchCommunities();
      }
    } catch (error) {
      console.error('Error deleting community:', error);
      toast.error('Failed to delete community');
    }
  };

  const handleCreateGrievance = async () => {
    if (!grievanceForm.subject.trim() || !grievanceForm.description.trim()) {
      toast.error('Subject and description are required');
      return;
    }
    try {
      const response = await createGrievance(grievanceForm);
      if (response.success) {
        toast.success('Grievance submitted successfully');
        setCreateGrievanceDialog(false);
        setGrievanceForm({
          subject: '',
          description: '',
          category: '',
          priority: 'medium',
          community_id: null,
        });
        fetchGrievances();
        if (hasRole(ROLES.ADMIN) || hasRole(ROLES.TEACHER)) {
          fetchGrievanceStats();
        }
      }
    } catch (error) {
      console.error('Error creating grievance:', error);
      toast.error(error.message || 'Failed to submit grievance');
    }
  };

  const handleViewGrievance = async (grievance) => {
    try {
      const response = await getGrievance(grievance.grievance_id);
      if (response.success) {
        setSelectedGrievance(response.data);
        setGrievanceDetailDialog(true);
      }
    } catch (error) {
      console.error('Error fetching grievance details:', error);
      toast.error('Failed to load grievance details');
    }
  };

  const handleUpdateGrievanceStatus = async (grievanceId, status, resolution = null, escalationReason = null) => {
    try {
      const response = await updateGrievanceStatus(grievanceId, status, resolution, escalationReason);
      if (response.success) {
        toast.success(`Grievance ${status === 'resolved' ? 'resolved' : status === 'escalated' ? 'escalated' : 'updated'}`);
        fetchGrievances();
        if (hasRole(ROLES.ADMIN) || hasRole(ROLES.TEACHER)) {
          fetchGrievanceStats();
        }
        // Refresh the detail view
        if (selectedGrievance && selectedGrievance.grievance_id === grievanceId) {
          const detailResponse = await getGrievance(grievanceId);
          if (detailResponse.success) {
            setSelectedGrievance(detailResponse.data);
          }
        }
      }
    } catch (error) {
      console.error('Error updating grievance:', error);
      toast.error('Failed to update grievance');
    }
  };

  const handleAddResponse = async (grievanceId, content) => {
    try {
      const response = await addGrievanceResponse(grievanceId, content);
      if (response.success) {
        toast.success('Response added');
        // Refresh the detail view
        const detailResponse = await getGrievance(grievanceId);
        if (detailResponse.success) {
          setSelectedGrievance(detailResponse.data);
        }
      }
    } catch (error) {
      console.error('Error adding response:', error);
      toast.error('Failed to add response');
    }
  };

  const handleOpenAddMembers = () => {
    setAddMembersDialog(true);
    fetchAvailableMembers(selectedCommunity.community_id);
  };

  const toggleMemberSelection = (memberId) => {
    setSelectedMembers(prev => 
      prev.includes(memberId) 
        ? prev.filter(id => id !== memberId)
        : [...prev, memberId]
    );
  };

  // ========== Render Functions ==========
  const renderCommunityList = () => (
    <Paper sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Typography variant="h6" fontWeight={600}>
          <GroupsIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
          Communities
        </Typography>
        {(hasRole(ROLES.ADMIN) || hasRole(ROLES.TEACHER)) && (
          <Tooltip title="Create Community">
            <IconButton color="primary" onClick={() => setCreateCommunityDialog(true)}>
              <AddIcon />
            </IconButton>
          </Tooltip>
        )}
      </Box>
      
      <Box sx={{ flex: 1, overflow: 'auto' }}>
        {loading ? (
          <Box sx={{ p: 2 }}>
            {[1, 2, 3].map(i => (
              <Skeleton key={i} variant="rectangular" height={70} sx={{ mb: 1, borderRadius: 2 }} />
            ))}
          </Box>
        ) : communities.length === 0 ? (
          <Box sx={{ p: 4, textAlign: 'center' }}>
            <GroupsIcon sx={{ fontSize: 64, color: 'text.disabled', mb: 2 }} />
            <Typography color="text.secondary">
              {hasRole(ROLES.STUDENT) 
                ? "You haven't been added to any community yet"
                : "No communities created yet"}
            </Typography>
            {(hasRole(ROLES.ADMIN) || hasRole(ROLES.TEACHER)) && (
              <Button 
                variant="contained" 
                startIcon={<AddIcon />}
                onClick={() => setCreateCommunityDialog(true)}
                sx={{ mt: 2 }}
              >
                Create Community
              </Button>
            )}
          </Box>
        ) : (
          <List sx={{ p: 1 }}>
            {communities.map((community) => (
              <ListItemButton
                key={community.community_id}
                selected={selectedCommunity?.community_id === community.community_id}
                onClick={() => handleSelectCommunity(community)}
                sx={{ 
                  borderRadius: 2, 
                  mb: 0.5,
                  '&.Mui-selected': {
                    backgroundColor: 'primary.light',
                    color: 'primary.contrastText',
                    '&:hover': {
                      backgroundColor: 'primary.main',
                    }
                  }
                }}
              >
                <ListItemAvatar>
                  <Avatar sx={{ 
                    bgcolor: community.community_type === 'admin_teacher' ? 'secondary.main' : 'primary.main'
                  }}>
                    {community.community_type === 'admin_teacher' ? <AdminIcon /> : <SchoolIcon />}
                  </Avatar>
                </ListItemAvatar>
                <ListItemText
                  primary={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Typography variant="subtitle1" fontWeight={500} noWrap>
                        {community.name}
                      </Typography>
                      {community.is_owner && (
                        <Chip label="Owner" size="small" color="primary" variant="outlined" />
                      )}
                    </Box>
                  }
                  secondary={
                    <Typography variant="body2" color="text.secondary" noWrap>
                      {community.latest_message?.content || community.description || 'No messages yet'}
                    </Typography>
                  }
                />
                {community.unread_count > 0 && (
                  <Badge badgeContent={community.unread_count} color="error" sx={{ mr: 1 }} />
                )}
              </ListItemButton>
            ))}
          </List>
        )}
      </Box>
    </Paper>
  );

  const renderChatArea = () => (
    <Paper sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {!selectedCommunity ? (
        <Box sx={{ 
          flex: 1, 
          display: 'flex', 
          flexDirection: 'column',
          alignItems: 'center', 
          justifyContent: 'center',
          p: 4
        }}>
          <GroupsIcon sx={{ fontSize: 80, color: 'text.disabled', mb: 2 }} />
          <Typography variant="h6" color="text.secondary" textAlign="center">
            Select a community to start chatting
          </Typography>
          <Typography variant="body2" color="text.disabled" textAlign="center" sx={{ mt: 1 }}>
            {hasRole(ROLES.ADMIN) && "Create communities to connect with teachers"}
            {hasRole(ROLES.TEACHER) && "Create communities to connect with students"}
            {hasRole(ROLES.STUDENT) && "Join communities to connect with your teachers"}
          </Typography>
        </Box>
      ) : (
        <>
          {/* Chat Header */}
          <Box sx={{ 
            p: 2, 
            borderBottom: 1, 
            borderColor: 'divider',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            bgcolor: 'primary.main',
            color: 'primary.contrastText'
          }}>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <Avatar sx={{ mr: 2, bgcolor: 'primary.light' }}>
                {selectedCommunity.community_type === 'admin_teacher' ? <AdminIcon /> : <SchoolIcon />}
              </Avatar>
              <Box>
                <Typography variant="h6" fontWeight={600}>
                  {selectedCommunity.name}
                </Typography>
                <Typography variant="body2" sx={{ opacity: 0.8 }}>
                  {communityDetails?.member_count || selectedCommunity.member_count} members
                </Typography>
              </Box>
            </Box>
            <Box>
              <Tooltip title="Community Info">
                <IconButton color="inherit" onClick={() => setCommunityInfoDialog(true)}>
                  <MoreVertIcon />
                </IconButton>
              </Tooltip>
            </Box>
          </Box>
          
          {/* Messages Area */}
          <Box sx={{ flex: 1, overflow: 'auto', p: 2, bgcolor: 'grey.50' }}>
            {loadingMessages ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
                <CircularProgress />
              </Box>
            ) : messages.length === 0 ? (
              <Box sx={{ textAlign: 'center', py: 4 }}>
                <Typography color="text.secondary">
                  No messages yet. Start the conversation!
                </Typography>
              </Box>
            ) : (
              messages.map((message) => (
                <Box
                  key={message.message_id}
                  sx={{
                    mb: 1.5,
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: message.sender_type === user?.role ? 'flex-end' : 'flex-start',
                  }}
                >
                  {message.message_type === 'system' ? (
                    <Chip
                      label={message.content}
                      size="small"
                      sx={{ bgcolor: 'grey.200', color: 'text.secondary' }}
                    />
                  ) : (
                    <>
                      <Typography variant="caption" color="text.secondary" sx={{ mb: 0.5, px: 1 }}>
                        {message.sender_name}
                        {message.message_type === 'announcement' && (
                          <Chip label="Announcement" size="small" color="warning" sx={{ ml: 1, height: 18 }} />
                        )}
                      </Typography>
                      <Paper
                        elevation={1}
                        sx={{
                          p: 1.5,
                          maxWidth: '70%',
                          borderRadius: 2,
                          bgcolor: message.sender_type === user?.role ? 'primary.main' : 'white',
                          color: message.sender_type === user?.role ? 'white' : 'text.primary',
                        }}
                      >
                        <Typography variant="body1">{message.content}</Typography>
                        <Typography 
                          variant="caption" 
                          sx={{ 
                            display: 'block', 
                            textAlign: 'right', 
                            mt: 0.5,
                            opacity: 0.7 
                          }}
                        >
                          {new Date(message.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </Typography>
                      </Paper>
                    </>
                  )}
                </Box>
              ))
            )}
            <div ref={messagesEndRef} />
          </Box>
          
          {/* Message Input */}
          <Box sx={{ p: 2, borderTop: 1, borderColor: 'divider', display: 'flex', gap: 1 }}>
            <TextField
              ref={messageInputRef}
              fullWidth
              placeholder="Type a message..."
              value={newMessage}
              onChange={(e) => setNewMessage(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && !e.shiftKey && handleSendMessage()}
              variant="outlined"
              size="small"
              multiline
              maxRows={4}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <IconButton size="small">
                      <AttachFileIcon />
                    </IconButton>
                  </InputAdornment>
                ),
              }}
            />
            <Button 
              variant="contained" 
              onClick={handleSendMessage}
              disabled={!newMessage.trim()}
              sx={{ minWidth: 'auto', px: 2 }}
            >
              <SendIcon />
            </Button>
          </Box>
        </>
      )}
    </Paper>
  );

  const renderGrievanceList = () => (
    <Paper sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
          <Typography variant="h6" fontWeight={600}>
            <ReportIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
            Grievances
          </Typography>
          <Box>
            <Tooltip title="Refresh">
              <IconButton onClick={fetchGrievances}>
                <RefreshIcon />
              </IconButton>
            </Tooltip>
            <Button 
              variant="contained" 
              startIcon={<AddIcon />}
              onClick={() => setCreateGrievanceDialog(true)}
              size="small"
            >
              New
            </Button>
          </Box>
        </Box>
        
        {/* Stats for Admin/Teacher */}
        {(hasRole(ROLES.ADMIN) || hasRole(ROLES.TEACHER)) && grievanceStats && (
          <Grid container spacing={1}>
            <Grid item xs={3}>
              <Box sx={{ textAlign: 'center', p: 1, bgcolor: 'warning.light', borderRadius: 1 }}>
                <Typography variant="h6" fontWeight={600}>{grievanceStats.pending || 0}</Typography>
                <Typography variant="caption">Pending</Typography>
              </Box>
            </Grid>
            <Grid item xs={3}>
              <Box sx={{ textAlign: 'center', p: 1, bgcolor: 'info.light', borderRadius: 1 }}>
                <Typography variant="h6" fontWeight={600}>{grievanceStats.in_review || 0}</Typography>
                <Typography variant="caption">In Review</Typography>
              </Box>
            </Grid>
            <Grid item xs={3}>
              <Box sx={{ textAlign: 'center', p: 1, bgcolor: 'success.light', borderRadius: 1 }}>
                <Typography variant="h6" fontWeight={600}>{grievanceStats.resolved || 0}</Typography>
                <Typography variant="caption">Resolved</Typography>
              </Box>
            </Grid>
            <Grid item xs={3}>
              <Box sx={{ textAlign: 'center', p: 1, bgcolor: 'error.light', borderRadius: 1 }}>
                <Typography variant="h6" fontWeight={600}>{grievanceStats.escalated || 0}</Typography>
                <Typography variant="caption">Escalated</Typography>
              </Box>
            </Grid>
          </Grid>
        )}
      </Box>
      
      <Box sx={{ flex: 1, overflow: 'auto' }}>
        {grievances.length === 0 ? (
          <Box sx={{ p: 4, textAlign: 'center' }}>
            <ReportIcon sx={{ fontSize: 64, color: 'text.disabled', mb: 2 }} />
            <Typography color="text.secondary">
              {hasRole(ROLES.STUDENT) 
                ? "You haven't submitted any grievances"
                : "No grievances to review"}
            </Typography>
            <Button 
              variant="outlined" 
              startIcon={<AddIcon />}
              onClick={() => setCreateGrievanceDialog(true)}
              sx={{ mt: 2 }}
            >
              Submit Grievance
            </Button>
          </Box>
        ) : (
          <List sx={{ p: 1 }}>
            {grievances.map((grievance) => (
              <Card 
                key={grievance.grievance_id} 
                sx={{ mb: 1, cursor: 'pointer' }}
                onClick={() => handleViewGrievance(grievance)}
              >
                <CardContent sx={{ pb: 1 }}>
                  <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
                    <Box sx={{ flex: 1 }}>
                      <Typography variant="subtitle1" fontWeight={600} gutterBottom>
                        {grievance.subject}
                      </Typography>
                      <Typography variant="body2" color="text.secondary" noWrap>
                        {grievance.description}
                      </Typography>
                    </Box>
                    <Box sx={{ ml: 2, display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 0.5 }}>
                      <StatusChip status={grievance.status} />
                      <PriorityChip priority={grievance.priority} />
                    </Box>
                  </Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mt: 1 }}>
                    <Typography variant="caption" color="text.secondary">
                      {grievance.category && <Chip label={grievance.category} size="small" variant="outlined" sx={{ mr: 1 }} />}
                      By: {grievance.complainant_name}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {new Date(grievance.created_at).toLocaleDateString()}
                    </Typography>
                  </Box>
                </CardContent>
              </Card>
            ))}
          </List>
        )}
      </Box>
    </Paper>
  );

  // ========== Dialogs ==========
  const CreateCommunityDialog = () => (
    <Dialog open={createCommunityDialog} onClose={() => setCreateCommunityDialog(false)} maxWidth="sm" fullWidth>
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <GroupsIcon sx={{ mr: 1 }} />
          Create New Community
        </Box>
      </DialogTitle>
      <DialogContent dividers>
        <TextField
          autoFocus
          fullWidth
          label="Community Name"
          value={communityForm.name}
          onChange={(e) => setCommunityForm({ ...communityForm, name: e.target.value })}
          margin="normal"
          required
        />
        <TextField
          fullWidth
          label="Description"
          value={communityForm.description}
          onChange={(e) => setCommunityForm({ ...communityForm, description: e.target.value })}
          margin="normal"
          multiline
          rows={3}
        />
        <FormControl fullWidth margin="normal">
          <InputLabel>Community Type</InputLabel>
          <Select
            value={communityForm.community_type}
            onChange={(e) => setCommunityForm({ ...communityForm, community_type: e.target.value })}
            label="Community Type"
          >
            {hasRole(ROLES.ADMIN) && (
              <MenuItem value="admin_teacher">
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <AdminIcon sx={{ mr: 1 }} /> Admin-Teacher Community
                </Box>
              </MenuItem>
            )}
            <MenuItem value="teacher_student">
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <SchoolIcon sx={{ mr: 1 }} /> Teacher-Student Community
              </Box>
            </MenuItem>
          </Select>
        </FormControl>
      </DialogContent>
      <DialogActions>
        <Button onClick={() => setCreateCommunityDialog(false)}>Cancel</Button>
        <Button variant="contained" onClick={handleCreateCommunity}>Create</Button>
      </DialogActions>
    </Dialog>
  );

  const CreateGrievanceDialog = () => (
    <Dialog open={createGrievanceDialog} onClose={() => setCreateGrievanceDialog(false)} maxWidth="sm" fullWidth>
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <ReportIcon sx={{ mr: 1 }} />
          Submit Grievance
        </Box>
      </DialogTitle>
      <DialogContent dividers>
        <TextField
          autoFocus
          fullWidth
          label="Subject"
          value={grievanceForm.subject}
          onChange={(e) => setGrievanceForm({ ...grievanceForm, subject: e.target.value })}
          margin="normal"
          required
        />
        <TextField
          fullWidth
          label="Description"
          value={grievanceForm.description}
          onChange={(e) => setGrievanceForm({ ...grievanceForm, description: e.target.value })}
          margin="normal"
          multiline
          rows={4}
          required
          placeholder="Please describe your issue in detail..."
        />
        <Grid container spacing={2}>
          <Grid item xs={6}>
            <FormControl fullWidth margin="normal">
              <InputLabel>Category</InputLabel>
              <Select
                value={grievanceForm.category}
                onChange={(e) => setGrievanceForm({ ...grievanceForm, category: e.target.value })}
                label="Category"
              >
                {GRIEVANCE_CATEGORIES.map(cat => (
                  <MenuItem key={cat} value={cat}>{cat}</MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={6}>
            <FormControl fullWidth margin="normal">
              <InputLabel>Priority</InputLabel>
              <Select
                value={grievanceForm.priority}
                onChange={(e) => setGrievanceForm({ ...grievanceForm, priority: e.target.value })}
                label="Priority"
              >
                {GRIEVANCE_PRIORITIES.map(p => (
                  <MenuItem key={p.value} value={p.value}>
                    <Chip label={p.label} color={p.color} size="small" />
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
        </Grid>
        {communities.length > 0 && (
          <FormControl fullWidth margin="normal">
            <InputLabel>Related Community (Optional)</InputLabel>
            <Select
              value={grievanceForm.community_id || ''}
              onChange={(e) => setGrievanceForm({ ...grievanceForm, community_id: e.target.value || null })}
              label="Related Community (Optional)"
            >
              <MenuItem value="">None</MenuItem>
              {communities.map(comm => (
                <MenuItem key={comm.community_id} value={comm.community_id}>{comm.name}</MenuItem>
              ))}
            </Select>
          </FormControl>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={() => setCreateGrievanceDialog(false)}>Cancel</Button>
        <Button variant="contained" color="warning" onClick={handleCreateGrievance}>Submit</Button>
      </DialogActions>
    </Dialog>
  );

  const GrievanceDetailDialog = () => {
    const [responseText, setResponseText] = useState('');
    const [resolutionText, setResolutionText] = useState('');
    const [escalationReason, setEscalationReason] = useState('');
    const [showResolveForm, setShowResolveForm] = useState(false);
    const [showEscalateForm, setShowEscalateForm] = useState(false);

    if (!selectedGrievance) return null;

    const canManage = (hasRole(ROLES.ADMIN) || hasRole(ROLES.TEACHER)) && 
                      selectedGrievance.status !== 'resolved' && 
                      selectedGrievance.status !== 'rejected';

    return (
      <Dialog 
        open={grievanceDetailDialog} 
        onClose={() => {
          setGrievanceDetailDialog(false);
          setSelectedGrievance(null);
        }} 
        maxWidth="md" 
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <ReportIcon sx={{ mr: 1 }} />
              Grievance Details
            </Box>
            <Box>
              <StatusChip status={selectedGrievance.status} />
            </Box>
          </Box>
        </DialogTitle>
        <DialogContent dividers>
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>{selectedGrievance.subject}</Typography>
              <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                <PriorityChip priority={selectedGrievance.priority} />
                {selectedGrievance.category && (
                  <Chip label={selectedGrievance.category} variant="outlined" size="small" />
                )}
              </Box>
              <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap', mb: 2 }}>
                {selectedGrievance.description}
              </Typography>
              <Divider sx={{ my: 2 }} />
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Typography variant="caption" color="text.secondary">Submitted By</Typography>
                  <Typography variant="body2">{selectedGrievance.complainant_name} ({selectedGrievance.complainant_type})</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="caption" color="text.secondary">Assigned To</Typography>
                  <Typography variant="body2">{selectedGrievance.assigned_to || 'Not assigned'}</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="caption" color="text.secondary">Created</Typography>
                  <Typography variant="body2">{new Date(selectedGrievance.created_at).toLocaleString()}</Typography>
                </Grid>
                {selectedGrievance.resolved_at && (
                  <Grid item xs={6}>
                    <Typography variant="caption" color="text.secondary">Resolved</Typography>
                    <Typography variant="body2">{new Date(selectedGrievance.resolved_at).toLocaleString()}</Typography>
                  </Grid>
                )}
              </Grid>
              
              {selectedGrievance.resolution && (
                <Alert severity="success" sx={{ mt: 2 }}>
                  <Typography variant="subtitle2">Resolution:</Typography>
                  {selectedGrievance.resolution}
                </Alert>
              )}
              
              {selectedGrievance.escalation_reason && (
                <Alert severity="warning" sx={{ mt: 2 }}>
                  <Typography variant="subtitle2">Escalation Reason:</Typography>
                  {selectedGrievance.escalation_reason}
                </Alert>
              )}
            </Grid>
            
            {/* Responses */}
            {selectedGrievance.responses && selectedGrievance.responses.length > 0 && (
              <Grid item xs={12}>
                <Typography variant="subtitle1" fontWeight={600} gutterBottom>
                  Responses ({selectedGrievance.responses.length})
                </Typography>
                <List>
                  {selectedGrievance.responses.map((response, index) => (
                    <ListItem key={response.response_id || index} alignItems="flex-start" sx={{ px: 0 }}>
                      <ListItemAvatar>
                        <Avatar sx={{ bgcolor: response.responder_type === 'admin' ? 'secondary.main' : 'primary.main' }}>
                          {response.responder_type === 'admin' ? <AdminIcon /> : 
                           response.responder_type === 'teacher' ? <SchoolIcon /> : <PersonIcon />}
                        </Avatar>
                      </ListItemAvatar>
                      <ListItemText
                        primary={
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <Typography variant="subtitle2">{response.responder_name}</Typography>
                            <Chip label={response.responder_type} size="small" variant="outlined" />
                            {response.action_taken && (
                              <Chip label={response.action_taken} size="small" color="info" />
                            )}
                          </Box>
                        }
                        secondary={
                          <>
                            <Typography variant="body2" sx={{ mt: 0.5 }}>{response.content}</Typography>
                            <Typography variant="caption" color="text.secondary">
                              {new Date(response.created_at).toLocaleString()}
                            </Typography>
                          </>
                        }
                      />
                    </ListItem>
                  ))}
                </List>
              </Grid>
            )}
            
            {/* Add Response */}
            {canManage && (
              <Grid item xs={12}>
                <Typography variant="subtitle1" fontWeight={600} gutterBottom>Add Response</Typography>
                <TextField
                  fullWidth
                  multiline
                  rows={2}
                  placeholder="Type your response..."
                  value={responseText}
                  onChange={(e) => setResponseText(e.target.value)}
                />
                <Button 
                  variant="outlined" 
                  sx={{ mt: 1 }}
                  onClick={() => {
                    if (responseText.trim()) {
                      handleAddResponse(selectedGrievance.grievance_id, responseText);
                      setResponseText('');
                    }
                  }}
                >
                  Add Response
                </Button>
              </Grid>
            )}
          </Grid>
        </DialogContent>
        <DialogActions>
          {canManage && (
            <>
              {!showResolveForm && !showEscalateForm && (
                <>
                  <Button 
                    color="info" 
                    onClick={() => handleUpdateGrievanceStatus(selectedGrievance.grievance_id, 'in_review')}
                    disabled={selectedGrievance.status === 'in_review'}
                  >
                    Mark In Review
                  </Button>
                  <Button 
                    color="success" 
                    variant="contained"
                    onClick={() => setShowResolveForm(true)}
                  >
                    Resolve
                  </Button>
                  {hasRole(ROLES.TEACHER) && selectedGrievance.status !== 'escalated' && (
                    <Button 
                      color="warning" 
                      variant="contained"
                      onClick={() => setShowEscalateForm(true)}
                    >
                      Escalate to Admin
                    </Button>
                  )}
                  <Button 
                    color="error" 
                    onClick={() => handleUpdateGrievanceStatus(selectedGrievance.grievance_id, 'rejected')}
                  >
                    Reject
                  </Button>
                </>
              )}
              
              {showResolveForm && (
                <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', width: '100%' }}>
                  <TextField
                    size="small"
                    placeholder="Resolution details..."
                    value={resolutionText}
                    onChange={(e) => setResolutionText(e.target.value)}
                    sx={{ flex: 1 }}
                  />
                  <Button 
                    color="success" 
                    variant="contained"
                    onClick={() => {
                      handleUpdateGrievanceStatus(selectedGrievance.grievance_id, 'resolved', resolutionText);
                      setShowResolveForm(false);
                      setResolutionText('');
                    }}
                  >
                    Confirm
                  </Button>
                  <Button onClick={() => setShowResolveForm(false)}>Cancel</Button>
                </Box>
              )}
              
              {showEscalateForm && (
                <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', width: '100%' }}>
                  <TextField
                    size="small"
                    placeholder="Reason for escalation..."
                    value={escalationReason}
                    onChange={(e) => setEscalationReason(e.target.value)}
                    sx={{ flex: 1 }}
                  />
                  <Button 
                    color="warning" 
                    variant="contained"
                    onClick={() => {
                      handleUpdateGrievanceStatus(selectedGrievance.grievance_id, 'escalated', null, escalationReason);
                      setShowEscalateForm(false);
                      setEscalationReason('');
                    }}
                  >
                    Confirm
                  </Button>
                  <Button onClick={() => setShowEscalateForm(false)}>Cancel</Button>
                </Box>
              )}
            </>
          )}
          <Button onClick={() => {
            setGrievanceDetailDialog(false);
            setSelectedGrievance(null);
          }}>
            Close
          </Button>
        </DialogActions>
      </Dialog>
    );
  };

  const AddMembersDialog = () => (
    <Dialog open={addMembersDialog} onClose={() => setAddMembersDialog(false)} maxWidth="sm" fullWidth>
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <PersonIcon sx={{ mr: 1 }} />
          Add Members to Community
        </Box>
      </DialogTitle>
      <DialogContent dividers>
        <TextField
          fullWidth
          placeholder="Search members..."
          value={memberSearch}
          onChange={(e) => {
            setMemberSearch(e.target.value);
            fetchAvailableMembers(selectedCommunity?.community_id, e.target.value);
          }}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon />
              </InputAdornment>
            ),
          }}
          sx={{ mb: 2 }}
        />
        {availableMembers.length === 0 ? (
          <Typography color="text.secondary" textAlign="center" py={2}>
            No available members found
          </Typography>
        ) : (
          <List sx={{ maxHeight: 300, overflow: 'auto' }}>
            {availableMembers.map((member) => (
              <ListItem 
                key={member.id} 
                dense
                onClick={() => toggleMemberSelection(member.id)}
                sx={{ cursor: 'pointer' }}
              >
                <Checkbox
                  checked={selectedMembers.includes(member.id)}
                  onChange={() => toggleMemberSelection(member.id)}
                />
                <ListItemAvatar>
                  <Avatar>
                    {member.type === 'teacher' ? <SchoolIcon /> : <PersonIcon />}
                  </Avatar>
                </ListItemAvatar>
                <ListItemText
                  primary={member.name}
                  secondary={`${member.type} • ${member.email || member.roll_no || ''}`}
                />
              </ListItem>
            ))}
          </List>
        )}
        {selectedMembers.length > 0 && (
          <Typography variant="body2" color="primary" sx={{ mt: 1 }}>
            {selectedMembers.length} member(s) selected
          </Typography>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={() => {
          setAddMembersDialog(false);
          setSelectedMembers([]);
        }}>Cancel</Button>
        <Button 
          variant="contained" 
          onClick={handleAddMembers}
          disabled={selectedMembers.length === 0}
        >
          Add Members
        </Button>
      </DialogActions>
    </Dialog>
  );

  const CommunityInfoDialog = () => (
    <Dialog 
      open={communityInfoDialog} 
      onClose={() => setCommunityInfoDialog(false)} 
      maxWidth="sm" 
      fullWidth
    >
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          Community Info
          <IconButton onClick={() => setCommunityInfoDialog(false)}>
            <CloseIcon />
          </IconButton>
        </Box>
      </DialogTitle>
      <DialogContent dividers>
        {communityDetails && (
          <>
            <Box sx={{ textAlign: 'center', mb: 3 }}>
              <Avatar sx={{ width: 80, height: 80, mx: 'auto', mb: 2, bgcolor: 'primary.main' }}>
                {communityDetails.community_type === 'admin_teacher' ? <AdminIcon fontSize="large" /> : <SchoolIcon fontSize="large" />}
              </Avatar>
              <Typography variant="h5" fontWeight={600}>{communityDetails.name}</Typography>
              <Typography variant="body2" color="text.secondary">{communityDetails.description || 'No description'}</Typography>
              <Chip 
                label={communityDetails.community_type === 'admin_teacher' ? 'Admin-Teacher' : 'Teacher-Student'} 
                color={communityDetails.community_type === 'admin_teacher' ? 'secondary' : 'primary'}
                sx={{ mt: 1 }}
              />
            </Box>
            
            <Divider sx={{ my: 2 }} />
            
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="subtitle1" fontWeight={600}>
                Members ({communityDetails.members?.length || 0})
              </Typography>
              {selectedCommunity?.is_owner && (
                <Button startIcon={<AddIcon />} size="small" onClick={handleOpenAddMembers}>
                  Add Members
                </Button>
              )}
            </Box>
            
            <List>
              {communityDetails.members?.map((member) => (
                <ListItem key={member.member_id}>
                  <ListItemAvatar>
                    <Avatar sx={{ 
                      bgcolor: member.member_type === 'admin' ? 'secondary.main' : 
                               member.member_type === 'teacher' ? 'primary.main' : 'grey.500'
                    }}>
                      {member.member_type === 'admin' ? <AdminIcon /> : 
                       member.member_type === 'teacher' ? <SchoolIcon /> : <PersonIcon />}
                    </Avatar>
                  </ListItemAvatar>
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        {member.member_name}
                        {member.member_role === 'owner' && (
                          <Chip label="Owner" size="small" color="primary" />
                        )}
                      </Box>
                    }
                    secondary={member.member_type}
                  />
                  {selectedCommunity?.is_owner && member.member_role !== 'owner' && (
                    <ListItemSecondaryAction>
                      <IconButton 
                        edge="end" 
                        color="error"
                        onClick={() => handleRemoveMember(member.member_id)}
                      >
                        <DeleteIcon />
                      </IconButton>
                    </ListItemSecondaryAction>
                  )}
                </ListItem>
              ))}
            </List>
          </>
        )}
      </DialogContent>
      <DialogActions>
        {selectedCommunity?.is_owner && (
          <Button color="error" onClick={handleDeleteCommunity}>
            Delete Community
          </Button>
        )}
        <Button onClick={() => setCommunityInfoDialog(false)}>Close</Button>
      </DialogActions>
    </Dialog>
  );

  // ========== Main Render ==========
  return (
    <Box sx={{ height: 'calc(100vh - 120px)', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Box sx={{ mb: 2 }}>
        <Typography variant="h4" fontWeight={700} gutterBottom>
          Community & Grievances
        </Typography>
        <Typography variant="body1" color="text.secondary">
          {hasRole(ROLES.ADMIN) && "Manage communities with teachers and handle escalated grievances"}
          {hasRole(ROLES.TEACHER) && "Manage communities with students and handle their grievances"}
          {hasRole(ROLES.STUDENT) && "Connect with your teachers and submit grievances"}
        </Typography>
      </Box>
      
      {/* Tabs */}
      <Paper sx={{ mb: 2 }}>
        <Tabs value={activeTab} onChange={(_, v) => setActiveTab(v)}>
          <Tab icon={<GroupsIcon />} label="Communities" iconPosition="start" />
          <Tab 
            icon={
              <Badge 
                badgeContent={grievanceStats?.pending || 0} 
                color="warning"
              >
                <ReportIcon />
              </Badge>
            } 
            label="Grievances" 
            iconPosition="start" 
          />
        </Tabs>
      </Paper>
      
      {/* Content */}
      <Box sx={{ flex: 1, overflow: 'hidden' }}>
        {activeTab === 0 ? (
          <Grid container spacing={2} sx={{ height: '100%' }}>
            <Grid item xs={12} md={4} sx={{ height: '100%' }}>
              {renderCommunityList()}
            </Grid>
            <Grid item xs={12} md={8} sx={{ height: '100%' }}>
              {renderChatArea()}
            </Grid>
          </Grid>
        ) : (
          renderGrievanceList()
        )}
      </Box>
      
      {/* Dialogs */}
      <CreateCommunityDialog />
      <CreateGrievanceDialog />
      <GrievanceDetailDialog />
      <AddMembersDialog />
      <CommunityInfoDialog />
    </Box>
  );
}
