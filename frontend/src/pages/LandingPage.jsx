/**
 * Landing Page - Professional Hero Section
 * ==========================================
 * Modern, animated landing page for AssessIQ
 * 
 * Features:
 * - Professional sticky header with auth
 * - Role-based Sign In/Sign Up
 * - Animated hero section
 * - Features, testimonials, CTA sections
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Container,
  Typography,
  Button,
  Grid,
  Card,
  CardContent,
  Avatar,
  Chip,
  Stack,
  Paper,
  IconButton,
  useTheme,
  alpha,
  Dialog,
  DialogContent,
  DialogTitle,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  LinearProgress,
} from '@mui/material';
import {
  PlayArrow as PlayIcon,
  ArrowForward as ArrowForwardIcon,
  CheckCircle as CheckIcon,
  Speed as SpeedIcon,
  Psychology as AIIcon,
  AutoAwesome as SparkleIcon,
  AutoAwesome as AutoAwesomeIcon,
  Security as SecurityIcon,
  TrendingUp as TrendingUpIcon,
  School as SchoolIcon,
  BarChart as ChartIcon,
  DocumentScanner as ScanIcon,
  Lightbulb as LightbulbIcon,
  Star as StarIcon,
  FormatQuote as QuoteIcon,
  KeyboardArrowDown as ScrollIcon,
  Close as CloseIcon,
  Upload as UploadIcon,
  Assessment as AssessmentIcon,
  Grading as GradingIcon,
  History as HistoryIcon,
  SmartToy as ChatBotIcon,
  FactCheck as ManualCheckIcon,
  Dashboard as DashboardIcon,
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import Header from '../components/Header';
import AuthModal from '../components/AuthModal';
import { useAuth } from '../context/AuthContext';

// Animated components
const MotionBox = motion(Box);
const MotionTypography = motion(Typography);
const MotionCard = motion(Card);
const MotionButton = motion(Button);

// Floating animation for decorative elements
const floatAnimation = {
  y: [0, -15, 0],
  transition: {
    duration: 3,
    repeat: Infinity,
    ease: "easeInOut"
  }
};

// Stats counter hook
const useCounter = (end, duration = 2000) => {
  const [count, setCount] = useState(0);
  
  useEffect(() => {
    let startTime;
    const animate = (currentTime) => {
      if (!startTime) startTime = currentTime;
      const progress = Math.min((currentTime - startTime) / duration, 1);
      setCount(Math.floor(progress * end));
      if (progress < 1) requestAnimationFrame(animate);
    };
    requestAnimationFrame(animate);
  }, [end, duration]);
  
  return count;
};

// Feature data
const features = [
  {
    icon: <ScanIcon sx={{ fontSize: 40 }} />,
    title: 'Smart OCR',
    description: 'Extract text from handwritten answer sheets with advanced image processing',
    color: '#6366f1',
  },
  {
    icon: <AIIcon sx={{ fontSize: 40 }} />,
    title: 'Semantic Analysis',
    description: 'Understand meaning, not just keywords using Sentence-BERT embeddings',
    color: '#8b5cf6',
  },
  {
    icon: <ChartIcon sx={{ fontSize: 40 }} />,
    title: 'Detailed Scoring',
    description: 'Get comprehensive breakdown of scores with actionable feedback',
    color: '#06b6d4',
  },
  {
    icon: <LightbulbIcon sx={{ fontSize: 40 }} />,
    title: 'Instant Feedback',
    description: 'Generate suggestions for improvement automatically',
    color: '#f59e0b',
  },
];

// Testimonials
const testimonials = [
  {
    name: 'Dr. Sarah Johnson',
    role: 'Professor, MIT',
    avatar: 'S',
    text: 'AssessIQ has transformed how I evaluate student work. What used to take hours now takes minutes.',
    rating: 5,
  },
  {
    name: 'Prof. Michael Chen',
    role: 'Dean, Stanford',
    avatar: 'M',
    text: 'The semantic understanding is remarkable. It catches nuances that keyword matching would miss.',
    rating: 5,
  },
  {
    name: 'Dr. Emily Brown',
    role: 'Educator, Oxford',
    avatar: 'E',
    text: 'Finally, an AI tool that understands academic evaluation. Our grading consistency has improved by 40%.',
    rating: 5,
  },
];

// Demo walkthrough steps
const demoSteps = [
  {
    label: 'Sign Up & Login',
    icon: <SchoolIcon />,
    description: 'Create your account as a Student, Teacher, or Admin. Each role has different features and access levels.',
    image: 'https://via.placeholder.com/600x400/6366f1/ffffff?text=Login+%26+Registration',
  },
  {
    label: 'Dashboard Overview',
    icon: <DashboardIcon />,
    description: 'Access your personalized dashboard with quick stats, recent evaluations, and easy navigation to all features.',
    image: 'https://via.placeholder.com/600x400/8b5cf6/ffffff?text=Dashboard',
  },
  {
    label: 'Upload Answer Sheets',
    icon: <UploadIcon />,
    description: 'Upload scanned answer sheets and model answers. Our OCR technology extracts text from handwritten content.',
    image: 'https://via.placeholder.com/600x400/06b6d4/ffffff?text=Upload+Answers',
  },
  {
    label: 'AI-Powered Evaluation',
    icon: <AIIcon />,
    description: 'Our semantic AI analyzes answers for meaning, not just keywords. Get accurate scores with detailed feedback.',
    image: 'https://via.placeholder.com/600x400/22c55e/ffffff?text=AI+Evaluation',
  },
  {
    label: 'Manual Checking',
    icon: <ManualCheckIcon />,
    description: 'Review AI evaluations or manually check answer sheets with our intuitive annotation tools and scoring panel.',
    image: 'https://via.placeholder.com/600x400/f59e0b/ffffff?text=Manual+Checking',
  },
  {
    label: 'View Results & Reports',
    icon: <AssessmentIcon />,
    description: 'Access detailed reports with score breakdowns, feedback, and improvement suggestions for each answer.',
    image: 'https://via.placeholder.com/600x400/ef4444/ffffff?text=Results+%26+Reports',
  },
  {
    label: 'AI Assistant',
    icon: <ChatBotIcon />,
    description: 'Get help anytime with our AI chatbot. Ask questions about evaluation, get study tips, or clarify doubts.',
    image: 'https://via.placeholder.com/600x400/a855f7/ffffff?text=AI+Assistant',
  },
  {
    label: 'History & Analytics',
    icon: <HistoryIcon />,
    description: 'Track all your evaluations, view trends, and export data for analysis and reporting.',
    image: 'https://via.placeholder.com/600x400/3b82f6/ffffff?text=History+%26+Analytics',
  },
];

function LandingPage() {
  const navigate = useNavigate();
  const theme = useTheme();
  const { isAuthenticated } = useAuth();
  const [activeTestimonial, setActiveTestimonial] = useState(0);
  const [authModal, setAuthModal] = useState({ open: false, mode: 'signin' });
  const [demoOpen, setDemoOpen] = useState(false);
  const [activeDemoStep, setActiveDemoStep] = useState(0);
  const [demoProgress, setDemoProgress] = useState(0);
  const [isAutoPlaying, setIsAutoPlaying] = useState(true);

  // Handle auth modal
  const handleOpenAuth = (mode = 'signin') => {
    setAuthModal({ open: true, mode });
  };

  const handleCloseAuth = () => {
    setAuthModal({ open: false, mode: 'signin' });
  };

  // Handle demo modal
  const handleOpenDemo = () => {
    setDemoOpen(true);
    setActiveDemoStep(0);
    setDemoProgress(0);
    setIsAutoPlaying(true);
  };

  const handleCloseDemo = () => {
    setDemoOpen(false);
    setActiveDemoStep(0);
    setDemoProgress(0);
    setIsAutoPlaying(false);
  };

  const handleNextStep = () => {
    if (activeDemoStep < demoSteps.length - 1) {
      setActiveDemoStep(prev => prev + 1);
      setDemoProgress(0);
    } else {
      handleCloseDemo();
    }
  };

  const handlePrevStep = () => {
    if (activeDemoStep > 0) {
      setActiveDemoStep(prev => prev - 1);
      setDemoProgress(0);
    }
  };

  // Auto-play demo
  useEffect(() => {
    if (demoOpen && isAutoPlaying) {
      const progressInterval = setInterval(() => {
        setDemoProgress(prev => {
          if (prev >= 100) {
            handleNextStep();
            return 0;
          }
          return prev + 2;
        });
      }, 100);
      return () => clearInterval(progressInterval);
    }
  }, [demoOpen, isAutoPlaying, activeDemoStep]);
  
  // Auto-rotate testimonials
  useEffect(() => {
    const interval = setInterval(() => {
      setActiveTestimonial((prev) => (prev + 1) % testimonials.length);
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  // Stats
  const evaluationsCount = useCounter(50000);
  const accuracyCount = useCounter(94);
  const timeCount = useCounter(85);

  return (
    <Box sx={{ overflow: 'hidden' }}>
      {/* Professional Header */}
      <Header />
      {/* ====== HERO SECTION ====== */}
      <Box
        sx={{
          minHeight: '100vh',
          position: 'relative',
          background: `linear-gradient(135deg, 
            ${alpha(theme.palette.primary.dark, 0.95)} 0%, 
            ${alpha('#1a1a2e', 0.98)} 50%,
            ${alpha(theme.palette.primary.dark, 0.95)} 100%)`,
          overflow: 'hidden',
        }}
      >
        {/* Animated background elements */}
        <Box sx={{ position: 'absolute', inset: 0, overflow: 'hidden' }}>
          {/* Gradient orbs */}
          <MotionBox
            animate={{
              x: [0, 100, 0],
              y: [0, -50, 0],
              scale: [1, 1.2, 1],
            }}
            transition={{ duration: 20, repeat: Infinity }}
            sx={{
              position: 'absolute',
              top: '10%',
              left: '10%',
              width: 500,
              height: 500,
              borderRadius: '50%',
              background: `radial-gradient(circle, ${alpha('#6366f1', 0.3)} 0%, transparent 70%)`,
              filter: 'blur(60px)',
            }}
          />
          <MotionBox
            animate={{
              x: [0, -100, 0],
              y: [0, 50, 0],
              scale: [1, 1.1, 1],
            }}
            transition={{ duration: 15, repeat: Infinity }}
            sx={{
              position: 'absolute',
              bottom: '10%',
              right: '10%',
              width: 400,
              height: 400,
              borderRadius: '50%',
              background: `radial-gradient(circle, ${alpha('#06b6d4', 0.3)} 0%, transparent 70%)`,
              filter: 'blur(60px)',
            }}
          />
          
          {/* Grid pattern overlay */}
          <Box
            sx={{
              position: 'absolute',
              inset: 0,
              backgroundImage: `
                linear-gradient(${alpha('#fff', 0.03)} 1px, transparent 1px),
                linear-gradient(90deg, ${alpha('#fff', 0.03)} 1px, transparent 1px)
              `,
              backgroundSize: '50px 50px',
            }}
          />
        </Box>

        <Container maxWidth="lg" sx={{ position: 'relative', zIndex: 1, pt: { xs: 10, md: 12 }, pb: { xs: 4, md: 8 }, px: { xs: 2, sm: 3 } }}>
          <Grid container spacing={{ xs: 3, md: 6 }} alignItems="center" minHeight={{ xs: 'auto', md: '80vh' }} sx={{ pt: { xs: 6, md: 0 } }}>
            <Grid item xs={12} md={6}>
              {/* Badge */}
              <MotionBox
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6 }}
                sx={{ textAlign: { xs: 'center', md: 'left' } }}
              >
                <Chip
                  icon={<SparkleIcon sx={{ color: '#fbbf24 !important', fontSize: { xs: 16, md: 20 } }} />}
                  label="AI-Powered Grading System"
                  sx={{
                    mb: { xs: 2, md: 3 },
                    px: { xs: 1, md: 2 },
                    py: { xs: 2, md: 2.5 },
                    bgcolor: alpha('#fff', 0.1),
                    color: 'white',
                    backdropFilter: 'blur(10px)',
                    border: `1px solid ${alpha('#fff', 0.2)}`,
                    '& .MuiChip-label': { fontSize: { xs: '0.75rem', md: '0.9rem' } },
                  }}
                />
              </MotionBox>

              {/* Main heading */}
              <MotionTypography
                variant="h1"
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.1 }}
                sx={{
                  color: 'white',
                  fontSize: { xs: '2rem', sm: '2.5rem', md: '3.5rem', lg: '4rem' },
                  fontWeight: 800,
                  lineHeight: 1.1,
                  mb: { xs: 2, md: 3 },
                  textAlign: { xs: 'center', md: 'left' },
                }}
              >
                Evaluate Answers{' '}
                <Box
                  component="span"
                  sx={{
                    background: 'linear-gradient(135deg, #60a5fa 0%, #a78bfa 50%, #f472b6 100%)',
                    backgroundClip: 'text',
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent',
                  }}
                >
                  Intelligently
                </Box>
              </MotionTypography>

              {/* Subtitle */}
              <MotionTypography
                variant="h6"
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.2 }}
                sx={{
                  color: alpha('#fff', 0.8),
                  fontWeight: 400,
                  lineHeight: 1.7,
                  mb: { xs: 3, md: 4 },
                  maxWidth: { xs: '100%', md: 500 },
                  fontSize: { xs: '0.95rem', md: '1.1rem' },
                  textAlign: { xs: 'center', md: 'left' },
                  px: { xs: 1, md: 0 },
                }}
              >
                Transform your grading workflow with AI that understands context, 
                meaning, and academic rigor. Get instant, accurate evaluations with 
                detailed feedback.
              </MotionTypography>

              {/* CTA Buttons */}
              <MotionBox
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.3 }}
                sx={{ 
                  display: 'flex', 
                  gap: { xs: 1.5, md: 2 }, 
                  flexWrap: 'wrap',
                  justifyContent: { xs: 'center', md: 'flex-start' },
                  flexDirection: { xs: 'column', sm: 'row' },
                  px: { xs: 2, sm: 0 },
                }}
              >
                <Button
                  variant="contained"
                  size="large"
                  fullWidth
                  endIcon={<ArrowForwardIcon />}
                  onClick={() => isAuthenticated ? navigate('/dashboard') : handleOpenAuth('signup')}
                  sx={{
                    px: { xs: 3, md: 4 },
                    py: { xs: 1.25, md: 1.5 },
                    fontSize: { xs: '1rem', md: '1.1rem' },
                    fontWeight: 600,
                    background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
                    boxShadow: `0 8px 30px ${alpha('#6366f1', 0.4)}`,
                    maxWidth: { sm: 220 },
                    '&:hover': {
                      background: 'linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)',
                      transform: 'translateY(-2px)',
                      boxShadow: `0 12px 40px ${alpha('#6366f1', 0.5)}`,
                    },
                  }}
                >
                  Get Started Free
                </Button>
                <Button
                  variant="outlined"
                  size="large"
                  fullWidth
                  startIcon={<PlayIcon />}
                  onClick={handleOpenDemo}
                  sx={{
                    px: { xs: 3, md: 4 },
                    py: { xs: 1.25, md: 1.5 },
                    fontSize: { xs: '1rem', md: '1.1rem' },
                    fontWeight: 600,
                    color: 'white',
                    borderColor: alpha('#fff', 0.3),
                    maxWidth: { sm: 180 },
                    '&:hover': {
                      borderColor: 'white',
                      bgcolor: alpha('#fff', 0.1),
                    },
                  }}
                >
                  Watch Demo
                </Button>
              </MotionBox>

              {/* Stats row */}
              <MotionBox
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.4 }}
                sx={{
                  display: 'flex',
                  gap: { xs: 2, sm: 3, md: 4 },
                  mt: { xs: 4, md: 6 },
                  pt: { xs: 3, md: 4 },
                  borderTop: `1px solid ${alpha('#fff', 0.1)}`,
                  justifyContent: { xs: 'center', md: 'flex-start' },
                  flexWrap: 'wrap',
                }}
              >
                <Box sx={{ textAlign: { xs: 'center', md: 'left' }, minWidth: { xs: 80, md: 'auto' } }}>
                  <Typography variant="h4" fontWeight={700} color="white" sx={{ fontSize: { xs: '1.5rem', md: '2rem' } }}>
                    {evaluationsCount.toLocaleString()}+
                  </Typography>
                  <Typography variant="body2" color={alpha('#fff', 0.6)} sx={{ fontSize: { xs: '0.7rem', md: '0.875rem' } }}>
                    Evaluations Done
                  </Typography>
                </Box>
                <Box sx={{ textAlign: { xs: 'center', md: 'left' }, minWidth: { xs: 80, md: 'auto' } }}>
                  <Typography variant="h4" fontWeight={700} color="white" sx={{ fontSize: { xs: '1.5rem', md: '2rem' } }}>
                    {accuracyCount}%
                  </Typography>
                  <Typography variant="body2" color={alpha('#fff', 0.6)} sx={{ fontSize: { xs: '0.7rem', md: '0.875rem' } }}>
                    Accuracy Rate
                  </Typography>
                </Box>
                <Box sx={{ textAlign: { xs: 'center', md: 'left' }, minWidth: { xs: 80, md: 'auto' } }}>
                  <Typography variant="h4" fontWeight={700} color="white" sx={{ fontSize: { xs: '1.5rem', md: '2rem' } }}>
                    {timeCount}%
                  </Typography>
                  <Typography variant="body2" color={alpha('#fff', 0.6)} sx={{ fontSize: { xs: '0.7rem', md: '0.875rem' } }}>
                    Time Saved
                  </Typography>
                </Box>
              </MotionBox>
            </Grid>

            {/* Right side - Floating Dashboard Preview - Hidden on mobile */}
            <Grid item xs={12} md={6} sx={{ display: { xs: 'none', md: 'block' } }}>
              <MotionBox
                initial={{ opacity: 0, x: 50, rotateY: -10 }}
                animate={{ opacity: 1, x: 0, rotateY: 0 }}
                transition={{ duration: 0.8, delay: 0.3 }}
                sx={{ perspective: 1000 }}
              >
                <Paper
                  elevation={24}
                  sx={{
                    borderRadius: 4,
                    overflow: 'hidden',
                    bgcolor: alpha('#fff', 0.05),
                    backdropFilter: 'blur(20px)',
                    border: `1px solid ${alpha('#fff', 0.1)}`,
                    p: 3,
                  }}
                >
                  {/* Mock dashboard header */}
                  <Box sx={{ display: 'flex', gap: 1, mb: 3 }}>
                    <Box sx={{ width: 12, height: 12, borderRadius: '50%', bgcolor: '#ff5f57' }} />
                    <Box sx={{ width: 12, height: 12, borderRadius: '50%', bgcolor: '#ffbd2e' }} />
                    <Box sx={{ width: 12, height: 12, borderRadius: '50%', bgcolor: '#28ca42' }} />
                  </Box>
                  
                  {/* Score card preview */}
                  <MotionBox animate={floatAnimation}>
                    <Paper
                      sx={{
                        p: 3,
                        mb: 2,
                        bgcolor: alpha('#6366f1', 0.2),
                        border: `1px solid ${alpha('#6366f1', 0.3)}`,
                        borderRadius: 3,
                      }}
                    >
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Box>
                          <Typography variant="overline" color={alpha('#fff', 0.7)}>
                            Evaluation Score
                          </Typography>
                          <Typography variant="h3" fontWeight={700} color="white">
                            87.5%
                          </Typography>
                        </Box>
                        <Box
                          sx={{
                            width: 80,
                            height: 80,
                            borderRadius: '50%',
                            border: `4px solid #22c55e`,
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                          }}
                        >
                          <Typography variant="h5" fontWeight={700} color="#22c55e">
                            A
                          </Typography>
                        </Box>
                      </Box>
                    </Paper>
                  </MotionBox>

                  {/* Analysis bars */}
                  {['Semantic Similarity', 'Keyword Coverage', 'Concept Match'].map((item, index) => (
                    <Box key={item} sx={{ mb: 2 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                        <Typography variant="body2" color={alpha('#fff', 0.8)}>
                          {item}
                        </Typography>
                        <Typography variant="body2" color={alpha('#fff', 0.6)}>
                          {[89, 76, 92][index]}%
                        </Typography>
                      </Box>
                      <Box
                        sx={{
                          height: 8,
                          borderRadius: 4,
                          bgcolor: alpha('#fff', 0.1),
                          overflow: 'hidden',
                        }}
                      >
                        <MotionBox
                          initial={{ width: 0 }}
                          animate={{ width: `${[89, 76, 92][index]}%` }}
                          transition={{ duration: 1, delay: 0.5 + index * 0.2 }}
                          sx={{
                            height: '100%',
                            borderRadius: 4,
                            background: `linear-gradient(90deg, ${['#6366f1', '#8b5cf6', '#06b6d4'][index]} 0%, ${['#8b5cf6', '#a78bfa', '#22d3ee'][index]} 100%)`,
                          }}
                        />
                      </Box>
                    </Box>
                  ))}
                </Paper>
              </MotionBox>
            </Grid>
          </Grid>

          {/* Scroll indicator - Hidden on mobile */}
          <MotionBox
            animate={{ y: [0, 10, 0] }}
            transition={{ duration: 2, repeat: Infinity }}
            sx={{
              position: 'absolute',
              bottom: { xs: 20, md: 40 },
              left: '50%',
              transform: 'translateX(-50%)',
              textAlign: 'center',
              display: { xs: 'none', md: 'block' },
            }}
          >
            <Typography variant="body2" color={alpha('#fff', 0.5)} sx={{ mb: 1 }}>
              Scroll to explore
            </Typography>
            <ScrollIcon sx={{ color: alpha('#fff', 0.5), fontSize: 30 }} />
          </MotionBox>
        </Container>
      </Box>

      {/* ====== FEATURES SECTION ====== */}
      <Box id="features" sx={{ py: { xs: 6, md: 12 }, bgcolor: '#fafafa', scrollMarginTop: '80px' }}>
        <Container maxWidth="lg" sx={{ px: { xs: 2, sm: 3 } }}>
          <Box sx={{ textAlign: 'center', mb: { xs: 4, md: 8 } }}>
            <Chip
              label="FEATURES"
              sx={{
                mb: 2,
                bgcolor: alpha('#6366f1', 0.1),
                color: '#6366f1',
                fontWeight: 600,
              }}
            />
            <Typography variant="h3" fontWeight={700} gutterBottom sx={{ fontSize: { xs: '1.75rem', md: '2.5rem' } }}>
              Everything You Need
            </Typography>
            <Typography variant="h6" color="text.secondary" sx={{ maxWidth: 600, mx: 'auto', fontSize: { xs: '0.95rem', md: '1.1rem' }, px: { xs: 2, md: 0 } }}>
              Powerful AI tools designed specifically for academic evaluation
            </Typography>
          </Box>

          <Grid container spacing={{ xs: 2, md: 4 }}>
            {features.map((feature, index) => (
              <Grid item xs={12} sm={6} md={3} key={feature.title}>
                <MotionCard
                  initial={{ opacity: 0, y: 30 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5, delay: index * 0.1 }}
                  viewport={{ once: true }}
                  whileHover={{ y: -10, boxShadow: '0 20px 40px rgba(0,0,0,0.1)' }}
                  sx={{
                    height: '100%',
                    p: { xs: 2, md: 3 },
                    textAlign: 'center',
                    border: '1px solid',
                    borderColor: 'divider',
                    boxShadow: 'none',
                    transition: 'all 0.3s ease',
                  }}
                >
                  <Box
                    sx={{
                      width: { xs: 60, md: 80 },
                      height: { xs: 60, md: 80 },
                      borderRadius: { xs: 2, md: 3 },
                      bgcolor: alpha(feature.color, 0.1),
                      color: feature.color,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      mx: 'auto',
                      mb: { xs: 2, md: 3 },
                      '& svg': { fontSize: { xs: 28, md: 40 } },
                    }}
                  >
                    {feature.icon}
                  </Box>
                  <Typography variant="h6" fontWeight={600} gutterBottom sx={{ fontSize: { xs: '1rem', md: '1.25rem' } }}>
                    {feature.title}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ fontSize: { xs: '0.8rem', md: '0.875rem' } }}>
                    {feature.description}
                  </Typography>
                </MotionCard>
              </Grid>
            ))}
          </Grid>
        </Container>
      </Box>

      {/* ====== HOW IT WORKS SECTION ====== */}
      <Box id="how-it-works" sx={{ py: { xs: 6, md: 12 }, bgcolor: 'white', scrollMarginTop: '80px' }}>
        <Container maxWidth="lg" sx={{ px: { xs: 2, sm: 3 } }}>
          <Box sx={{ textAlign: 'center', mb: { xs: 4, md: 8 } }}>
            <Chip
              label="HOW IT WORKS"
              sx={{
                mb: 2,
                bgcolor: alpha('#06b6d4', 0.1),
                color: '#06b6d4',
                fontWeight: 600,
              }}
            />
            <Typography variant="h3" fontWeight={700} gutterBottom sx={{ fontSize: { xs: '1.75rem', md: '2.5rem' } }}>
              Three Simple Steps
            </Typography>
          </Box>

          <Grid container spacing={{ xs: 4, md: 6 }} alignItems="center">
            {[
              { step: '01', title: 'Upload Answers', desc: 'Upload student answer sheets and model answers (images, PDFs, or text)' },
              { step: '02', title: 'AI Analyzes', desc: 'Our AI extracts text, understands meaning, and compares semantically' },
              { step: '03', title: 'Get Results', desc: 'Receive detailed scores, feedback, and suggestions instantly' },
            ].map((item, index) => (
              <Grid item xs={12} md={4} key={item.step}>
                <MotionBox
                  initial={{ opacity: 0, y: 30 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5, delay: index * 0.2 }}
                  viewport={{ once: true }}
                  sx={{ textAlign: 'center', position: 'relative' }}
                >
                  <Typography
                    variant="h1"
                    sx={{
                      fontSize: { xs: '4rem', md: '6rem' },
                      fontWeight: 800,
                      color: alpha('#6366f1', 0.1),
                      position: 'absolute',
                      top: { xs: -30, md: -40 },
                      left: '50%',
                      transform: 'translateX(-50%)',
                      zIndex: 0,
                    }}
                  >
                    {item.step}
                  </Typography>
                  <Box sx={{ position: 'relative', zIndex: 1, pt: { xs: 3, md: 4 } }}>
                    <Typography variant="h5" fontWeight={600} gutterBottom sx={{ fontSize: { xs: '1.1rem', md: '1.5rem' } }}>
                      {item.title}
                    </Typography>
                    <Typography variant="body1" color="text.secondary" sx={{ fontSize: { xs: '0.9rem', md: '1rem' } }}>
                      {item.desc}
                    </Typography>
                  </Box>
                </MotionBox>
              </Grid>
            ))}
          </Grid>
        </Container>
      </Box>

      {/* ====== TESTIMONIALS SECTION ====== */}
      <Box
        id="testimonials"
        sx={{
          py: { xs: 6, md: 12 },
          background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)',
          scrollMarginTop: '80px',
        }}
      >
        <Container maxWidth="md" sx={{ px: { xs: 2, sm: 3 } }}>
          <Box sx={{ textAlign: 'center', mb: { xs: 4, md: 6 } }}>
            <Chip
              label="TESTIMONIALS"
              sx={{
                mb: 2,
                bgcolor: alpha('#fff', 0.1),
                color: 'white',
                fontWeight: 600,
              }}
            />
            <Typography variant="h3" fontWeight={700} color="white" gutterBottom sx={{ fontSize: { xs: '1.5rem', md: '2.5rem' } }}>
              Trusted by Educators
            </Typography>
          </Box>

          <AnimatePresence mode="wait">
            <MotionBox
              key={activeTestimonial}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.5 }}
              sx={{ textAlign: 'center', px: { xs: 1, md: 0 } }}
            >
              <QuoteIcon sx={{ fontSize: { xs: 40, md: 60 }, color: alpha('#fff', 0.2), mb: 2 }} />
              <Typography
                variant="h5"
                color="white"
                sx={{ fontStyle: 'italic', mb: { xs: 3, md: 4 }, lineHeight: 1.8, fontSize: { xs: '1rem', md: '1.5rem' } }}
              >
                "{testimonials[activeTestimonial].text}"
              </Typography>
              <Box sx={{ display: 'flex', justifyContent: 'center', gap: 0.5, mb: 2 }}>
                {[...Array(testimonials[activeTestimonial].rating)].map((_, i) => (
                  <StarIcon key={i} sx={{ color: '#fbbf24', fontSize: { xs: 20, md: 24 } }} />
                ))}
              </Box>
              <Avatar
                sx={{
                  width: { xs: 48, md: 60 },
                  height: { xs: 48, md: 60 },
                  mx: 'auto',
                  mb: 2,
                  bgcolor: '#6366f1',
                  fontSize: { xs: '1.25rem', md: '1.5rem' },
                }}
              >
                {testimonials[activeTestimonial].avatar}
              </Avatar>
              <Typography variant="h6" color="white" fontWeight={600} sx={{ fontSize: { xs: '1rem', md: '1.25rem' } }}>
                {testimonials[activeTestimonial].name}
              </Typography>
              <Typography variant="body2" color={alpha('#fff', 0.6)} sx={{ fontSize: { xs: '0.8rem', md: '0.875rem' } }}>
                {testimonials[activeTestimonial].role}
              </Typography>
            </MotionBox>
          </AnimatePresence>

          {/* Testimonial dots */}
          <Box sx={{ display: 'flex', justifyContent: 'center', gap: 1, mt: 4 }}>
            {testimonials.map((_, index) => (
              <Box
                key={index}
                onClick={() => setActiveTestimonial(index)}
                sx={{
                  width: 10,
                  height: 10,
                  borderRadius: '50%',
                  bgcolor: activeTestimonial === index ? '#6366f1' : alpha('#fff', 0.3),
                  cursor: 'pointer',
                  transition: 'all 0.3s ease',
                }}
              />
            ))}
          </Box>
        </Container>
      </Box>

      {/* ====== CTA SECTION ====== */}
      <Box
        sx={{
          py: 12,
          background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
          textAlign: 'center',
        }}
      >
        <Container maxWidth="md" sx={{ px: { xs: 3, sm: 4 } }}>
          <Typography variant="h3" fontWeight={700} color="white" gutterBottom sx={{ fontSize: { xs: '1.5rem', md: '2.5rem' } }}>
            Ready to Transform Your Grading?
          </Typography>
          <Typography
            variant="h6"
            color={alpha('#fff', 0.9)}
            sx={{ mb: { xs: 3, md: 4 }, maxWidth: 600, mx: 'auto', fontSize: { xs: '0.95rem', md: '1.1rem' } }}
          >
            Join thousands of educators who are saving time and improving accuracy with AssessIQ.
          </Typography>
          <Button
            variant="contained"
            size="large"
            fullWidth
            endIcon={<ArrowForwardIcon />}
            onClick={() => navigate('/dashboard')}
            sx={{
              px: { xs: 4, md: 6 },
              py: { xs: 1.5, md: 2 },
              fontSize: { xs: '1rem', md: '1.2rem' },
              fontWeight: 600,
              bgcolor: 'white',
              color: '#6366f1',
              maxWidth: { sm: 300 },
              mx: 'auto',
              display: 'flex',
              '&:hover': {
                bgcolor: alpha('#fff', 0.9),
                transform: 'translateY(-2px)',
              },
            }}
          >
            Start Evaluating Now
          </Button>
        </Container>
      </Box>

      {/* ====== FOOTER ====== */}
      <Box
        component="footer"
        sx={{
          bgcolor: '#0f0f1a',
          pt: { xs: 6, md: 10 },
          pb: { xs: 4, md: 6 },
        }}
      >
        <Container maxWidth="lg" sx={{ px: { xs: 3, sm: 4 } }}>
          {/* Footer Main Content */}
          <Grid container spacing={{ xs: 4, md: 6 }}>
            {/* Brand Section */}
            <Grid item xs={12} md={4}>
              <Box sx={{ mb: { xs: 3, md: 0 } }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 2 }}>
                  <Box
                    sx={{
                      width: 45,
                      height: 45,
                      borderRadius: 2,
                      background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                    }}
                  >
                    <AutoAwesomeIcon sx={{ color: 'white', fontSize: 24 }} />
                  </Box>
                  <Typography
                    variant="h5"
                    fontWeight={700}
                    sx={{
                      background: 'linear-gradient(135deg, #6366f1 0%, #a855f7 100%)',
                      WebkitBackgroundClip: 'text',
                      WebkitTextFillColor: 'transparent',
                    }}
                  >
                    AssessIQ
                  </Typography>
                </Box>
                <Typography
                  variant="body2"
                  sx={{
                    color: alpha('#fff', 0.6),
                    lineHeight: 1.8,
                    maxWidth: 300,
                    fontSize: { xs: '0.85rem', md: '0.9rem' },
                  }}
                >
                  Revolutionizing education with AI-powered answer evaluation. 
                  Save time, ensure fairness, and provide meaningful feedback to students.
                </Typography>
                {/* Social Links */}
                <Box sx={{ display: 'flex', gap: 1.5, mt: 3 }}>
                  {[
                    { icon: '𝕏', label: 'Twitter' },
                    { icon: 'in', label: 'LinkedIn' },
                    { icon: 'f', label: 'Facebook' },
                    { icon: '▶', label: 'YouTube' },
                  ].map((social) => (
                    <Box
                      key={social.label}
                      sx={{
                        width: 40,
                        height: 40,
                        borderRadius: '50%',
                        bgcolor: alpha('#fff', 0.1),
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        cursor: 'pointer',
                        transition: 'all 0.3s ease',
                        '&:hover': {
                          bgcolor: '#6366f1',
                          transform: 'translateY(-3px)',
                        },
                      }}
                    >
                      <Typography sx={{ color: 'white', fontSize: '0.85rem', fontWeight: 600 }}>
                        {social.icon}
                      </Typography>
                    </Box>
                  ))}
                </Box>
              </Box>
            </Grid>

            {/* Quick Links */}
            <Grid item xs={6} sm={4} md={2}>
              <Typography
                variant="subtitle1"
                fontWeight={600}
                sx={{ color: 'white', mb: 2.5, fontSize: { xs: '0.95rem', md: '1rem' } }}
              >
                Product
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
                {['Features', 'Pricing', 'Integrations', 'API', 'Changelog'].map((item) => (
                  <Typography
                    key={item}
                    variant="body2"
                    sx={{
                      color: alpha('#fff', 0.6),
                      cursor: 'pointer',
                      transition: 'color 0.2s',
                      fontSize: { xs: '0.85rem', md: '0.9rem' },
                      '&:hover': { color: '#a855f7' },
                    }}
                  >
                    {item}
                  </Typography>
                ))}
              </Box>
            </Grid>

            {/* Company Links */}
            <Grid item xs={6} sm={4} md={2}>
              <Typography
                variant="subtitle1"
                fontWeight={600}
                sx={{ color: 'white', mb: 2.5, fontSize: { xs: '0.95rem', md: '1rem' } }}
              >
                Company
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
                {['About Us', 'Careers', 'Blog', 'Press', 'Contact'].map((item) => (
                  <Typography
                    key={item}
                    variant="body2"
                    sx={{
                      color: alpha('#fff', 0.6),
                      cursor: 'pointer',
                      transition: 'color 0.2s',
                      fontSize: { xs: '0.85rem', md: '0.9rem' },
                      '&:hover': { color: '#a855f7' },
                    }}
                  >
                    {item}
                  </Typography>
                ))}
              </Box>
            </Grid>

            {/* Resources Links */}
            <Grid item xs={6} sm={4} md={2}>
              <Typography
                variant="subtitle1"
                fontWeight={600}
                sx={{ color: 'white', mb: 2.5, fontSize: { xs: '0.95rem', md: '1rem' } }}
              >
                Resources
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
                {['Documentation', 'Help Center', 'Tutorials', 'Webinars', 'Community'].map((item) => (
                  <Typography
                    key={item}
                    variant="body2"
                    sx={{
                      color: alpha('#fff', 0.6),
                      cursor: 'pointer',
                      transition: 'color 0.2s',
                      fontSize: { xs: '0.85rem', md: '0.9rem' },
                      '&:hover': { color: '#a855f7' },
                    }}
                  >
                    {item}
                  </Typography>
                ))}
              </Box>
            </Grid>

            {/* Legal Links */}
            <Grid item xs={6} sm={4} md={2}>
              <Typography
                variant="subtitle1"
                fontWeight={600}
                sx={{ color: 'white', mb: 2.5, fontSize: { xs: '0.95rem', md: '1rem' } }}
              >
                Legal
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
                {['Privacy Policy', 'Terms of Service', 'Cookie Policy', 'GDPR', 'Security'].map((item) => (
                  <Typography
                    key={item}
                    variant="body2"
                    sx={{
                      color: alpha('#fff', 0.6),
                      cursor: 'pointer',
                      transition: 'color 0.2s',
                      fontSize: { xs: '0.85rem', md: '0.9rem' },
                      '&:hover': { color: '#a855f7' },
                    }}
                  >
                    {item}
                  </Typography>
                ))}
              </Box>
            </Grid>
          </Grid>

          {/* Newsletter Section */}
          <Box
            sx={{
              mt: { xs: 5, md: 8 },
              p: { xs: 3, md: 4 },
              borderRadius: 3,
              background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(139, 92, 246, 0.15) 100%)',
              border: '1px solid',
              borderColor: alpha('#6366f1', 0.3),
            }}
          >
            <Grid container spacing={3} alignItems="center">
              <Grid item xs={12} md={6}>
                <Typography
                  variant="h6"
                  fontWeight={600}
                  sx={{ color: 'white', mb: 1, fontSize: { xs: '1rem', md: '1.25rem' } }}
                >
                  Stay Updated with AssessIQ
                </Typography>
                <Typography
                  variant="body2"
                  sx={{ color: alpha('#fff', 0.6), fontSize: { xs: '0.85rem', md: '0.9rem' } }}
                >
                  Get the latest updates on AI in education, product features, and tips for educators.
                </Typography>
              </Grid>
              <Grid item xs={12} md={6}>
                <Box
                  sx={{
                    display: 'flex',
                    gap: 1.5,
                    flexDirection: { xs: 'column', sm: 'row' },
                  }}
                >
                  <Box
                    component="input"
                    placeholder="Enter your email"
                    sx={{
                      flex: 1,
                      px: 2.5,
                      py: 1.5,
                      borderRadius: 2,
                      border: '1px solid',
                      borderColor: alpha('#fff', 0.2),
                      bgcolor: alpha('#fff', 0.05),
                      color: 'white',
                      fontSize: '0.9rem',
                      outline: 'none',
                      transition: 'all 0.3s',
                      '&:focus': {
                        borderColor: '#6366f1',
                        bgcolor: alpha('#fff', 0.1),
                      },
                      '&::placeholder': {
                        color: alpha('#fff', 0.4),
                      },
                    }}
                  />
                  <Button
                    variant="contained"
                    sx={{
                      px: 4,
                      py: 1.5,
                      background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
                      fontWeight: 600,
                      whiteSpace: 'nowrap',
                      '&:hover': {
                        background: 'linear-gradient(135deg, #5558e3 0%, #7c4fe0 100%)',
                      },
                    }}
                  >
                    Subscribe
                  </Button>
                </Box>
              </Grid>
            </Grid>
          </Box>

          {/* Divider */}
          <Box
            sx={{
              height: 1,
              bgcolor: alpha('#fff', 0.1),
              my: { xs: 4, md: 5 },
            }}
          />

          {/* Bottom Footer */}
          <Box
            sx={{
              display: 'flex',
              flexDirection: { xs: 'column', md: 'row' },
              justifyContent: 'space-between',
              alignItems: 'center',
              gap: 2,
            }}
          >
            <Typography
              variant="body2"
              sx={{
                color: alpha('#fff', 0.5),
                fontSize: { xs: '0.8rem', md: '0.85rem' },
                textAlign: { xs: 'center', md: 'left' },
              }}
            >
              © {new Date().getFullYear()} AssessIQ. All rights reserved. Made with ❤️ for educators worldwide.
            </Typography>
            <Box
              sx={{
                display: 'flex',
                gap: { xs: 2, md: 3 },
                flexWrap: 'wrap',
                justifyContent: 'center',
              }}
            >
              {['Status', 'Accessibility', 'Sitemap'].map((item) => (
                <Typography
                  key={item}
                  variant="body2"
                  sx={{
                    color: alpha('#fff', 0.5),
                    cursor: 'pointer',
                    fontSize: { xs: '0.8rem', md: '0.85rem' },
                    transition: 'color 0.2s',
                    '&:hover': { color: '#a855f7' },
                  }}
                >
                  {item}
                </Typography>
              ))}
            </Box>
          </Box>
        </Container>
      </Box>

      {/* Auth Modal */}
      <AuthModal
        open={authModal.open}
        onClose={handleCloseAuth}
        initialMode={authModal.mode}
      />

      {/* Demo Walkthrough Modal */}
      <Dialog
        open={demoOpen}
        onClose={handleCloseDemo}
        maxWidth="md"
        fullWidth
        PaperProps={{
          sx: {
            borderRadius: 4,
            overflow: 'hidden',
            background: 'linear-gradient(135deg, #1e1e2f 0%, #2d2d44 100%)',
          },
        }}
      >
        <DialogTitle
          sx={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            background: 'linear-gradient(90deg, #6366f1 0%, #8b5cf6 100%)',
            color: 'white',
            py: 2,
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <PlayIcon sx={{ fontSize: 28 }} />
            <Typography variant="h6" fontWeight={600}>
              AssessIQ Demo Walkthrough
            </Typography>
          </Box>
          <IconButton onClick={handleCloseDemo} sx={{ color: 'white' }}>
            <CloseIcon />
          </IconButton>
        </DialogTitle>

        <DialogContent sx={{ p: 0 }}>
          {/* Progress bar */}
          <LinearProgress
            variant="determinate"
            value={demoProgress}
            sx={{
              height: 4,
              bgcolor: alpha('#fff', 0.1),
              '& .MuiLinearProgress-bar': {
                background: 'linear-gradient(90deg, #6366f1 0%, #8b5cf6 100%)',
              },
            }}
          />

          <Box sx={{ display: 'flex', minHeight: 500 }}>
            {/* Left sidebar - Steps */}
            <Box
              sx={{
                width: 280,
                bgcolor: alpha('#000', 0.3),
                p: 2,
                display: { xs: 'none', md: 'block' },
              }}
            >
              <Typography variant="caption" sx={{ color: alpha('#fff', 0.5), mb: 2, display: 'block' }}>
                WALKTHROUGH STEPS
              </Typography>
              <Stepper activeStep={activeDemoStep} orientation="vertical" nonLinear>
                {demoSteps.map((step, index) => (
                  <Step key={step.label} completed={index < activeDemoStep}>
                    <StepLabel
                      onClick={() => {
                        setActiveDemoStep(index);
                        setDemoProgress(0);
                      }}
                      sx={{
                        cursor: 'pointer',
                        '& .MuiStepLabel-label': {
                          color: index === activeDemoStep ? '#fff' : alpha('#fff', 0.6),
                          fontWeight: index === activeDemoStep ? 600 : 400,
                        },
                        '& .MuiStepIcon-root': {
                          color: index === activeDemoStep ? '#8b5cf6' : alpha('#fff', 0.3),
                          '&.Mui-completed': {
                            color: '#22c55e',
                          },
                        },
                      }}
                    >
                      {step.label}
                    </StepLabel>
                  </Step>
                ))}
              </Stepper>
            </Box>

            {/* Main content area */}
            <Box sx={{ flex: 1, p: 4 }}>
              <AnimatePresence mode="wait">
                <MotionBox
                  key={activeDemoStep}
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  transition={{ duration: 0.3 }}
                >
                  {/* Step header */}
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
                    <Box
                      sx={{
                        width: 56,
                        height: 56,
                        borderRadius: 3,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
                        color: 'white',
                      }}
                    >
                      {demoSteps[activeDemoStep]?.icon}
                    </Box>
                    <Box>
                      <Typography variant="caption" sx={{ color: alpha('#fff', 0.5) }}>
                        Step {activeDemoStep + 1} of {demoSteps.length}
                      </Typography>
                      <Typography variant="h5" fontWeight={700} sx={{ color: 'white' }}>
                        {demoSteps[activeDemoStep]?.label}
                      </Typography>
                    </Box>
                  </Box>

                  {/* Step description */}
                  <Typography
                    variant="body1"
                    sx={{
                      color: alpha('#fff', 0.8),
                      lineHeight: 1.8,
                      mb: 4,
                    }}
                  >
                    {demoSteps[activeDemoStep]?.description}
                  </Typography>

                  {/* Demo visual/animation area */}
                  <Paper
                    elevation={0}
                    sx={{
                      height: 250,
                      borderRadius: 3,
                      overflow: 'hidden',
                      bgcolor: alpha('#fff', 0.05),
                      border: `1px solid ${alpha('#fff', 0.1)}`,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      position: 'relative',
                    }}
                  >
                    {/* Animated elements based on step */}
                    <MotionBox
                      animate={{
                        scale: [1, 1.05, 1],
                        opacity: [0.8, 1, 0.8],
                      }}
                      transition={{
                        duration: 3,
                        repeat: Infinity,
                        ease: 'easeInOut',
                      }}
                      sx={{
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        gap: 2,
                      }}
                    >
                      <Box
                        sx={{
                          width: 80,
                          height: 80,
                          borderRadius: '50%',
                          background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          color: 'white',
                          boxShadow: '0 0 40px rgba(99, 102, 241, 0.4)',
                        }}
                      >
                        {React.cloneElement(demoSteps[activeDemoStep]?.icon || <></>, { sx: { fontSize: 40 } })}
                      </Box>
                      <Typography
                        variant="h6"
                        sx={{
                          color: alpha('#fff', 0.9),
                          fontWeight: 600,
                          textAlign: 'center',
                        }}
                      >
                        {demoSteps[activeDemoStep]?.label}
                      </Typography>
                    </MotionBox>

                    {/* Decorative floating elements */}
                    <MotionBox
                      animate={floatAnimation}
                      sx={{
                        position: 'absolute',
                        top: 20,
                        right: 40,
                        width: 40,
                        height: 40,
                        borderRadius: 2,
                        bgcolor: alpha('#6366f1', 0.2),
                      }}
                    />
                    <MotionBox
                      animate={{
                        ...floatAnimation,
                        transition: { ...floatAnimation.transition, delay: 1 },
                      }}
                      sx={{
                        position: 'absolute',
                        bottom: 30,
                        left: 50,
                        width: 30,
                        height: 30,
                        borderRadius: '50%',
                        bgcolor: alpha('#8b5cf6', 0.2),
                      }}
                    />
                  </Paper>

                  {/* Navigation buttons */}
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 4 }}>
                    <Button
                      variant="outlined"
                      onClick={handlePrevStep}
                      disabled={activeDemoStep === 0}
                      sx={{
                        borderColor: alpha('#fff', 0.3),
                        color: 'white',
                        '&:hover': {
                          borderColor: 'white',
                          bgcolor: alpha('#fff', 0.1),
                        },
                        '&:disabled': {
                          borderColor: alpha('#fff', 0.1),
                          color: alpha('#fff', 0.3),
                        },
                      }}
                    >
                      Previous
                    </Button>
                    <Button
                      variant="outlined"
                      onClick={() => setIsAutoPlaying(!isAutoPlaying)}
                      sx={{
                        borderColor: alpha('#fff', 0.3),
                        color: 'white',
                        '&:hover': {
                          borderColor: 'white',
                          bgcolor: alpha('#fff', 0.1),
                        },
                      }}
                    >
                      {isAutoPlaying ? 'Pause' : 'Auto-Play'}
                    </Button>
                    <Button
                      variant="contained"
                      onClick={activeDemoStep === demoSteps.length - 1 ? handleCloseDemo : handleNextStep}
                      endIcon={<ArrowForwardIcon />}
                      sx={{
                        background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
                        '&:hover': {
                          background: 'linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)',
                        },
                      }}
                    >
                      {activeDemoStep === demoSteps.length - 1 ? 'Get Started' : 'Next'}
                    </Button>
                  </Box>
                </MotionBox>
              </AnimatePresence>
            </Box>
          </Box>

          {/* Mobile step indicators */}
          <Box
            sx={{
              display: { xs: 'flex', md: 'none' },
              justifyContent: 'center',
              gap: 1,
              py: 2,
              bgcolor: alpha('#000', 0.3),
            }}
          >
            {demoSteps.map((_, index) => (
              <Box
                key={index}
                onClick={() => {
                  setActiveDemoStep(index);
                  setDemoProgress(0);
                }}
                sx={{
                  width: index === activeDemoStep ? 24 : 8,
                  height: 8,
                  borderRadius: 4,
                  bgcolor: index === activeDemoStep ? '#8b5cf6' : alpha('#fff', 0.3),
                  cursor: 'pointer',
                  transition: 'all 0.3s',
                }}
              />
            ))}
          </Box>
        </DialogContent>
      </Dialog>
    </Box>
  );
}

export default LandingPage;
