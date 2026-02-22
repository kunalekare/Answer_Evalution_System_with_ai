/**
 * Evaluate Page
 * ==============
 * Main evaluation interface with file upload and text input.
 */

import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Stepper,
  Step,
  StepLabel,
  Paper,
  Chip,
  CircularProgress,
  Alert,
  Divider,
  IconButton,
  Collapse,
  Switch,
  FormControlLabel,
  Skeleton,
  useTheme,
} from '@mui/material';
import { useThemeMode } from '../context/ThemeContext';
import {
  CloudUpload as UploadIcon,
  Image as ImageIcon,
  Description as DocumentIcon,
  Delete as DeleteIcon,
  CheckCircle as CheckIcon,
  ArrowForward as ArrowForwardIcon,
  ArrowBack as ArrowBackIcon,
  Psychology as AIIcon,
  ExpandMore as ExpandMoreIcon,
  Visibility as PreviewIcon,
  TextFields as TextIcon,
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import toast from 'react-hot-toast';

import { evaluateText, uploadAndEvaluate, extractTextFromUpload } from '../services/api';
import axios from 'axios';

// Motion components
const MotionBox = motion(Box);

// Steps for the evaluation process
const steps = ['Upload Files', 'Preview Extracted Text', 'Configure Settings', 'Review & Evaluate'];

// Allowed file types
const ALLOWED_TYPES = ['image/png', 'image/jpeg', 'image/jpg', 'image/tiff', 'image/bmp', 'image/jfif', 'image/webp', 'image/gif', 'application/pdf'];
const ALLOWED_EXTENSIONS = '.png,.jpg,.jpeg,.tiff,.bmp,.pdf,.jfif,.webp,.gif';

// API base URL
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function Evaluate() {
  const navigate = useNavigate();
  const theme = useTheme();
  const { isDark } = useThemeMode();
  const [activeStep, setActiveStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [extracting, setExtracting] = useState(false);
  const [error, setError] = useState(null);
  
  // File input refs
  const modelInputRef = useRef(null);
  const studentInputRef = useRef(null);
  
  // Form state
  const [modelAnswerFile, setModelAnswerFile] = useState(null);
  const [studentAnswerFile, setStudentAnswerFile] = useState(null);
  const [useTextInput, setUseTextInput] = useState(true);  // Default to text input for free hosting
  const [modelAnswerText, setModelAnswerText] = useState('');
  const [studentAnswerText, setStudentAnswerText] = useState('');
  const [questionType, setQuestionType] = useState('descriptive');
  const [maxMarks, setMaxMarks] = useState(10);
  const [subject, setSubject] = useState('');
  const [includeDiagram, setIncludeDiagram] = useState(false);
  const [advancedOpen, setAdvancedOpen] = useState(false);
  
  // Extracted text state
  const [evaluationId, setEvaluationId] = useState(null);
  const [extractedModelText, setExtractedModelText] = useState('');
  const [extractedStudentText, setExtractedStudentText] = useState('');
  const [modelWordCount, setModelWordCount] = useState(0);
  const [studentWordCount, setStudentWordCount] = useState(0);
  
  // Drag states
  const [modelDragActive, setModelDragActive] = useState(false);
  const [studentDragActive, setStudentDragActive] = useState(false);

  // Validate file type
  const isValidFileType = (file) => {
    return ALLOWED_TYPES.includes(file.type) || 
           file.name.match(/\.(png|jpg|jpeg|tiff|bmp|pdf|jfif|webp|gif)$/i);
  };

  // Handle model file selection
  const handleModelFileChange = (event) => {
    const file = event.target.files?.[0];
    if (file) {
      if (isValidFileType(file)) {
        console.log('Model file selected:', file.name, file.type, file.size);
        setModelAnswerFile(file);
        toast.success(`Model answer uploaded: ${file.name}`);
      } else {
        toast.error('Invalid file type. Please upload PDF, PNG, JPG, JPEG, JFIF, WEBP, TIFF, or BMP files.');
      }
    }
    // Reset input so same file can be selected again
    event.target.value = '';
  };

  // Handle student file selection
  const handleStudentFileChange = (event) => {
    const file = event.target.files?.[0];
    if (file) {
      if (isValidFileType(file)) {
        console.log('Student file selected:', file.name, file.type, file.size);
        setStudentAnswerFile(file);
        toast.success(`Student answer uploaded: ${file.name}`);
      } else {
        toast.error('Invalid file type. Please upload PDF, PNG, JPG, JPEG, JFIF, WEBP, TIFF, or BMP files.');
      }
    }
    // Reset input so same file can be selected again
    event.target.value = '';
  };

  // Handle drag events for model
  const handleModelDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setModelDragActive(true);
    } else if (e.type === 'dragleave') {
      setModelDragActive(false);
    }
  };

  const handleModelDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setModelDragActive(false);
    
    const file = e.dataTransfer.files?.[0];
    if (file) {
      if (isValidFileType(file)) {
        console.log('Model file dropped:', file.name, file.type, file.size);
        setModelAnswerFile(file);
        toast.success(`Model answer uploaded: ${file.name}`);
      } else {
        toast.error('Invalid file type. Please upload PDF, PNG, JPG, JPEG, JFIF, WEBP, TIFF, or BMP files.');
      }
    }
  };

  // Handle drag events for student
  const handleStudentDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setStudentDragActive(true);
    } else if (e.type === 'dragleave') {
      setStudentDragActive(false);
    }
  };

  const handleStudentDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setStudentDragActive(false);
    
    const file = e.dataTransfer.files?.[0];
    if (file) {
      if (isValidFileType(file)) {
        console.log('Student file dropped:', file.name, file.type, file.size);
        setStudentAnswerFile(file);
        toast.success(`Student answer uploaded: ${file.name}`);
      } else {
        toast.error('Invalid file type. Please upload PDF, PNG, JPG, JPEG, JFIF, WEBP, TIFF, or BMP files.');
      }
    }
  };

  const handleNext = async () => {
    if (activeStep === 0) {
      // Validate step 1
      if (useTextInput) {
        if (!modelAnswerText.trim() || !studentAnswerText.trim()) {
          toast.error('Please enter both model and student answers');
          return;
        }
        // For text input, skip to configure step
        setExtractedModelText(modelAnswerText);
        setExtractedStudentText(studentAnswerText);
        setModelWordCount(modelAnswerText.split(/\s+/).length);
        setStudentWordCount(studentAnswerText.split(/\s+/).length);
        setActiveStep(2); // Skip to configure step
        return;
      } else {
        if (!modelAnswerFile) {
          toast.error('Please upload a model answer');
          return;
        }
        if (!studentAnswerFile) {
          toast.error('Please upload a student answer');
          return;
        }
        
        // Upload files and extract text
        setExtracting(true);
        setError(null);
        
        try {
          // Step 1: Upload files
          const formData = new FormData();
          formData.append('model_answer', modelAnswerFile);
          formData.append('student_answer', studentAnswerFile);
          formData.append('question_type', questionType);
          formData.append('max_marks', maxMarks.toString());
          if (subject) {
            formData.append('subject', subject);
          }
          
          toast.loading('Uploading files...', { id: 'upload' });
          
          const uploadResponse = await axios.post(`${API_BASE_URL}/api/v1/upload/`, formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
            timeout: 60000,
          });
          
          if (!uploadResponse.data.success) {
            throw new Error(uploadResponse.data.message || 'Upload failed');
          }
          
          const evalId = uploadResponse.data.data.evaluation_id;
          setEvaluationId(evalId);
          
          toast.success('Files uploaded!', { id: 'upload' });
          toast.loading('Extracting text with OCR...', { id: 'extract' });
          
          // Step 2: Extract text
          const extractResponse = await axios.get(`${API_BASE_URL}/api/v1/upload/${evalId}/extract-text`, {
            timeout: 180000, // 3 minutes for OCR
          });
          
          if (extractResponse.data.success) {
            const data = extractResponse.data.data;
            
            if (data.model_answer?.text) {
              setExtractedModelText(data.model_answer.text);
              setModelWordCount(data.model_answer.word_count || 0);
            } else if (data.model_answer?.error) {
              setExtractedModelText(`Error: ${data.model_answer.error}`);
            }
            
            if (data.student_answer?.text) {
              setExtractedStudentText(data.student_answer.text);
              setStudentWordCount(data.student_answer.word_count || 0);
            } else if (data.student_answer?.error) {
              setExtractedStudentText(`Error: ${data.student_answer.error}`);
            }
            
            toast.success('Text extracted successfully!', { id: 'extract' });
          } else {
            throw new Error('Failed to extract text');
          }
          
          setActiveStep(1); // Move to preview step
          
        } catch (err) {
          console.error('Upload/Extract error:', err);
          toast.dismiss('upload');
          toast.dismiss('extract');
          toast.error(err.response?.data?.detail || err.message || 'Failed to process files');
          setError(err.message);
        } finally {
          setExtracting(false);
        }
        return;
      }
    }
    setActiveStep((prev) => prev + 1);
  };

  const handleBack = () => {
    setActiveStep((prev) => prev - 1);
  };

  const handleEvaluate = async () => {
    setLoading(true);
    setError(null);

    try {
      let result;
      
      if (useTextInput) {
        // Use text-based evaluation
        result = await evaluateText({
          model_answer: modelAnswerText,
          student_answer: studentAnswerText,
          question_type: questionType,
          max_marks: maxMarks,
        });
      } else {
        // Files already uploaded, just trigger evaluation
        toast.loading('Running AI evaluation...', { id: 'eval' });
        
        const evalResponse = await axios.post(`${API_BASE_URL}/api/v1/evaluate/`, {
          evaluation_id: evaluationId,
          question_type: questionType,
          max_marks: maxMarks,
          include_diagram: includeDiagram,
        }, {
          timeout: 120000,
        });
        
        result = evalResponse.data;
        toast.dismiss('eval');
      }

      toast.success('Evaluation complete!');
      navigate(`/results/${result.evaluation_id}`, { state: { result } });
    } catch (err) {
      console.error('Evaluation error:', err);
      toast.dismiss('eval');
      setError(err.response?.data?.detail || err.message || 'Evaluation failed. Please try again.');
      toast.error('Evaluation failed');
    } finally {
      setLoading(false);
    }
  };

  // File Preview Component
  const FilePreview = ({ file, onRemove, showRemove = true }) => (
    <Paper
      elevation={0}
      sx={{
        p: 2,
        display: 'flex',
        alignItems: 'center',
        gap: 2,
        bgcolor: '#e8f5e9',
        border: '2px solid',
        borderColor: '#4caf50',
        borderRadius: 2,
      }}
    >
      <CheckIcon sx={{ color: '#4caf50' }} />
      {file.type?.startsWith('image/') ? (
        <ImageIcon sx={{ color: '#4caf50' }} />
      ) : (
        <DocumentIcon sx={{ color: '#4caf50' }} />
      )}
      <Box sx={{ flex: 1 }}>
        <Typography variant="body2" fontWeight={600} color="success.dark">
          {file.name}
        </Typography>
        <Typography variant="caption" color="text.secondary">
          {(file.size / 1024).toFixed(1)} KB
        </Typography>
      </Box>
      {showRemove && (
        <IconButton size="small" onClick={onRemove} color="error">
          <DeleteIcon fontSize="small" />
        </IconButton>
      )}
    </Paper>
  );

  // Upload Zone Component
  const UploadZone = ({ 
    label, 
    file, 
    onRemove, 
    inputRef, 
    onFileChange, 
    isDragActive, 
    onDragEnter, 
    onDragLeave, 
    onDragOver, 
    onDrop 
  }) => {
    const handleClick = () => {
      console.log('Upload zone clicked, triggering file input...');
      if (inputRef.current) {
        inputRef.current.click();
      }
    };

    return (
      <Box>
        <Typography variant="subtitle2" fontWeight={600} gutterBottom>
          {label}
        </Typography>
        
        {/* Hidden file input */}
        <input
          type="file"
          ref={inputRef}
          onChange={onFileChange}
          accept={ALLOWED_EXTENSIONS}
          style={{ display: 'none' }}
        />
        
        {file ? (
          <FilePreview file={file} onRemove={onRemove} />
        ) : (
          <Paper
            elevation={0}
            onClick={handleClick}
            onDragEnter={onDragEnter}
            onDragOver={onDragOver}
            onDragLeave={onDragLeave}
            onDrop={onDrop}
            sx={{
              p: { xs: 2.5, md: 4 },
              textAlign: 'center',
              cursor: 'pointer',
              border: '2px dashed',
              borderColor: isDragActive ? 'primary.main' : isDark ? 'grey.600' : 'grey.400',
              bgcolor: isDragActive ? (isDark ? 'rgba(99, 102, 241, 0.1)' : 'primary.50') : (isDark ? 'rgba(255,255,255,0.03)' : 'grey.50'),
              borderRadius: 2,
              transition: 'all 0.2s ease',
              '&:hover': {
                borderColor: 'primary.main',
                bgcolor: isDark ? 'rgba(99, 102, 241, 0.1)' : 'primary.50',
                transform: 'scale(1.01)',
              },
            }}
          >
            <UploadIcon
              sx={{
                fontSize: { xs: 40, md: 56 },
                color: isDragActive ? 'primary.main' : isDark ? 'grey.400' : 'grey.500',
                mb: { xs: 1, md: 2 },
              }}
            />
            <Typography variant="h6" fontWeight={500} gutterBottom sx={{ fontSize: { xs: '0.9rem', md: '1.25rem' }, color: isDark ? 'grey.300' : 'text.primary' }}>
              {isDragActive ? 'Drop the file here!' : 'Drag & drop file here'}
            </Typography>
            <Typography variant="body1" color="primary" fontWeight={500} sx={{ mb: { xs: 1, md: 2 }, fontSize: { xs: '0.8rem', md: '1rem' } }}>
              or click to browse
            </Typography>
            <Box sx={{ mt: { xs: 1, md: 2 } }}>
              <Chip label="PDF" size="small" variant={isDark ? 'outlined' : 'filled'} sx={{ mr: 0.5, mb: 0.5, fontSize: { xs: '0.65rem', md: '0.8rem' } }} />
              <Chip label="PNG" size="small" variant={isDark ? 'outlined' : 'filled'} sx={{ mr: 0.5, mb: 0.5, fontSize: { xs: '0.65rem', md: '0.8rem' } }} />
              <Chip label="JPG" size="small" variant={isDark ? 'outlined' : 'filled'} sx={{ mr: 0.5, mb: 0.5, fontSize: { xs: '0.65rem', md: '0.8rem' } }} />
              <Chip label="TIFF" size="small" variant={isDark ? 'outlined' : 'filled'} sx={{ mb: 0.5, fontSize: { xs: '0.65rem', md: '0.8rem' } }} />
            </Box>
          </Paper>
        )}
      </Box>
    );
  };

  // Step content
  const renderStepContent = () => {
    switch (activeStep) {
      case 0:
        return (
          <MotionBox
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
          >
            <Box sx={{ mb: 3 }}>
              <FormControlLabel
                control={
                  <Switch
                    checked={useTextInput}
                    onChange={(e) => setUseTextInput(e.target.checked)}
                    color="primary"
                  />
                }
                label="Use text input instead of file upload"
              />
              {!useTextInput && (
                <Alert severity="warning" sx={{ mt: 2 }}>
                  <strong>Note:</strong> File upload with OCR requires significant server resources. 
                  If you experience errors, please use <strong>Text Input mode</strong> instead.
                </Alert>
              )}
            </Box>

            {useTextInput ? (
              <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" fontWeight={600} gutterBottom>
                    Model Answer (Expected Answer)
                  </Typography>
                  <TextField
                    fullWidth
                    multiline
                    rows={10}
                    placeholder="Enter the correct/expected answer here..."
                    value={modelAnswerText}
                    onChange={(e) => setModelAnswerText(e.target.value)}
                    variant="outlined"
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" fontWeight={600} gutterBottom>
                    Student Answer
                  </Typography>
                  <TextField
                    fullWidth
                    multiline
                    rows={10}
                    placeholder="Enter the student's answer here..."
                    value={studentAnswerText}
                    onChange={(e) => setStudentAnswerText(e.target.value)}
                    variant="outlined"
                  />
                </Grid>
              </Grid>
            ) : (
              <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                  <UploadZone
                    label="Model Answer (Answer Key)"
                    file={modelAnswerFile}
                    onRemove={() => setModelAnswerFile(null)}
                    inputRef={modelInputRef}
                    onFileChange={handleModelFileChange}
                    isDragActive={modelDragActive}
                    onDragEnter={handleModelDrag}
                    onDragOver={handleModelDrag}
                    onDragLeave={handleModelDrag}
                    onDrop={handleModelDrop}
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <UploadZone
                    label="Student Answer"
                    file={studentAnswerFile}
                    onRemove={() => setStudentAnswerFile(null)}
                    inputRef={studentInputRef}
                    onFileChange={handleStudentFileChange}
                    isDragActive={studentDragActive}
                    onDragEnter={handleStudentDrag}
                    onDragOver={handleStudentDrag}
                    onDragLeave={handleStudentDrag}
                    onDrop={handleStudentDrop}
                  />
                </Grid>
              </Grid>
            )}
          </MotionBox>
        );

      case 1:
        // Preview Extracted Text step
        return (
          <MotionBox
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
          >
            <Alert severity="info" sx={{ mb: 3 }}>
              <Typography variant="body2">
                Review the extracted text below. This is what the AI will use to evaluate the answers.
                If the text looks incorrect, go back and upload clearer images.
              </Typography>
            </Alert>
            
            <Grid container spacing={3}>
              {/* Model Answer Text */}
              <Grid item xs={12} md={6}>
                <Paper 
                  elevation={0} 
                  sx={{ 
                    p: 3, 
                    bgcolor: isDark ? 'rgba(34, 197, 94, 0.1)' : 'success.50', 
                    border: '1px solid',
                    borderColor: isDark ? 'rgba(34, 197, 94, 0.3)' : 'success.200',
                    borderRadius: 2,
                    height: '100%'
                  }}
                >
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                    <TextIcon color="success" />
                    <Typography variant="h6" fontWeight={600} color={isDark ? 'success.light' : 'success.dark'}>
                      Model Answer (Extracted)
                    </Typography>
                  </Box>
                  <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
                    <Chip 
                      label={`${modelWordCount} words`} 
                      size="small" 
                      color="success" 
                      variant="outlined"
                    />
                    <Chip 
                      label={`${extractedModelText.length} characters`} 
                      size="small" 
                      variant="outlined"
                    />
                  </Box>
                  <TextField
                    fullWidth
                    multiline
                    rows={12}
                    value={extractedModelText}
                    onChange={(e) => {
                      setExtractedModelText(e.target.value);
                      setModelWordCount(e.target.value.split(/\s+/).filter(w => w).length);
                    }}
                    variant="outlined"
                    sx={{ 
                      bgcolor: isDark ? 'rgba(255,255,255,0.05)' : 'white',
                      '& .MuiOutlinedInput-root': {
                        fontFamily: 'monospace',
                        fontSize: '0.9rem',
                      }
                    }}
                    placeholder="Extracted text will appear here..."
                  />
                </Paper>
              </Grid>
              
              {/* Student Answer Text */}
              <Grid item xs={12} md={6}>
                <Paper 
                  elevation={0} 
                  sx={{ 
                    p: 3, 
                    bgcolor: isDark ? 'rgba(99, 102, 241, 0.1)' : 'primary.50', 
                    border: '1px solid',
                    borderColor: isDark ? 'rgba(99, 102, 241, 0.3)' : 'primary.200',
                    borderRadius: 2,
                    height: '100%'
                  }}
                >
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                    <TextIcon color="primary" />
                    <Typography variant="h6" fontWeight={600} color={isDark ? 'primary.light' : 'primary.dark'}>
                      Student Answer (Extracted)
                    </Typography>
                  </Box>
                  <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
                    <Chip 
                      label={`${studentWordCount} words`} 
                      size="small" 
                      color="primary" 
                      variant="outlined"
                    />
                    <Chip 
                      label={`${extractedStudentText.length} characters`} 
                      size="small" 
                      variant="outlined"
                    />
                  </Box>
                  <TextField
                    fullWidth
                    multiline
                    rows={12}
                    value={extractedStudentText}
                    onChange={(e) => {
                      setExtractedStudentText(e.target.value);
                      setStudentWordCount(e.target.value.split(/\s+/).filter(w => w).length);
                    }}
                    variant="outlined"
                    sx={{ 
                      bgcolor: isDark ? 'rgba(255,255,255,0.05)' : 'white',
                      '& .MuiOutlinedInput-root': {
                        fontFamily: 'monospace',
                        fontSize: '0.9rem',
                      }
                    }}
                    placeholder="Extracted text will appear here..."
                  />
                </Paper>
              </Grid>
            </Grid>
            
            <Alert severity="success" sx={{ mt: 3 }} icon={<CheckIcon />}>
              <Typography variant="body2">
                <strong>Text extraction complete!</strong> You can edit the text above if needed before proceeding to evaluation.
              </Typography>
            </Alert>
          </MotionBox>
        );

      case 2:
        return (
          <MotionBox
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
          >
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <InputLabel>Question Type</InputLabel>
                  <Select
                    value={questionType}
                    label="Question Type"
                    onChange={(e) => setQuestionType(e.target.value)}
                  >
                    <MenuItem value="factual">Factual (Keywords Matter)</MenuItem>
                    <MenuItem value="descriptive">Descriptive (Understanding Matters)</MenuItem>
                    <MenuItem value="diagram">Diagram-based</MenuItem>
                    <MenuItem value="mixed">Mixed</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  type="number"
                  label="Maximum Marks"
                  value={maxMarks}
                  onChange={(e) => setMaxMarks(parseInt(e.target.value) || 10)}
                  inputProps={{ min: 1, max: 100 }}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Subject (Optional)"
                  value={subject}
                  onChange={(e) => setSubject(e.target.value)}
                  placeholder="e.g., Biology, Physics, Chemistry"
                />
              </Grid>

              {/* Advanced Options */}
              <Grid item xs={12}>
                <Divider sx={{ my: 2 }} />
                <Button
                  onClick={() => setAdvancedOpen(!advancedOpen)}
                  endIcon={
                    <ExpandMoreIcon
                      sx={{
                        transform: advancedOpen ? 'rotate(180deg)' : 'rotate(0deg)',
                        transition: 'transform 0.2s',
                      }}
                    />
                  }
                  sx={{ mb: 2 }}
                >
                  Advanced Options
                </Button>
                <Collapse in={advancedOpen}>
                  <Paper elevation={0} sx={{ p: 3, bgcolor: 'grey.50', borderRadius: 2 }}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={includeDiagram}
                          onChange={(e) => setIncludeDiagram(e.target.checked)}
                        />
                      }
                      label="Include Diagram Evaluation"
                    />
                    <Typography variant="caption" display="block" color="text.secondary">
                      Enable this if the answer contains diagrams that need to be evaluated.
                    </Typography>
                  </Paper>
                </Collapse>
              </Grid>
            </Grid>
          </MotionBox>
        );

      case 3:
        return (
          <MotionBox
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
          >
            <Paper elevation={0} sx={{ p: 3, bgcolor: 'grey.50', borderRadius: 2, mb: 3 }}>
              <Typography variant="h6" fontWeight={600} gutterBottom>
                Evaluation Summary
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <Typography variant="body2" color="text.secondary">
                    Input Method
                  </Typography>
                  <Typography variant="body1" fontWeight={500}>
                    {useTextInput ? 'Text Input' : 'File Upload'}
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="body2" color="text.secondary">
                    Question Type
                  </Typography>
                  <Typography variant="body1" fontWeight={500} sx={{ textTransform: 'capitalize' }}>
                    {questionType}
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="body2" color="text.secondary">
                    Maximum Marks
                  </Typography>
                  <Typography variant="body1" fontWeight={500}>
                    {maxMarks}
                  </Typography>
                </Grid>
                {subject && (
                  <Grid item xs={12} sm={6}>
                    <Typography variant="body2" color="text.secondary">
                      Subject
                    </Typography>
                    <Typography variant="body1" fontWeight={500}>
                      {subject}
                    </Typography>
                  </Grid>
                )}
                <Grid item xs={12} sm={6}>
                  <Typography variant="body2" color="text.secondary">
                    Diagram Evaluation
                  </Typography>
                  <Typography variant="body1" fontWeight={500}>
                    {includeDiagram ? 'Enabled' : 'Disabled'}
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="body2" color="text.secondary">
                    Model Answer Words
                  </Typography>
                  <Typography variant="body1" fontWeight={500}>
                    {modelWordCount} words
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="body2" color="text.secondary">
                    Student Answer Words
                  </Typography>
                  <Typography variant="body1" fontWeight={500}>
                    {studentWordCount} words
                  </Typography>
                </Grid>
              </Grid>
            </Paper>

            {!useTextInput && (
              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" fontWeight={600} gutterBottom>
                    Model Answer File
                  </Typography>
                  {modelAnswerFile && (
                    <FilePreview file={modelAnswerFile} onRemove={() => {}} showRemove={false} />
                  )}
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" fontWeight={600} gutterBottom>
                    Student Answer File
                  </Typography>
                  {studentAnswerFile && (
                    <FilePreview file={studentAnswerFile} onRemove={() => {}} showRemove={false} />
                  )}
                </Grid>
              </Grid>
            )}

            {error && (
              <Alert severity="error" sx={{ mt: 2 }}>
                {error}
              </Alert>
            )}
          </MotionBox>
        );

      default:
        return null;
    }
  };

  return (
    <Box>
      <Typography variant="h4" fontWeight={700} gutterBottom sx={{ fontSize: { xs: '1.5rem', md: '2rem' } }}>
        Evaluate Answer
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: { xs: 2, md: 4 }, fontSize: { xs: '0.875rem', md: '1rem' } }}>
        Upload or enter answers to get AI-powered evaluation with detailed feedback.
      </Typography>

      {/* Stepper */}
      <Card sx={{ mb: { xs: 2, md: 4 }, borderRadius: { xs: 2, md: 3 } }}>
        <CardContent sx={{ py: { xs: 2, md: 3 }, px: { xs: 1, md: 3 } }}>
          <Stepper 
            activeStep={activeStep} 
            alternativeLabel
            sx={{
              '& .MuiStepLabel-label': {
                fontSize: { xs: '0.65rem', sm: '0.75rem', md: '0.875rem' },
              },
              '& .MuiStepIcon-root': {
                fontSize: { xs: '1.25rem', md: '1.5rem' },
              },
            }}
          >
            {steps.map((label) => (
              <Step key={label}>
                <StepLabel>{label}</StepLabel>
              </Step>
            ))}
          </Stepper>
        </CardContent>
      </Card>

      {/* Step Content */}
      <Card sx={{ borderRadius: { xs: 2, md: 3 } }}>
        <CardContent sx={{ p: { xs: 2, md: 4 } }}>
          <AnimatePresence mode="wait">
            {renderStepContent()}
          </AnimatePresence>

          {/* Navigation Buttons */}
          <Box sx={{ 
            display: 'flex', 
            justifyContent: 'space-between', 
            mt: { xs: 2, md: 4 }, 
            pt: { xs: 2, md: 3 }, 
            borderTop: '1px solid', 
            borderColor: 'divider',
            flexDirection: { xs: 'column-reverse', sm: 'row' },
            gap: { xs: 1.5, sm: 0 },
          }}>
            <Button
              disabled={activeStep === 0 || extracting}
              onClick={handleBack}
              startIcon={<ArrowBackIcon />}
              sx={{ fontSize: { xs: '0.8rem', md: '0.875rem' } }}
            >
              Back
            </Button>

            {activeStep === steps.length - 1 ? (
              <Button
                variant="contained"
                color="primary"
                size="large"
                onClick={handleEvaluate}
                disabled={loading}
                startIcon={loading ? <CircularProgress size={20} color="inherit" /> : <AIIcon />}
                sx={{ fontSize: { xs: '0.8rem', md: '0.875rem' }, py: { xs: 1.25, md: 1.5 } }}
              >
                {loading ? 'Evaluating...' : 'Start Evaluation'}
              </Button>
            ) : (
              <Button
                variant="contained"
                onClick={handleNext}
                disabled={extracting}
                endIcon={extracting ? <CircularProgress size={20} color="inherit" /> : <ArrowForwardIcon />}
                sx={{ fontSize: { xs: '0.8rem', md: '0.875rem' } }}
              >
                {extracting ? 'Processing...' : 'Next'}
              </Button>
            )}
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
}

export default Evaluate;
