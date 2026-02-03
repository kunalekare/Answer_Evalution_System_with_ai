/**
 * API Service
 * ============
 * Handles all API calls to the backend.
 */

import axios from 'axios';

// Base URL for API
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Create axios instance with base configuration
const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 120000, // 120 seconds for long operations like OCR
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    console.error('API Error:', error);
    const message = error.response?.data?.detail || error.message || 'An error occurred';
    return Promise.reject(new Error(message));
  }
);

/**
 * Upload and evaluate files
 */
export const uploadAndEvaluate = async ({
  modelAnswerFile,
  studentAnswerFile,
  questionType = 'descriptive',
  maxMarks = 10,
  subject = '',
  includeDiagram = false,
}) => {
  // Step 1: Upload files
  const formData = new FormData();
  formData.append('model_answer', modelAnswerFile);
  formData.append('student_answer', studentAnswerFile);
  formData.append('question_type', questionType);
  formData.append('max_marks', maxMarks.toString());
  
  if (subject) {
    formData.append('subject', subject);
  }

  console.log('Uploading files...', {
    modelAnswer: modelAnswerFile.name,
    studentAnswer: studentAnswerFile.name,
    questionType,
    maxMarks,
  });

  const uploadResponse = await api.post('/upload/', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });

  console.log('Upload response:', uploadResponse);

  if (!uploadResponse.success) {
    throw new Error(uploadResponse.message || 'Upload failed');
  }

  // Step 2: Trigger evaluation
  const evaluationResponse = await api.post('/evaluate/', {
    evaluation_id: uploadResponse.data.evaluation_id,
    question_type: questionType,
    max_marks: maxMarks,
    include_diagram: includeDiagram,
  });

  console.log('Evaluation response:', evaluationResponse);
  
  // Return with evaluation_id for navigation
  return {
    ...evaluationResponse,
    evaluation_id: evaluationResponse.evaluation_id || uploadResponse.data.evaluation_id,
  };
};

/**
 * Evaluate text directly without file upload
 */
export const evaluateText = async ({
  model_answer,
  student_answer,
  question_type = 'descriptive',
  max_marks = 10,
  custom_keywords = null,
}) => {
  console.log('Evaluating text...', {
    modelLength: model_answer.length,
    studentLength: student_answer.length,
    questionType: question_type,
    maxMarks: max_marks,
  });

  const response = await api.post('/evaluate/text', {
    model_answer,
    student_answer,
    question_type,
    max_marks,
    custom_keywords,
  });

  console.log('Text evaluation response:', response);
  return response;
};

/**
 * Get evaluation result by ID
 */
export const getResult = async (evaluationId) => {
  const response = await api.get(`/results/${evaluationId}`);
  return response;
};

/**
 * Extract OCR text from uploaded files
 * This allows users to preview what text was extracted before evaluation.
 */
export const extractTextFromUpload = async (evaluationId) => {
  console.log('Extracting text from upload:', evaluationId);
  const response = await api.get(`/upload/${evaluationId}/extract-text`);
  console.log('Text extraction response:', response);
  return response;
};

/**
 * Get all evaluation results (with error handling)
 */
export const getResults = async (params = {}) => {
  try {
    const response = await api.get('/results/', { params });
    return response;
  } catch (error) {
    console.error('Failed to fetch results:', error);
    return { results: [], total: 0 };
  }
};

/**
 * Delete an evaluation result
 */
export const deleteResult = async (evaluationId) => {
  const response = await api.delete(`/results/${evaluationId}`);
  return response;
};

/**
 * Get statistics (with error handling)
 */
export const getStatistics = async () => {
  try {
    const response = await api.get('/results/stats/summary');
    return response;
  } catch (error) {
    console.error('Failed to fetch statistics:', error);
    return { total_evaluations: 0, average_score: 0, subjects: [] };
  }
};

/**
 * Get scoring weights
 */
export const getScoringWeights = async () => {
  const response = await api.get('/evaluate/weights');
  return response;
};

/**
 * Get API health status
 */
export const healthCheck = async () => {
  try {
    const response = await axios.get(
      (process.env.REACT_APP_API_URL || 'http://localhost:8000') + '/health'
    );
    return response.data;
  } catch (error) {
    console.error('Health check failed:', error);
    return { status: 'error', message: error.message };
  }
};

export default api;
