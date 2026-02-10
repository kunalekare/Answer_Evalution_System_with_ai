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
 */

import React, { useState, useRef, useEffect, useCallback } from 'react';
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
} from '@mui/material';
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
  const canvasRef = useRef(null);
  const containerRef = useRef(null);
  const fileInputRef = useRef(null);

  // State management
  const [currentTool, setCurrentTool] = useState(TOOLS.SELECT);
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

  // Calculate total score
  const totalMaxMarks = questions.reduce((sum, q) => sum + q.maxMarks, 0);
  const totalAwardedMarks = questions.reduce((sum, q) => sum + (q.awardedMarks || 0), 0);

  // Handle file upload
  const handleFileUpload = useCallback((event) => {
    const files = Array.from(event.target.files);
    if (files.length === 0) return;

    setLoading(true);
    const imagePromises = files.map((file) => {
      return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = (e) => resolve(e.target.result);
        reader.onerror = reject;
        reader.readAsDataURL(file);
      });
    });

    Promise.all(imagePromises)
      .then((images) => {
        setUploadedImages(images);
        setCurrentImage(images[0]);
        setTotalPages(images.length);
        setCurrentPage(1);
        setVisitedPages(new Set([1]));
        setLoading(false);
        showSnackbar('Answer sheets uploaded successfully!', 'success');
      })
      .catch((error) => {
        console.error('Error loading images:', error);
        setLoading(false);
        showSnackbar('Error loading images', 'error');
      });
  }, []);

  // Show snackbar notification
  const showSnackbar = (message, severity = 'success') => {
    setSnackbar({ open: true, message, severity });
  };

  // Handle page navigation
  const handlePageChange = (page) => {
    if (page >= 1 && page <= totalPages) {
      setCurrentPage(page);
      setVisitedPages((prev) => new Set([...prev, page]));
      if (uploadedImages.length > 0) {
        setCurrentImage(uploadedImages[page - 1]);
      }
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

  // Clear all annotations
  const handleClearAnnotations = () => {
    const canvas = canvasRef.current;
    if (canvas) {
      const ctx = canvas.getContext('2d');
      ctx.clearRect(0, 0, canvas.width, canvas.height);
    }
    setAnnotations([]);
    showSnackbar('All annotations cleared', 'info');
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
      submitPaper();
    }
  };

  const submitPaper = () => {
    showSnackbar('Paper submitted successfully!', 'success');
    setConfirmDialog({ open: false, type: '', title: '', message: '' });
    // In real app, save to backend
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

  // Number button for quick scores
  const ScoreButton = ({ value, label, color, onClick }) => (
    <Box
      onClick={onClick}
      sx={{
        width: 36,
        height: 36,
        borderRadius: '50%',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        bgcolor: color,
        color: '#fff',
        fontWeight: 'bold',
        cursor: 'pointer',
        fontSize: '0.85rem',
        transition: 'transform 0.2s',
        '&:hover': {
          transform: 'scale(1.1)',
        },
      }}
    >
      {label}
    </Box>
  );

  return (
    <Box
      ref={containerRef}
      sx={{
        display: 'flex',
        height: 'calc(100vh - 64px)',
        bgcolor: '#f0f2f5',
        overflow: 'hidden',
      }}
    >
      {/* Left Panel - Annotation Tools */}
      <Paper
        elevation={3}
        sx={{
          width: 70,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          py: 2,
          gap: 1,
          borderRadius: 0,
          bgcolor: '#1e293b',
        }}
      >
        <Typography
          variant="caption"
          sx={{
            color: '#94a3b8',
            mb: 1,
            writingMode: 'vertical-rl',
            textOrientation: 'mixed',
            transform: 'rotate(180deg)',
            letterSpacing: 1,
          }}
        >
          Annotation
        </Typography>

        {/* Score buttons */}
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5, mb: 1 }}>
          <ScoreButton value={0} label="0" color="#374151" onClick={() => {}} />
          <ScoreButton value={0.25} label="¼" color="#374151" onClick={() => {}} />
          <ScoreButton value={0.5} label="½" color="#374151" onClick={() => {}} />
          <ScoreButton value={1} label="1" color="#374151" onClick={() => {}} />
          <ScoreButton value={2} label="2" color="#10b981" onClick={() => {}} />
          <ScoreButton value={3} label="3" color="#10b981" onClick={() => {}} />
          <ScoreButton value={4} label="4" color="#10b981" onClick={() => {}} />
          <ScoreButton value={5} label="5" color="#10b981" onClick={() => {}} />
          <ScoreButton value={6} label="6" color="#10b981" onClick={() => {}} />
          <ScoreButton value={7} label="7" color="#3b82f6" onClick={() => {}} />
          <ScoreButton value={8} label="8" color="#3b82f6" onClick={() => {}} />
          <ScoreButton value={9} label="9" color="#3b82f6" onClick={() => {}} />
          <ScoreButton value={10} label="10" color="#3b82f6" onClick={() => {}} />
        </Box>

        <Divider sx={{ width: '70%', bgcolor: '#475569' }} />

        {/* Tick/Cross tools */}
        <ToolButton tool={TOOLS.TICK} icon={<CheckIcon />} label="Tick (Correct)" color={COLORS.GREEN} />
        <ToolButton tool={TOOLS.CROSS} icon={<CloseIcon />} label="Cross (Wrong)" color={COLORS.RED} />

        <Divider sx={{ width: '70%', bgcolor: '#475569' }} />

        {/* Show/Hide annotations */}
        <Tooltip title={showAnnotations ? "Hide Annotations" : "Show Annotations"} placement="right">
          <IconButton
            onClick={() => setShowAnnotations(!showAnnotations)}
            sx={{ color: showAnnotations ? '#22c55e' : '#94a3b8' }}
          >
            {showAnnotations ? <VisibilityIcon /> : <VisibilityOffIcon />}
          </IconButton>
        </Tooltip>

        <Tooltip title="Clear Annotations" placement="right">
          <IconButton onClick={() => setConfirmDialog({ open: true, type: 'clear', title: 'Clear Annotations', message: 'Clear all annotations on this page?' })} sx={{ color: '#94a3b8' }}>
            <RefreshIcon />
          </IconButton>
        </Tooltip>

        <Divider sx={{ width: '70%', bgcolor: '#475569' }} />

        {/* Drawing tools */}
        <ToolButton tool={TOOLS.PEN} icon={<PenIcon />} label="Pen Tool" color={COLORS.BLACK} />
        <ToolButton tool={TOOLS.ERASER} icon={<EraserIcon />} label="Eraser" color="#94a3b8" />

        <Divider sx={{ width: '70%', bgcolor: '#475569' }} />

        {/* Highlight/Underline */}
        <ToolButton tool={TOOLS.UNDERLINE} icon={<UnderlineIcon />} label="Underline" color={COLORS.RED} />
        <ToolButton tool={TOOLS.HIGHLIGHT} icon={<HighlightIcon />} label="Highlight" color={COLORS.YELLOW} />
        <ToolButton tool={TOOLS.COMMENT} icon={<CommentIcon />} label="Add Comment" color={COLORS.BLUE} />

        <Box sx={{ flexGrow: 1 }} />

        {/* Help and additional tools */}
        <Tooltip title="Help" placement="right">
          <IconButton sx={{ color: '#94a3b8' }}>
            <HelpIcon />
          </IconButton>
        </Tooltip>

        <Tooltip title="Undo" placement="right">
          <IconButton onClick={handleUndo} sx={{ color: '#94a3b8' }}>
            <UndoIcon />
          </IconButton>
        </Tooltip>

        <Tooltip title="Delete" placement="right">
          <IconButton onClick={() => setConfirmDialog({ open: true, type: 'clear', title: 'Clear All', message: 'Delete all annotations?' })} sx={{ color: '#ef4444' }}>
            <DeleteIcon />
          </IconButton>
        </Tooltip>

        <Divider sx={{ width: '70%', bgcolor: '#475569', my: 1 }} />

        {/* File operations */}
        <Tooltip title="Upload Answer Sheet" placement="right">
          <IconButton onClick={() => fileInputRef.current?.click()} sx={{ color: '#6366f1' }}>
            <UploadIcon />
          </IconButton>
        </Tooltip>

        <Tooltip title="Save Progress" placement="right">
          <IconButton sx={{ color: '#22c55e' }}>
            <SaveIcon />
          </IconButton>
        </Tooltip>

        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileUpload}
          accept="image/*"
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
          bgcolor: '#334155',
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
            bgcolor: '#1e293b',
            borderBottom: '1px solid #475569',
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
                src={currentImage}
                alt={`Answer sheet page ${currentPage}`}
                style={{
                  maxWidth: '100%',
                  maxHeight: '100%',
                  borderRadius: 8,
                  boxShadow: '0 4px 20px rgba(0,0,0,0.3)',
                }}
              />
              <canvas
                ref={canvasRef}
                width={800}
                height={1000}
                style={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  width: '100%',
                  height: '100%',
                  cursor: currentTool === TOOLS.SELECT ? 'default' : 'crosshair',
                  opacity: showAnnotations ? 1 : 0,
                }}
                onMouseDown={startDrawing}
                onMouseMove={draw}
                onMouseUp={stopDrawing}
                onMouseLeave={stopDrawing}
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
            bgcolor: '#1e293b',
            borderTop: '1px solid #475569',
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
          bgcolor: '#fff',
        }}
      >
        {/* Questions header */}
        <Box
          sx={{
            p: 2,
            bgcolor: '#f1f5f9',
            borderBottom: '1px solid #e2e8f0',
          }}
        >
          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell sx={{ fontWeight: 700, color: '#1e293b' }}>Questions</TableCell>
                  <TableCell align="center" sx={{ fontWeight: 700, color: '#1e293b' }}>Out of</TableCell>
                  <TableCell align="center" sx={{ fontWeight: 700, color: '#1e293b' }}>Evaluator Score</TableCell>
                </TableRow>
              </TableHead>
            </Table>
          </TableContainer>
        </Box>

        {/* Questions list */}
        <Box sx={{ flex: 1, overflow: 'auto', p: 1 }}>
          {questions.map((question) => (
            <Box
              key={question.id}
              sx={{
                display: 'flex',
                alignItems: 'center',
                gap: 1,
                py: 1.5,
                px: 1,
                borderBottom: '1px solid #e2e8f0',
                '&:hover': {
                  bgcolor: '#f8fafc',
                },
              }}
            >
              <Chip
                label={question.label}
                sx={{
                  minWidth: 48,
                  bgcolor: '#06b6d4',
                  color: '#fff',
                  fontWeight: 600,
                }}
              />
              <Typography
                sx={{
                  flex: 1,
                  textAlign: 'center',
                  color: '#64748b',
                }}
              >
                {question.maxMarks}
              </Typography>
              <TextField
                type="number"
                size="small"
                value={question.awardedMarks ?? ''}
                onChange={(e) => handleMarksChange(question.id, e.target.value)}
                inputProps={{
                  min: 0,
                  max: question.maxMarks,
                  style: { textAlign: 'center', fontWeight: 600 },
                }}
                sx={{
                  width: 70,
                  '& .MuiOutlinedInput-root': {
                    bgcolor: question.awardedMarks !== null ? alpha('#22c55e', 0.1) : '#fff',
                    '& fieldset': {
                      borderColor: question.awardedMarks !== null ? '#22c55e' : '#e2e8f0',
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
            bgcolor: '#f1f5f9',
            borderTop: '1px solid #e2e8f0',
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
            borderTop: '1px solid #e2e8f0',
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
            bgcolor: '#f8fafc',
            borderTop: '1px solid #e2e8f0',
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
            borderTop: '1px solid #e2e8f0',
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
              else if (confirmDialog.type === 'warning') submitPaper();
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
    </Box>
  );
}

export default ManualChecking;
