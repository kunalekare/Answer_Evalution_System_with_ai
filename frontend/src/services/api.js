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

// ========== Community API ==========

/**
 * Get list of communities
 */
export const getCommunities = async (page = 1, limit = 20) => {
  const response = await api.get('/community', { params: { page, limit } });
  return response;
};

/**
 * Create a new community
 */
export const createCommunity = async (data) => {
  const response = await api.post('/community', data);
  return response;
};

/**
 * Get community details
 */
export const getCommunity = async (communityId) => {
  const response = await api.get(`/community/${communityId}`);
  return response;
};

/**
 * Update community
 */
export const updateCommunity = async (communityId, data) => {
  const response = await api.put(`/community/${communityId}`, data);
  return response;
};

/**
 * Delete community
 */
export const deleteCommunity = async (communityId) => {
  const response = await api.delete(`/community/${communityId}`);
  return response;
};

/**
 * Add members to community
 */
export const addCommunityMembers = async (communityId, memberIds) => {
  const response = await api.post(`/community/${communityId}/members`, { member_ids: memberIds });
  return response;
};

/**
 * Remove member from community
 */
export const removeCommunityMember = async (communityId, memberId) => {
  const response = await api.delete(`/community/${communityId}/members/${memberId}`);
  return response;
};

/**
 * Get community messages
 */
export const getCommunityMessages = async (communityId, page = 1, limit = 50, beforeId = null) => {
  const params = { page, limit };
  if (beforeId) params.before_id = beforeId;
  const response = await api.get(`/community/${communityId}/messages`, { params });
  return response;
};

/**
 * Send message to community
 */
export const sendCommunityMessage = async (communityId, content, messageType = 'text', replyToId = null) => {
  const response = await api.post(`/community/${communityId}/messages`, {
    content,
    message_type: messageType,
    reply_to_id: replyToId
  });
  return response;
};

/**
 * Send file message to community
 */
export const sendCommunityFileMessage = async (communityId, file, content = '') => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('content', content);
  const response = await api.post(`/community/${communityId}/messages/file`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
  return response;
};

/**
 * Delete message
 */
export const deleteCommunityMessage = async (communityId, messageId) => {
  const response = await api.delete(`/community/${communityId}/messages/${messageId}`);
  return response;
};

/**
 * Pin/unpin message
 */
export const pinCommunityMessage = async (communityId, messageId) => {
  const response = await api.put(`/community/${communityId}/messages/${messageId}/pin`);
  return response;
};

/**
 * Get available members to add
 */
export const getAvailableMembers = async (communityId, search = '') => {
  const response = await api.get(`/community/${communityId}/available-members`, { params: { search } });
  return response;
};

// ========== Grievance API ==========

/**
 * Get list of grievances
 */
export const getGrievances = async (page = 1, limit = 20, filters = {}) => {
  const params = { page, limit, ...filters };
  const response = await api.get('/grievance', { params });
  return response;
};

/**
 * Create a new grievance
 */
export const createGrievance = async (data) => {
  const response = await api.post('/grievance', data);
  return response;
};

/**
 * Create grievance with attachments
 */
export const createGrievanceWithAttachments = async (data, files = []) => {
  const formData = new FormData();
  formData.append('subject', data.subject);
  formData.append('description', data.description);
  if (data.category) formData.append('category', data.category);
  if (data.priority) formData.append('priority', data.priority);
  if (data.community_id) formData.append('community_id', data.community_id);
  files.forEach(file => formData.append('files', file));
  
  const response = await api.post('/grievance/with-attachments', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
  return response;
};

/**
 * Get grievance statistics
 */
export const getGrievanceStats = async () => {
  const response = await api.get('/grievance/stats');
  return response;
};

/**
 * Get grievance details
 */
export const getGrievance = async (grievanceId) => {
  const response = await api.get(`/grievance/${grievanceId}`);
  return response;
};

/**
 * Update grievance status
 */
export const updateGrievanceStatus = async (grievanceId, status, resolution = null, escalationReason = null) => {
  const response = await api.put(`/grievance/${grievanceId}/status`, {
    status,
    resolution,
    escalation_reason: escalationReason
  });
  return response;
};

/**
 * Add response to grievance
 */
export const addGrievanceResponse = async (grievanceId, content, actionTaken = null) => {
  const response = await api.post(`/grievance/${grievanceId}/response`, {
    content,
    action_taken: actionTaken
  });
  return response;
};

/**
 * Get grievance categories
 */
export const getGrievanceCategories = async () => {
  const response = await api.get('/grievance/categories/list');
  return response;
};

// ========== Student Management API ==========

/**
 * Get list of students (for teachers/admin)
 */
export const getStudents = async (page = 1, limit = 10, search = '', classId = '') => {
  const params = { page, limit };
  if (search) params.search = search;
  if (classId) params.class_id = classId;
  const response = await api.get('/teacher/students', { params });
  return response;
};

/**
 * Create a new student
 */
export const createStudent = async (data) => {
  const response = await api.post('/teacher/students', data);
  return response;
};

/**
 * Update a student
 */
export const updateStudent = async (studentId, data) => {
  const response = await api.put(`/teacher/students/${studentId}`, data);
  return response;
};

/**
 * Delete a student
 */
export const deleteStudent = async (studentId) => {
  const response = await api.delete(`/teacher/students/${studentId}`);
  return response;
};

/**
 * Get student evaluations
 */
export const getStudentEvaluations = async (studentId) => {
  const response = await api.get(`/teacher/students/${studentId}/evaluations`);
  return response;
};

// ========== Teacher Management API (Admin) ==========

/**
 * Get list of teachers (for admin)
 */
export const getTeachers = async (page = 1, limit = 10, search = '') => {
  const params = { page, limit };
  if (search) params.search = search;
  const response = await api.get('/admin/teachers', { params });
  return response;
};

/**
 * Create a new teacher
 */
export const createTeacher = async (data) => {
  const response = await api.post('/admin/teachers', data);
  return response;
};

/**
 * Update a teacher
 */
export const updateTeacher = async (teacherId, data) => {
  const response = await api.put(`/admin/teachers/${teacherId}`, data);
  return response;
};

/**
 * Delete a teacher
 */
export const deleteTeacher = async (teacherId) => {
  const response = await api.delete(`/admin/teachers/${teacherId}`);
  return response;
};

// ========== Classes API ==========

/**
 * Get list of classes
 */
export const getClasses = async () => {
  const response = await api.get('/teacher/classes');
  return response;
};

/**
 * Create a new class
 */
export const createClass = async (data) => {
  const response = await api.post('/teacher/classes', data);
  return response;
};

// ========== Student Profile API ==========

/**
 * Get student's own profile
 */
export const getStudentProfile = async () => {
  const response = await api.get('/student/profile');
  return response;
};

/**
 * Update student's own profile
 */
export const updateStudentProfile = async (data) => {
  const response = await api.put('/student/profile', data);
  return response;
};

/**
 * Change password
 */
export const changePassword = async (data) => {
  const response = await api.post('/student/change-password', data);
  return response;
};

export default api;
