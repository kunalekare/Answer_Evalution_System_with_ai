/**
 * ManualChecking Component
 * =========================
 * User-Friendly UI for Manual Answer Sheet Checking
 * 
 * Features:
 * - Left Panel: Annotation & Tools (tick, cross, pen, eraser, highlight, comments)
 * - Center Panel: Answer Sheet Viewer with zoom and pagination
 * - Right Panel: Question-Wise Evaluation Panel
 * - Bottom Action Bar: Control buttons and status indicators
 * - PDF Support: View and annotate PDF files
 */

import React, { useState, useRef, useEffect, useCallback } from 'react';
import * as pdfjsLib from 'pdfjs-dist';
import {
  Box,
  Paper,
  Typography,
  IconButton,
  Button,
  TextField,
  Tooltip,
  Divider,
  Badge,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Slider,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Alert,
  Snackbar,
  CircularProgress,
  InputAdornment,
  alpha,
  Fab,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  useTheme,
} from '@mui/material';
import { useThemeMode } from '../context/ThemeContext';
import {
  Check as CheckIcon,
  Close as CloseIcon,
  Remove as RemoveIcon,
  Edit as EditIcon,
  Create as PenIcon,
  AutoFixOff as EraserIcon,
  FormatUnderlined as UnderlineIcon,
  Highlight as HighlightIcon,
  Comment as CommentIcon,
  ZoomIn as ZoomInIcon,
  ZoomOut as ZoomOutIcon,
  NavigateBefore as PrevIcon,
  NavigateNext as NextIcon,
  Visibility as VisibilityIcon,
  VisibilityOff as VisibilityOffIcon,
  Refresh as RefreshIcon,
  Delete as DeleteIcon,
  Undo as UndoIcon,
  Save as SaveIcon,
  CloudUpload as UploadIcon,
  Description as QuestionPaperIcon,
  Calculate as CalculateIcon,
  ThumbDown as RejectIcon,
  ThumbUp as FinishIcon,
  MoreVert as MoreVertIcon,
  Brush as BrushIcon,
  Circle as CircleIcon,
  Help as HelpIcon,
  Fullscreen as FullscreenIcon,
  FullscreenExit as FullscreenExitIcon,
  Palette as PaletteIcon,
  TextFields as TextIcon,
  Download as DownloadIcon,
  Print as PrintIcon,
  Person as PersonIcon,
  Assessment as AssessmentIcon,
  Email as EmailIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';

// Annotation tool types
const TOOLS = {
  TICK: 'tick',
  CROSS: 'cross',
  PARTIAL: 'partial',
  PEN: 'pen',
  ERASER: 'eraser',
  UNDERLINE: 'underline',
  HIGHLIGHT: 'highlight',
  COMMENT: 'comment',
  TEXT: 'text',
  SELECT: 'select',
  NUMBER: 'number',
};

// Color options for annotations
const COLORS = {
  GREEN: '#22c55e',
  RED: '#ef4444',
  BLUE: '#3b82f6',
  YELLOW: '#fbbf24',
  ORANGE: '#f97316',
  PURPLE: '#8b5cf6',
  BLACK: '#1f2937',
};

// Sample questions data - in real app, this would come from API
const sampleQuestions = [
  { id: 'Q1', label: 'Q1', maxMarks: 20, awardedMarks: null },
  { id: 'Q2', label: 'Q2', maxMarks: 10, awardedMarks: null },
  { id: 'Q3', label: 'Q3', maxMarks: 10, awardedMarks: null },
  { id: 'Q4', label: 'Q4', maxMarks: 10, awardedMarks: null },
  { id: 'Q5', label: 'Q5', maxMarks: 10, awardedMarks: null },
  { id: 'Q6', label: 'Q6', maxMarks: 10, awardedMarks: null },
  { id: 'Q7', label: 'Q7', maxMarks: 10, awardedMarks: null },
];

function ManualChecking() {
  const navigate = useNavigate();
  const theme = useTheme();
  const { isDark } = useThemeMode();
  const canvasRef = useRef(null);
  const imageRef = useRef(null);
  const containerRef = useRef(null);
  const fileInputRef = useRef(null);

  // Set up PDF.js worker - use unpkg CDN which has the correct version
  useEffect(() => {
    // Use unpkg CDN which mirrors npm packages directly
    pdfjsLib.GlobalWorkerOptions.workerSrc = `https://unpkg.com/pdfjs-dist@${pdfjsLib.version}/build/pdf.worker.min.mjs`;
  }, []);

  // State management
  const [currentTool, setCurrentTool] = useState(TOOLS.SELECT);
  const [currentNumber, setCurrentNumber] = useState(null); // For number annotation
  const [currentColor, setCurrentColor] = useState(COLORS.GREEN);
  const [brushSize, setBrushSize] = useState(3);
  const [isDrawing, setIsDrawing] = useState(false);
  const [annotations, setAnnotations] = useState([]);
  const [undoStack, setUndoStack] = useState([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(8);
  const [visitedPages, setVisitedPages] = useState(new Set([1]));
  const [zoomLevel, setZoomLevel] = useState(100);
  const [questions, setQuestions] = useState(sampleQuestions);
  const [showAnnotations, setShowAnnotations] = useState(true);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [uploadedImages, setUploadedImages] = useState([]);
  const [currentImage, setCurrentImage] = useState(null);
  const [loading, setLoading] = useState(false);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' });
  const [questionPaperOpen, setQuestionPaperOpen] = useState(false);
  const [commentDialogOpen, setCommentDialogOpen] = useState(false);
  const [commentText, setCommentText] = useState('');
  const [commentPosition, setCommentPosition] = useState({ x: 0, y: 0 });
  const [colorPickerAnchor, setColorPickerAnchor] = useState(null);
  const [confirmDialog, setConfirmDialog] = useState({ open: false, type: '', title: '', message: '' });
  const [canvasDimensions, setCanvasDimensions] = useState({ width: 800, height: 1000 });
  const [pageAnnotations, setPageAnnotations] = useState({}); // Store annotations per page
  const [selectedQuestionIndex, setSelectedQuestionIndex] = useState(0); // Track selected question for auto-scoring
  
  // Student & Paper Info for Marksheet
  const [studentInfo, setStudentInfo] = useState({
    name: '',
    rollNo: '',
    paperName: '',
    class: '',
    subject: '',
    examDate: new Date().toISOString().split('T')[0],
  });
  const [marksheetDialogOpen, setMarksheetDialogOpen] = useState(false);
  const [generatedMarksheet, setGeneratedMarksheet] = useState(null);
  const [showStudentInfoDialog, setShowStudentInfoDialog] = useState(false);

  // Calculate total score
  const totalMaxMarks = questions.reduce((sum, q) => sum + q.maxMarks, 0);
  const totalAwardedMarks = questions.reduce((sum, q) => sum + (q.awardedMarks || 0), 0);

  // Convert PDF page to image
  const pdfPageToImage = async (pdfDoc, pageNum) => {
    const page = await pdfDoc.getPage(pageNum);
    const scale = 2; // Higher scale for better quality
    const viewport = page.getViewport({ scale });
    
    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d');
    canvas.height = viewport.height;
    canvas.width = viewport.width;
    
    await page.render({
      canvasContext: context,
      viewport: viewport,
    }).promise;
    
    return canvas.toDataURL('image/png');
  };

  // Handle file upload - supports both images and PDFs
  const handleFileUpload = useCallback(async (event) => {
    const files = Array.from(event.target.files);
    if (files.length === 0) return;

    setLoading(true);
    
    try {
      const allImages = [];
      
      for (const file of files) {
        if (file.type === 'application/pdf') {
          // Handle PDF files
          const arrayBuffer = await file.arrayBuffer();
          const pdfDoc = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;
          const numPages = pdfDoc.numPages;
          
          for (let i = 1; i <= numPages; i++) {
            const pageImage = await pdfPageToImage(pdfDoc, i);
            allImages.push(pageImage);
          }
          
          showSnackbar(`PDF loaded: ${numPages} pages extracted`, 'success');
        } else {
          // Handle image files
          const dataUrl = await new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = (e) => resolve(e.target.result);
            reader.onerror = reject;
            reader.readAsDataURL(file);
          });
          allImages.push(dataUrl);
        }
      }
      
      if (allImages.length > 0) {
        setUploadedImages(allImages);
        setCurrentImage(allImages[0]);
        setTotalPages(allImages.length);
        setCurrentPage(1);
        setVisitedPages(new Set([1]));
        setPageAnnotations({}); // Reset annotations for new upload
        showSnackbar(`${allImages.length} page(s) uploaded successfully!`, 'success');
      }
    } catch (error) {
      console.error('Error loading files:', error);
      showSnackbar('Error loading files: ' + error.message, 'error');
    } finally {
      setLoading(false);
    }
  }, []);

  // Show snackbar notification
  const showSnackbar = (message, severity = 'success') => {
    setSnackbar({ open: true, message, severity });
  };

  // Save current page annotations before switching
  const saveCurrentPageAnnotations = useCallback(() => {
    const canvas = canvasRef.current;
    if (canvas) {
      const dataUrl = canvas.toDataURL();
      setPageAnnotations(prev => ({
        ...prev,
        [currentPage]: dataUrl
      }));
    }
  }, [currentPage]);

  // Load annotations for a page
  const loadPageAnnotations = useCallback((page) => {
    const canvas = canvasRef.current;
    if (canvas && pageAnnotations[page]) {
      const ctx = canvas.getContext('2d');
      const img = new Image();
      img.onload = () => {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.drawImage(img, 0, 0);
      };
      img.src = pageAnnotations[page];
    } else if (canvas) {
      const ctx = canvas.getContext('2d');
      ctx.clearRect(0, 0, canvas.width, canvas.height);
    }
  }, [pageAnnotations]);

  // Handle page navigation
  const handlePageChange = (page) => {
    if (page >= 1 && page <= totalPages) {
      // Save current page annotations before switching
      saveCurrentPageAnnotations();
      
      setCurrentPage(page);
      setVisitedPages((prev) => new Set([...prev, page]));
      if (uploadedImages.length > 0) {
        setCurrentImage(uploadedImages[page - 1]);
      }
      
      // Load annotations for the new page after a short delay
      setTimeout(() => loadPageAnnotations(page), 100);
    }
  };

  // Handle zoom
  const handleZoom = (direction) => {
    setZoomLevel((prev) => {
      const newZoom = direction === 'in' ? prev + 10 : prev - 10;
      return Math.max(50, Math.min(200, newZoom));
    });
  };

  // Handle marks update
  const handleMarksChange = (questionId, value) => {
    const numValue = value === '' ? null : Math.max(0, Math.min(questions.find(q => q.id === questionId).maxMarks, parseInt(value) || 0));
    setQuestions((prev) =>
      prev.map((q) => (q.id === questionId ? { ...q, awardedMarks: numValue } : q))
    );
  };

  // Handle quick mark buttons
  const handleQuickMark = (questionId, type) => {
    const question = questions.find(q => q.id === questionId);
    let marks;
    switch (type) {
      case 'full':
        marks = question.maxMarks;
        break;
      case 'half':
        marks = Math.floor(question.maxMarks / 2);
        break;
      case 'quarter':
        marks = Math.floor(question.maxMarks / 4);
        break;
      case 'zero':
        marks = 0;
        break;
      default:
        marks = null;
    }
    handleMarksChange(questionId, marks);
  };

  // Canvas drawing handlers
  const startDrawing = (e) => {
    if (currentTool === TOOLS.SELECT) return;
    
    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const x = (e.clientX - rect.left) * (canvas.width / rect.width);
    const y = (e.clientY - rect.top) * (canvas.height / rect.height);

    if (currentTool === TOOLS.COMMENT) {
      setCommentPosition({ x, y });
      setCommentDialogOpen(true);
      return;
    }

    if (currentTool === TOOLS.TICK || currentTool === TOOLS.CROSS || currentTool === TOOLS.PARTIAL) {
      addSymbol(x, y);
      return;
    }

    if (currentTool === TOOLS.NUMBER && currentNumber !== null) {
      addNumberAnnotation(x, y);
      return;
    }

    setIsDrawing(true);
    const ctx = canvas.getContext('2d');
    ctx.beginPath();
    ctx.moveTo(x, y);
  };

  const draw = (e) => {
    if (!isDrawing || currentTool === TOOLS.SELECT) return;
    
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const rect = canvas.getBoundingClientRect();
    const x = (e.clientX - rect.left) * (canvas.width / rect.width);
    const y = (e.clientY - rect.top) * (canvas.height / rect.height);

    ctx.lineWidth = brushSize;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';

    if (currentTool === TOOLS.ERASER) {
      ctx.globalCompositeOperation = 'destination-out';
      ctx.strokeStyle = 'rgba(255,255,255,1)';
    } else if (currentTool === TOOLS.HIGHLIGHT) {
      ctx.globalCompositeOperation = 'multiply';
      ctx.strokeStyle = alpha(COLORS.YELLOW, 0.4);
      ctx.lineWidth = brushSize * 5;
    } else {
      ctx.globalCompositeOperation = 'source-over';
      ctx.strokeStyle = currentColor;
    }

    ctx.lineTo(x, y);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(x, y);
  };

  const stopDrawing = () => {
    setIsDrawing(false);
    const canvas = canvasRef.current;
    if (canvas) {
      const ctx = canvas.getContext('2d');
      ctx.beginPath();
    }
  };

  // Touch event handlers for mobile/tablet support
  const handleTouchStart = (e) => {
    e.preventDefault();
    const touch = e.touches[0];
    const mouseEvent = new MouseEvent('mousedown', {
      clientX: touch.clientX,
      clientY: touch.clientY
    });
    startDrawing(mouseEvent);
  };

  const handleTouchMove = (e) => {
    e.preventDefault();
    const touch = e.touches[0];
    const mouseEvent = new MouseEvent('mousemove', {
      clientX: touch.clientX,
      clientY: touch.clientY
    });
    draw(mouseEvent);
  };

  const handleTouchEnd = (e) => {
    e.preventDefault();
    stopDrawing();
  };

  // Add tick/cross/partial symbols
  const addSymbol = (x, y) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    ctx.save();
    ctx.globalCompositeOperation = 'source-over';
    
    const size = 20;
    ctx.lineWidth = 3;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';

    if (currentTool === TOOLS.TICK) {
      ctx.strokeStyle = COLORS.GREEN;
      ctx.beginPath();
      ctx.moveTo(x - size/2, y);
      ctx.lineTo(x - size/6, y + size/2);
      ctx.lineTo(x + size/2, y - size/2);
      ctx.stroke();
    } else if (currentTool === TOOLS.CROSS) {
      ctx.strokeStyle = COLORS.RED;
      ctx.beginPath();
      ctx.moveTo(x - size/2, y - size/2);
      ctx.lineTo(x + size/2, y + size/2);
      ctx.moveTo(x + size/2, y - size/2);
      ctx.lineTo(x - size/2, y + size/2);
      ctx.stroke();
    } else if (currentTool === TOOLS.PARTIAL) {
      ctx.strokeStyle = COLORS.ORANGE;
      ctx.beginPath();
      ctx.moveTo(x - size/2, y);
      ctx.lineTo(x + size/2, y);
      ctx.stroke();
      // Add small curve for partial mark
      ctx.beginPath();
      ctx.arc(x + size/2 + 5, y, 5, 0, Math.PI);
      ctx.stroke();
    }

    ctx.restore();
    
    setAnnotations(prev => [...prev, { type: currentTool, x, y, page: currentPage }]);
  };

  // Add number annotation on canvas
  const addNumberAnnotation = (x, y) => {
    const canvas = canvasRef.current;
    if (!canvas || currentNumber === null) return;

    const ctx = canvas.getContext('2d');
    ctx.save();
    ctx.globalCompositeOperation = 'source-over';
    
    // Draw circle background
    const radius = 16;
    ctx.beginPath();
    ctx.arc(x, y, radius, 0, Math.PI * 2);
    ctx.fillStyle = '#3b82f6';
    ctx.fill();
    ctx.strokeStyle = '#1e40af';
    ctx.lineWidth = 2;
    ctx.stroke();
    
    // Draw number text
    ctx.fillStyle = '#ffffff';
    ctx.font = 'bold 14px Arial';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(currentNumber.toString(), x, y);
    
    ctx.restore();
    
    setAnnotations(prev => [...prev, { 
      type: TOOLS.NUMBER, 
      x, 
      y, 
      value: currentNumber,
      page: currentPage 
    }]);

    // Auto-fill the score to the selected question
    if (selectedQuestionIndex >= 0 && selectedQuestionIndex < questions.length) {
      const selectedQuestion = questions[selectedQuestionIndex];
      const scoreValue = Math.min(currentNumber, selectedQuestion.maxMarks);
      
      setQuestions(prev => 
        prev.map((q, idx) => 
          idx === selectedQuestionIndex 
            ? { ...q, awardedMarks: scoreValue } 
            : q
        )
      );
      
      // Show feedback
      showSnackbar(`Q${selectedQuestionIndex + 1}: ${scoreValue}/${selectedQuestion.maxMarks} marks awarded`, 'success');
      
      // Auto-move to next question
      if (selectedQuestionIndex < questions.length - 1) {
        setSelectedQuestionIndex(prev => prev + 1);
      }
    }
  };

  // Add comment annotation
  const handleAddComment = () => {
    if (commentText.trim()) {
      setAnnotations(prev => [...prev, { 
        type: TOOLS.COMMENT, 
        x: commentPosition.x, 
        y: commentPosition.y, 
        text: commentText,
        page: currentPage 
      }]);
      
      // Draw comment indicator on canvas
      const canvas = canvasRef.current;
      if (canvas) {
        const ctx = canvas.getContext('2d');
        ctx.save();
        ctx.fillStyle = COLORS.BLUE;
        ctx.beginPath();
        ctx.arc(commentPosition.x, commentPosition.y, 8, 0, Math.PI * 2);
        ctx.fill();
        ctx.fillStyle = '#fff';
        ctx.font = 'bold 10px Arial';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText('!', commentPosition.x, commentPosition.y);
        ctx.restore();
      }
    }
    setCommentDialogOpen(false);
    setCommentText('');
  };

  // Clear annotations for current page
  const handleClearAnnotations = () => {
    const canvas = canvasRef.current;
    if (canvas) {
      const ctx = canvas.getContext('2d');
      ctx.clearRect(0, 0, canvas.width, canvas.height);
    }
    // Clear annotations for current page only
    setAnnotations(prev => prev.filter(a => a.page !== currentPage));
    setPageAnnotations(prev => {
      const newAnnotations = { ...prev };
      delete newAnnotations[currentPage];
      return newAnnotations;
    });
    showSnackbar(`Annotations cleared for page ${currentPage}`, 'info');
  };

  // Undo last annotation
  const handleUndo = () => {
    const canvas = canvasRef.current;
    if (canvas && annotations.length > 0) {
      // This is a simplified undo - in production, you'd want to store canvas states
      setAnnotations(prev => prev.slice(0, -1));
      showSnackbar('Last annotation undone', 'info');
    }
  };

  // Handle paper actions
  const handleFinishPaper = () => {
    const unansweredQuestions = questions.filter(q => q.awardedMarks === null);
    if (unansweredQuestions.length > 0) {
      setConfirmDialog({
        open: true,
        type: 'warning',
        title: 'Incomplete Evaluation',
        message: `${unansweredQuestions.length} question(s) have not been marked. Do you want to continue?`
      });
    } else {
      // Show student info dialog before generating marksheet
      setShowStudentInfoDialog(true);
    }
  };

  const submitPaper = () => {
    // Generate marksheet
    const marksheet = {
      id: Date.now().toString(),
      studentInfo: { ...studentInfo },
      paperDetails: {
        paperName: studentInfo.paperName,
        subject: studentInfo.subject,
        examDate: studentInfo.examDate,
        totalPages: totalPages,
      },
      evaluation: questions.map((q, idx) => ({
        questionNo: q.label,
        maxMarks: q.maxMarks,
        awardedMarks: q.awardedMarks || 0,
      })),
      totalMaxMarks: totalMaxMarks,
      totalObtainedMarks: totalAwardedMarks,
      percentage: ((totalAwardedMarks / totalMaxMarks) * 100).toFixed(2),
      grade: getGrade((totalAwardedMarks / totalMaxMarks) * 100),
      evaluatedBy: 'Teacher', // In production, get from auth context
      evaluatedAt: new Date().toISOString(),
    };
    
    setGeneratedMarksheet(marksheet);
    
    // Save marksheet to localStorage for access in StudentManagement
    const existingMarksheets = JSON.parse(localStorage.getItem('marksheets') || '[]');
    localStorage.setItem('marksheets', JSON.stringify([...existingMarksheets, marksheet]));
    
    setShowStudentInfoDialog(false);
    setMarksheetDialogOpen(true);
    showSnackbar('Marksheet generated successfully!', 'success');
  };

  // Get grade based on percentage
  const getGrade = (percentage) => {
    if (percentage >= 90) return 'A+';
    if (percentage >= 80) return 'A';
    if (percentage >= 70) return 'B+';
    if (percentage >= 60) return 'B';
    if (percentage >= 50) return 'C';
    if (percentage >= 40) return 'D';
    return 'F';
  };

  const handleConfirmIncomplete = () => {
    setConfirmDialog({ open: false, type: '', title: '', message: '' });
    setShowStudentInfoDialog(true);
  };

  const handleRejectPaper = () => {
    setConfirmDialog({
      open: true,
      type: 'reject',
      title: 'Reject Paper',
      message: 'Are you sure you want to reject this paper? This action cannot be undone.'
    });
  };

  const confirmReject = () => {
    showSnackbar('Paper has been rejected', 'warning');
    setConfirmDialog({ open: false, type: '', title: '', message: '' });
    // In real app, mark paper as rejected in backend
  };

  const handleUFM = () => {
    setConfirmDialog({
      open: true,
      type: 'ufm',
      title: 'Mark as UFM',
      message: 'Mark this paper for Unfair Means? This will flag the paper for review.'
    });
  };

  const confirmUFM = () => {
    showSnackbar('Paper marked as UFM', 'error');
    setConfirmDialog({ open: false, type: '', title: '', message: '' });
  };

  // Calculate total
  const handleCalculateTotal = () => {
    showSnackbar(`Total Score: ${totalAwardedMarks} / ${totalMaxMarks}`, 'info');
  };

  // Toggle fullscreen
  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      containerRef.current?.requestFullscreen();
      setIsFullscreen(true);
    } else {
      document.exitFullscreen();
      setIsFullscreen(false);
    }
  };

  // Tool button component
  const ToolButton = ({ tool, icon, label, color }) => (
    <Tooltip title={label} placement="right" arrow>
      <IconButton
        onClick={() => setCurrentTool(tool)}
        sx={{
          width: 48,
          height: 48,
          borderRadius: 2,
          bgcolor: currentTool === tool ? alpha(color || '#1976d2', 0.2) : 'transparent',
          border: currentTool === tool ? `2px solid ${color || '#1976d2'}` : '2px solid transparent',
          color: color || 'inherit',
          '&:hover': {
            bgcolor: alpha(color || '#1976d2', 0.1),
          },
        }}
      >
        {icon}
      </IconButton>
    </Tooltip>
  );

  // Number button for quick scores - updated to set NUMBER tool
  const ScoreButton = ({ value, label, color }) => {
    const isSelected = currentTool === TOOLS.NUMBER && currentNumber === value;
    return (
      <Tooltip title={`Mark ${label}`} placement="top" arrow>
        <Box
          onClick={() => {
            setCurrentTool(TOOLS.NUMBER);
            setCurrentNumber(value);
          }}
          sx={{
            width: 32,
            height: 32,
            borderRadius: '50%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            bgcolor: isSelected ? '#fff' : color,
            color: isSelected ? color : '#fff',
            fontWeight: 'bold',
            cursor: 'pointer',
            fontSize: '0.75rem',
            transition: 'all 0.2s',
            border: isSelected ? `2px solid ${color}` : '2px solid transparent',
            boxShadow: isSelected ? '0 0 8px rgba(59, 130, 246, 0.5)' : 'none',
            '&:hover': {
              transform: 'scale(1.1)',
              boxShadow: '0 2px 8px rgba(0,0,0,0.3)',
            },
          }}
        >
          {label}
        </Box>
      </Tooltip>
    );
  };

  return (
    <Box
      ref={containerRef}
      sx={{
        display: 'flex',
        height: 'calc(100vh - 64px)',
        bgcolor: isDark ? '#0f172a' : '#f0f2f5',
        overflow: 'hidden',
      }}
    >
      {/* Left Panel - Annotation Tools */}
      <Paper
        elevation={3}
        sx={{
          width: 100,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          py: 1.5,
          gap: 0.5,
          borderRadius: 0,
          bgcolor: '#1e293b',
          overflowY: 'auto',
        }}
      >
        <Typography
          variant="caption"
          sx={{
            color: '#94a3b8',
            mb: 0.5,
            fontSize: '0.65rem',
            letterSpacing: 1,
            textTransform: 'uppercase',
          }}
        >
          Numbers
        </Typography>

        {/* Score buttons in 2-column grid */}
        <Box sx={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(2, 1fr)', 
          gap: 0.5, 
          mb: 1,
          px: 0.5,
        }}>
          <ScoreButton value={0} label="0" color="#6b7280" />
          <ScoreButton value={0.25} label="¼" color="#6b7280" />
          <ScoreButton value={0.5} label="½" color="#6b7280" />
          <ScoreButton value={1} label="1" color="#10b981" />
          <ScoreButton value={2} label="2" color="#10b981" />
          <ScoreButton value={3} label="3" color="#10b981" />
          <ScoreButton value={4} label="4" color="#10b981" />
          <ScoreButton value={5} label="5" color="#10b981" />
          <ScoreButton value={6} label="6" color="#3b82f6" />
          <ScoreButton value={7} label="7" color="#3b82f6" />
          <ScoreButton value={8} label="8" color="#3b82f6" />
          <ScoreButton value={9} label="9" color="#3b82f6" />
          <ScoreButton value={10} label="10" color="#8b5cf6" />
        </Box>

        <Divider sx={{ width: '80%', bgcolor: '#475569' }} />

        <Typography
          variant="caption"
          sx={{
            color: '#94a3b8',
            mt: 0.5,
            fontSize: '0.65rem',
            letterSpacing: 1,
            textTransform: 'uppercase',
          }}
        >
          Tools
        </Typography>

        {/* Small tools in 2-column grid */}
        <Box sx={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(2, 1fr)', 
          gap: 0.5,
          px: 0.5,
        }}>
          {/* Tick/Cross tools */}
          <Tooltip title="Tick (Correct)" placement="top" arrow>
            <IconButton
              onClick={() => { setCurrentTool(TOOLS.TICK); setCurrentNumber(null); }}
              sx={{
                width: 36,
                height: 36,
                borderRadius: 1,
                bgcolor: currentTool === TOOLS.TICK ? alpha(COLORS.GREEN, 0.3) : 'transparent',
                border: currentTool === TOOLS.TICK ? `2px solid ${COLORS.GREEN}` : '2px solid transparent',
                color: COLORS.GREEN,
                '&:hover': { bgcolor: alpha(COLORS.GREEN, 0.2) },
              }}
            >
              <CheckIcon sx={{ fontSize: 18 }} />
            </IconButton>
          </Tooltip>
          <Tooltip title="Cross (Wrong)" placement="top" arrow>
            <IconButton
              onClick={() => { setCurrentTool(TOOLS.CROSS); setCurrentNumber(null); }}
              sx={{
                width: 36,
                height: 36,
                borderRadius: 1,
                bgcolor: currentTool === TOOLS.CROSS ? alpha(COLORS.RED, 0.3) : 'transparent',
                border: currentTool === TOOLS.CROSS ? `2px solid ${COLORS.RED}` : '2px solid transparent',
                color: COLORS.RED,
                '&:hover': { bgcolor: alpha(COLORS.RED, 0.2) },
              }}
            >
              <CloseIcon sx={{ fontSize: 18 }} />
            </IconButton>
          </Tooltip>

          {/* Pen/Eraser */}
          <Tooltip title="Pen Tool" placement="top" arrow>
            <IconButton
              onClick={() => { setCurrentTool(TOOLS.PEN); setCurrentNumber(null); }}
              sx={{
                width: 36,
                height: 36,
                borderRadius: 1,
                bgcolor: currentTool === TOOLS.PEN ? alpha('#94a3b8', 0.3) : 'transparent',
                border: currentTool === TOOLS.PEN ? '2px solid #94a3b8' : '2px solid transparent',
                color: '#94a3b8',
                '&:hover': { bgcolor: alpha('#94a3b8', 0.2) },
              }}
            >
              <PenIcon sx={{ fontSize: 18 }} />
            </IconButton>
          </Tooltip>
          <Tooltip title="Eraser" placement="top" arrow>
            <IconButton
              onClick={() => { setCurrentTool(TOOLS.ERASER); setCurrentNumber(null); }}
              sx={{
                width: 36,
                height: 36,
                borderRadius: 1,
                bgcolor: currentTool === TOOLS.ERASER ? alpha('#94a3b8', 0.3) : 'transparent',
                border: currentTool === TOOLS.ERASER ? '2px solid #94a3b8' : '2px solid transparent',
                color: '#94a3b8',
                '&:hover': { bgcolor: alpha('#94a3b8', 0.2) },
              }}
            >
              <EraserIcon sx={{ fontSize: 18 }} />
            </IconButton>
          </Tooltip>

          {/* Highlight/Underline */}
          <Tooltip title="Highlight" placement="top" arrow>
            <IconButton
              onClick={() => { setCurrentTool(TOOLS.HIGHLIGHT); setCurrentNumber(null); }}
              sx={{
                width: 36,
                height: 36,
                borderRadius: 1,
                bgcolor: currentTool === TOOLS.HIGHLIGHT ? alpha(COLORS.YELLOW, 0.3) : 'transparent',
                border: currentTool === TOOLS.HIGHLIGHT ? `2px solid ${COLORS.YELLOW}` : '2px solid transparent',
                color: COLORS.YELLOW,
                '&:hover': { bgcolor: alpha(COLORS.YELLOW, 0.2) },
              }}
            >
              <HighlightIcon sx={{ fontSize: 18 }} />
            </IconButton>
          </Tooltip>
          <Tooltip title="Comment" placement="top" arrow>
            <IconButton
              onClick={() => { setCurrentTool(TOOLS.COMMENT); setCurrentNumber(null); }}
              sx={{
                width: 36,
                height: 36,
                borderRadius: 1,
                bgcolor: currentTool === TOOLS.COMMENT ? alpha(COLORS.BLUE, 0.3) : 'transparent',
                border: currentTool === TOOLS.COMMENT ? `2px solid ${COLORS.BLUE}` : '2px solid transparent',
                color: COLORS.BLUE,
                '&:hover': { bgcolor: alpha(COLORS.BLUE, 0.2) },
              }}
            >
              <CommentIcon sx={{ fontSize: 18 }} />
            </IconButton>
          </Tooltip>
        </Box>

        <Divider sx={{ width: '80%', bgcolor: '#475569', my: 0.5 }} />

        {/* Quick actions row */}
        <Box sx={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(2, 1fr)', 
          gap: 0.5,
          px: 0.5,
        }}>
          <Tooltip title={showAnnotations ? "Hide" : "Show"} placement="top">
            <IconButton
              onClick={() => setShowAnnotations(!showAnnotations)}
              sx={{ 
                width: 36, 
                height: 36,
                borderRadius: 1,
                color: showAnnotations ? '#22c55e' : '#94a3b8',
                '&:hover': { bgcolor: alpha('#94a3b8', 0.2) },
              }}
            >
              {showAnnotations ? <VisibilityIcon sx={{ fontSize: 18 }} /> : <VisibilityOffIcon sx={{ fontSize: 18 }} />}
            </IconButton>
          </Tooltip>
          <Tooltip title="Undo" placement="top">
            <IconButton 
              onClick={handleUndo} 
              sx={{ 
                width: 36, 
                height: 36,
                borderRadius: 1,
                color: '#94a3b8',
                '&:hover': { bgcolor: alpha('#94a3b8', 0.2) },
              }}
            >
              <UndoIcon sx={{ fontSize: 18 }} />
            </IconButton>
          </Tooltip>
          <Tooltip title="Clear Page" placement="top">
            <IconButton 
              onClick={() => setConfirmDialog({ open: true, type: 'clear', title: 'Clear Annotations', message: 'Clear all annotations on this page?' })} 
              sx={{ 
                width: 36, 
                height: 36,
                borderRadius: 1,
                color: '#f97316',
                '&:hover': { bgcolor: alpha('#f97316', 0.2) },
              }}
            >
              <RefreshIcon sx={{ fontSize: 18 }} />
            </IconButton>
          </Tooltip>
          <Tooltip title="Delete All" placement="top">
            <IconButton 
              onClick={() => setConfirmDialog({ open: true, type: 'clear', title: 'Clear All', message: 'Delete all annotations?' })} 
              sx={{ 
                width: 36, 
                height: 36,
                borderRadius: 1,
                color: '#ef4444',
                '&:hover': { bgcolor: alpha('#ef4444', 0.2) },
              }}
            >
              <DeleteIcon sx={{ fontSize: 18 }} />
            </IconButton>
          </Tooltip>
        </Box>

        <Box sx={{ flexGrow: 1 }} />

        <Divider sx={{ width: '80%', bgcolor: '#475569', my: 0.5 }} />

        {/* File operations */}
        <Box sx={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(2, 1fr)', 
          gap: 0.5,
          px: 0.5,
        }}>
          <Tooltip title="Upload" placement="top">
            <IconButton 
              onClick={() => fileInputRef.current?.click()} 
              sx={{ 
                width: 36, 
                height: 36,
                borderRadius: 1,
                color: '#6366f1',
                '&:hover': { bgcolor: alpha('#6366f1', 0.2) },
              }}
            >
              <UploadIcon sx={{ fontSize: 18 }} />
            </IconButton>
          </Tooltip>
          <Tooltip title="Save" placement="top">
            <IconButton 
              sx={{ 
                width: 36, 
                height: 36,
                borderRadius: 1,
                color: '#22c55e',
                '&:hover': { bgcolor: alpha('#22c55e', 0.2) },
              }}
            >
              <SaveIcon sx={{ fontSize: 18 }} />
            </IconButton>
          </Tooltip>
        </Box>

        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileUpload}
          accept="image/*,.pdf,application/pdf"
          multiple
          style={{ display: 'none' }}
        />
      </Paper>

      {/* Center Panel - Answer Sheet Viewer */}
      <Box
        sx={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          bgcolor: isDark ? '#334155' : '#64748b',
          position: 'relative',
        }}
      >
        {/* Page header */}
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            px: 2,
            py: 1,
            bgcolor: isDark ? '#1e293b' : '#475569',
            borderBottom: `1px solid ${isDark ? '#475569' : '#64748b'}`,
          }}
        >
          <Typography variant="h6" sx={{ color: '#fff', fontWeight: 600 }}>
            Page Number : {currentPage}
          </Typography>
          
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <IconButton onClick={() => handleZoom('out')} sx={{ color: '#fff' }}>
              <ZoomOutIcon />
            </IconButton>
            <Typography sx={{ color: '#fff', minWidth: 50, textAlign: 'center' }}>
              {zoomLevel}%
            </Typography>
            <IconButton onClick={() => handleZoom('in')} sx={{ color: '#fff' }}>
              <ZoomInIcon />
            </IconButton>
            <IconButton onClick={toggleFullscreen} sx={{ color: '#fff' }}>
              {isFullscreen ? <FullscreenExitIcon /> : <FullscreenIcon />}
            </IconButton>
          </Box>

          <IconButton
            onClick={() => handlePageChange(currentPage + 1)}
            disabled={currentPage >= totalPages}
            sx={{ 
              bgcolor: '#06b6d4',
              color: '#fff',
              '&:hover': { bgcolor: '#0891b2' },
              '&:disabled': { bgcolor: '#475569', color: '#94a3b8' },
            }}
          >
            <NextIcon />
          </IconButton>
        </Box>

        {/* Answer sheet display area */}
        <Box
          sx={{
            flex: 1,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            overflow: 'auto',
            p: 2,
          }}
        >
          {loading ? (
            <CircularProgress sx={{ color: '#fff' }} />
          ) : currentImage ? (
            <Box
              sx={{
                position: 'relative',
                transform: `scale(${zoomLevel / 100})`,
                transformOrigin: 'center center',
                transition: 'transform 0.2s',
              }}
            >
              <img
                ref={imageRef}
                src={currentImage}
                alt={`Answer sheet page ${currentPage}`}
                onLoad={(e) => {
                  // Update canvas dimensions to match image
                  const img = e.target;
                  setCanvasDimensions({
                    width: img.naturalWidth,
                    height: img.naturalHeight
                  });
                  // Load annotations for current page after image loads
                  setTimeout(() => loadPageAnnotations(currentPage), 50);
                }}
                style={{
                  display: 'block',
                  maxWidth: '100%',
                  maxHeight: 'calc(100vh - 200px)',
                  borderRadius: 8,
                  boxShadow: '0 4px 20px rgba(0,0,0,0.3)',
                }}
              />
              <canvas
                ref={canvasRef}
                width={canvasDimensions.width}
                height={canvasDimensions.height}
                style={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  width: '100%',
                  height: '100%',
                  cursor: currentTool === TOOLS.SELECT ? 'default' : 'crosshair',
                  opacity: showAnnotations ? 1 : 0,
                  pointerEvents: showAnnotations ? 'auto' : 'none',
                  touchAction: 'none',
                }}
                onMouseDown={startDrawing}
                onMouseMove={draw}
                onMouseUp={stopDrawing}
                onMouseLeave={stopDrawing}
                onTouchStart={handleTouchStart}
                onTouchMove={handleTouchMove}
                onTouchEnd={handleTouchEnd}
              />
            </Box>
          ) : (
            <Box
              sx={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: 2,
              }}
            >
              <Paper
                onClick={() => fileInputRef.current?.click()}
                sx={{
                  width: 500,
                  height: 650,
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  bgcolor: '#fff',
                  cursor: 'pointer',
                  border: '3px dashed #94a3b8',
                  borderRadius: 3,
                  transition: 'all 0.3s',
                  '&:hover': {
                    borderColor: '#6366f1',
                    bgcolor: alpha('#6366f1', 0.05),
                  },
                }}
              >
                <UploadIcon sx={{ fontSize: 64, color: '#94a3b8', mb: 2 }} />
                <Typography variant="h6" color="textSecondary">
                  Upload Answer Sheets
                </Typography>
                <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
                  Click or drag and drop scanned images
                </Typography>
                <Typography variant="caption" color="textSecondary" sx={{ mt: 2 }}>
                  Supported formats: JPG, PNG, PDF
                </Typography>
              </Paper>
            </Box>
          )}
        </Box>

        {/* Page navigation */}
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 1,
            py: 1,
            bgcolor: isDark ? '#1e293b' : '#475569',
            borderTop: `1px solid ${isDark ? '#475569' : '#64748b'}`,
          }}
        >
          <IconButton
            onClick={() => handlePageChange(currentPage - 1)}
            disabled={currentPage <= 1}
            sx={{ color: '#fff' }}
          >
            <PrevIcon />
          </IconButton>
          
          {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => (
            <Box
              key={page}
              onClick={() => handlePageChange(page)}
              sx={{
                width: 32,
                height: 32,
                borderRadius: '50%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                cursor: 'pointer',
                bgcolor: currentPage === page ? '#6366f1' : visitedPages.has(page) ? '#10b981' : '#f97316',
                color: '#fff',
                fontWeight: 600,
                fontSize: '0.85rem',
                transition: 'all 0.2s',
                '&:hover': {
                  transform: 'scale(1.1)',
                },
              }}
            >
              {page}
            </Box>
          ))}
          
          <IconButton
            onClick={() => handlePageChange(currentPage + 1)}
            disabled={currentPage >= totalPages}
            sx={{ color: '#fff' }}
          >
            <NextIcon />
          </IconButton>
        </Box>
      </Box>

      {/* Right Panel - Question-Wise Evaluation */}
      <Paper
        elevation={3}
        sx={{
          width: 320,
          display: 'flex',
          flexDirection: 'column',
          borderRadius: 0,
          bgcolor: isDark ? theme.palette.background.paper : '#fff',
        }}
      >
        {/* Currently scoring indicator */}
        <Box
          sx={{
            p: 1.5,
            bgcolor: isDark ? 'rgba(99, 102, 241, 0.15)' : 'rgba(99, 102, 241, 0.1)',
            borderBottom: `1px solid ${isDark ? '#475569' : '#e2e8f0'}`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 1,
          }}
        >
          <Typography variant="body2" sx={{ color: isDark ? '#a5b4fc' : '#6366f1', fontWeight: 500 }}>
            Now Scoring:
          </Typography>
          <Chip
            label={questions[selectedQuestionIndex]?.label || 'Q1'}
            size="small"
            sx={{
              bgcolor: '#6366f1',
              color: '#fff',
              fontWeight: 700,
              animation: 'pulse 2s infinite',
              '@keyframes pulse': {
                '0%, 100%': { boxShadow: '0 0 0 0 rgba(99, 102, 241, 0.4)' },
                '50%': { boxShadow: '0 0 0 8px rgba(99, 102, 241, 0)' },
              },
            }}
          />
          <Typography variant="body2" sx={{ color: isDark ? '#94a3b8' : '#64748b' }}>
            (max: {questions[selectedQuestionIndex]?.maxMarks || 0})
          </Typography>
        </Box>

        {/* Questions header */}
        <Box
          sx={{
            p: 2,
            bgcolor: isDark ? '#334155' : '#f1f5f9',
            borderBottom: `1px solid ${isDark ? '#475569' : '#e2e8f0'}`,
          }}
        >
          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell sx={{ fontWeight: 700, color: isDark ? '#f1f5f9' : '#1e293b' }}>Questions</TableCell>
                  <TableCell align="center" sx={{ fontWeight: 700, color: isDark ? '#f1f5f9' : '#1e293b' }}>Out of</TableCell>
                  <TableCell align="center" sx={{ fontWeight: 700, color: isDark ? '#f1f5f9' : '#1e293b' }}>Evaluator Score</TableCell>
                </TableRow>
              </TableHead>
            </Table>
          </TableContainer>
        </Box>

        {/* Questions list */}
        <Box sx={{ flex: 1, overflow: 'auto', p: 1 }}>
          {questions.map((question, index) => (
            <Box
              key={question.id}
              onClick={() => setSelectedQuestionIndex(index)}
              sx={{
                display: 'flex',
                alignItems: 'center',
                gap: 1,
                py: 1.5,
                px: 1,
                borderBottom: `1px solid ${isDark ? '#475569' : '#e2e8f0'}`,
                cursor: 'pointer',
                bgcolor: selectedQuestionIndex === index 
                  ? (isDark ? 'rgba(99, 102, 241, 0.2)' : 'rgba(99, 102, 241, 0.1)') 
                  : 'transparent',
                borderLeft: selectedQuestionIndex === index 
                  ? '4px solid #6366f1' 
                  : '4px solid transparent',
                transition: 'all 0.2s ease',
                '&:hover': {
                  bgcolor: selectedQuestionIndex === index 
                    ? (isDark ? 'rgba(99, 102, 241, 0.25)' : 'rgba(99, 102, 241, 0.15)')
                    : (isDark ? '#334155' : '#f8fafc'),
                },
              }}
            >
              <Chip
                label={question.label}
                sx={{
                  minWidth: 48,
                  bgcolor: selectedQuestionIndex === index ? '#6366f1' : '#06b6d4',
                  color: '#fff',
                  fontWeight: 600,
                  transition: 'all 0.2s ease',
                }}
              />
              <Typography
                sx={{
                  flex: 1,
                  textAlign: 'center',
                  color: isDark ? '#94a3b8' : '#64748b',
                }}
              >
                {question.maxMarks}
              </Typography>
              <TextField
                type="number"
                size="small"
                value={question.awardedMarks ?? ''}
                onChange={(e) => {
                  handleMarksChange(question.id, e.target.value);
                  // Auto-advance to next question after manual input
                  if (e.target.value !== '' && index < questions.length - 1) {
                    setTimeout(() => setSelectedQuestionIndex(index + 1), 300);
                  }
                }}
                onClick={(e) => {
                  e.stopPropagation();
                  setSelectedQuestionIndex(index);
                }}
                inputProps={{
                  min: 0,
                  max: question.maxMarks,
                  style: { textAlign: 'center', fontWeight: 600 },
                }}
                sx={{
                  width: 70,
                  '& .MuiOutlinedInput-root': {
                    bgcolor: question.awardedMarks !== null 
                      ? alpha('#22c55e', 0.1) 
                      : selectedQuestionIndex === index 
                        ? (isDark ? 'rgba(99, 102, 241, 0.2)' : 'rgba(99, 102, 241, 0.1)')
                        : (isDark ? '#334155' : '#fff'),
                    '& fieldset': {
                      borderColor: question.awardedMarks !== null 
                        ? '#22c55e' 
                        : selectedQuestionIndex === index 
                          ? '#6366f1'
                          : (isDark ? '#475569' : '#e2e8f0'),
                      borderWidth: selectedQuestionIndex === index ? 2 : 1,
                    },
                  },
                }}
              />
            </Box>
          ))}
        </Box>

        {/* Total score */}
        <Box
          sx={{
            p: 2,
            bgcolor: isDark ? '#334155' : '#f1f5f9',
            borderTop: `1px solid ${isDark ? '#475569' : '#e2e8f0'}`,
          }}
        >
          <Button
            fullWidth
            variant="contained"
            onClick={handleCalculateTotal}
            startIcon={<CalculateIcon />}
            sx={{
              bgcolor: '#3b82f6',
              py: 1.5,
              fontSize: '1rem',
              fontWeight: 600,
              '&:hover': { bgcolor: '#2563eb' },
            }}
          >
            Calculate Total Score : {totalAwardedMarks.toFixed(2)} / {totalMaxMarks.toFixed(2)}
          </Button>
        </Box>

        {/* Action buttons */}
        <Box
          sx={{
            display: 'flex',
            gap: 1,
            p: 2,
            borderTop: `1px solid ${isDark ? '#475569' : '#e2e8f0'}`,
          }}
        >
          <Button
            variant="contained"
            onClick={handleRejectPaper}
            sx={{
              bgcolor: '#ef4444',
              flex: 1,
              fontWeight: 600,
              '&:hover': { bgcolor: '#dc2626' },
            }}
          >
            Reject Paper
          </Button>
          <Button
            variant="contained"
            onClick={handleUFM}
            sx={{
              bgcolor: '#f97316',
              flex: 1,
              fontWeight: 600,
              '&:hover': { bgcolor: '#ea580c' },
            }}
          >
            UFM
          </Button>
          <Button
            variant="contained"
            onClick={handleFinishPaper}
            sx={{
              bgcolor: '#22c55e',
              flex: 1,
              fontWeight: 600,
              '&:hover': { bgcolor: '#16a34a' },
            }}
          >
            Finish Paper
          </Button>
        </Box>

        {/* Question paper button */}
        <Button
          fullWidth
          variant="contained"
          onClick={() => setQuestionPaperOpen(true)}
          startIcon={<QuestionPaperIcon />}
          sx={{
            bgcolor: '#8b5cf6',
            borderRadius: 0,
            py: 1.5,
            fontWeight: 600,
            '&:hover': { bgcolor: '#7c3aed' },
          }}
        >
          Question Paper
        </Button>

        {/* Page status */}
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            p: 2,
            bgcolor: isDark ? '#334155' : '#f8fafc',
            borderTop: `1px solid ${isDark ? '#475569' : '#e2e8f0'}`,
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Typography variant="body2" color="textSecondary">Total Pages :</Typography>
            <Chip label={totalPages} size="small" sx={{ bgcolor: '#3b82f6', color: '#fff' }} />
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Typography variant="body2" color="textSecondary">Visited :</Typography>
            <Chip label={visitedPages.size} size="small" sx={{ bgcolor: '#22c55e', color: '#fff' }} />
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Typography variant="body2" color="textSecondary">Not Visited :</Typography>
            <Chip label={totalPages - visitedPages.size} size="small" sx={{ bgcolor: '#f97316', color: '#fff' }} />
          </Box>
        </Box>

        {/* Page thumbnails */}
        <Box
          sx={{
            display: 'flex',
            flexWrap: 'wrap',
            gap: 0.5,
            p: 2,
            justifyContent: 'center',
            borderTop: `1px solid ${isDark ? '#475569' : '#e2e8f0'}`,
          }}
        >
          {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => (
            <Box
              key={page}
              onClick={() => handlePageChange(page)}
              sx={{
                width: 28,
                height: 28,
                borderRadius: '50%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                cursor: 'pointer',
                bgcolor: currentPage === page ? '#6366f1' : visitedPages.has(page) ? '#10b981' : '#f97316',
                color: '#fff',
                fontWeight: 600,
                fontSize: '0.75rem',
                transition: 'all 0.2s',
                '&:hover': {
                  transform: 'scale(1.1)',
                },
              }}
            >
              {page}
            </Box>
          ))}
        </Box>
      </Paper>

      {/* Snackbar notifications */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={4000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert
          onClose={() => setSnackbar({ ...snackbar, open: false })}
          severity={snackbar.severity}
          variant="filled"
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>

      {/* Comment Dialog */}
      <Dialog open={commentDialogOpen} onClose={() => setCommentDialogOpen(false)}>
        <DialogTitle>Add Comment</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Comment"
            fullWidth
            multiline
            rows={3}
            value={commentText}
            onChange={(e) => setCommentText(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCommentDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleAddComment} variant="contained">Add</Button>
        </DialogActions>
      </Dialog>

      {/* Question Paper Dialog */}
      <Dialog
        open={questionPaperOpen}
        onClose={() => setQuestionPaperOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            Question Paper
            <IconButton onClick={() => setQuestionPaperOpen(false)}>
              <CloseIcon />
            </IconButton>
          </Box>
        </DialogTitle>
        <DialogContent>
          <Box
            sx={{
              minHeight: 400,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              bgcolor: '#f8fafc',
              borderRadius: 2,
              p: 4,
            }}
          >
            <Typography color="textSecondary">
              Question paper will be displayed here
            </Typography>
          </Box>
        </DialogContent>
      </Dialog>

      {/* Confirmation Dialog */}
      <Dialog
        open={confirmDialog.open}
        onClose={() => setConfirmDialog({ ...confirmDialog, open: false })}
      >
        <DialogTitle>{confirmDialog.title}</DialogTitle>
        <DialogContent>
          <Typography>{confirmDialog.message}</Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfirmDialog({ ...confirmDialog, open: false })}>
            Cancel
          </Button>
          <Button
            variant="contained"
            color={confirmDialog.type === 'reject' || confirmDialog.type === 'ufm' ? 'error' : 'primary'}
            onClick={() => {
              if (confirmDialog.type === 'reject') confirmReject();
              else if (confirmDialog.type === 'ufm') confirmUFM();
              else if (confirmDialog.type === 'warning') handleConfirmIncomplete();
              else if (confirmDialog.type === 'clear') {
                handleClearAnnotations();
                setConfirmDialog({ ...confirmDialog, open: false });
              }
            }}
          >
            Confirm
          </Button>
        </DialogActions>
      </Dialog>

      {/* Student Info Dialog - Before generating marksheet */}
      <Dialog
        open={showStudentInfoDialog}
        onClose={() => setShowStudentInfoDialog(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle sx={{ bgcolor: isDark ? '#1e293b' : '#f8fafc', borderBottom: `1px solid ${isDark ? '#334155' : '#e2e8f0'}` }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <PersonIcon color="primary" />
            <Typography variant="h6" fontWeight={600}>Enter Student Details</Typography>
          </Box>
        </DialogTitle>
        <DialogContent sx={{ mt: 2 }}>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
            <TextField
              label="Student Name"
              fullWidth
              value={studentInfo.name}
              onChange={(e) => setStudentInfo(prev => ({ ...prev, name: e.target.value }))}
              required
            />
            <TextField
              label="Roll Number"
              fullWidth
              value={studentInfo.rollNo}
              onChange={(e) => setStudentInfo(prev => ({ ...prev, rollNo: e.target.value }))}
              required
            />
            <TextField
              label="Class"
              fullWidth
              value={studentInfo.class}
              onChange={(e) => setStudentInfo(prev => ({ ...prev, class: e.target.value }))}
            />
            <TextField
              label="Paper/Exam Name"
              fullWidth
              value={studentInfo.paperName}
              onChange={(e) => setStudentInfo(prev => ({ ...prev, paperName: e.target.value }))}
              required
            />
            <TextField
              label="Subject"
              fullWidth
              value={studentInfo.subject}
              onChange={(e) => setStudentInfo(prev => ({ ...prev, subject: e.target.value }))}
            />
            <TextField
              label="Exam Date"
              type="date"
              fullWidth
              value={studentInfo.examDate}
              onChange={(e) => setStudentInfo(prev => ({ ...prev, examDate: e.target.value }))}
              InputLabelProps={{ shrink: true }}
            />
          </Box>
        </DialogContent>
        <DialogActions sx={{ p: 2, borderTop: `1px solid ${isDark ? '#334155' : '#e2e8f0'}` }}>
          <Button onClick={() => setShowStudentInfoDialog(false)}>Cancel</Button>
          <Button
            variant="contained"
            color="primary"
            onClick={submitPaper}
            disabled={!studentInfo.name || !studentInfo.rollNo || !studentInfo.paperName}
          >
            Generate Marksheet
          </Button>
        </DialogActions>
      </Dialog>

      {/* Marksheet Preview Dialog */}
      <Dialog
        open={marksheetDialogOpen}
        onClose={() => setMarksheetDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle sx={{ 
          bgcolor: isDark ? '#1e293b' : '#f8fafc', 
          borderBottom: `1px solid ${isDark ? '#334155' : '#e2e8f0'}`,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <AssessmentIcon color="primary" />
            <Typography variant="h6" fontWeight={600}>Evaluation Marksheet</Typography>
          </Box>
          <Chip 
            label={generatedMarksheet?.grade || 'N/A'} 
            color={
              generatedMarksheet?.grade === 'A+' || generatedMarksheet?.grade === 'A' ? 'success' :
              generatedMarksheet?.grade === 'B+' || generatedMarksheet?.grade === 'B' ? 'primary' :
              generatedMarksheet?.grade === 'C' ? 'warning' : 'error'
            }
            sx={{ fontWeight: 700, fontSize: '1rem', px: 2 }}
          />
        </DialogTitle>
        <DialogContent sx={{ p: 0 }}>
          {generatedMarksheet && (
            <Box sx={{ p: 3 }}>
              {/* Header Section */}
              <Paper
                elevation={0}
                sx={{
                  p: 3,
                  mb: 3,
                  bgcolor: isDark ? 'rgba(99, 102, 241, 0.1)' : 'rgba(99, 102, 241, 0.05)',
                  border: `1px solid ${isDark ? 'rgba(99, 102, 241, 0.3)' : 'rgba(99, 102, 241, 0.2)'}`,
                  borderRadius: 2,
                }}
              >
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 2 }}>
                  <Box>
                    <Typography variant="h5" fontWeight={700} color="primary.main" gutterBottom>
                      {generatedMarksheet.studentInfo.name}
                    </Typography>
                    <Typography variant="body1" color="text.secondary">
                      Roll No: <strong>{generatedMarksheet.studentInfo.rollNo}</strong>
                    </Typography>
                    <Typography variant="body1" color="text.secondary">
                      Class: <strong>{generatedMarksheet.studentInfo.class || 'N/A'}</strong>
                    </Typography>
                  </Box>
                  <Box sx={{ textAlign: 'right' }}>
                    <Typography variant="body1" color="text.secondary">
                      Paper: <strong>{generatedMarksheet.paperDetails.paperName}</strong>
                    </Typography>
                    <Typography variant="body1" color="text.secondary">
                      Subject: <strong>{generatedMarksheet.paperDetails.subject || 'N/A'}</strong>
                    </Typography>
                    <Typography variant="body1" color="text.secondary">
                      Date: <strong>{new Date(generatedMarksheet.paperDetails.examDate).toLocaleDateString()}</strong>
                    </Typography>
                  </Box>
                </Box>
              </Paper>

              {/* Evaluation Table */}
              <TableContainer component={Paper} elevation={0} sx={{ border: `1px solid ${isDark ? '#334155' : '#e2e8f0'}`, mb: 3 }}>
                <Table>
                  <TableHead>
                    <TableRow sx={{ bgcolor: isDark ? '#334155' : '#f1f5f9' }}>
                      <TableCell sx={{ fontWeight: 700 }}>Question No.</TableCell>
                      <TableCell align="center" sx={{ fontWeight: 700 }}>Out of</TableCell>
                      <TableCell align="center" sx={{ fontWeight: 700 }}>Evaluator Score</TableCell>
                      <TableCell align="center" sx={{ fontWeight: 700 }}>Percentage</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {generatedMarksheet.evaluation.map((item, index) => (
                      <TableRow 
                        key={index}
                        sx={{ 
                          bgcolor: item.awardedMarks === item.maxMarks 
                            ? (isDark ? 'rgba(34, 197, 94, 0.1)' : 'rgba(34, 197, 94, 0.05)')
                            : item.awardedMarks === 0 
                              ? (isDark ? 'rgba(239, 68, 68, 0.1)' : 'rgba(239, 68, 68, 0.05)')
                              : 'transparent'
                        }}
                      >
                        <TableCell>
                          <Chip 
                            label={item.questionNo} 
                            size="small" 
                            sx={{ 
                              bgcolor: '#06b6d4', 
                              color: '#fff', 
                              fontWeight: 600,
                              minWidth: 45,
                            }} 
                          />
                        </TableCell>
                        <TableCell align="center">{item.maxMarks}</TableCell>
                        <TableCell align="center">
                          <Typography 
                            fontWeight={600} 
                            color={
                              item.awardedMarks === item.maxMarks ? 'success.main' :
                              item.awardedMarks >= item.maxMarks * 0.5 ? 'primary.main' :
                              item.awardedMarks > 0 ? 'warning.main' : 'error.main'
                            }
                          >
                            {item.awardedMarks}
                          </Typography>
                        </TableCell>
                        <TableCell align="center">
                          {((item.awardedMarks / item.maxMarks) * 100).toFixed(0)}%
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>

              {/* Summary Section */}
              <Paper
                elevation={0}
                sx={{
                  p: 3,
                  bgcolor: isDark ? '#334155' : '#f8fafc',
                  border: `1px solid ${isDark ? '#475569' : '#e2e8f0'}`,
                  borderRadius: 2,
                }}
              >
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 2 }}>
                  <Box>
                    <Typography variant="body2" color="text.secondary">Total Marks</Typography>
                    <Typography variant="h4" fontWeight={700}>
                      <span style={{ color: '#6366f1' }}>{generatedMarksheet.totalObtainedMarks}</span>
                      <span style={{ color: isDark ? '#94a3b8' : '#64748b' }}> / {generatedMarksheet.totalMaxMarks}</span>
                    </Typography>
                  </Box>
                  <Box>
                    <Typography variant="body2" color="text.secondary">Percentage</Typography>
                    <Typography variant="h4" fontWeight={700} color={
                      parseFloat(generatedMarksheet.percentage) >= 60 ? 'success.main' :
                      parseFloat(generatedMarksheet.percentage) >= 40 ? 'warning.main' : 'error.main'
                    }>
                      {generatedMarksheet.percentage}%
                    </Typography>
                  </Box>
                  <Box>
                    <Typography variant="body2" color="text.secondary">Grade</Typography>
                    <Typography variant="h4" fontWeight={700} color="primary.main">
                      {generatedMarksheet.grade}
                    </Typography>
                  </Box>
                </Box>
                <Divider sx={{ my: 2 }} />
                <Typography variant="caption" color="text.secondary">
                  Evaluated by: {generatedMarksheet.evaluatedBy} | Date: {new Date(generatedMarksheet.evaluatedAt).toLocaleString()}
                </Typography>
              </Paper>
            </Box>
          )}
        </DialogContent>
        <DialogActions sx={{ p: 2, borderTop: `1px solid ${isDark ? '#334155' : '#e2e8f0'}` }}>
          <Button
            variant="outlined"
            color="secondary"
            startIcon={<EmailIcon />}
            onClick={() => {
              // Send via Gmail compose
              const email = 'kunalekare02@gmail.com';
              const studentName = generatedMarksheet?.studentInfo?.name || 'Student';
              const subject = `Evaluation Marksheet - ${studentName} | ${generatedMarksheet?.paperDetails?.paperName || 'Exam'}`;
              
              // Create professional email body
              const evaluationRows = generatedMarksheet?.evaluation?.map(item => 
                `   Q${item.questionNo}:  ${item.awardedMarks} / ${item.maxMarks}  (${((item.awardedMarks / item.maxMarks) * 100).toFixed(0)}%)`
              ).join('\n') || '';
              
              const body = 
`Dear ${studentName},

Please find below your evaluation marksheet for the recently conducted examination.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
          EVALUATION MARKSHEET
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STUDENT INFORMATION
──────────────────────────────────────
   Name:        ${generatedMarksheet?.studentInfo?.name}
   Roll No:     ${generatedMarksheet?.studentInfo?.rollNo}
   Class:       ${generatedMarksheet?.studentInfo?.class || 'N/A'}

EXAMINATION DETAILS
──────────────────────────────────────
   Paper:       ${generatedMarksheet?.paperDetails?.paperName}
   Subject:     ${generatedMarksheet?.paperDetails?.subject || 'N/A'}
   Date:        ${new Date(generatedMarksheet?.paperDetails?.examDate).toLocaleDateString()}

QUESTION-WISE EVALUATION
──────────────────────────────────────
${evaluationRows}

RESULT SUMMARY
──────────────────────────────────────
   Total Marks:    ${generatedMarksheet?.totalObtainedMarks} / ${generatedMarksheet?.totalMaxMarks}
   Percentage:     ${generatedMarksheet?.percentage}%
   Grade:          ${generatedMarksheet?.grade}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

This is an official evaluation report generated by the Answer Evaluation System.

Evaluated by: ${generatedMarksheet?.evaluatedBy}
Date & Time:  ${new Date(generatedMarksheet?.evaluatedAt).toLocaleString()}

If you have any queries regarding this evaluation, please contact your teacher.

Best Regards,
Examination Department`;

              // Open Gmail compose
              const gmailUrl = `https://mail.google.com/mail/?view=cm&fs=1&to=${encodeURIComponent(email)}&su=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
              window.open(gmailUrl, '_blank');
              showSnackbar('Opening Gmail compose...', 'info');
            }}
          >
            Send
          </Button>
          <Button
            variant="outlined"
            onClick={() => {
              // Print functionality
              window.print();
            }}
          >
            Print
          </Button>
          <Button
            variant="contained"
            color="primary"
            onClick={() => {
              setMarksheetDialogOpen(false);
              showSnackbar('Marksheet saved successfully!', 'success');
            }}
          >
            Done
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default ManualChecking;
