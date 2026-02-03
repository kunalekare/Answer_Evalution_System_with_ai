/**
 * Dashboard Page
 * ===============
 * Main landing page with statistics and quick actions.
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  Paper,
  LinearProgress,
  Chip,
  Avatar,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  IconButton,
} from '@mui/material';
import {
  Assignment as AssignmentIcon,
  TrendingUp as TrendingUpIcon,
  CheckCircle as CheckCircleIcon,
  Schedule as ScheduleIcon,
  ArrowForward as ArrowForwardIcon,
  School as SchoolIcon,
  EmojiEvents as TrophyIcon,
  AutoAwesome as SparkleIcon,
} from '@mui/icons-material';
import { motion } from 'framer-motion';

// Animated card wrapper
const MotionCard = motion(Card);

// Stats data (would come from API in production)
const stats = [
  {
    title: 'Total Evaluations',
    value: '1,234',
    change: '+12%',
    icon: <AssignmentIcon />,
    color: '#1565c0',
    bgColor: 'rgba(21, 101, 192, 0.1)',
  },
  {
    title: 'Average Score',
    value: '78.5%',
    change: '+5%',
    icon: <TrendingUpIcon />,
    color: '#00897b',
    bgColor: 'rgba(0, 137, 123, 0.1)',
  },
  {
    title: 'Excellent Grades',
    value: '342',
    change: '+18%',
    icon: <CheckCircleIcon />,
    color: '#2e7d32',
    bgColor: 'rgba(46, 125, 50, 0.1)',
  },
  {
    title: 'Pending Review',
    value: '23',
    change: '-3',
    icon: <ScheduleIcon />,
    color: '#f9a825',
    bgColor: 'rgba(249, 168, 37, 0.1)',
  },
];

// Recent evaluations (would come from API)
const recentEvaluations = [
  { id: 1, student: 'John Doe', subject: 'Biology', score: 92, grade: 'Excellent', time: '2 hours ago' },
  { id: 2, student: 'Jane Smith', subject: 'Physics', score: 78, grade: 'Good', time: '3 hours ago' },
  { id: 3, student: 'Bob Wilson', subject: 'Chemistry', score: 65, grade: 'Average', time: '5 hours ago' },
  { id: 4, student: 'Alice Brown', subject: 'Biology', score: 88, grade: 'Excellent', time: '1 day ago' },
];

const gradeColors = {
  Excellent: 'success',
  Good: 'primary',
  Average: 'warning',
  Poor: 'error',
};

function Dashboard() {
  const navigate = useNavigate();

  return (
    <Box>
      {/* Welcome Section */}
      <Box sx={{ mb: { xs: 2, md: 4 } }}>
        <Typography variant="h4" fontWeight={700} gutterBottom sx={{ fontSize: { xs: '1.5rem', md: '2rem' } }}>
          Welcome back, Teacher! 👋
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ fontSize: { xs: '0.875rem', md: '1rem' } }}>
          Here's what's happening with your evaluations today.
        </Typography>
      </Box>

      {/* Quick Action Banner */}
      <MotionCard
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        sx={{
          mb: { xs: 2, md: 4 },
          background: 'linear-gradient(135deg, #1565c0 0%, #0d47a1 100%)',
          color: 'white',
          overflow: 'hidden',
          position: 'relative',
          borderRadius: { xs: 2, md: 3 },
        }}
      >
        <CardContent sx={{ p: { xs: 2.5, md: 4 } }}>
          <Grid container spacing={{ xs: 2, md: 3 }} alignItems="center">
            <Grid item xs={12} md={8}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: { xs: 1, md: 2 } }}>
                <SparkleIcon sx={{ fontSize: { xs: 18, md: 24 } }} />
                <Typography variant="overline" sx={{ opacity: 0.9, fontSize: { xs: '0.6rem', md: '0.75rem' } }}>
                  AI-Powered Evaluation
                </Typography>
              </Box>
              <Typography variant="h5" fontWeight={600} gutterBottom sx={{ fontSize: { xs: '1.1rem', md: '1.5rem' } }}>
                Start Evaluating Student Answers
              </Typography>
              <Typography variant="body1" sx={{ opacity: 0.9, mb: { xs: 2, md: 3 }, fontSize: { xs: '0.8rem', md: '1rem' } }}>
                Upload answer sheets and model answers to get instant, accurate evaluations
                using advanced semantic analysis.
              </Typography>
              <Button
                variant="contained"
                size="large"
                endIcon={<ArrowForwardIcon />}
                onClick={() => navigate('/evaluate')}
                sx={{
                  bgcolor: 'white',
                  color: 'primary.main',
                  fontSize: { xs: '0.8rem', md: '1rem' },
                  py: { xs: 1, md: 1.5 },
                  px: { xs: 2, md: 3 },
                  '&:hover': {
                    bgcolor: 'rgba(255, 255, 255, 0.9)',
                  },
                }}
              >
                Start Evaluation
              </Button>
            </Grid>
            <Grid item xs={12} md={4}>
              <Box
                sx={{
                  display: { xs: 'none', md: 'flex' },
                  justifyContent: 'center',
                }}
              >
                <SchoolIcon sx={{ fontSize: 180, opacity: 0.2 }} />
              </Box>
            </Grid>
          </Grid>
        </CardContent>
      </MotionCard>

      {/* Statistics Cards */}
      <Grid container spacing={{ xs: 2, md: 3 }} sx={{ mb: { xs: 2, md: 4 } }}>
        {stats.map((stat, index) => (
          <Grid item xs={6} sm={6} md={3} key={stat.title}>
            <MotionCard
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
              sx={{
                height: '100%',
                cursor: 'pointer',
                borderRadius: { xs: 2, md: 3 },
                transition: 'transform 0.2s, box-shadow 0.2s',
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: '0 8px 30px rgba(0, 0, 0, 0.12)',
                },
              }}
            >
              <CardContent sx={{ p: { xs: 2, md: 3 } }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: { xs: 1, md: 2 }, flexDirection: { xs: 'column', sm: 'row' }, gap: 1 }}>
                  <Box
                    sx={{
                      width: { xs: 36, md: 48 },
                      height: { xs: 36, md: 48 },
                      borderRadius: { xs: 1.5, md: 2 },
                      bgcolor: stat.bgColor,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: stat.color,
                      '& svg': { fontSize: { xs: 18, md: 24 } },
                    }}
                  >
                    {stat.icon}
                  </Box>
                  <Chip
                    label={stat.change}
                    size="small"
                    color={stat.change.startsWith('+') ? 'success' : 'warning'}
                    sx={{ fontWeight: 500, fontSize: { xs: '0.6rem', md: '0.75rem' }, height: { xs: 20, md: 24 }, alignSelf: { xs: 'flex-start', sm: 'center' } }}
                  />
                </Box>
                <Typography variant="h4" fontWeight={700} sx={{ fontSize: { xs: '1.25rem', md: '2rem' } }}>
                  {stat.value}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ fontSize: { xs: '0.7rem', md: '0.875rem' } }}>
                  {stat.title}
                </Typography>
              </CardContent>
            </MotionCard>
          </Grid>
        ))}
      </Grid>

      {/* Main Content Grid */}
      <Grid container spacing={{ xs: 2, md: 3 }}>
        {/* Recent Evaluations */}
        <Grid item xs={12} md={8}>
          <Card sx={{ borderRadius: { xs: 2, md: 3 } }}>
            <CardContent sx={{ p: 0 }}>
              <Box
                sx={{
                  p: { xs: 2, md: 3 },
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  borderBottom: '1px solid',
                  borderColor: 'divider',
                }}
              >
                <Typography variant="h6" fontWeight={600} sx={{ fontSize: { xs: '1rem', md: '1.25rem' } }}>
                  Recent Evaluations
                </Typography>
                <Button size="small" onClick={() => navigate('/history')} sx={{ fontSize: { xs: '0.75rem', md: '0.875rem' } }}>
                  View All
                </Button>
              </Box>
              <List sx={{ p: 0 }}>
                {recentEvaluations.map((evaluation, index) => (
                  <ListItem
                    key={evaluation.id}
                    sx={{
                      borderBottom: index < recentEvaluations.length - 1 ? '1px solid' : 'none',
                      borderColor: 'divider',
                      py: { xs: 1.5, md: 2 },
                      px: { xs: 2, md: 3 },
                      flexWrap: { xs: 'wrap', sm: 'nowrap' },
                    }}
                    secondaryAction={
                      <IconButton edge="end" onClick={() => navigate(`/results/${evaluation.id}`)} size="small">
                        <ArrowForwardIcon sx={{ fontSize: { xs: 18, md: 24 } }} />
                      </IconButton>
                    }
                  >
                    <ListItemAvatar sx={{ minWidth: { xs: 40, md: 56 } }}>
                      <Avatar sx={{ bgcolor: 'primary.light', width: { xs: 32, md: 40 }, height: { xs: 32, md: 40 }, fontSize: { xs: '0.875rem', md: '1rem' } }}>
                        {evaluation.student.charAt(0)}
                      </Avatar>
                    </ListItemAvatar>
                    <ListItemText
                      primary={
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
                          <Typography variant="subtitle1" fontWeight={500} sx={{ fontSize: { xs: '0.875rem', md: '1rem' } }}>
                            {evaluation.student}
                          </Typography>
                          <Chip
                            label={evaluation.grade}
                            size="small"
                            color={gradeColors[evaluation.grade]}
                            sx={{ fontWeight: 500, fontSize: { xs: '0.6rem', md: '0.75rem' }, height: { xs: 18, md: 24 } }}
                          />
                        </Box>
                      }
                      secondary={
                        <Typography variant="body2" color="text.secondary" sx={{ fontSize: { xs: '0.7rem', md: '0.875rem' } }}>
                          {evaluation.subject} • {evaluation.time}
                        </Typography>
                      }
                    />
                    <Box sx={{ mr: { xs: 3, md: 4 }, textAlign: 'right', display: { xs: 'none', sm: 'block' } }}>
                      <Typography variant="h6" fontWeight={600} color="primary.main" sx={{ fontSize: { xs: '1rem', md: '1.25rem' } }}>
                        {evaluation.score}%
                      </Typography>
                    </Box>
                  </ListItem>
                ))}
              </List>
            </CardContent>
          </Card>
        </Grid>

        {/* Performance Overview */}
        <Grid item xs={12} md={4}>
          <Card sx={{ height: '100%', borderRadius: { xs: 2, md: 3 } }}>
            <CardContent sx={{ p: { xs: 2, md: 3 } }}>
              <Typography variant="h6" fontWeight={600} gutterBottom sx={{ fontSize: { xs: '1rem', md: '1.25rem' } }}>
                Performance Overview
              </Typography>
              
              <Box sx={{ mt: { xs: 2, md: 3 } }}>
                {[
                  { label: 'Excellent (85%+)', value: 28, color: 'success' },
                  { label: 'Good (70-85%)', value: 45, color: 'primary' },
                  { label: 'Average (50-70%)', value: 20, color: 'warning' },
                  { label: 'Needs Improvement', value: 7, color: 'error' },
                ].map((item) => (
                  <Box key={item.label} sx={{ mb: { xs: 2, md: 3 } }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                      <Typography variant="body2" color="text.secondary" sx={{ fontSize: { xs: '0.7rem', md: '0.875rem' } }}>
                        {item.label}
                      </Typography>
                      <Typography variant="body2" fontWeight={600} sx={{ fontSize: { xs: '0.7rem', md: '0.875rem' } }}>
                        {item.value}%
                      </Typography>
                    </Box>
                    <LinearProgress
                      variant="determinate"
                      value={item.value}
                      color={item.color}
                      sx={{
                        height: { xs: 6, md: 8 },
                        borderRadius: 4,
                        bgcolor: 'grey.100',
                      }}
                    />
                  </Box>
                ))}
              </Box>

              {/* Top Performer */}
              <Paper
                elevation={0}
                sx={{
                  mt: { xs: 2, md: 4 },
                  p: { xs: 1.5, md: 2 },
                  bgcolor: 'rgba(46, 125, 50, 0.08)',
                  borderRadius: 2,
                  display: 'flex',
                  alignItems: 'center',
                  gap: { xs: 1.5, md: 2 },
                }}
              >
                <Box
                  sx={{
                    width: { xs: 32, md: 40 },
                    height: { xs: 32, md: 40 },
                    borderRadius: '50%',
                    bgcolor: 'success.main',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  <TrophyIcon sx={{ color: 'white', fontSize: { xs: 16, md: 20 } }} />
                </Box>
                <Box>
                  <Typography variant="subtitle2" fontWeight={600} sx={{ fontSize: { xs: '0.75rem', md: '0.875rem' } }}>
                    Top Performer
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ fontSize: { xs: '0.7rem', md: '0.875rem' } }}>
                    John Doe - 92% avg
                  </Typography>
                </Box>
              </Paper>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}

export default Dashboard;
