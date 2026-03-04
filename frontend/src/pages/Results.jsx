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
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Tooltip,
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
  ExpandMore as ExpandMoreIcon,
  Quiz as QuizIcon,
  CheckCircleOutline as AnsweredIcon,
  HighlightOff as UnansweredIcon,
  Psychology as PsychologyIcon,
  VerifiedUser as VerifiedUserIcon,
  Warning as WarningIcon,
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

  const grade = gradeConfig[result.grade] || gradeConfig[result.overall_grade] || gradeConfig.average;

  // ─── Multi-Question Results ───────────────────────────────────────
  const isMultiQuestion = location.state?.isMultiQuestion || !!result.per_question;

  if (isMultiQuestion && result.per_question) {
    const overallGrade = gradeConfig[result.overall_grade] || gradeConfig.average;

    return (
      <Box>
        {/* Header */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: { xs: 2, md: 4 }, flexDirection: { xs: 'column', md: 'row' }, gap: { xs: 2, md: 0 } }}>
          <Box>
            <Button startIcon={<ArrowBackIcon />} onClick={() => navigate('/evaluate')} sx={{ mb: { xs: 1, md: 2 } }}>
              Back to Evaluate
            </Button>
            <Typography variant="h4" fontWeight={700} sx={{ fontSize: { xs: '1.5rem', md: '2rem' } }}>
              Per-Question Evaluation
            </Typography>
            <Typography variant="body1" color="text.secondary" sx={{ fontSize: { xs: '0.8rem', md: '1rem' } }}>
              {result.total_questions} question{result.total_questions !== 1 ? 's' : ''} evaluated independently &bull; ID: {result.evaluation_id}
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', gap: 1, width: { xs: '100%', md: 'auto' }, alignSelf: 'flex-start' }}>
            <Button variant="outlined" startIcon={<RefreshIcon />} onClick={() => navigate('/evaluate')} sx={{ flex: { xs: 1, md: 'unset' } }}>
              New Evaluation
            </Button>
          </Box>
        </Box>

        {/* Overall Summary Banner */}
        <Card
          component={motion.div}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          sx={{
            mb: 3,
            background: isDark
              ? `linear-gradient(135deg, ${overallGrade.bgColor} 0%, ${theme.palette.background.paper} 100%)`
              : `linear-gradient(135deg, ${overallGrade.bgColor} 0%, white 100%)`,
            borderRadius: 3,
          }}
        >
          <CardContent sx={{ p: { xs: 2.5, md: 4 } }}>
            <Grid container spacing={3} alignItems="center">
              {/* Score Ring */}
              <Grid item xs={12} md={3} sx={{ textAlign: 'center' }}>
                <Box sx={{ transform: { xs: 'scale(0.7)', md: 'scale(0.85)' }, display: 'inline-flex' }}>
                  <ScoreRing score={result.overall_percentage ?? 0} size={180} isDark={isDark} />
                </Box>
              </Grid>

              {/* Stats */}
              <Grid item xs={12} md={5}>
                <Typography variant="h5" fontWeight={700} gutterBottom sx={{ fontSize: { xs: '1.25rem', md: '1.5rem' } }}>
                  Overall Summary
                </Typography>
                <Chip icon={overallGrade.icon} label={overallGrade.label} color={overallGrade.color} sx={{ mb: 2 }} />

                <Grid container spacing={2}>
                  <Grid item xs={6}>
                    <Typography variant="h4" fontWeight={700} color="primary.main" sx={{ fontSize: { xs: '1.3rem', md: '1.8rem' } }}>
                      {Number(result.total_obtained_marks ?? 0).toFixed(1)}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">Obtained Marks</Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="h4" fontWeight={700} sx={{ fontSize: { xs: '1.3rem', md: '1.8rem' } }}>
                      {Number(result.total_max_marks ?? 0).toFixed(1)}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">Maximum Marks</Typography>
                  </Grid>
                </Grid>
              </Grid>

              {/* Question Stats */}
              <Grid item xs={12} md={4}>
                <Paper elevation={0} sx={{ p: 2, bgcolor: isDark ? 'rgba(255,255,255,0.05)' : 'grey.50', borderRadius: 2 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1.5 }}>
                    <QuizIcon color="primary" />
                    <Typography variant="subtitle2" fontWeight={600}>Question Breakdown</Typography>
                  </Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                    <Typography variant="body2" color="text.secondary">Total Questions</Typography>
                    <Typography variant="body2" fontWeight={600}>{result.total_questions}</Typography>
                  </Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                      <AnsweredIcon sx={{ fontSize: 16 }} color="success" />
                      <Typography variant="body2" color="text.secondary">Answered</Typography>
                    </Box>
                    <Typography variant="body2" fontWeight={600} color="success.main">{result.answered_questions}</Typography>
                  </Box>
                  {result.unanswered_questions > 0 && (
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                        <UnansweredIcon sx={{ fontSize: 16 }} color="error" />
                        <Typography variant="body2" color="text.secondary">Unanswered</Typography>
                      </Box>
                      <Typography variant="body2" fontWeight={600} color="error.main">{result.unanswered_questions}</Typography>
                    </Box>
                  )}
                  {result.segmentation_info && (
                    <Box sx={{ mt: 1.5, pt: 1.5, borderTop: '1px solid', borderColor: 'divider' }}>
                      <Typography variant="caption" color="text.secondary">
                        Detection: {result.segmentation_info.method} ({(result.segmentation_info.confidence * 100).toFixed(0)}% confidence)
                      </Typography>
                    </Box>
                  )}
                </Paper>
              </Grid>
            </Grid>
          </CardContent>
        </Card>

        {/* Per-Question Grade Overview Bar */}
        <Paper sx={{ p: 2, mb: 3, borderRadius: 2 }}>
          <Typography variant="subtitle2" fontWeight={600} sx={{ mb: 1.5 }}>
            Question-wise Score Map
          </Typography>
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
            {result.per_question.map((q) => {
              const qg = gradeConfig[q.grade] || gradeConfig.average;
              return (
                <Tooltip key={q.question_number} title={`${q.question_label || `Q${q.question_number}`}: ${Number(q.obtained_marks ?? 0).toFixed(1)}/${Number(q.max_marks ?? 0).toFixed(1)} — ${qg.label}`}>
                  <Box sx={{
                    flex: '1 1 0',
                    minWidth: 48,
                    maxWidth: 100,
                    textAlign: 'center',
                    py: 1,
                    px: 0.5,
                    borderRadius: 1.5,
                    bgcolor: q.is_unanswered ? (isDark ? 'rgba(198,40,40,0.15)' : 'rgba(198,40,40,0.08)') : qg.bgColor,
                    border: '1px solid',
                    borderColor: q.is_unanswered ? 'error.main' : `${qg.color}.main`,
                    cursor: 'default',
                  }}>
                    <Typography variant="caption" fontWeight={700} sx={{ display: 'block' }}>
                      {q.question_label || `Q${q.question_number}`}
                    </Typography>
                    <Typography variant="h6" fontWeight={700} sx={{ fontSize: '1rem', lineHeight: 1.2 }}>
                      {q.is_unanswered ? '—' : `${Number(q.final_score ?? 0).toFixed(0)}%`}
                    </Typography>
                    <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.6rem' }}>
                      {Number(q.obtained_marks ?? 0).toFixed(1)}/{Number(q.max_marks ?? 0).toFixed(1)}
                    </Typography>
                  </Box>
                </Tooltip>
              );
            })}
          </Box>
        </Paper>

        {/* Per-Question Accordions */}
        {result.per_question.map((q, idx) => {
          const qGrade = gradeConfig[q.grade] || gradeConfig.average;
          return (
            <Accordion
              key={q.question_number}
              component={motion.div}
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.05 }}
              defaultExpanded={result.per_question.length <= 3}
              sx={{ mb: 1.5, borderRadius: '12px !important', overflow: 'hidden', '&:before': { display: 'none' } }}
            >
              <AccordionSummary
                expandIcon={<ExpandMoreIcon />}
                sx={{
                  bgcolor: q.is_unanswered
                    ? (isDark ? 'rgba(198,40,40,0.12)' : 'rgba(198,40,40,0.05)')
                    : qGrade.bgColor,
                  '& .MuiAccordionSummary-content': { alignItems: 'center', gap: 2, flexWrap: 'wrap' },
                }}
              >
                <Chip
                  label={q.question_label || `Q${q.question_number}`}
                  size="small"
                  color={q.is_unanswered ? 'error' : qGrade.color}
                  sx={{ fontWeight: 700, minWidth: 44 }}
                />
                <Typography variant="subtitle1" fontWeight={600} sx={{ flex: 1, minWidth: 120 }}>
                  {q.is_unanswered ? 'Unanswered' : `${Number(q.final_score ?? 0).toFixed(1)}%`}
                  <Typography component="span" variant="body2" color="text.secondary" sx={{ ml: 1 }}>
                    ({Number(q.obtained_marks ?? 0).toFixed(1)} / {Number(q.max_marks ?? 0).toFixed(1)} marks)
                  </Typography>
                </Typography>
                <Chip
                  label={q.is_unanswered ? 'No Answer' : qGrade.label}
                  size="small"
                  variant="outlined"
                  color={q.is_unanswered ? 'error' : qGrade.color}
                />
              </AccordionSummary>

              <AccordionDetails sx={{ p: { xs: 2, md: 3 } }}>
                {q.is_unanswered ? (
                  <Alert severity="error" sx={{ mb: 2 }}>
                    No answer was provided for this question. 0 marks awarded.
                  </Alert>
                ) : (
                  <Grid container spacing={2}>
                    {/* Score Ring + Marks */}
                    <Grid item xs={12} sm={4} sx={{ textAlign: 'center' }}>
                      <Box sx={{ transform: 'scale(0.75)', display: 'inline-flex' }}>
                        <ScoreRing score={q.final_score ?? 0} size={150} strokeWidth={10} isDark={isDark} />
                      </Box>
                      <Box sx={{ mt: 1 }}>
                        <Chip icon={qGrade.icon} label={qGrade.label} color={qGrade.color} size="small" />
                      </Box>
                    </Grid>

                    {/* Score Breakdown */}
                    <Grid item xs={12} sm={8}>
                      <Typography variant="subtitle2" fontWeight={600} gutterBottom>Score Breakdown</Typography>
                      {q.score_breakdown && (
                        <Box>
                          <ScoreBar label="Semantic Similarity" score={q.score_breakdown.semantic_score ?? 0} color="primary" isDark={isDark} />
                          <ScoreBar label="Keyword Coverage" score={q.score_breakdown.keyword_score ?? 0} color="secondary" isDark={isDark} />
                          {q.score_breakdown.concept_graph_score != null && (
                            <ScoreBar label="Concept Graph" score={q.score_breakdown.concept_graph_score} color="info" isDark={isDark} />
                          )}
                          {q.score_breakdown.sentence_alignment_score != null && (
                            <ScoreBar label="Sentence Alignment" score={q.score_breakdown.sentence_alignment_score} color="info" isDark={isDark} />
                          )}
                          {q.score_breakdown.structural_score != null && (
                            <ScoreBar label="Structural Quality" score={q.score_breakdown.structural_score} color="info" isDark={isDark} />
                          )}

                          {/* Rubric for this question */}
                          {q.score_breakdown.rubric_score != null && q.concepts?.rubric_details?.dimensions && (
                            <Box sx={{ mt: 1 }}>
                              <Divider sx={{ mb: 1 }} />
                              <Typography variant="caption" fontWeight={600}>
                                Rubric ({(q.score_breakdown.rubric_score * 100).toFixed(1)}%)
                              </Typography>
                              {q.concepts.rubric_details.dimensions.map((dim) => (
                                <Box key={dim.name} sx={{ mb: 0.5 }}>
                                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                    <Typography variant="caption">{dim.display_name} ({(dim.weight * 100).toFixed(0)}%)</Typography>
                                    <Chip label={dim.band} size="small" color={dim.band === 'Excellent' ? 'success' : dim.band === 'Good' ? 'primary' : dim.band === 'Average' ? 'warning' : 'error'} sx={{ height: 18, fontSize: '0.6rem' }} />
                                  </Box>
                                  <ScoreBar label="" score={dim.score ?? 0} color={dim.band === 'Excellent' ? 'success' : dim.band === 'Good' ? 'primary' : dim.band === 'Average' ? 'warning' : 'error'} isDark={isDark} />
                                </Box>
                              ))}
                            </Box>
                          )}

                          {q.score_breakdown.length_penalty > 0 && (
                            <Alert severity="warning" sx={{ mt: 1, py: 0, fontSize: '0.75rem' }}>
                              Length penalty: -{(q.score_breakdown.length_penalty * 100).toFixed(1)}%
                            </Alert>
                          )}
                          {q.score_breakdown.anti_gaming_penalty > 0 && (
                            <Alert severity="error" sx={{ mt: 0.5, py: 0, fontSize: '0.75rem' }}>
                              Anti-gaming penalty: -{(q.score_breakdown.anti_gaming_penalty * 100).toFixed(1)}%
                            </Alert>
                          )}
                          {q.score_breakdown.bloom_modifier != null && q.score_breakdown.bloom_modifier !== 0 && (
                            <Alert severity={q.score_breakdown.bloom_modifier > 0 ? 'success' : 'info'} sx={{ mt: 0.5, py: 0, fontSize: '0.75rem' }}>
                              Bloom's modifier: {q.score_breakdown.bloom_modifier > 0 ? '+' : ''}{(q.score_breakdown.bloom_modifier * 100).toFixed(1)}%
                            </Alert>
                          )}
                        </Box>
                      )}
                    </Grid>

                    {/* Explanation */}
                    {q.explanation && (
                      <Grid item xs={12}>
                        <Divider sx={{ my: 1 }} />
                        <Typography variant="subtitle2" fontWeight={600} gutterBottom>Explanation</Typography>
                        <Paper elevation={0} sx={{ p: 1.5, bgcolor: isDark ? 'rgba(255,255,255,0.05)' : 'grey.50', borderRadius: 2 }}>
                          <Typography variant="body2">{q.explanation}</Typography>
                        </Paper>
                      </Grid>
                    )}

                    {/* Concepts */}
                    {q.concepts && (
                      <Grid item xs={12} sm={6}>
                        <Typography variant="subtitle2" fontWeight={600} gutterBottom>Concept Coverage</Typography>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                          <CircularProgress variant="determinate" value={q.concepts.coverage_percentage ?? 0} size={36} thickness={5} color="success" />
                          <Typography variant="body2" fontWeight={600}>{Number(q.concepts.coverage_percentage ?? 0).toFixed(0)}%</Typography>
                        </Box>
                        {q.concepts.matched?.length > 0 && (
                          <Box sx={{ mb: 1 }}>
                            <Typography variant="caption" color="success.main" fontWeight={600}>✓ Matched ({q.concepts.matched.length})</Typography>
                            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 0.5 }}>
                              {q.concepts.matched.map((c) => <Chip key={c} label={c} size="small" color="success" variant="outlined" sx={{ fontSize: '0.7rem' }} />)}
                            </Box>
                          </Box>
                        )}
                        {q.concepts.missing?.length > 0 && (
                          <Box>
                            <Typography variant="caption" color="error.main" fontWeight={600}>✗ Missing ({q.concepts.missing.length})</Typography>
                            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 0.5 }}>
                              {q.concepts.missing.map((c) => <Chip key={c} label={c} size="small" color="error" variant="outlined" sx={{ fontSize: '0.7rem' }} />)}
                            </Box>
                          </Box>
                        )}
                      </Grid>
                    )}

                    {/* Suggestions */}
                    {q.suggestions?.length > 0 && (
                      <Grid item xs={12} sm={6}>
                        <Typography variant="subtitle2" fontWeight={600} gutterBottom>Suggestions</Typography>
                        <List dense sx={{ py: 0 }}>
                          {q.suggestions.map((s, si) => (
                            <ListItem key={si} sx={{ px: 0, py: 0.25 }}>
                              <ListItemIcon sx={{ minWidth: 28 }}><LightbulbIcon color="warning" sx={{ fontSize: 18 }} /></ListItemIcon>
                              <ListItemText primary={s} primaryTypographyProps={{ fontSize: '0.8rem' }} />
                            </ListItem>
                          ))}
                        </List>
                      </Grid>
                    )}

                    {/* Bloom's Taxonomy + Confidence (compact per-question view) */}
                    {(q.concepts?.bloom_taxonomy_details || q.concepts?.confidence_details) && (
                      <Grid item xs={12}>
                        <Divider sx={{ my: 1 }} />
                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1.5, alignItems: 'center' }}>
                          {q.concepts?.bloom_taxonomy_details && (() => {
                            const bd = q.concepts.bloom_taxonomy_details;
                            const bloomColors = {
                              'Remember': '#ef5350', 'Understand': '#ff9800', 'Apply': '#ffeb3b',
                              'Analyse': '#66bb6a', 'Evaluate': '#42a5f5', 'Create': '#ab47bc',
                            };
                            return (
                              <Tooltip title={bd.feedback || `Q: ${bd.question_bloom_name}, Student: ${bd.student_bloom_name}`}>
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                                  <PsychologyIcon sx={{ fontSize: 16, color: 'secondary.main' }} />
                                  <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.7rem' }}>Bloom's:</Typography>
                                  <Chip
                                    label={bd.student_bloom_name || '?'}
                                    size="small"
                                    sx={{
                                      height: 20, fontSize: '0.6rem', fontWeight: 700,
                                      bgcolor: bloomColors[bd.student_bloom_name] || '#9e9e9e',
                                      color: ['Understand', 'Apply', 'Analyse'].includes(bd.student_bloom_name) ? '#000' : '#fff',
                                    }}
                                  />
                                  {bd.cognitive_alignment != null && (
                                    <Typography variant="caption" sx={{ fontSize: '0.65rem' }}>
                                      (align: {(bd.cognitive_alignment * 100).toFixed(0)}%)
                                    </Typography>
                                  )}
                                </Box>
                              </Tooltip>
                            );
                          })()}
                          {q.concepts?.confidence_details && (() => {
                            const cd = q.concepts.confidence_details;
                            const cp = cd.confidence_percentage ?? 0;
                            return (
                              <Tooltip title={cd.needs_manual_review ? 'Flagged for manual review' : `${cd.confidence_label} confidence`}>
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                                  <VerifiedUserIcon sx={{ fontSize: 16, color: cd.needs_manual_review ? 'warning.main' : 'success.main' }} />
                                  <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.7rem' }}>Confidence:</Typography>
                                  <Chip
                                    label={`${cp.toFixed(0)}% ${cd.confidence_label || ''}`}
                                    size="small"
                                    color={cp >= 70 ? 'success' : cp >= 50 ? 'warning' : 'error'}
                                    variant="outlined"
                                    sx={{ height: 20, fontSize: '0.6rem', fontWeight: 600 }}
                                  />
                                  {cd.needs_manual_review && <WarningIcon sx={{ fontSize: 14, color: 'warning.main' }} />}
                                </Box>
                              </Tooltip>
                            );
                          })()}
                        </Box>
                      </Grid>
                    )}

                    {/* Answer Previews */}
                    {(q.model_answer_preview || q.student_answer_preview) && (
                      <Grid item xs={12}>
                        <Divider sx={{ my: 1 }} />
                        <Grid container spacing={1}>
                          {q.model_answer_preview && (
                            <Grid item xs={12} sm={6}>
                              <Typography variant="caption" fontWeight={600} color="success.main">Model Answer (preview)</Typography>
                              <Paper elevation={0} sx={{ p: 1, bgcolor: isDark ? 'rgba(46,125,50,0.08)' : 'rgba(46,125,50,0.04)', borderRadius: 1, mt: 0.5 }}>
                                <Typography variant="caption" sx={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>{q.model_answer_preview}</Typography>
                              </Paper>
                            </Grid>
                          )}
                          {q.student_answer_preview && (
                            <Grid item xs={12} sm={6}>
                              <Typography variant="caption" fontWeight={600} color="primary.main">Student Answer (preview)</Typography>
                              <Paper elevation={0} sx={{ p: 1, bgcolor: isDark ? 'rgba(21,101,192,0.08)' : 'rgba(21,101,192,0.04)', borderRadius: 1, mt: 0.5 }}>
                                <Typography variant="caption" sx={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>{q.student_answer_preview}</Typography>
                              </Paper>
                            </Grid>
                          )}
                        </Grid>
                      </Grid>
                    )}
                  </Grid>
                )}
              </AccordionDetails>
            </Accordion>
          );
        })}

        {/* Processing Time */}
        <Box sx={{ textAlign: 'center', mt: 3, mb: 2 }}>
          <Typography variant="caption" color="text.secondary">
            Total processing time: {Number(result.processing_time ?? 0).toFixed(2)}s &bull; {result.total_questions} questions evaluated
          </Typography>
        </Box>
      </Box>
    );
  }
  // ─── End Multi-Question Results ────────────────────────────────────

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

                {/* Rubric Dimension Scores */}
                {result.score_breakdown.rubric_score != null && (
                  <Box sx={{ mt: 2 }}>
                    <Divider sx={{ mb: 2 }} />
                    <Typography variant="subtitle2" fontWeight={600} sx={{ mb: 1 }}>
                      📊 Rubric Evaluation (Score: {(result.score_breakdown.rubric_score * 100).toFixed(1)}%)
                    </Typography>
                    {result.concepts?.rubric_details?.dimensions?.map((dim) => (
                      <Box key={dim.name} sx={{ mb: 1 }}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 0.25 }}>
                          <Typography variant="caption" fontWeight={500}>
                            {dim.display_name} ({(dim.weight * 100).toFixed(0)}%)
                          </Typography>
                          <Chip
                            label={dim.band}
                            size="small"
                            color={
                              dim.band === 'Excellent' ? 'success' :
                              dim.band === 'Good' ? 'primary' :
                              dim.band === 'Average' ? 'warning' : 'error'
                            }
                            sx={{ height: 20, fontSize: '0.65rem' }}
                          />
                        </Box>
                        <ScoreBar
                          label=""
                          score={dim.score}
                          color={
                            dim.band === 'Excellent' ? 'success' :
                            dim.band === 'Good' ? 'primary' :
                            dim.band === 'Average' ? 'warning' : 'error'
                          }
                          isDark={isDark}
                        />
                        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: -0.5, mb: 0.5 }}>
                          {dim.feedback}
                        </Typography>
                      </Box>
                    ))}
                    {result.concepts?.rubric_details?.rubric_grade && (
                      <Typography variant="body2" fontWeight={600} sx={{ mt: 1 }}>
                        Rubric Grade: {result.concepts.rubric_details.rubric_grade}
                      </Typography>
                    )}
                  </Box>
                )}
              </Box>

              {result.score_breakdown.length_penalty > 0 && (
                <Alert severity="warning" sx={{ mt: 2, fontSize: { xs: '0.75rem', md: '0.875rem' } }}>
                  Length penalty applied: -{(result.score_breakdown.length_penalty * 100).toFixed(1)}%
                  (Answer was shorter than expected)
                </Alert>
              )}

              {result.score_breakdown.anti_gaming_penalty > 0 && (
                <Alert severity="error" sx={{ mt: 1, fontSize: { xs: '0.75rem', md: '0.875rem' } }}>
                  Anti-gaming penalty: -{(result.score_breakdown.anti_gaming_penalty * 100).toFixed(1)}%
                  (Possible gaming behaviour detected)
                </Alert>
              )}

              {result.score_breakdown.bloom_modifier != null && result.score_breakdown.bloom_modifier !== 0 && (
                <Alert
                  severity={result.score_breakdown.bloom_modifier > 0 ? 'success' : 'info'}
                  sx={{ mt: 1, fontSize: { xs: '0.75rem', md: '0.875rem' } }}
                >
                  Bloom's Taxonomy modifier: {result.score_breakdown.bloom_modifier > 0 ? '+' : ''}{(result.score_breakdown.bloom_modifier * 100).toFixed(1)}%
                  {result.score_breakdown.bloom_modifier > 0 ? ' (Higher-order thinking detected)' : ' (Below expected cognitive level)'}
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

        {/* Bloom's Taxonomy Analysis */}
        {result.concepts?.bloom_taxonomy_details && (
          <Grid item xs={12} md={6}>
            <Card
              component={motion.div}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
              sx={{ borderRadius: { xs: 2, md: 3 } }}
            >
              <CardContent sx={{ p: { xs: 2.5, md: 4 } }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                  <PsychologyIcon color="secondary" />
                  <Typography variant="h6" fontWeight={600} sx={{ fontSize: { xs: '1rem', md: '1.25rem' } }}>
                    Bloom's Taxonomy Analysis
                  </Typography>
                </Box>
                
                {(() => {
                  const bd = result.concepts.bloom_taxonomy_details;
                  const bloomColors = {
                    'Remember': '#ef5350', 'Understand': '#ff9800', 'Apply': '#ffeb3b',
                    'Analyse': '#66bb6a', 'Evaluate': '#42a5f5', 'Create': '#ab47bc',
                  };
                  const qLevel = bd.question_bloom_name || 'Understand';
                  const sLevel = bd.student_bloom_name || 'Understand';
                  return (
                    <>
                      {/* Question Expected Level */}
                      <Box sx={{ mb: 2 }}>
                        <Typography variant="caption" fontWeight={600} color="text.secondary" gutterBottom>
                          Expected Cognitive Level
                        </Typography>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
                          <Chip
                            label={`Level ${bd.question_bloom_level || '?'}: ${qLevel}`}
                            size="small"
                            sx={{
                              bgcolor: bloomColors[qLevel] || '#9e9e9e',
                              color: ['Understand', 'Apply', 'Analyse'].includes(qLevel) ? '#000' : '#fff',
                              fontWeight: 700,
                            }}
                          />
                          {bd.question_detection_confidence != null && (
                            <Typography variant="caption" color="text.secondary">
                              ({(bd.question_detection_confidence * 100).toFixed(0)}% confidence)
                            </Typography>
                          )}
                        </Box>
                      </Box>
                      
                      {/* Student Demonstrated Level */}
                      <Box sx={{ mb: 2 }}>
                        <Typography variant="caption" fontWeight={600} color="text.secondary" gutterBottom>
                          Student Demonstrated Level
                        </Typography>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
                          <Chip
                            label={`Level ${bd.student_bloom_level || '?'}: ${sLevel}`}
                            size="small"
                            sx={{
                              bgcolor: bloomColors[sLevel] || '#9e9e9e',
                              color: ['Understand', 'Apply', 'Analyse'].includes(sLevel) ? '#000' : '#fff',
                              fontWeight: 700,
                            }}
                          />
                          {bd.student_detection_confidence != null && (
                            <Typography variant="caption" color="text.secondary">
                              ({(bd.student_detection_confidence * 100).toFixed(0)}% confidence)
                            </Typography>
                          )}
                        </Box>
                      </Box>

                      {/* Cognitive Alignment Bar */}
                      {bd.cognitive_alignment != null && (
                        <Box sx={{ mb: 2 }}>
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                            <Typography variant="caption" fontWeight={600}>Cognitive Alignment</Typography>
                            <Typography variant="caption" fontWeight={700}>
                              {(bd.cognitive_alignment * 100).toFixed(0)}%
                            </Typography>
                          </Box>
                          <LinearProgress
                            variant="determinate"
                            value={bd.cognitive_alignment * 100}
                            color={bd.cognitive_alignment >= 0.7 ? 'success' : bd.cognitive_alignment >= 0.4 ? 'warning' : 'error'}
                            sx={{ height: 8, borderRadius: 4, bgcolor: isDark ? 'rgba(255,255,255,0.1)' : 'grey.100' }}
                          />
                        </Box>
                      )}

                      {/* Bloom Pyramid Visualization */}
                      {bd.student_level_breakdown && bd.student_level_breakdown.length > 0 && (
                        <Box sx={{ mb: 2 }}>
                          <Typography variant="caption" fontWeight={600} gutterBottom sx={{ display: 'block', mb: 1 }}>
                            Cognitive Level Distribution
                          </Typography>
                          {bd.student_level_breakdown.slice().reverse().map((lvl) => (
                            <Box key={lvl.level} sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                              <Typography variant="caption" sx={{ minWidth: 70, fontSize: '0.65rem', fontWeight: lvl.name === sLevel ? 700 : 400 }}>
                                {lvl.name}
                              </Typography>
                              <Box sx={{ flex: 1, position: 'relative' }}>
                                <LinearProgress
                                  variant="determinate"
                                  value={Math.min((lvl.hit_count || 0) * 20, 100)}
                                  sx={{
                                    height: 6, borderRadius: 3,
                                    bgcolor: isDark ? 'rgba(255,255,255,0.06)' : 'grey.100',
                                    '& .MuiLinearProgress-bar': {
                                      bgcolor: bloomColors[lvl.name] || '#9e9e9e',
                                    },
                                  }}
                                />
                              </Box>
                              <Typography variant="caption" sx={{ minWidth: 20, textAlign: 'right', fontSize: '0.6rem' }}>
                                {lvl.hit_count || 0}
                              </Typography>
                            </Box>
                          ))}
                        </Box>
                      )}

                      {/* Score Modifier */}
                      {bd.bloom_score_modifier != null && bd.bloom_score_modifier !== 0 && (
                        <Alert
                          severity={bd.bloom_score_modifier > 0 ? 'success' : 'info'}
                          sx={{ mt: 1, py: 0.5, fontSize: '0.8rem' }}
                        >
                          Bloom's modifier: {bd.bloom_score_modifier > 0 ? '+' : ''}{(bd.bloom_score_modifier * 100).toFixed(1)}%
                          {bd.exceeds_expectations && ' — Exceeds expected cognitive level!'}
                          {bd.below_expectations && ' — Below expected cognitive level'}
                        </Alert>
                      )}

                      {/* Feedback */}
                      {bd.feedback && (
                        <Paper elevation={0} sx={{ p: 1.5, mt: 1.5, bgcolor: isDark ? 'rgba(255,255,255,0.04)' : 'grey.50', borderRadius: 2 }}>
                          <Typography variant="body2" sx={{ fontSize: '0.85rem' }}>
                            {bd.feedback}
                          </Typography>
                        </Paper>
                      )}
                    </>
                  );
                })()}
              </CardContent>
            </Card>
          </Grid>
        )}

        {/* Confidence & Reliability Index */}
        {result.concepts?.confidence_details && (
          <Grid item xs={12} md={6}>
            <Card
              component={motion.div}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5 }}
              sx={{ borderRadius: { xs: 2, md: 3 } }}
            >
              <CardContent sx={{ p: { xs: 2.5, md: 4 } }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                  <VerifiedUserIcon color={
                    result.concepts.confidence_details.needs_manual_review ? 'warning' : 'success'
                  } />
                  <Typography variant="h6" fontWeight={600} sx={{ fontSize: { xs: '1rem', md: '1.25rem' } }}>
                    Confidence & Reliability
                  </Typography>
                </Box>
                
                {(() => {
                  const cd = result.concepts.confidence_details;
                  const confPercent = cd.confidence_percentage ?? 0;
                  const confColor = confPercent >= 80 ? '#2e7d32' : confPercent >= 60 ? '#f9a825' : '#c62828';
                  return (
                    <>
                      {/* Confidence Gauge */}
                      <Box sx={{ textAlign: 'center', mb: 2 }}>
                        <Box sx={{ position: 'relative', display: 'inline-flex' }}>
                          <CircularProgress
                            variant="determinate"
                            value={confPercent}
                            size={100}
                            thickness={6}
                            sx={{
                              color: confColor,
                              '& .MuiCircularProgress-circle': { strokeLinecap: 'round' },
                            }}
                          />
                          <Box sx={{
                            position: 'absolute', top: 0, left: 0, right: 0, bottom: 0,
                            display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column',
                          }}>
                            <Typography variant="h5" fontWeight={700} sx={{ color: confColor, lineHeight: 1 }}>
                              {confPercent.toFixed(0)}%
                            </Typography>
                            <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.6rem' }}>
                              {cd.confidence_label || 'N/A'}
                            </Typography>
                          </Box>
                        </Box>
                      </Box>

                      {/* Manual Review Warning */}
                      {cd.needs_manual_review && (
                        <Alert severity="warning" icon={<WarningIcon />} sx={{ mb: 2, fontSize: '0.8rem' }}>
                          <strong>Flagged for Manual Review</strong>
                          {cd.review_reasons?.length > 0 && (
                            <Box component="ul" sx={{ m: 0, pl: 2, mt: 0.5, fontSize: '0.75rem' }}>
                              {cd.review_reasons.map((r, i) => <li key={i}>{r}</li>)}
                            </Box>
                          )}
                        </Alert>
                      )}

                      {/* Factor Breakdown */}
                      {cd.factors && cd.factors.length > 0 && (
                        <Box>
                          <Typography variant="caption" fontWeight={600} gutterBottom sx={{ display: 'block', mb: 1 }}>
                            Factor Breakdown
                          </Typography>
                          {cd.factors.map((f) => (
                            <Box key={f.name} sx={{ mb: 1 }}>
                              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.25 }}>
                                <Typography variant="caption" sx={{ fontSize: '0.7rem' }}>
                                  {f.display_name} ({(f.weight * 100).toFixed(0)}%)
                                </Typography>
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                                  {f.is_warning && <WarningIcon sx={{ fontSize: 12, color: 'warning.main' }} />}
                                  <Typography variant="caption" fontWeight={600} sx={{ fontSize: '0.7rem' }}>
                                    {(f.score * 100).toFixed(0)}%
                                  </Typography>
                                </Box>
                              </Box>
                              <LinearProgress
                                variant="determinate"
                                value={f.score * 100}
                                sx={{
                                  height: 5, borderRadius: 3,
                                  bgcolor: isDark ? 'rgba(255,255,255,0.06)' : 'grey.100',
                                  '& .MuiLinearProgress-bar': {
                                    bgcolor: f.is_warning ? '#f9a825' : f.score >= 0.7 ? '#2e7d32' : f.score >= 0.4 ? '#1565c0' : '#c62828',
                                  },
                                }}
                              />
                            </Box>
                          ))}
                        </Box>
                      )}

                      {/* Flags */}
                      {cd.flags?.length > 0 && (
                        <Box sx={{ mt: 1.5, display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                          {cd.flags.map((flag, i) => (
                            <Chip key={i} label={flag} size="small" color="warning" variant="outlined" sx={{ fontSize: '0.65rem' }} />
                          ))}
                        </Box>
                      )}
                    </>
                  );
                })()}
              </CardContent>
            </Card>
          </Grid>
        )}
      </Grid>
    </Box>
  );
}

export default Results;
