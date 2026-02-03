/**
 * Student Dashboard Page
 * =======================
 * A simplified dashboard for students that shows only their evaluation scores.
 * 
 * Features:
 * - View assigned evaluations
 * - See scores and grades
 * - Read feedback
 * - Track progress
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Typography,
  Grid,
  Card,
  CardContent,
  Paper,
  Avatar,
  Chip,
  LinearProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Tooltip,
  useTheme,
  alpha,
  Alert,
} from '@mui/material';
import {
  School as SchoolIcon,
  TrendingUp as TrendingUpIcon,
  Assignment as AssignmentIcon,
  Grade as GradeIcon,
  Visibility as ViewIcon,
  CheckCircle as CheckIcon,
  Schedule as ScheduleIcon,
  Star as StarIcon,
  EmojiEvents as TrophyIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useAuth } from '../context/AuthContext';

const MotionCard = motion(Card);

// Mock student results data (in production, fetch from API based on logged-in student)
const mockStudentResults = [
  {
    id: '7220d6fb-bc5a-489d-92bc-abb0b4781263',
    subject: 'Computer Science',
    assignment: 'Data Structures Quiz',
    date: '2024-01-15',
    score: 87.5,
    grade: 'A',
    status: 'evaluated',
    feedback: 'Great understanding of linked lists and trees.',
  },
  {
    id: '5525a56a-4653-4b0e-b796-3eb7933f28b9',
    subject: 'Mathematics',
    assignment: 'Calculus Test',
    date: '2024-01-10',
    score: 75.0,
    grade: 'B',
    status: 'evaluated',
    feedback: 'Good work on derivatives, needs improvement on integrals.',
  },
  {
    id: '132939ed-f26f-4df3-9935-0fab1c975712',
    subject: 'Physics',
    assignment: 'Mechanics Assignment',
    date: '2024-01-05',
    score: 92.0,
    grade: 'A+',
    status: 'evaluated',
    feedback: 'Excellent problem-solving skills demonstrated.',
  },
];

function getGradeColor(grade) {
  if (grade.startsWith('A')) return '#22c55e';
  if (grade.startsWith('B')) return '#3b82f6';
  if (grade.startsWith('C')) return '#f59e0b';
  if (grade.startsWith('D')) return '#f97316';
  return '#ef4444';
}

function StatCard({ icon, title, value, subtitle, color }) {
  const theme = useTheme();
  
  return (
    <MotionCard
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -5 }}
      sx={{
        height: '100%',
        borderRadius: { xs: 2, md: 3 },
        border: '1px solid',
        borderColor: 'divider',
        boxShadow: 'none',
      }}
    >
      <CardContent sx={{ p: { xs: 2, md: 3 } }}>
        <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
          <Box>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5, fontSize: { xs: '0.75rem', md: '0.875rem' } }}>
              {title}
            </Typography>
            <Typography variant="h4" fontWeight={700} sx={{ color, fontSize: { xs: '1.5rem', md: '2rem' } }}>
              {value}
            </Typography>
            {subtitle && (
              <Typography variant="caption" color="text.secondary" sx={{ fontSize: { xs: '0.65rem', md: '0.75rem' } }}>
                {subtitle}
              </Typography>
            )}
          </Box>
          <Box
            sx={{
              width: { xs: 40, md: 50 },
              height: { xs: 40, md: 50 },
              borderRadius: { xs: 1.5, md: 2 },
              bgcolor: alpha(color, 0.1),
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: color,
              '& svg': { fontSize: { xs: 22, md: 28 } },
            }}
          >
            {icon}
          </Box>
        </Box>
      </CardContent>
    </MotionCard>
  );
}

export default function StudentDashboard() {
  const theme = useTheme();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [results, setResults] = useState(mockStudentResults);

  // Calculate statistics
  const totalEvaluations = results.length;
  const averageScore = results.reduce((acc, r) => acc + r.score, 0) / (results.length || 1);
  const highestScore = Math.max(...results.map(r => r.score), 0);
  const aGradeCount = results.filter(r => r.grade.startsWith('A')).length;

  return (
    <Box sx={{ py: { xs: 2, md: 4 } }}>
      <Container maxWidth="lg" sx={{ px: { xs: 0, sm: 2 } }}>
        {/* Welcome Section */}
        <MotionCard
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          sx={{
            mb: { xs: 2, md: 4 },
            borderRadius: { xs: 2, md: 4 },
            background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
            color: 'white',
            overflow: 'hidden',
            position: 'relative',
          }}
        >
          <CardContent sx={{ p: { xs: 2.5, md: 4 }, position: 'relative', zIndex: 1 }}>
            <Grid container spacing={{ xs: 2, md: 3 }} alignItems="center">
              <Grid item xs={12} md={8}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: { xs: 1.5, md: 2 }, mb: { xs: 1, md: 2 } }}>
                  <Avatar
                    sx={{
                      width: { xs: 48, md: 60 },
                      height: { xs: 48, md: 60 },
                      bgcolor: alpha('#fff', 0.2),
                      fontSize: { xs: '1.25rem', md: '1.5rem' },
                    }}
                  >
                    {user?.name?.charAt(0) || 'S'}
                  </Avatar>
                  <Box>
                    <Typography variant="h5" fontWeight={700} sx={{ fontSize: { xs: '1.1rem', md: '1.5rem' } }}>
                      Welcome back, {user?.name || 'Student'}!
                    </Typography>
                    <Chip
                      icon={<SchoolIcon sx={{ color: 'white !important', fontSize: { xs: 14, md: 16 } }} />}
                      label="Student"
                      size="small"
                      sx={{
                        mt: 0.5,
                        bgcolor: alpha('#fff', 0.2),
                        color: 'white',
                        fontSize: { xs: '0.65rem', md: '0.75rem' },
                        height: { xs: 22, md: 26 },
                      }}
                    />
                  </Box>
                </Box>
                <Typography variant="body1" sx={{ opacity: 0.9, fontSize: { xs: '0.875rem', md: '1rem' } }}>
                  Track your academic progress and view evaluation results here.
                </Typography>
              </Grid>
              <Grid item xs={12} md={4}>
                <Box sx={{ textAlign: { xs: 'left', md: 'right' }, mt: { xs: 1, md: 0 } }}>
                  <Typography variant="overline" sx={{ opacity: 0.8, fontSize: { xs: '0.65rem', md: '0.75rem' } }}>
                    Average Score
                  </Typography>
                  <Typography variant="h2" fontWeight={800} sx={{ fontSize: { xs: '2rem', md: '3rem' } }}>
                    {averageScore.toFixed(1)}%
                  </Typography>
                </Box>
              </Grid>
            </Grid>
          </CardContent>
          {/* Background decoration */}
          <Box
            sx={{
              position: 'absolute',
              top: -50,
              right: -50,
              width: 200,
              height: 200,
              borderRadius: '50%',
              bgcolor: alpha('#fff', 0.1),
            }}
          />
        </MotionCard>

        {/* Statistics Cards */}
        <Grid container spacing={{ xs: 2, md: 3 }} sx={{ mb: { xs: 2, md: 4 } }}>
          <Grid item xs={6} sm={6} md={3}>
            <StatCard
              icon={<AssignmentIcon />}
              title="Total Evaluations"
              value={totalEvaluations}
              subtitle="Completed assessments"
              color="#6366f1"
            />
          </Grid>
          <Grid item xs={6} sm={6} md={3}>
            <StatCard
              icon={<TrendingUpIcon />}
              title="Average Score"
              value={`${averageScore.toFixed(1)}%`}
              subtitle="Across all subjects"
              color="#06b6d4"
            />
          </Grid>
          <Grid item xs={6} sm={6} md={3}>
            <StatCard
              icon={<TrophyIcon />}
              title="Highest Score"
              value={`${highestScore}%`}
              subtitle="Personal best"
              color="#22c55e"
            />
          </Grid>
          <Grid item xs={6} sm={6} md={3}>
            <StatCard
              icon={<StarIcon />}
              title="A Grades"
              value={aGradeCount}
              subtitle={`Out of ${totalEvaluations} total`}
              color="#f59e0b"
            />
          </Grid>
        </Grid>

        {/* Results Table */}
        <MotionCard
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          sx={{
            borderRadius: { xs: 2, md: 3 },
            border: '1px solid',
            borderColor: 'divider',
            boxShadow: 'none',
          }}
        >
          <CardContent sx={{ p: 0 }}>
            <Box sx={{ p: { xs: 2, md: 3 }, borderBottom: '1px solid', borderColor: 'divider' }}>
              <Typography variant="h6" fontWeight={600} sx={{ fontSize: { xs: '1rem', md: '1.25rem' } }}>
                My Evaluation Results
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ fontSize: { xs: '0.75rem', md: '0.875rem' } }}>
                View your graded assignments and feedback
              </Typography>
            </Box>

            {results.length === 0 ? (
              <Box sx={{ p: { xs: 4, md: 6 }, textAlign: 'center' }}>
                <AssignmentIcon sx={{ fontSize: { xs: 48, md: 60 }, color: 'text.disabled', mb: 2 }} />
                <Typography variant="h6" color="text.secondary" sx={{ fontSize: { xs: '1rem', md: '1.25rem' } }}>
                  No evaluations yet
                </Typography>
                <Typography variant="body2" color="text.disabled" sx={{ fontSize: { xs: '0.75rem', md: '0.875rem' } }}>
                  Your graded assignments will appear here
                </Typography>
              </Box>
            ) : (
              <>
                {/* Mobile Card View */}
                <Box sx={{ display: { xs: 'block', md: 'none' }, p: 2 }}>
                  {results.map((result, index) => (
                    <Box
                      key={result.id}
                      sx={{
                        p: 2,
                        mb: 2,
                        borderRadius: 2,
                        bgcolor: alpha('#6366f1', 0.02),
                        border: '1px solid',
                        borderColor: 'divider',
                        '&:last-child': { mb: 0 },
                      }}
                    >
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1.5 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                          <Avatar
                            sx={{
                              width: 32,
                              height: 32,
                              bgcolor: alpha('#6366f1', 0.1),
                              color: '#6366f1',
                              fontSize: '0.8rem',
                            }}
                          >
                            {result.subject.charAt(0)}
                          </Avatar>
                          <Box>
                            <Typography variant="body2" fontWeight={600} sx={{ fontSize: '0.875rem' }}>
                              {result.subject}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {result.assignment}
                            </Typography>
                          </Box>
                        </Box>
                        <Chip
                          label={result.grade}
                          size="small"
                          sx={{
                            fontWeight: 700,
                            bgcolor: alpha(getGradeColor(result.grade), 0.1),
                            color: getGradeColor(result.grade),
                            minWidth: 36,
                            height: 24,
                            fontSize: '0.75rem',
                          }}
                        />
                      </Box>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                        <LinearProgress
                          variant="determinate"
                          value={result.score}
                          sx={{
                            flex: 1,
                            height: 6,
                            borderRadius: 3,
                            bgcolor: alpha(getGradeColor(result.grade), 0.2),
                            '& .MuiLinearProgress-bar': {
                              borderRadius: 3,
                              bgcolor: getGradeColor(result.grade),
                            },
                          }}
                        />
                        <Typography variant="body2" fontWeight={700} sx={{ minWidth: 45, textAlign: 'right' }}>
                          {result.score}%
                        </Typography>
                      </Box>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Typography variant="caption" color="text.secondary">
                          {new Date(result.date).toLocaleDateString()}
                        </Typography>
                        <IconButton
                          size="small"
                          onClick={() => navigate(`/results/${result.id}`)}
                          sx={{
                            color: '#6366f1',
                            p: 0.5,
                            '&:hover': {
                              bgcolor: alpha('#6366f1', 0.1),
                            },
                          }}
                        >
                          <ViewIcon fontSize="small" />
                        </IconButton>
                      </Box>
                    </Box>
                  ))}
                </Box>

                {/* Desktop Table View */}
                <TableContainer sx={{ display: { xs: 'none', md: 'block' } }}>
                  <Table>
                    <TableHead>
                      <TableRow sx={{ bgcolor: alpha('#6366f1', 0.05) }}>
                        <TableCell sx={{ fontWeight: 600 }}>Subject</TableCell>
                        <TableCell sx={{ fontWeight: 600 }}>Assignment</TableCell>
                        <TableCell sx={{ fontWeight: 600 }}>Date</TableCell>
                        <TableCell sx={{ fontWeight: 600 }} align="center">Score</TableCell>
                        <TableCell sx={{ fontWeight: 600 }} align="center">Grade</TableCell>
                        <TableCell sx={{ fontWeight: 600 }}>Feedback</TableCell>
                        <TableCell align="right"></TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {results.map((result, index) => (
                        <TableRow
                          key={result.id}
                          hover
                          sx={{
                            '&:last-child td': { borderBottom: 0 },
                          }}
                        >
                          <TableCell>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                              <Avatar
                                sx={{
                                  width: 36,
                                  height: 36,
                                  bgcolor: alpha('#6366f1', 0.1),
                                  color: '#6366f1',
                                  fontSize: '0.9rem',
                                }}
                              >
                                {result.subject.charAt(0)}
                              </Avatar>
                              <Typography variant="body2" fontWeight={500}>
                                {result.subject}
                              </Typography>
                            </Box>
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2">
                              {result.assignment}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2" color="text.secondary">
                              {new Date(result.date).toLocaleDateString()}
                            </Typography>
                          </TableCell>
                          <TableCell align="center">
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, justifyContent: 'center' }}>
                              <LinearProgress
                                variant="determinate"
                                value={result.score}
                                sx={{
                                  width: 60,
                                  height: 6,
                                  borderRadius: 3,
                                  bgcolor: alpha(getGradeColor(result.grade), 0.2),
                                  '& .MuiLinearProgress-bar': {
                                    borderRadius: 3,
                                    bgcolor: getGradeColor(result.grade),
                                  },
                                }}
                              />
                              <Typography variant="body2" fontWeight={600}>
                                {result.score}%
                              </Typography>
                            </Box>
                          </TableCell>
                          <TableCell align="center">
                            <Chip
                              label={result.grade}
                              size="small"
                              sx={{
                                fontWeight: 700,
                                bgcolor: alpha(getGradeColor(result.grade), 0.1),
                                color: getGradeColor(result.grade),
                                minWidth: 40,
                              }}
                            />
                          </TableCell>
                          <TableCell>
                            <Typography
                              variant="body2"
                              color="text.secondary"
                              sx={{
                                maxWidth: 200,
                                overflow: 'hidden',
                                textOverflow: 'ellipsis',
                                whiteSpace: 'nowrap',
                              }}
                            >
                              {result.feedback}
                            </Typography>
                          </TableCell>
                          <TableCell align="right">
                            <Tooltip title="View Details">
                              <IconButton
                                size="small"
                                onClick={() => navigate(`/results/${result.id}`)}
                                sx={{
                                  color: '#6366f1',
                                  '&:hover': {
                                    bgcolor: alpha('#6366f1', 0.1),
                                  },
                                }}
                              >
                                <ViewIcon />
                              </IconButton>
                            </Tooltip>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </>
            )}
          </CardContent>
        </MotionCard>

        {/* Info Alert */}
        <Alert
          severity="info"
          sx={{
            mt: { xs: 2, md: 3 },
            borderRadius: 2,
            py: { xs: 1, md: 1.5 },
            '& .MuiAlert-icon': {
              color: '#6366f1',
            },
            '& .MuiAlert-message': {
              fontSize: { xs: '0.75rem', md: '0.875rem' },
            },
          }}
        >
          <Typography variant="body2" sx={{ fontSize: 'inherit' }}>
            <strong>Note:</strong> Contact your teacher if you have questions about your evaluation scores or need additional feedback.
          </Typography>
        </Alert>
      </Container>
    </Box>
  );
}
