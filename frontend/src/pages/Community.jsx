/**
 * Community Page
 * ===============
 * WhatsApp-like Community System with:
 * - Community management (Admin → Teachers, Teachers → Students)
 * - Group chat functionality
 * - Grievance handling
 * - Announcements
 */

import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Grid,
  Paper,
  Typography,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  ListItemButton,
  Avatar,
  TextField,
  IconButton,
  Button,
  Divider,
  Chip,
  Badge,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Tab,
  Tabs,
  Menu,
  MenuItem,
  Tooltip,
  CircularProgress,
  Alert,
  InputAdornment,
  Card,
  CardContent,
  FormControl,
  InputLabel,
  Select,
  Checkbox,
  ListItemIcon,
  alpha,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import {
  Send as SendIcon,
  AttachFile as AttachIcon,
  Search as SearchIcon,
  Add as AddIcon,
  MoreVert as MoreIcon,
  Group as GroupIcon,
  Person as PersonIcon,
  Campaign as AnnouncementIcon,
  ReportProblem as GrievanceIcon,
  CheckCircle as ResolvedIcon,
  Pending as PendingIcon,
  ArrowUpward as EscalateIcon,
  Close as CloseIcon,
  PushPin as PinIcon,
  Delete as DeleteIcon,
  Reply as ReplyIcon,
  ArrowBack as BackIcon,
  FilterList as FilterIcon,
  Refresh as RefreshIcon,
  InsertDriveFile as FileIcon,
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import toast from 'react-hot-toast';
import { useAuth, ROLES } from '../context/AuthContext';
import * as api from '../services/api';

// Tab Panel Component
function TabPanel({ children, value, index, ...other }) {
  return (
    <div hidden={value !== index} {...other}>
      {value === index && <Box sx={{ height: '100%' }}>{children}</Box>}
    </div>
  );
}

// Status Colors
const statusColors = {
  pending: { color: '#f59e0b', bg: '#fef3c7' },
  in_review: { color: '#3b82f6', bg: '#dbeafe' },
  resolved: { color: '#10b981', bg: '#d1fae5' },
  rejected: { color: '#ef4444', bg: '#fee2e2' },
  escalated: { color: '#8b5cf6', bg: '#ede9fe' },
};

const priorityColors = {
  low: { color: '#6b7280', bg: '#f3f4f6' },
  medium: { color: '#f59e0b', bg: '#fef3c7' },
  high: { color: '#ef4444', bg: '#fee2e2' },
  urgent: { color: '#dc2626', bg: '#fecaca' },
};

function Community() {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const { user } = useAuth();
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);

  // Main state
  const [tabValue, setTabValue] = useState(0);
  const [communities, setCommunities] = useState([]);
  const [selectedCommunity, setSelectedCommunity] = useState(null);
  const [messages, setMessages] = useState([]);
  const [messageInput, setMessageInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sendingMessage, setSendingMessage] = useState(false);

  // Grievance state
  const [grievances, setGrievances] = useState([]);
  const [selectedGrievance, setSelectedGrievance] = useState(null);
  const [grievanceStats, setGrievanceStats] = useState(null);
  const [grievanceFilter, setGrievanceFilter] = useState('all');

  // Dialogs
  const [createCommunityOpen, setCreateCommunityOpen] = useState(false);
  const [addMembersOpen, setAddMembersOpen] = useState(false);
  const [createGrievanceOpen, setCreateGrievanceOpen] = useState(false);
  const [grievanceDetailOpen, setGrievanceDetailOpen] = useState(false);

  // Forms
  const [newCommunity, setNewCommunity] = useState({ name: '', description: '', community_type: 'teacher_student' });
  const [availableMembers, setAvailableMembers] = useState([]);
  const [selectedMembers, setSelectedMembers] = useState([]);
  const [memberSearch, setMemberSearch] = useState('');
  const [newGrievance, setNewGrievance] = useState({ subject: '', description: '', category: 'academic', priority: 'medium' });
  const [grievanceResponse, setGrievanceResponse] = useState('');

  // Menu
  const [menuAnchor, setMenuAnchor] = useState(null);

  // Mobile view state
  const [mobileShowChat, setMobileShowChat] = useState(false);

  // Fetch communities
  useEffect(() => {
    fetchCommunities();
    fetchGrievances();
    fetchGrievanceStats();
  }, []);

  // Auto-scroll to bottom of messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Fetch functions
  const fetchCommunities = async () => {
    try {
      setLoading(true);
      const response = await api.getCommunities();
      if (response.success) {
        setCommunities(response.data || []);
      }
    } catch (error) {
      console.error('Error fetching communities:', error);
      toast.error('Failed to load communities');
    } finally {
      setLoading(false);
    }
  };

  const fetchMessages = async (communityId) => {
    try {
      const response = await api.getCommunityMessages(communityId);
      if (response.success) {
        setMessages(response.data || []);
      }
    } catch (error) {
      console.error('Error fetching messages:', error);
    }
  };

  const fetchGrievances = async () => {
    try {
      const filters = grievanceFilter !== 'all' ? { status_filter: grievanceFilter } : {};
      const response = await api.getGrievances(1, 50, filters);
      if (response.success) {
        setGrievances(response.data || []);
      }
    } catch (error) {
      console.error('Error fetching grievances:', error);
    }
  };

  const fetchGrievanceStats = async () => {
    try {
      const response = await api.getGrievanceStats();
      if (response.success) {
        setGrievanceStats(response.data);
      }
    } catch (error) {
      console.error('Error fetching grievance stats:', error);
    }
  };

  const fetchAvailableMembers = async (communityId, search = '') => {
    try {
      const response = await api.getAvailableMembers(communityId, search);
      if (response.success) {
        setAvailableMembers(response.data || []);
      }
    } catch (error) {
      console.error('Error fetching available members:', error);
    }
  };

  // Event handlers
  const handleSelectCommunity = async (community) => {
    setSelectedCommunity(community);
    if (isMobile) setMobileShowChat(true);
    await fetchMessages(community.community_id);
  };

  const handleSendMessage = async () => {
    if (!messageInput.trim() || !selectedCommunity) return;

    try {
      setSendingMessage(true);
      const response = await api.sendCommunityMessage(
        selectedCommunity.community_id,
        messageInput.trim()
      );
      if (response.success) {
        setMessages([...messages, response.data]);
        setMessageInput('');
      }
    } catch (error) {
      toast.error('Failed to send message');
    } finally {
      setSendingMessage(false);
    }
  };

  const handleSendAnnouncement = async () => {
    if (!messageInput.trim() || !selectedCommunity) return;

    try {
      setSendingMessage(true);
      const response = await api.sendCommunityMessage(
        selectedCommunity.community_id,
        messageInput.trim(),
        'announcement'
      );
      if (response.success) {
        setMessages([...messages, response.data]);
        setMessageInput('');
        toast.success('Announcement sent!');
      }
    } catch (error) {
      toast.error('Failed to send announcement');
    } finally {
      setSendingMessage(false);
    }
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file || !selectedCommunity) return;

    try {
      setSendingMessage(true);
      const response = await api.sendCommunityFileMessage(
        selectedCommunity.community_id,
        file
      );
      if (response.success) {
        setMessages([...messages, response.data]);
        toast.success('File sent!');
      }
    } catch (error) {
      toast.error('Failed to send file');
    } finally {
      setSendingMessage(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleCreateCommunity = async () => {
    try {
      const response = await api.createCommunity(newCommunity);
      if (response.success) {
        toast.success('Community created!');
        setCreateCommunityOpen(false);
        setNewCommunity({ name: '', description: '', community_type: 'teacher_student' });
        fetchCommunities();
      }
    } catch (error) {
      toast.error(error.message || 'Failed to create community');
    }
  };

  const handleAddMembers = async () => {
    if (selectedMembers.length === 0) return;

    try {
      const response = await api.addCommunityMembers(
        selectedCommunity.community_id,
        selectedMembers
      );
      if (response.success) {
        toast.success(`Added ${response.data.added.length} members`);
        setAddMembersOpen(false);
        setSelectedMembers([]);
        fetchCommunities();
      }
    } catch (error) {
      toast.error('Failed to add members');
    }
  };

  const handleCreateGrievance = async () => {
    try {
      const response = await api.createGrievance(newGrievance);
      if (response.success) {
        toast.success('Grievance submitted!');
        setCreateGrievanceOpen(false);
        setNewGrievance({ subject: '', description: '', category: 'academic', priority: 'medium' });
        fetchGrievances();
        fetchGrievanceStats();
      }
    } catch (error) {
      toast.error(error.message || 'Failed to submit grievance');
    }
  };

  const handleGrievanceStatusChange = async (grievanceId, status, resolution = null) => {
    try {
      const response = await api.updateGrievanceStatus(grievanceId, status, resolution);
      if (response.success) {
        toast.success(`Status updated to ${status}`);
        fetchGrievances();
        fetchGrievanceStats();
        if (selectedGrievance) {
          const updated = await api.getGrievance(grievanceId);
          if (updated.success) setSelectedGrievance(updated.data);
        }
      }
    } catch (error) {
      toast.error('Failed to update status');
    }
  };

  const handleAddGrievanceResponse = async () => {
    if (!grievanceResponse.trim() || !selectedGrievance) return;

    try {
      const response = await api.addGrievanceResponse(
        selectedGrievance.grievance_id,
        grievanceResponse.trim()
      );
      if (response.success) {
        toast.success('Response added');
        setGrievanceResponse('');
        const updated = await api.getGrievance(selectedGrievance.grievance_id);
        if (updated.success) setSelectedGrievance(updated.data);
      }
    } catch (error) {
      toast.error('Failed to add response');
    }
  };

  // Render community list
  const renderCommunityList = () => (
    <Paper 
      sx={{ 
        height: '100%', 
        display: 'flex', 
        flexDirection: 'column',
        borderRadius: 2,
        overflow: 'hidden'
      }}
    >
      {/* Header */}
      <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Typography variant="h6" fontWeight={600}>
          Communities
        </Typography>
        {(user?.role === 'admin' || user?.role === 'teacher') && (
          <Tooltip title="Create Community">
            <IconButton onClick={() => setCreateCommunityOpen(true)} color="primary">
              <AddIcon />
            </IconButton>
          </Tooltip>
        )}
      </Box>

      {/* Search */}
      <Box sx={{ p: 1.5, borderBottom: 1, borderColor: 'divider' }}>
        <TextField
          size="small"
          fullWidth
          placeholder="Search communities..."
          InputProps={{
            startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />
          }}
          sx={{ '& .MuiOutlinedInput-root': { borderRadius: 2 } }}
        />
      </Box>

      {/* Community List */}
      <List sx={{ flex: 1, overflow: 'auto', p: 1 }}>
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
            <CircularProgress />
          </Box>
        ) : communities.length === 0 ? (
          <Box sx={{ textAlign: 'center', p: 4 }}>
            <GroupIcon sx={{ fontSize: 48, color: 'text.disabled', mb: 2 }} />
            <Typography color="text.secondary">
              No communities yet
            </Typography>
            {(user?.role === 'admin' || user?.role === 'teacher') && (
              <Button
                variant="outlined"
                startIcon={<AddIcon />}
                onClick={() => setCreateCommunityOpen(true)}
                sx={{ mt: 2 }}
              >
                Create Community
              </Button>
            )}
          </Box>
        ) : (
          communities.map((community) => (
            <ListItemButton
              key={community.community_id}
              onClick={() => handleSelectCommunity(community)}
              selected={selectedCommunity?.community_id === community.community_id}
              sx={{
                borderRadius: 2,
                mb: 0.5,
                '&.Mui-selected': {
                  bgcolor: alpha(theme.palette.primary.main, 0.1),
                }
              }}
            >
              <ListItemAvatar>
                <Avatar sx={{ bgcolor: 'primary.main' }}>
                  <GroupIcon />
                </Avatar>
              </ListItemAvatar>
              <ListItemText
                primary={
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Typography fontWeight={500} noWrap>
                      {community.name}
                    </Typography>
                    {community.is_owner && (
                      <Chip label="Owner" size="small" color="primary" sx={{ height: 20, fontSize: '0.7rem' }} />
                    )}
                  </Box>
                }
                secondary={
                  <Typography variant="caption" color="text.secondary" noWrap>
                    {community.latest_message?.content || `${community.member_count} members`}
                  </Typography>
                }
              />
              {community.unread_count > 0 && (
                <Badge badgeContent={community.unread_count} color="primary" />
              )}
            </ListItemButton>
          ))
        )}
      </List>
    </Paper>
  );

  // Render chat area
  const renderChatArea = () => (
    <Paper 
      sx={{ 
        height: '100%', 
        display: 'flex', 
        flexDirection: 'column',
        borderRadius: 2,
        overflow: 'hidden'
      }}
    >
      {selectedCommunity ? (
        <>
          {/* Chat Header */}
          <Box sx={{ 
            p: 2, 
            borderBottom: 1, 
            borderColor: 'divider',
            display: 'flex',
            alignItems: 'center',
            gap: 2,
            bgcolor: alpha(theme.palette.primary.main, 0.05)
          }}>
            {isMobile && (
              <IconButton onClick={() => setMobileShowChat(false)}>
                <BackIcon />
              </IconButton>
            )}
            <Avatar sx={{ bgcolor: 'primary.main' }}>
              <GroupIcon />
            </Avatar>
            <Box sx={{ flex: 1 }}>
              <Typography fontWeight={600}>{selectedCommunity.name}</Typography>
              <Typography variant="caption" color="text.secondary">
                {selectedCommunity.member_count} members
              </Typography>
            </Box>
            {selectedCommunity.is_owner && (
              <>
                <Tooltip title="Add Members">
                  <IconButton onClick={() => {
                    setAddMembersOpen(true);
                    fetchAvailableMembers(selectedCommunity.community_id);
                  }}>
                    <PersonIcon />
                  </IconButton>
                </Tooltip>
                <IconButton onClick={(e) => setMenuAnchor(e.currentTarget)}>
                  <MoreIcon />
                </IconButton>
                <Menu
                  anchorEl={menuAnchor}
                  open={Boolean(menuAnchor)}
                  onClose={() => setMenuAnchor(null)}
                >
                  <MenuItem onClick={() => {
                    handleSendAnnouncement();
                    setMenuAnchor(null);
                  }}>
                    <ListItemIcon><AnnouncementIcon /></ListItemIcon>
                    Send Announcement
                  </MenuItem>
                </Menu>
              </>
            )}
          </Box>

          {/* Messages Area */}
          <Box sx={{ flex: 1, overflow: 'auto', p: 2, bgcolor: '#f5f5f5' }}>
            <AnimatePresence>
              {messages.map((msg, index) => (
                <motion.div
                  key={msg.message_id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                >
                  <Box
                    sx={{
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: msg.sender_type === user?.role && 
                        (msg.sender_id === user?.[`${user?.role}_id`] || 
                         msg.sender_name === user?.name) ? 'flex-end' : 'flex-start',
                      mb: 2
                    }}
                  >
                    {/* Announcement Badge */}
                    {msg.message_type === 'announcement' && (
                      <Chip
                        icon={<AnnouncementIcon />}
                        label="Announcement"
                        color="warning"
                        size="small"
                        sx={{ mb: 0.5 }}
                      />
                    )}
                    
                    {/* System Message */}
                    {msg.message_type === 'system' ? (
                      <Chip
                        label={msg.content}
                        size="small"
                        sx={{ bgcolor: alpha(theme.palette.info.main, 0.1), color: 'info.main' }}
                      />
                    ) : (
                      <Paper
                        sx={{
                          p: 1.5,
                          maxWidth: '70%',
                          bgcolor: msg.sender_name === user?.name ? 'primary.main' : 'white',
                          color: msg.sender_name === user?.name ? 'white' : 'text.primary',
                          borderRadius: 2,
                          boxShadow: 1
                        }}
                      >
                        {msg.sender_name !== user?.name && (
                          <Typography variant="caption" fontWeight={600} color={msg.sender_name === user?.name ? 'inherit' : 'primary'}>
                            {msg.sender_name}
                          </Typography>
                        )}
                        
                        {/* File Message */}
                        {msg.message_type === 'file' && msg.file_name && (
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                            <FileIcon />
                            <Typography variant="body2">{msg.file_name}</Typography>
                          </Box>
                        )}
                        
                        <Typography variant="body2">{msg.content}</Typography>
                        
                        <Typography 
                          variant="caption" 
                          sx={{ 
                            display: 'block', 
                            mt: 0.5, 
                            opacity: 0.7,
                            textAlign: 'right'
                          }}
                        >
                          {new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </Typography>
                      </Paper>
                    )}
                  </Box>
                </motion.div>
              ))}
            </AnimatePresence>
            <div ref={messagesEndRef} />
          </Box>

          {/* Message Input */}
          <Box sx={{ p: 2, borderTop: 1, borderColor: 'divider', display: 'flex', gap: 1 }}>
            <input
              type="file"
              ref={fileInputRef}
              style={{ display: 'none' }}
              onChange={handleFileUpload}
            />
            <IconButton onClick={() => fileInputRef.current?.click()} disabled={sendingMessage}>
              <AttachIcon />
            </IconButton>
            <TextField
              fullWidth
              size="small"
              placeholder="Type a message..."
              value={messageInput}
              onChange={(e) => setMessageInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && !e.shiftKey && handleSendMessage()}
              disabled={sendingMessage}
              sx={{ '& .MuiOutlinedInput-root': { borderRadius: 3 } }}
            />
            <IconButton 
              color="primary" 
              onClick={handleSendMessage}
              disabled={!messageInput.trim() || sendingMessage}
            >
              {sendingMessage ? <CircularProgress size={24} /> : <SendIcon />}
            </IconButton>
          </Box>
        </>
      ) : (
        <Box sx={{ 
          height: '100%', 
          display: 'flex', 
          flexDirection: 'column',
          alignItems: 'center', 
          justifyContent: 'center',
          p: 4
        }}>
          <GroupIcon sx={{ fontSize: 80, color: 'text.disabled', mb: 2 }} />
          <Typography variant="h6" color="text.secondary">
            Select a community to start chatting
          </Typography>
        </Box>
      )}
    </Paper>
  );

  // Render grievance list
  const renderGrievanceList = () => (
    <Paper sx={{ height: '100%', display: 'flex', flexDirection: 'column', borderRadius: 2, overflow: 'hidden' }}>
      {/* Header */}
      <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
          <Typography variant="h6" fontWeight={600}>
            Grievances
          </Typography>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <IconButton onClick={() => { fetchGrievances(); fetchGrievanceStats(); }}>
              <RefreshIcon />
            </IconButton>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => setCreateGrievanceOpen(true)}
              size="small"
            >
              New
            </Button>
          </Box>
        </Box>

        {/* Stats */}
        {grievanceStats && (
          <Grid container spacing={1} sx={{ mb: 2 }}>
            <Grid item xs={3}>
              <Card sx={{ bgcolor: statusColors.pending.bg }}>
                <CardContent sx={{ p: 1, '&:last-child': { pb: 1 } }}>
                  <Typography variant="h6" sx={{ color: statusColors.pending.color }}>
                    {grievanceStats.pending}
                  </Typography>
                  <Typography variant="caption">Pending</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={3}>
              <Card sx={{ bgcolor: statusColors.in_review.bg }}>
                <CardContent sx={{ p: 1, '&:last-child': { pb: 1 } }}>
                  <Typography variant="h6" sx={{ color: statusColors.in_review.color }}>
                    {grievanceStats.in_review}
                  </Typography>
                  <Typography variant="caption">In Review</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={3}>
              <Card sx={{ bgcolor: statusColors.resolved.bg }}>
                <CardContent sx={{ p: 1, '&:last-child': { pb: 1 } }}>
                  <Typography variant="h6" sx={{ color: statusColors.resolved.color }}>
                    {grievanceStats.resolved}
                  </Typography>
                  <Typography variant="caption">Resolved</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={3}>
              <Card sx={{ bgcolor: statusColors.escalated.bg }}>
                <CardContent sx={{ p: 1, '&:last-child': { pb: 1 } }}>
                  <Typography variant="h6" sx={{ color: statusColors.escalated.color }}>
                    {grievanceStats.escalated}
                  </Typography>
                  <Typography variant="caption">Escalated</Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        )}

        {/* Filter */}
        <FormControl size="small" fullWidth>
          <InputLabel>Status Filter</InputLabel>
          <Select
            value={grievanceFilter}
            label="Status Filter"
            onChange={(e) => {
              setGrievanceFilter(e.target.value);
              setTimeout(fetchGrievances, 100);
            }}
          >
            <MenuItem value="all">All</MenuItem>
            <MenuItem value="pending">Pending</MenuItem>
            <MenuItem value="in_review">In Review</MenuItem>
            <MenuItem value="resolved">Resolved</MenuItem>
            <MenuItem value="rejected">Rejected</MenuItem>
            <MenuItem value="escalated">Escalated</MenuItem>
          </Select>
        </FormControl>
      </Box>

      {/* Grievance List */}
      <List sx={{ flex: 1, overflow: 'auto', p: 1 }}>
        {grievances.length === 0 ? (
          <Box sx={{ textAlign: 'center', p: 4 }}>
            <GrievanceIcon sx={{ fontSize: 48, color: 'text.disabled', mb: 2 }} />
            <Typography color="text.secondary">No grievances found</Typography>
          </Box>
        ) : (
          grievances.map((grievance) => (
            <ListItemButton
              key={grievance.grievance_id}
              onClick={async () => {
                const response = await api.getGrievance(grievance.grievance_id);
                if (response.success) {
                  setSelectedGrievance(response.data);
                  setGrievanceDetailOpen(true);
                }
              }}
              sx={{
                borderRadius: 2,
                mb: 1,
                border: 1,
                borderColor: 'divider',
                bgcolor: 'white'
              }}
            >
              <ListItemAvatar>
                <Avatar sx={{ bgcolor: statusColors[grievance.status]?.bg || '#f5f5f5' }}>
                  {grievance.status === 'resolved' ? <ResolvedIcon sx={{ color: statusColors.resolved.color }} /> :
                   grievance.status === 'escalated' ? <EscalateIcon sx={{ color: statusColors.escalated.color }} /> :
                   <PendingIcon sx={{ color: statusColors[grievance.status]?.color || '#666' }} />}
                </Avatar>
              </ListItemAvatar>
              <ListItemText
                primary={
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Typography fontWeight={500} noWrap sx={{ flex: 1 }}>
                      {grievance.subject}
                    </Typography>
                    <Chip
                      label={grievance.priority}
                      size="small"
                      sx={{
                        height: 20,
                        fontSize: '0.65rem',
                        bgcolor: priorityColors[grievance.priority]?.bg,
                        color: priorityColors[grievance.priority]?.color
                      }}
                    />
                  </Box>
                }
                secondary={
                  <Box>
                    <Typography variant="caption" display="block" noWrap>
                      {grievance.description?.substring(0, 50)}...
                    </Typography>
                    <Box sx={{ display: 'flex', gap: 1, mt: 0.5 }}>
                      <Chip
                        label={grievance.status.replace('_', ' ')}
                        size="small"
                        sx={{
                          height: 18,
                          fontSize: '0.6rem',
                          bgcolor: statusColors[grievance.status]?.bg,
                          color: statusColors[grievance.status]?.color
                        }}
                      />
                      <Typography variant="caption" color="text.secondary">
                        {new Date(grievance.created_at).toLocaleDateString()}
                      </Typography>
                    </Box>
                  </Box>
                }
              />
            </ListItemButton>
          ))
        )}
      </List>
    </Paper>
  );

  return (
    <Box sx={{ height: 'calc(100vh - 100px)', display: 'flex', flexDirection: 'column' }}>
      {/* Tabs */}
      <Paper sx={{ mb: 2, borderRadius: 2 }}>
        <Tabs value={tabValue} onChange={(e, v) => setTabValue(v)} variant="fullWidth">
          <Tab icon={<GroupIcon />} label="Communities" iconPosition="start" />
          <Tab icon={<GrievanceIcon />} label="Grievances" iconPosition="start" />
        </Tabs>
      </Paper>

      {/* Content */}
      <Box sx={{ flex: 1, overflow: 'hidden' }}>
        <TabPanel value={tabValue} index={0}>
          <Grid container spacing={2} sx={{ height: '100%' }}>
            {/* Community List */}
            {(!isMobile || !mobileShowChat) && (
              <Grid item xs={12} md={4} sx={{ height: '100%' }}>
                {renderCommunityList()}
              </Grid>
            )}
            
            {/* Chat Area */}
            {(!isMobile || mobileShowChat) && (
              <Grid item xs={12} md={8} sx={{ height: '100%' }}>
                {renderChatArea()}
              </Grid>
            )}
          </Grid>
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          <Box sx={{ height: '100%' }}>
            {renderGrievanceList()}
          </Box>
        </TabPanel>
      </Box>

      {/* Create Community Dialog */}
      <Dialog open={createCommunityOpen} onClose={() => setCreateCommunityOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create New Community</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Community Name"
            value={newCommunity.name}
            onChange={(e) => setNewCommunity({ ...newCommunity, name: e.target.value })}
            sx={{ mt: 2, mb: 2 }}
          />
          <TextField
            fullWidth
            label="Description"
            multiline
            rows={3}
            value={newCommunity.description}
            onChange={(e) => setNewCommunity({ ...newCommunity, description: e.target.value })}
            sx={{ mb: 2 }}
          />
          <FormControl fullWidth>
            <InputLabel>Community Type</InputLabel>
            <Select
              value={newCommunity.community_type}
              label="Community Type"
              onChange={(e) => setNewCommunity({ ...newCommunity, community_type: e.target.value })}
            >
              {user?.role === 'admin' && (
                <MenuItem value="admin_teacher">Admin-Teacher Community</MenuItem>
              )}
              <MenuItem value="teacher_student">Teacher-Student Community</MenuItem>
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateCommunityOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleCreateCommunity} disabled={!newCommunity.name}>
            Create
          </Button>
        </DialogActions>
      </Dialog>

      {/* Add Members Dialog */}
      <Dialog open={addMembersOpen} onClose={() => setAddMembersOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Add Members</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            placeholder="Search members..."
            value={memberSearch}
            onChange={(e) => {
              setMemberSearch(e.target.value);
              fetchAvailableMembers(selectedCommunity?.community_id, e.target.value);
            }}
            InputProps={{
              startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />
            }}
            sx={{ mt: 2, mb: 2 }}
          />
          <List sx={{ maxHeight: 300, overflow: 'auto' }}>
            {availableMembers.map((member) => (
              <ListItem key={member.id} disablePadding>
                <ListItemButton
                  onClick={() => {
                    if (selectedMembers.includes(member.id)) {
                      setSelectedMembers(selectedMembers.filter(id => id !== member.id));
                    } else {
                      setSelectedMembers([...selectedMembers, member.id]);
                    }
                  }}
                >
                  <ListItemIcon>
                    <Checkbox checked={selectedMembers.includes(member.id)} />
                  </ListItemIcon>
                  <ListItemAvatar>
                    <Avatar>{member.name?.charAt(0)}</Avatar>
                  </ListItemAvatar>
                  <ListItemText
                    primary={member.name}
                    secondary={member.email || member.roll_no}
                  />
                </ListItemButton>
              </ListItem>
            ))}
          </List>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAddMembersOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleAddMembers} disabled={selectedMembers.length === 0}>
            Add {selectedMembers.length} Members
          </Button>
        </DialogActions>
      </Dialog>

      {/* Create Grievance Dialog */}
      <Dialog open={createGrievanceOpen} onClose={() => setCreateGrievanceOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Submit Grievance</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Subject"
            value={newGrievance.subject}
            onChange={(e) => setNewGrievance({ ...newGrievance, subject: e.target.value })}
            sx={{ mt: 2, mb: 2 }}
          />
          <TextField
            fullWidth
            label="Description"
            multiline
            rows={4}
            value={newGrievance.description}
            onChange={(e) => setNewGrievance({ ...newGrievance, description: e.target.value })}
            sx={{ mb: 2 }}
          />
          <Grid container spacing={2}>
            <Grid item xs={6}>
              <FormControl fullWidth>
                <InputLabel>Category</InputLabel>
                <Select
                  value={newGrievance.category}
                  label="Category"
                  onChange={(e) => setNewGrievance({ ...newGrievance, category: e.target.value })}
                >
                  <MenuItem value="academic">Academic</MenuItem>
                  <MenuItem value="behavioral">Behavioral</MenuItem>
                  <MenuItem value="technical">Technical</MenuItem>
                  <MenuItem value="administrative">Administrative</MenuItem>
                  <MenuItem value="other">Other</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={6}>
              <FormControl fullWidth>
                <InputLabel>Priority</InputLabel>
                <Select
                  value={newGrievance.priority}
                  label="Priority"
                  onChange={(e) => setNewGrievance({ ...newGrievance, priority: e.target.value })}
                >
                  <MenuItem value="low">Low</MenuItem>
                  <MenuItem value="medium">Medium</MenuItem>
                  <MenuItem value="high">High</MenuItem>
                  <MenuItem value="urgent">Urgent</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateGrievanceOpen(false)}>Cancel</Button>
          <Button 
            variant="contained" 
            onClick={handleCreateGrievance} 
            disabled={!newGrievance.subject || !newGrievance.description}
          >
            Submit
          </Button>
        </DialogActions>
      </Dialog>

      {/* Grievance Detail Dialog */}
      <Dialog 
        open={grievanceDetailOpen} 
        onClose={() => setGrievanceDetailOpen(false)} 
        maxWidth="md" 
        fullWidth
        PaperProps={{ sx: { height: '80vh' } }}
      >
        {selectedGrievance && (
          <>
            <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Box sx={{ flex: 1 }}>
                <Typography variant="h6">{selectedGrievance.subject}</Typography>
                <Box sx={{ display: 'flex', gap: 1, mt: 0.5 }}>
                  <Chip
                    label={selectedGrievance.status.replace('_', ' ')}
                    size="small"
                    sx={{
                      bgcolor: statusColors[selectedGrievance.status]?.bg,
                      color: statusColors[selectedGrievance.status]?.color
                    }}
                  />
                  <Chip
                    label={selectedGrievance.priority}
                    size="small"
                    sx={{
                      bgcolor: priorityColors[selectedGrievance.priority]?.bg,
                      color: priorityColors[selectedGrievance.priority]?.color
                    }}
                  />
                  <Chip label={selectedGrievance.category} size="small" variant="outlined" />
                </Box>
              </Box>
              <IconButton onClick={() => setGrievanceDetailOpen(false)}>
                <CloseIcon />
              </IconButton>
            </DialogTitle>
            <DialogContent dividers sx={{ display: 'flex', flexDirection: 'column' }}>
              {/* Description */}
              <Paper sx={{ p: 2, mb: 2, bgcolor: '#f5f5f5' }}>
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  Description
                </Typography>
                <Typography>{selectedGrievance.description}</Typography>
                <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                  Submitted by {selectedGrievance.complainant_name} on {new Date(selectedGrievance.created_at).toLocaleString()}
                </Typography>
              </Paper>

              {/* Resolution (if any) */}
              {selectedGrievance.resolution && (
                <Alert severity="success" sx={{ mb: 2 }}>
                  <Typography variant="subtitle2">Resolution</Typography>
                  <Typography variant="body2">{selectedGrievance.resolution}</Typography>
                </Alert>
              )}

              {/* Status Actions */}
              {(user?.role === 'admin' || user?.role === 'teacher') && 
               selectedGrievance.status !== 'resolved' && 
               selectedGrievance.status !== 'rejected' && (
                <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                  {selectedGrievance.status === 'pending' && (
                    <Button
                      variant="outlined"
                      onClick={() => handleGrievanceStatusChange(selectedGrievance.grievance_id, 'in_review')}
                    >
                      Start Review
                    </Button>
                  )}
                  <Button
                    variant="contained"
                    color="success"
                    startIcon={<ResolvedIcon />}
                    onClick={() => {
                      const resolution = prompt('Enter resolution:');
                      if (resolution) {
                        handleGrievanceStatusChange(selectedGrievance.grievance_id, 'resolved', resolution);
                      }
                    }}
                  >
                    Resolve
                  </Button>
                  <Button
                    variant="outlined"
                    color="error"
                    onClick={() => handleGrievanceStatusChange(selectedGrievance.grievance_id, 'rejected')}
                  >
                    Reject
                  </Button>
                  {user?.role === 'teacher' && (
                    <Button
                      variant="outlined"
                      color="warning"
                      startIcon={<EscalateIcon />}
                      onClick={() => {
                        const reason = prompt('Enter escalation reason:');
                        if (reason) {
                          handleGrievanceStatusChange(selectedGrievance.grievance_id, 'escalated', null);
                        }
                      }}
                    >
                      Escalate to Admin
                    </Button>
                  )}
                </Box>
              )}

              {/* Responses */}
              <Typography variant="subtitle2" sx={{ mb: 1 }}>Responses</Typography>
              <Box sx={{ flex: 1, overflow: 'auto', mb: 2 }}>
                {selectedGrievance.responses?.length === 0 ? (
                  <Typography color="text.secondary" sx={{ textAlign: 'center', py: 4 }}>
                    No responses yet
                  </Typography>
                ) : (
                  selectedGrievance.responses?.map((response) => (
                    <Paper key={response.response_id} sx={{ p: 2, mb: 1 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                        <Avatar sx={{ width: 28, height: 28, fontSize: '0.8rem' }}>
                          {response.responder_name?.charAt(0)}
                        </Avatar>
                        <Typography variant="subtitle2">{response.responder_name}</Typography>
                        <Chip label={response.responder_type} size="small" sx={{ height: 18, fontSize: '0.65rem' }} />
                        <Typography variant="caption" color="text.secondary" sx={{ ml: 'auto' }}>
                          {new Date(response.created_at).toLocaleString()}
                        </Typography>
                      </Box>
                      <Typography variant="body2">{response.content}</Typography>
                      {response.action_taken && (
                        <Chip label={response.action_taken} size="small" sx={{ mt: 1 }} variant="outlined" />
                      )}
                    </Paper>
                  ))
                )}
              </Box>

              {/* Add Response */}
              <Box sx={{ display: 'flex', gap: 1 }}>
                <TextField
                  fullWidth
                  placeholder="Add a response..."
                  value={grievanceResponse}
                  onChange={(e) => setGrievanceResponse(e.target.value)}
                  size="small"
                />
                <Button
                  variant="contained"
                  onClick={handleAddGrievanceResponse}
                  disabled={!grievanceResponse.trim()}
                >
                  Send
                </Button>
              </Box>
            </DialogContent>
          </>
        )}
      </Dialog>
    </Box>
  );
}

export default Community;
