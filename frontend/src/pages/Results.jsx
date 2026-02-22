/**
 * Results Page
 * =============
 * Displays evaluation results with detailed breakdown.
 */

import React from 'react';
import { useLocation, useNavigate, useParams } from 'react-router-dom';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  Paper,
  Chip,
  LinearProgress,
  Divider,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Alert,
  CircularProgress,
  useTheme,
} from '@mui/material';
import { useThemeMode } from '../context/ThemeContext';
import {
  CheckCircle as CheckIcon,
  Cancel as MissIcon,
  TrendingUp as TrendingUpIcon,
  EmojiEvents as TrophyIcon,
  Lightbulb as LightbulbIcon,
  ArrowBack as ArrowBackIcon,
  Download as DownloadIcon,
  Share as ShareIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { motion } from 'framer-motion';

// Grade configuration
const gradeConfig = {
  excellent: {
    color: 'success',
    bgColor: 'rgba(46, 125, 50, 0.1)',
    icon: <TrophyIcon />,
    label: 'Excellent',
    description: 'Outstanding performance!',
  },
  good: {
    color: 'primary',
    bgColor: 'rgba(21, 101, 192, 0.1)',
    icon: <TrendingUpIcon />,
    label: 'Good',
    description: 'Well done!',
  },
  average: {
    color: 'warning',
    bgColor: 'rgba(249, 168, 37, 0.1)',
    icon: <LightbulbIcon />,
    label: 'Average',
    description: 'Room for improvement',
  },
  poor: {
    color: 'error',
    bgColor: 'rgba(198, 40, 40, 0.1)',
    icon: <LightbulbIcon />,
    label: 'Needs Improvement',
    description: 'Keep practicing!',
  },
};

// Score Ring Component
const ScoreRing = ({ score, size = 200, strokeWidth = 12, isDark }) => {
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  const offset = circumference - (score / 100) * circumference;

  const getColor = (score) => {
    if (score >= 85) return '#2e7d32';
    if (score >= 70) return '#1565c0';
    if (score >= 50) return '#f9a825';
    return '#c62828';
  };

  return (
    <Box sx={{ position: 'relative', display: 'inline-flex' }}>
      <svg width={size} height={size}>
        {/* Background circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={isDark ? '#334155' : '#e0e0e0'}
          strokeWidth={strokeWidth}
        />
        {/* Score circle */}
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={getColor(score)}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: 1.5, ease: 'easeOut' }}
          style={{
            transform: 'rotate(-90deg)',
            transformOrigin: '50% 50%',
          }}
        />
      </svg>
      <Box
        sx={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexDirection: 'column',
        }}
      >
        <motion.div
          initial={{ opacity: 0, scale: 0.5 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.5, duration: 0.5 }}
        >
          <Typography 
            variant="h2" 
            fontWeight={700} 
            color={getColor(score)}
            sx={{ fontSize: { xs: '2rem', md: '3rem' } }}
          >
            {score.toFixed(0)}%
          </Typography>
        </motion.div>
        <Typography variant="body2" color="text.secondary" sx={{ fontSize: { xs: '0.75rem', md: '0.875rem' } }}>
          Final Score
        </Typography>
      </Box>
    </Box>
  );
};

// Score Bar Component
const ScoreBar = ({ label, score, color = 'primary', isDark }) => (
  <Box sx={{ mb: 2 }}>
    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
      <Typography variant="body2" color="text.secondary">
        {label}
      </Typography>
      <Typography variant="body2" fontWeight={600}>
        {(score * 100).toFixed(1)}%
      </Typography>
    </Box>
    <LinearProgress
      variant="determinate"
      value={score * 100}
      color={color}
      sx={{
        height: 10,
        borderRadius: 5,
        bgcolor: isDark ? 'rgba(255,255,255,0.1)' : 'grey.100',
      }}
    />
  </Box>
);

function Results() {
  const { id } = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  const theme = useTheme();
  const { isDark } = useThemeMode();

  // Get result from navigation state or mock data
  const result = location.state?.result || {
    success: true,
    evaluation_id: id,
    final_score: 78.5,
    max_marks: 10,
    obtained_marks: 7.85,
    grade: 'good',
    score_breakdown: {
      semantic_score: 0.82,
      keyword_score: 0.75,
      diagram_score: null,
      length_penalty: 0.02,
      weighted_score: 0.785,
    },
    concepts: {
      matched: ['photosynthesis', 'chlorophyll', 'glucose', 'oxygen'],
      missing: ['carbon dioxide', 'sunlight'],
      coverage_percentage: 66.7,
    },
    explanation: "Good attempt! Your answer shows a reasonable understanding of the topic. The semantic similarity is 82%. You covered 67% of the key concepts. Consider elaborating on: carbon dioxide, sunlight.",
    suggestions: [
      "Include more specific examples",
      "Mention the role of carbon dioxide in the process",
      "Explain how sunlight is converted to energy"
    ],
    processing_time: 1.234,
    timestamp: new Date().toISOString(),
  };

  if (!result) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  const grade = gradeConfig[result.grade] || gradeConfig.average;

  return (
    <Box>
      {/* Header */}
      <Box sx={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: { xs: 'flex-start', md: 'flex-start' }, 
        mb: { xs: 2, md: 4 },
        flexDirection: { xs: 'column', md: 'row' },
        gap: { xs: 2, md: 0 },
      }}>
        <Box>
          <Button
            startIcon={<ArrowBackIcon />}
            onClick={() => navigate('/evaluate')}
            sx={{ mb: { xs: 1, md: 2 }, fontSize: { xs: '0.8rem', md: '0.875rem' } }}
          >
            Back to Evaluate
          </Button>
          <Typography variant="h4" fontWeight={700} sx={{ fontSize: { xs: '1.5rem', md: '2rem' } }}>
            Evaluation Results
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ fontSize: { xs: '0.8rem', md: '1rem' } }}>
            Evaluation ID: {result.evaluation_id}
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 1, width: { xs: '100%', md: 'auto' } }}>
          <Button 
            variant="outlined" 
            startIcon={<RefreshIcon sx={{ fontSize: { xs: 16, md: 20 } }} />} 
            onClick={() => navigate('/evaluate')}
            sx={{ fontSize: { xs: '0.75rem', md: '0.875rem' }, flex: { xs: 1, md: 'unset' } }}
          >
            New Evaluation
          </Button>
          <Button 
            variant="outlined" 
            startIcon={<DownloadIcon sx={{ fontSize: { xs: 16, md: 20 } }} />}
            sx={{ fontSize: { xs: '0.75rem', md: '0.875rem' }, flex: { xs: 1, md: 'unset' } }}
          >
            Export
          </Button>
        </Box>
      </Box>

      <Grid container spacing={{ xs: 2, md: 3 }}>
        {/* Main Score Card */}
        <Grid item xs={12} md={5}>
          <Card
            component={motion.div}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            sx={{
              height: '100%',
              background: isDark 
                ? `linear-gradient(135deg, ${grade.bgColor} 0%, ${theme.palette.background.paper} 100%)`
                : `linear-gradient(135deg, ${grade.bgColor} 0%, white 100%)`,
              borderRadius: { xs: 2, md: 3 },
            }}
          >
            <CardContent sx={{ p: { xs: 2.5, md: 4 }, textAlign: 'center' }}>
              <Box sx={{ transform: { xs: 'scale(0.8)', md: 'scale(1)' } }}>
                <ScoreRing score={result.final_score} isDark={isDark} />
              </Box>
              
              <Box sx={{ mt: { xs: 2, md: 3 } }}>
                <Chip
                  icon={grade.icon}
                  label={grade.label}
                  color={grade.color}
                  size="large"
                  sx={{ fontSize: { xs: '0.85rem', md: '1rem' }, py: { xs: 2, md: 2.5 }, px: 1 }}
                />
                <Typography variant="body1" color="text.secondary" sx={{ mt: 2, fontSize: { xs: '0.85rem', md: '1rem' } }}>
                  {grade.description}
                </Typography>
              </Box>

              <Divider sx={{ my: { xs: 2, md: 3 } }} />

              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Typography variant="h4" fontWeight={700} color="primary.main" sx={{ fontSize: { xs: '1.5rem', md: '2rem' } }}>
                    {result.obtained_marks}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ fontSize: { xs: '0.75rem', md: '0.875rem' } }}>
                    Obtained Marks
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="h4" fontWeight={700} sx={{ fontSize: { xs: '1.5rem', md: '2rem' } }}>
                    {result.max_marks}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ fontSize: { xs: '0.75rem', md: '0.875rem' } }}>
                    Maximum Marks
                  </Typography>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Score Breakdown */}
        <Grid item xs={12} md={7}>
          <Card
            component={motion.div}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            sx={{ borderRadius: { xs: 2, md: 3 } }}
          >
            <CardContent sx={{ p: { xs: 2.5, md: 4 } }}>
              <Typography variant="h6" fontWeight={600} gutterBottom sx={{ fontSize: { xs: '1rem', md: '1.25rem' } }}>
                Score Breakdown
              </Typography>
              
              <Box sx={{ mt: { xs: 2, md: 3 } }}>
                <ScoreBar
                  label="Semantic Similarity (Meaning Match)"
                  score={result.score_breakdown.semantic_score}
                  color="primary"
                  isDark={isDark}
                />
                <ScoreBar
                  label="Keyword Coverage"
                  score={result.score_breakdown.keyword_score}
                  color="secondary"
                  isDark={isDark}
                />
                {result.score_breakdown.diagram_score !== null && (
                  <ScoreBar
                    label="Diagram Similarity"
                    score={result.score_breakdown.diagram_score}
                    color="info"
                    isDark={isDark}
                  />
                )}
              </Box>

              {result.score_breakdown.length_penalty > 0 && (
                <Alert severity="warning" sx={{ mt: 2, fontSize: { xs: '0.75rem', md: '0.875rem' } }}>
                  Length penalty applied: -{(result.score_breakdown.length_penalty * 100).toFixed(1)}%
                  (Answer was shorter than expected)
                </Alert>
              )}

              <Divider sx={{ my: { xs: 2, md: 3 } }} />

              {/* Explanation */}
              <Typography variant="h6" fontWeight={600} gutterBottom sx={{ fontSize: { xs: '1rem', md: '1.25rem' } }}>
                Explanation
              </Typography>
              <Paper elevation={0} sx={{ p: { xs: 1.5, md: 2 }, bgcolor: isDark ? 'rgba(255,255,255,0.05)' : 'grey.50', borderRadius: 2 }}>
                <Typography variant="body1" sx={{ fontSize: { xs: '0.85rem', md: '1rem' } }}>
                  {result.explanation}
                </Typography>
              </Paper>
            </CardContent>
          </Card>
        </Grid>

        {/* Concepts Analysis */}
        <Grid item xs={12} md={6}>
          <Card
            component={motion.div}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            sx={{ borderRadius: { xs: 2, md: 3 } }}
          >
            <CardContent sx={{ p: { xs: 2.5, md: 4 } }}>
              <Typography variant="h6" fontWeight={600} gutterBottom sx={{ fontSize: { xs: '1rem', md: '1.25rem' } }}>
                Concept Coverage
              </Typography>
              
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: { xs: 2, md: 3 } }}>
                <CircularProgress
                  variant="determinate"
                  value={result.concepts.coverage_percentage}
                  size={50}
                  thickness={6}
                  color="success"
                />
                <Box>
                  <Typography variant="h5" fontWeight={600} sx={{ fontSize: { xs: '1.25rem', md: '1.5rem' } }}>
                    {result.concepts.coverage_percentage.toFixed(0)}%
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ fontSize: { xs: '0.75rem', md: '0.875rem' } }}>
                    Concepts Covered
                  </Typography>
                </Box>
              </Box>

              <Typography variant="subtitle2" fontWeight={600} color="success.main" gutterBottom sx={{ fontSize: { xs: '0.8rem', md: '0.875rem' } }}>
                ✓ Matched Concepts ({result.concepts.matched.length})
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: { xs: 0.5, md: 1 }, mb: { xs: 2, md: 3 } }}>
                {result.concepts.matched.map((concept) => (
                  <Chip
                    key={concept}
                    label={concept}
                    size="small"
                    color="success"
                    variant="outlined"
                    sx={{ fontSize: { xs: '0.7rem', md: '0.8rem' } }}
                  />
                ))}
              </Box>

              {result.concepts.missing.length > 0 && (
                <>
                  <Typography variant="subtitle2" fontWeight={600} color="error.main" gutterBottom sx={{ fontSize: { xs: '0.8rem', md: '0.875rem' } }}>
                    ✗ Missing Concepts ({result.concepts.missing.length})
                  </Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: { xs: 0.5, md: 1 } }}>
                    {result.concepts.missing.map((concept) => (
                      <Chip
                        key={concept}
                        label={concept}
                        size="small"
                        color="error"
                        variant="outlined"
                        sx={{ fontSize: { xs: '0.7rem', md: '0.8rem' } }}
                      />
                    ))}
                  </Box>
                </>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Suggestions */}
        <Grid item xs={12} md={6}>
          <Card
            component={motion.div}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            sx={{ borderRadius: { xs: 2, md: 3 } }}
          >
            <CardContent sx={{ p: { xs: 2.5, md: 4 } }}>
              <Typography variant="h6" fontWeight={600} gutterBottom sx={{ fontSize: { xs: '1rem', md: '1.25rem' } }}>
                Suggestions for Improvement
              </Typography>
              
              <List sx={{ py: 0 }}>
                {result.suggestions.map((suggestion, index) => (
                  <ListItem key={index} sx={{ px: 0, py: { xs: 0.5, md: 1 } }}>
                    <ListItemIcon sx={{ minWidth: { xs: 32, md: 36 } }}>
                      <LightbulbIcon color="warning" sx={{ fontSize: { xs: 20, md: 24 } }} />
                    </ListItemIcon>
                    <ListItemText 
                      primary={suggestion} 
                      primaryTypographyProps={{ fontSize: { xs: '0.85rem', md: '1rem' } }}
                    />
                  </ListItem>
                ))}
              </List>

              <Divider sx={{ my: 2 }} />

              <Typography variant="caption" color="text.secondary" sx={{ fontSize: { xs: '0.65rem', md: '0.75rem' } }}>
                Processing time: {result.processing_time.toFixed(2)}s
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}

export default Results;
