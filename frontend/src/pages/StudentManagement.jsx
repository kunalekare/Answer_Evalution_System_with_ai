/**
 * Student Management Page
 * ========================
 * For teachers to manage their students - view, add, edit, delete students.
 * Shows student details, evaluations, marks, etc.
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  TextField,
  IconButton,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Grid,
  Chip,
  Avatar,
  Tooltip,
  InputAdornment,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Card,
  CardContent,
  LinearProgress,
  Alert,
  Tabs,
  Tab,
  Divider,
  CircularProgress,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Search as SearchIcon,
  Visibility as ViewIcon,
  Person as PersonIcon,
  School as SchoolIcon,
  Grade as GradeIcon,
  Assessment as AssessmentIcon,
  Download as DownloadIcon,
  Refresh as RefreshIcon,
  FilterList as FilterIcon,
  Close as CloseIcon,
  Assignment as MarksheetIcon,
  Email as EmailIcon,
} from '@mui/icons-material';
import { toast } from 'react-hot-toast';
import { useAuth, ROLES } from '../context/AuthContext';
import {
  getStudents,
  createStudent,
  updateStudent,
  deleteStudent,
  getStudentEvaluations,
  getClasses,
} from '../services/api';

const initialStudentForm = {
  roll_no: '',
  name: '',
  email: '',
  password: '',
  phone: '',
  enrollment_no: '',
  gender: '',
  date_of_birth: '',
  address: '',
  class_id: '',
  academic_year: new Date().getFullYear() + '-' + (new Date().getFullYear() + 1),
};

export default function StudentManagement() {
  const { user, hasRole } = useAuth();
  const [loading, setLoading] = useState(true);
  const [students, setStudents] = useState([]);
  const [classes, setClasses] = useState([]);
  const [totalStudents, setTotalStudents] = useState(0);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterClass, setFilterClass] = useState('');
  
  // Dialog states
  const [openAddDialog, setOpenAddDialog] = useState(false);
  const [openEditDialog, setOpenEditDialog] = useState(false);
  const [openViewDialog, setOpenViewDialog] = useState(false);
  const [selectedStudent, setSelectedStudent] = useState(null);
  const [studentForm, setStudentForm] = useState(initialStudentForm);
  const [studentEvaluations, setStudentEvaluations] = useState([]);
  const [loadingEvaluations, setLoadingEvaluations] = useState(false);
  const [viewTab, setViewTab] = useState(0);
  
  // Marksheet states
  const [marksheetDialogOpen, setMarksheetDialogOpen] = useState(false);
  const [selectedMarksheet, setSelectedMarksheet] = useState(null);
  const [studentMarksheets, setStudentMarksheets] = useState([]);

  // Fetch students
  const fetchStudents = useCallback(async () => {
    try {
      setLoading(true);
      const response = await getStudents(page + 1, rowsPerPage, searchQuery, filterClass);
      if (response.success && response.data) {
        setStudents(response.data.students || response.data || []);
        setTotalStudents(response.data.pagination?.total || response.total || 0);
      }
    } catch (error) {
      console.error('Error fetching students:', error);
      toast.error('Failed to load students');
    } finally {
      setLoading(false);
    }
  }, [page, rowsPerPage, searchQuery, filterClass]);

  // Fetch classes
  const fetchClasses = useCallback(async () => {
    try {
      const response = await getClasses();
      if (response.success && response.data) {
        setClasses(response.data.classes || response.data || []);
      }
    } catch (error) {
      console.error('Error fetching classes:', error);
    }
  }, []);

  useEffect(() => {
    fetchStudents();
    fetchClasses();
  }, [fetchStudents, fetchClasses]);

  // Fetch student evaluations
  const fetchStudentEvaluations = async (studentId) => {
    try {
      setLoadingEvaluations(true);
      const response = await getStudentEvaluations(studentId);
      if (response.success && response.data) {
        setStudentEvaluations(response.data.evaluations || response.data || []);
      }
    } catch (error) {
      console.error('Error fetching evaluations:', error);
    } finally {
      setLoadingEvaluations(false);
    }
  };

  // Handlers
  const handleAddStudent = async () => {
    if (!studentForm.roll_no || !studentForm.name) {
      toast.error('Roll number and name are required');
      return;
    }
    try {
      const response = await createStudent(studentForm);
      if (response.success) {
        toast.success('Student added successfully');
        setOpenAddDialog(false);
        setStudentForm(initialStudentForm);
        fetchStudents();
      }
    } catch (error) {
      console.error('Error adding student:', error);
      toast.error(error.message || 'Failed to add student');
    }
  };

  const handleUpdateStudent = async () => {
    if (!selectedStudent) return;
    try {
      const response = await updateStudent(selectedStudent.student_id, studentForm);
      if (response.success) {
        toast.success('Student updated successfully');
        setOpenEditDialog(false);
        setSelectedStudent(null);
        setStudentForm(initialStudentForm);
        fetchStudents();
      }
    } catch (error) {
      console.error('Error updating student:', error);
      toast.error(error.message || 'Failed to update student');
    }
  };

  const handleDeleteStudent = async (student) => {
    if (!window.confirm(`Are you sure you want to delete ${student.name}?`)) return;
    try {
      const response = await deleteStudent(student.student_id);
      if (response.success) {
        toast.success('Student deleted successfully');
        fetchStudents();
      }
    } catch (error) {
      console.error('Error deleting student:', error);
      toast.error(error.message || 'Failed to delete student');
    }
  };

  const handleViewStudent = (student) => {
    setSelectedStudent(student);
    setViewTab(0);
    fetchStudentEvaluations(student.student_id);
    setOpenViewDialog(true);
  };

  const handleViewMarksheets = (student) => {
    // Get marksheets from localStorage
    const storedMarksheets = JSON.parse(localStorage.getItem('marksheets') || '[]');
    // Filter marksheets for this student
    const studentSheets = storedMarksheets.filter(m => m.studentInfo?.rollNo === student.roll_no);
    setStudentMarksheets(studentSheets);
    setSelectedMarksheet(studentSheets.length > 0 ? studentSheets[0] : null);
    setSelectedStudent(student);
    setMarksheetDialogOpen(true);
  };

  const handleEditStudent = (student) => {
    setSelectedStudent(student);
    setStudentForm({
      roll_no: student.roll_no || '',
      name: student.name || '',
      email: student.email || '',
      password: '',
      phone: student.phone || '',
      enrollment_no: student.enrollment_no || '',
      gender: student.gender || '',
      date_of_birth: student.date_of_birth || '',
      address: student.address || '',
      class_id: student.class_id || '',
      academic_year: student.academic_year || '',
    });
    setOpenEditDialog(true);
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'active': return 'success';
      case 'inactive': return 'default';
      case 'suspended': return 'error';
      default: return 'default';
    }
  };

  const getGradeColor = (grade) => {
    switch (grade) {
      case 'excellent': return '#4caf50';
      case 'good': return '#2196f3';
      case 'average': return '#ff9800';
      case 'poor': return '#f44336';
      default: return '#9e9e9e';
    }
  };

  // Calculate stats
  const totalActive = students.filter(s => s.status === 'active').length;
  const avgScore = students.length > 0 
    ? (students.reduce((sum, s) => sum + (s.avg_score || 0), 0) / students.length).toFixed(1)
    : 0;

  return (
    <Box sx={{ p: { xs: 1.5, sm: 2, md: 3 } }}>
      {/* Header */}
      <Box sx={{ display: 'flex', flexDirection: { xs: 'column', sm: 'row' }, justifyContent: 'space-between', alignItems: { xs: 'stretch', sm: 'center' }, gap: { xs: 2, sm: 0 }, mb: { xs: 2, md: 3 } }}>
        <Box>
          <Typography variant="h4" fontWeight={700} gutterBottom sx={{ fontSize: { xs: '1.5rem', sm: '1.75rem', md: '2.125rem' } }}>
            Student Management
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ fontSize: { xs: '0.875rem', md: '1rem' } }}>
            Manage your students, view their progress and evaluations
          </Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => {
            setStudentForm(initialStudentForm);
            setOpenAddDialog(true);
          }}
          sx={{ py: { xs: 1, md: 1.2 }, fontSize: { xs: '0.875rem', md: '1rem' }, alignSelf: { xs: 'stretch', sm: 'auto' } }}
        >
          Add Student
        </Button>
      </Box>

      {/* Stats Cards */}
      <Grid container spacing={{ xs: 1.5, sm: 2, md: 3 }} sx={{ mb: { xs: 2, md: 3 } }}>
        <Grid item xs={6} sm={6} md={3}>
          <Card sx={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', borderRadius: { xs: 2, md: 3 } }}>
            <CardContent sx={{ p: { xs: 1.5, sm: 2, md: 3 }, '&:last-child': { pb: { xs: 1.5, sm: 2, md: 3 } } }}>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.8)', fontSize: { xs: '0.7rem', sm: '0.75rem', md: '0.875rem' } }}>
                    Total Students
                  </Typography>
                  <Typography variant="h4" sx={{ color: 'white', fontWeight: 700, fontSize: { xs: '1.25rem', sm: '1.5rem', md: '2rem' } }}>
                    {totalStudents}
                  </Typography>
                </Box>
                <Avatar sx={{ bgcolor: 'rgba(255,255,255,0.2)', width: { xs: 36, sm: 44, md: 56 }, height: { xs: 36, sm: 44, md: 56 } }}>
                  <PersonIcon sx={{ fontSize: { xs: 20, sm: 24, md: 32 } }} />
                </Avatar>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={6} sm={6} md={3}>
          <Card sx={{ background: 'linear-gradient(135deg, #11998e 0%, #38ef7d 100%)', borderRadius: { xs: 2, md: 3 } }}>
            <CardContent sx={{ p: { xs: 1.5, sm: 2, md: 3 }, '&:last-child': { pb: { xs: 1.5, sm: 2, md: 3 } } }}>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.8)', fontSize: { xs: '0.7rem', sm: '0.75rem', md: '0.875rem' } }}>
                    Active Students
                  </Typography>
                  <Typography variant="h4" sx={{ color: 'white', fontWeight: 700, fontSize: { xs: '1.25rem', sm: '1.5rem', md: '2rem' } }}>
                    {totalActive}
                  </Typography>
                </Box>
                <Avatar sx={{ bgcolor: 'rgba(255,255,255,0.2)', width: { xs: 36, sm: 44, md: 56 }, height: { xs: 36, sm: 44, md: 56 } }}>
                  <SchoolIcon sx={{ fontSize: { xs: 20, sm: 24, md: 32 } }} />
                </Avatar>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={6} sm={6} md={3}>
          <Card sx={{ background: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)', borderRadius: { xs: 2, md: 3 } }}>
            <CardContent sx={{ p: { xs: 1.5, sm: 2, md: 3 }, '&:last-child': { pb: { xs: 1.5, sm: 2, md: 3 } } }}>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.8)', fontSize: { xs: '0.7rem', sm: '0.75rem', md: '0.875rem' } }}>
                    Classes
                  </Typography>
                  <Typography variant="h4" sx={{ color: 'white', fontWeight: 700, fontSize: { xs: '1.25rem', sm: '1.5rem', md: '2rem' } }}>
                    {classes.length}
                  </Typography>
                </Box>
                <Avatar sx={{ bgcolor: 'rgba(255,255,255,0.2)', width: { xs: 36, sm: 44, md: 56 }, height: { xs: 36, sm: 44, md: 56 } }}>
                  <GradeIcon sx={{ fontSize: { xs: 20, sm: 24, md: 32 } }} />
                </Avatar>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={6} sm={6} md={3}>
          <Card sx={{ background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)', borderRadius: { xs: 2, md: 3 } }}>
            <CardContent sx={{ p: { xs: 1.5, sm: 2, md: 3 }, '&:last-child': { pb: { xs: 1.5, sm: 2, md: 3 } } }}>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.8)', fontSize: { xs: '0.7rem', sm: '0.75rem', md: '0.875rem' } }}>
                    Avg Score
                  </Typography>
                  <Typography variant="h4" sx={{ color: 'white', fontWeight: 700, fontSize: { xs: '1.25rem', sm: '1.5rem', md: '2rem' } }}>
                    {avgScore}%
                  </Typography>
                </Box>
                <Avatar sx={{ bgcolor: 'rgba(255,255,255,0.2)', width: { xs: 36, sm: 44, md: 56 }, height: { xs: 36, sm: 44, md: 56 } }}>
                  <AssessmentIcon sx={{ fontSize: { xs: 20, sm: 24, md: 32 } }} />
                </Avatar>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Search and Filter */}
      <Paper sx={{ p: { xs: 1.5, sm: 2 }, mb: { xs: 2, md: 3 }, borderRadius: { xs: 2, md: 3 } }}>
        <Grid container spacing={{ xs: 1.5, sm: 2 }} alignItems="center">
          <Grid item xs={12} sm={6} md={6}>
            <TextField
              fullWidth
              placeholder="Search by name, roll no, email..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              size="small"
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon sx={{ fontSize: { xs: 18, md: 22 } }} />
                  </InputAdornment>
                ),
              }}
              sx={{ '& .MuiInputBase-input': { fontSize: { xs: '0.875rem', md: '1rem' } } }}
            />
          </Grid>
          <Grid item xs={7} sm={4} md={4}>
            <FormControl fullWidth size="small">
              <InputLabel sx={{ fontSize: { xs: '0.875rem', md: '1rem' } }}>Filter by Class</InputLabel>
              <Select
                value={filterClass}
                onChange={(e) => setFilterClass(e.target.value)}
                label="Filter by Class"
                sx={{ fontSize: { xs: '0.875rem', md: '1rem' } }}
              >
                <MenuItem value="">All Classes</MenuItem>
                {classes.map((cls) => (
                  <MenuItem key={cls.class_id || cls.id} value={cls.id}>
                    {cls.name || 'Unknown'} {cls.section && `- ${cls.section}`}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={5} sm={2} md={2}>
            <Button
              fullWidth
              variant="outlined"
              startIcon={<RefreshIcon sx={{ fontSize: { xs: 18, md: 22 } }} />}
              onClick={fetchStudents}
              sx={{ py: { xs: 0.9, md: 1 }, fontSize: { xs: '0.8rem', md: '0.875rem' } }}
            >
              Refresh
            </Button>
          </Grid>
        </Grid>
      </Paper>

      {/* Students Table */}
      <Paper sx={{ width: '100%', overflow: 'hidden', borderRadius: { xs: 2, md: 3 } }}>
        {loading && <LinearProgress />}
        <TableContainer sx={{ maxHeight: { xs: 400, md: 600 } }}>
          <Table stickyHeader size="small">
            <TableHead>
              <TableRow>
                <TableCell sx={{ fontWeight: 700, fontSize: { xs: '0.75rem', md: '0.875rem' }, py: { xs: 1, md: 1.5 } }}>Roll No</TableCell>
                <TableCell sx={{ fontWeight: 700, fontSize: { xs: '0.75rem', md: '0.875rem' }, py: { xs: 1, md: 1.5 } }}>Name</TableCell>
                <TableCell sx={{ fontWeight: 700, fontSize: { xs: '0.75rem', md: '0.875rem' }, py: { xs: 1, md: 1.5 }, display: { xs: 'none', md: 'table-cell' } }}>Email</TableCell>
                <TableCell sx={{ fontWeight: 700, fontSize: { xs: '0.75rem', md: '0.875rem' }, py: { xs: 1, md: 1.5 }, display: { xs: 'none', sm: 'table-cell' } }}>Class</TableCell>
                <TableCell sx={{ fontWeight: 700, fontSize: { xs: '0.75rem', md: '0.875rem' }, py: { xs: 1, md: 1.5 } }}>Status</TableCell>
                <TableCell sx={{ fontWeight: 700, fontSize: { xs: '0.75rem', md: '0.875rem' }, py: { xs: 1, md: 1.5 }, display: { xs: 'none', lg: 'table-cell' } }}>Evaluations</TableCell>
                <TableCell sx={{ fontWeight: 700, fontSize: { xs: '0.75rem', md: '0.875rem' }, py: { xs: 1, md: 1.5 }, display: { xs: 'none', sm: 'table-cell' } }}>Avg Score</TableCell>
                <TableCell sx={{ fontWeight: 700, fontSize: { xs: '0.75rem', md: '0.875rem' }, py: { xs: 1, md: 1.5 } }} align="center">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {students.length === 0 && !loading ? (
                <TableRow>
                  <TableCell colSpan={8} align="center" sx={{ py: 4 }}>
                    <Typography color="text.secondary">
                      No students found. Click "Add Student" to add one.
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                students.map((student) => (
                  <TableRow key={student.student_id} hover>
                    <TableCell sx={{ py: { xs: 1, md: 1.5 } }}>
                      <Typography fontWeight={600} sx={{ fontSize: { xs: '0.75rem', md: '0.875rem' } }}>{student.roll_no}</Typography>
                    </TableCell>
                    <TableCell sx={{ py: { xs: 1, md: 1.5 } }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: { xs: 0.75, md: 1 } }}>
                        <Avatar
                          src={student.profile_image}
                          sx={{ width: { xs: 28, md: 32 }, height: { xs: 28, md: 32 }, bgcolor: 'primary.main', fontSize: { xs: '0.75rem', md: '0.875rem' } }}
                        >
                          {student.name?.charAt(0)}
                        </Avatar>
                        <Box>
                          <Typography sx={{ fontSize: { xs: '0.8rem', md: '0.875rem' } }}>{student.name}</Typography>
                          <Typography sx={{ fontSize: '0.7rem', color: 'text.secondary', display: { xs: 'block', md: 'none' } }}>{student.email || '-'}</Typography>
                        </Box>
                      </Box>
                    </TableCell>
                    <TableCell sx={{ py: { xs: 1, md: 1.5 }, fontSize: { xs: '0.75rem', md: '0.875rem' }, display: { xs: 'none', md: 'table-cell' } }}>{student.email || '-'}</TableCell>
                    <TableCell sx={{ py: { xs: 1, md: 1.5 }, fontSize: { xs: '0.75rem', md: '0.875rem' }, display: { xs: 'none', sm: 'table-cell' } }}>{student.class_name || '-'}</TableCell>
                    <TableCell sx={{ py: { xs: 1, md: 1.5 } }}>
                      <Chip
                        label={student.status || 'active'}
                        color={getStatusColor(student.status)}
                        size="small"
                        sx={{ fontSize: { xs: '0.65rem', md: '0.75rem' }, height: { xs: 20, md: 24 } }}
                      />
                    </TableCell>
                    <TableCell sx={{ py: { xs: 1, md: 1.5 }, fontSize: { xs: '0.75rem', md: '0.875rem' }, display: { xs: 'none', lg: 'table-cell' } }}>{student.evaluation_count || 0}</TableCell>
                    <TableCell sx={{ py: { xs: 1, md: 1.5 }, display: { xs: 'none', sm: 'table-cell' } }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Typography sx={{ fontSize: { xs: '0.75rem', md: '0.875rem' } }}>{student.avg_score?.toFixed(1) || 0}%</Typography>
                        <LinearProgress
                          variant="determinate"
                          value={student.avg_score || 0}
                          sx={{ width: { xs: 30, md: 50 }, height: { xs: 4, md: 6 }, borderRadius: 3 }}
                        />
                      </Box>
                    </TableCell>
                    <TableCell align="center" sx={{ py: { xs: 1, md: 1.5 } }}>
                      <Tooltip title="View Details">
                        <IconButton
                          size="small"
                          color="primary"
                          onClick={() => handleViewStudent(student)}
                          sx={{ p: { xs: 0.5, md: 1 } }}
                        >
                          <ViewIcon sx={{ fontSize: { xs: 18, md: 20 } }} />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="View Marksheets">
                        <IconButton
                          size="small"
                          color="secondary"
                          onClick={() => handleViewMarksheets(student)}
                          sx={{ p: { xs: 0.5, md: 1 } }}
                        >
                          <MarksheetIcon sx={{ fontSize: { xs: 18, md: 20 } }} />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Edit">
                        <IconButton
                          size="small"
                          color="info"
                          onClick={() => handleEditStudent(student)}
                          sx={{ p: { xs: 0.5, md: 1 } }}
                        >
                          <EditIcon sx={{ fontSize: { xs: 18, md: 20 } }} />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Delete">
                        <IconButton
                          size="small"
                          color="error"
                          onClick={() => handleDeleteStudent(student)}
                          sx={{ p: { xs: 0.5, md: 1 } }}
                        >
                          <DeleteIcon sx={{ fontSize: { xs: 18, md: 20 } }} />
                        </IconButton>
                      </Tooltip>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
        <TablePagination
          rowsPerPageOptions={[5, 10, 25, 50]}
          component="div"
          count={totalStudents}
          rowsPerPage={rowsPerPage}
          page={page}
          onPageChange={(_, newPage) => setPage(newPage)}
          onRowsPerPageChange={(e) => {
            setRowsPerPage(parseInt(e.target.value, 10));
            setPage(0);
          }}
          sx={{ 
            '& .MuiTablePagination-selectLabel, & .MuiTablePagination-displayedRows': { 
              fontSize: { xs: '0.75rem', md: '0.875rem' } 
            },
            '& .MuiTablePagination-select': { fontSize: { xs: '0.75rem', md: '0.875rem' } },
          }}
        />
      </Paper>

      {/* Add Student Dialog */}
      <Dialog open={openAddDialog} onClose={() => setOpenAddDialog(false)} maxWidth="md" fullWidth fullScreen={window.innerWidth < 600}>
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <PersonIcon color="primary" />
            Add New Student
          </Box>
        </DialogTitle>
        <DialogContent dividers>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Roll Number"
                value={studentForm.roll_no}
                onChange={(e) => setStudentForm({ ...studentForm, roll_no: e.target.value })}
                required
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Full Name"
                value={studentForm.name}
                onChange={(e) => setStudentForm({ ...studentForm, name: e.target.value })}
                required
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Email"
                type="email"
                value={studentForm.email}
                onChange={(e) => setStudentForm({ ...studentForm, email: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Password"
                type="password"
                value={studentForm.password}
                onChange={(e) => setStudentForm({ ...studentForm, password: e.target.value })}
                helperText="For student login (optional)"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Phone"
                value={studentForm.phone}
                onChange={(e) => setStudentForm({ ...studentForm, phone: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Enrollment Number"
                value={studentForm.enrollment_no}
                onChange={(e) => setStudentForm({ ...studentForm, enrollment_no: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Gender</InputLabel>
                <Select
                  value={studentForm.gender}
                  onChange={(e) => setStudentForm({ ...studentForm, gender: e.target.value })}
                  label="Gender"
                >
                  <MenuItem value="">Select</MenuItem>
                  <MenuItem value="Male">Male</MenuItem>
                  <MenuItem value="Female">Female</MenuItem>
                  <MenuItem value="Other">Other</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Date of Birth"
                type="date"
                value={studentForm.date_of_birth}
                onChange={(e) => setStudentForm({ ...studentForm, date_of_birth: e.target.value })}
                InputLabelProps={{ shrink: true }}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Class</InputLabel>
                <Select
                  value={studentForm.class_id}
                  onChange={(e) => setStudentForm({ ...studentForm, class_id: e.target.value })}
                  label="Class"
                >
                  <MenuItem value="">Select Class</MenuItem>
                  {classes.map((cls) => (
                    <MenuItem key={cls.class_id || cls.id} value={cls.id}>
                      {cls.name || 'Unknown'} {cls.section && `- ${cls.section}`}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Academic Year"
                value={studentForm.academic_year}
                onChange={(e) => setStudentForm({ ...studentForm, academic_year: e.target.value })}
                placeholder="e.g., 2025-2026"
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Address"
                value={studentForm.address}
                onChange={(e) => setStudentForm({ ...studentForm, address: e.target.value })}
                multiline
                rows={2}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenAddDialog(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleAddStudent}>Add Student</Button>
        </DialogActions>
      </Dialog>

      {/* Edit Student Dialog */}
      <Dialog open={openEditDialog} onClose={() => setOpenEditDialog(false)} maxWidth="md" fullWidth fullScreen={window.innerWidth < 600}>
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <EditIcon color="primary" />
            Edit Student
          </Box>
        </DialogTitle>
        <DialogContent dividers>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Roll Number"
                value={studentForm.roll_no}
                onChange={(e) => setStudentForm({ ...studentForm, roll_no: e.target.value })}
                required
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Full Name"
                value={studentForm.name}
                onChange={(e) => setStudentForm({ ...studentForm, name: e.target.value })}
                required
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Email"
                type="email"
                value={studentForm.email}
                onChange={(e) => setStudentForm({ ...studentForm, email: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Phone"
                value={studentForm.phone}
                onChange={(e) => setStudentForm({ ...studentForm, phone: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Enrollment Number"
                value={studentForm.enrollment_no}
                onChange={(e) => setStudentForm({ ...studentForm, enrollment_no: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Gender</InputLabel>
                <Select
                  value={studentForm.gender}
                  onChange={(e) => setStudentForm({ ...studentForm, gender: e.target.value })}
                  label="Gender"
                >
                  <MenuItem value="">Select</MenuItem>
                  <MenuItem value="Male">Male</MenuItem>
                  <MenuItem value="Female">Female</MenuItem>
                  <MenuItem value="Other">Other</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Class</InputLabel>
                <Select
                  value={studentForm.class_id}
                  onChange={(e) => setStudentForm({ ...studentForm, class_id: e.target.value })}
                  label="Class"
                >
                  <MenuItem value="">Select Class</MenuItem>
                  {classes.map((cls) => (
                    <MenuItem key={cls.class_id || cls.id} value={cls.id}>
                      {cls.name || 'Unknown'} {cls.section && `- ${cls.section}`}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Academic Year"
                value={studentForm.academic_year}
                onChange={(e) => setStudentForm({ ...studentForm, academic_year: e.target.value })}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Address"
                value={studentForm.address}
                onChange={(e) => setStudentForm({ ...studentForm, address: e.target.value })}
                multiline
                rows={2}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenEditDialog(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleUpdateStudent}>Save Changes</Button>
        </DialogActions>
      </Dialog>

      {/* View Student Dialog */}
      <Dialog
        open={openViewDialog}
        onClose={() => setOpenViewDialog(false)}
        maxWidth="md"
        fullWidth
        fullScreen={window.innerWidth < 600}
      >
        <DialogTitle sx={{ p: { xs: 1.5, md: 2 } }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: { xs: 1.5, md: 2 } }}>
              <Avatar
                src={selectedStudent?.profile_image}
                sx={{ width: { xs: 40, md: 56 }, height: { xs: 40, md: 56 }, bgcolor: 'primary.main', fontSize: { xs: '1rem', md: '1.25rem' } }}
              >
                {selectedStudent?.name?.charAt(0)}
              </Avatar>
              <Box>
                <Typography variant="h6" sx={{ fontSize: { xs: '1rem', md: '1.25rem' } }}>{selectedStudent?.name}</Typography>
                <Typography variant="body2" color="text.secondary" sx={{ fontSize: { xs: '0.75rem', md: '0.875rem' } }}>
                  Roll No: {selectedStudent?.roll_no}
                </Typography>
              </Box>
            </Box>
            <IconButton onClick={() => setOpenViewDialog(false)} sx={{ p: { xs: 0.5, md: 1 } }}>
              <CloseIcon sx={{ fontSize: { xs: 20, md: 24 } }} />
            </IconButton>
          </Box>
        </DialogTitle>
        <DialogContent dividers sx={{ p: { xs: 1.5, md: 2 } }}>
          <Tabs value={viewTab} onChange={(_, v) => setViewTab(v)} sx={{ mb: 2, '& .MuiTab-root': { fontSize: { xs: '0.8rem', md: '0.875rem' }, minWidth: { xs: 'auto', md: 90 }, px: { xs: 1.5, md: 2 } } }}>
            <Tab label="Profile" />
            <Tab label="Evaluations" />
          </Tabs>

          {viewTab === 0 && (
            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" color="text.secondary">Email</Typography>
                <Typography>{selectedStudent?.email || '-'}</Typography>
              </Grid>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" color="text.secondary">Phone</Typography>
                <Typography>{selectedStudent?.phone || '-'}</Typography>
              </Grid>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" color="text.secondary">Enrollment No</Typography>
                <Typography>{selectedStudent?.enrollment_no || '-'}</Typography>
              </Grid>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" color="text.secondary">Class</Typography>
                <Typography>{selectedStudent?.class_name || '-'}</Typography>
              </Grid>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" color="text.secondary">Gender</Typography>
                <Typography>{selectedStudent?.gender || '-'}</Typography>
              </Grid>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" color="text.secondary">Academic Year</Typography>
                <Typography>{selectedStudent?.academic_year || '-'}</Typography>
              </Grid>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" color="text.secondary">Status</Typography>
                <Chip
                  label={selectedStudent?.status || 'active'}
                  color={getStatusColor(selectedStudent?.status)}
                  size="small"
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" color="text.secondary">Created</Typography>
                <Typography>
                  {selectedStudent?.created_at
                    ? new Date(selectedStudent.created_at).toLocaleDateString()
                    : '-'}
                </Typography>
              </Grid>
            </Grid>
          )}

          {viewTab === 1 && (
            <Box>
              {loadingEvaluations ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                  <CircularProgress />
                </Box>
              ) : studentEvaluations.length === 0 ? (
                <Alert severity="info">No evaluations found for this student.</Alert>
              ) : (
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell sx={{ fontSize: { xs: '0.75rem', md: '0.875rem' }, py: { xs: 0.75, md: 1 } }}>Date</TableCell>
                        <TableCell sx={{ fontSize: { xs: '0.75rem', md: '0.875rem' }, py: { xs: 0.75, md: 1 }, display: { xs: 'none', sm: 'table-cell' } }}>Subject</TableCell>
                        <TableCell sx={{ fontSize: { xs: '0.75rem', md: '0.875rem' }, py: { xs: 0.75, md: 1 } }}>Score</TableCell>
                        <TableCell sx={{ fontSize: { xs: '0.75rem', md: '0.875rem' }, py: { xs: 0.75, md: 1 }, display: { xs: 'none', sm: 'table-cell' } }}>Max</TableCell>
                        <TableCell sx={{ fontSize: { xs: '0.75rem', md: '0.875rem' }, py: { xs: 0.75, md: 1 } }}>Grade</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {studentEvaluations.map((eval_) => (
                        <TableRow key={eval_.evaluation_id}>
                          <TableCell sx={{ fontSize: { xs: '0.75rem', md: '0.875rem' }, py: { xs: 0.75, md: 1 } }}>
                            {new Date(eval_.created_at).toLocaleDateString()}
                          </TableCell>
                          <TableCell sx={{ fontSize: { xs: '0.75rem', md: '0.875rem' }, py: { xs: 0.75, md: 1 }, display: { xs: 'none', sm: 'table-cell' } }}>{eval_.subject || '-'}</TableCell>
                          <TableCell sx={{ py: { xs: 0.75, md: 1 } }}>
                            <Typography fontWeight={600} sx={{ fontSize: { xs: '0.75rem', md: '0.875rem' } }}>
                              {eval_.final_score?.toFixed(1)}
                            </Typography>
                          </TableCell>
                          <TableCell sx={{ fontSize: { xs: '0.75rem', md: '0.875rem' }, py: { xs: 0.75, md: 1 }, display: { xs: 'none', sm: 'table-cell' } }}>{eval_.max_marks}</TableCell>
                          <TableCell sx={{ py: { xs: 0.75, md: 1 } }}>
                            <Chip
                              label={eval_.grade}
                              size="small"
                              sx={{
                                bgcolor: getGradeColor(eval_.grade),
                                color: 'white',
                                fontSize: { xs: '0.65rem', md: '0.75rem' },
                                height: { xs: 20, md: 24 },
                              }}
                            />
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions sx={{ p: { xs: 1, md: 2 } }}>
          <Button onClick={() => setOpenViewDialog(false)} sx={{ fontSize: { xs: '0.8rem', md: '0.875rem' } }}>Close</Button>
          <Button
            variant="outlined"
            startIcon={<EditIcon sx={{ fontSize: { xs: 18, md: 20 } }} />}
            onClick={() => {
              setOpenViewDialog(false);
              handleEditStudent(selectedStudent);
            }}
            sx={{ fontSize: { xs: '0.8rem', md: '0.875rem' } }}
          >
            Edit
          </Button>
        </DialogActions>
      </Dialog>

      {/* Marksheet Dialog */}
      <Dialog
        open={marksheetDialogOpen}
        onClose={() => setMarksheetDialogOpen(false)}
        maxWidth="md"
        fullWidth
        PaperProps={{
          sx: {
            minHeight: '60vh',
          }
        }}
      >
        <DialogTitle sx={{ 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'space-between',
          borderBottom: '1px solid',
          borderColor: 'divider',
        }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <MarksheetIcon color="primary" />
            <Typography variant="h6">
              Marksheets - {selectedStudent?.name}
            </Typography>
          </Box>
          <IconButton onClick={() => setMarksheetDialogOpen(false)} size="small">
            <CloseIcon />
          </IconButton>
        </DialogTitle>
        <DialogContent sx={{ p: 3 }}>
          {studentMarksheets.length === 0 ? (
            <Box sx={{ 
              display: 'flex', 
              flexDirection: 'column', 
              alignItems: 'center', 
              justifyContent: 'center',
              minHeight: 200,
              gap: 2,
            }}>
              <MarksheetIcon sx={{ fontSize: 64, color: 'text.disabled' }} />
              <Typography color="text.secondary">
                No marksheets found for this student
              </Typography>
            </Box>
          ) : (
            <Box>
              {/* Marksheet Selector */}
              {studentMarksheets.length > 1 && (
                <Box sx={{ mb: 3 }}>
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    Select Marksheet:
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                    {studentMarksheets.map((sheet, index) => (
                      <Chip
                        key={sheet.id}
                        label={`${sheet.studentInfo?.paperName || 'Paper'} - ${new Date(sheet.timestamp).toLocaleDateString()}`}
                        onClick={() => setSelectedMarksheet(sheet)}
                        color={selectedMarksheet?.id === sheet.id ? 'primary' : 'default'}
                        variant={selectedMarksheet?.id === sheet.id ? 'filled' : 'outlined'}
                      />
                    ))}
                  </Box>
                </Box>
              )}

              {/* Selected Marksheet Details */}
              {selectedMarksheet && (
                <Paper variant="outlined" sx={{ p: 3 }}>
                  {/* Header */}
                  <Box sx={{ textAlign: 'center', mb: 3, pb: 2, borderBottom: '2px solid', borderColor: 'primary.main' }}>
                    <Typography variant="h5" fontWeight="bold" color="primary.main">
                      Evaluation Marksheet
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Generated on {new Date(selectedMarksheet.timestamp).toLocaleString()}
                    </Typography>
                  </Box>

                  {/* Student Info */}
                  <Grid container spacing={2} sx={{ mb: 3 }}>
                    <Grid item xs={6} sm={4}>
                      <Typography variant="body2" color="text.secondary">Student Name</Typography>
                      <Typography variant="body1" fontWeight="medium">{selectedMarksheet.studentInfo?.name || '-'}</Typography>
                    </Grid>
                    <Grid item xs={6} sm={4}>
                      <Typography variant="body2" color="text.secondary">Roll No</Typography>
                      <Typography variant="body1" fontWeight="medium">{selectedMarksheet.studentInfo?.rollNo || '-'}</Typography>
                    </Grid>
                    <Grid item xs={6} sm={4}>
                      <Typography variant="body2" color="text.secondary">Paper Name</Typography>
                      <Typography variant="body1" fontWeight="medium">{selectedMarksheet.studentInfo?.paperName || '-'}</Typography>
                    </Grid>
                    <Grid item xs={6} sm={4}>
                      <Typography variant="body2" color="text.secondary">Class</Typography>
                      <Typography variant="body1" fontWeight="medium">{selectedMarksheet.studentInfo?.class || '-'}</Typography>
                    </Grid>
                    <Grid item xs={6} sm={4}>
                      <Typography variant="body2" color="text.secondary">Subject</Typography>
                      <Typography variant="body1" fontWeight="medium">{selectedMarksheet.studentInfo?.subject || '-'}</Typography>
                    </Grid>
                    <Grid item xs={6} sm={4}>
                      <Typography variant="body2" color="text.secondary">Date</Typography>
                      <Typography variant="body1" fontWeight="medium">{selectedMarksheet.studentInfo?.examDate || '-'}</Typography>
                    </Grid>
                  </Grid>

                  {/* Evaluation Table */}
                  <TableContainer component={Paper} variant="outlined">
                    <Table size="small">
                      <TableHead>
                        <TableRow sx={{ bgcolor: 'primary.main' }}>
                          <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>Q. No.</TableCell>
                          <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>Out of</TableCell>
                          <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>Score</TableCell>
                          <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>%</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {selectedMarksheet.evaluations?.map((evalItem, index) => (
                          <TableRow key={index} sx={{ 
                            bgcolor: index % 2 === 0 ? 'background.default' : 'action.hover' 
                          }}>
                            <TableCell sx={{ fontWeight: 'medium' }}>Q{evalItem.questionNumber}</TableCell>
                            <TableCell>{evalItem.maxMarks}</TableCell>
                            <TableCell sx={{ 
                              fontWeight: 'bold',
                              color: (evalItem.score / evalItem.maxMarks) >= 0.7 ? 'success.main' :
                                     (evalItem.score / evalItem.maxMarks) >= 0.4 ? 'warning.main' : 'error.main'
                            }}>
                              {evalItem.score}
                            </TableCell>
                            <TableCell>
                              {((evalItem.score / evalItem.maxMarks) * 100).toFixed(0)}%
                            </TableCell>
                          </TableRow>
                        ))}
                        {/* Total Row */}
                        <TableRow sx={{ bgcolor: 'primary.light' }}>
                          <TableCell sx={{ fontWeight: 'bold', color: 'primary.contrastText' }}>
                            Total
                          </TableCell>
                          <TableCell sx={{ fontWeight: 'bold', color: 'primary.contrastText' }}>
                            {selectedMarksheet.totalMarks || '-'}
                          </TableCell>
                          <TableCell sx={{ fontWeight: 'bold', color: 'primary.contrastText' }}>
                            {selectedMarksheet.obtainedMarks || '-'}
                          </TableCell>
                          <TableCell sx={{ fontWeight: 'bold', color: 'primary.contrastText' }}>
                            {selectedMarksheet.percentage?.toFixed(1)}%
                          </TableCell>
                        </TableRow>
                      </TableBody>
                    </Table>
                  </TableContainer>

                  {/* Grade */}
                  <Box sx={{ mt: 3, display: 'flex', justifyContent: 'center' }}>
                    <Chip
                      label={`Grade: ${selectedMarksheet.grade || '-'}`}
                      color="primary"
                      sx={{ fontSize: '1.1rem', py: 2.5, px: 3 }}
                    />
                  </Box>
                </Paper>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions sx={{ p: 2, borderTop: '1px solid', borderColor: 'divider' }}>
          <Button 
            variant="outlined"
            color="secondary"
            startIcon={<EmailIcon />}
            onClick={() => {
              if (!selectedMarksheet) return;
              
              // Send via Gmail compose
              const email = 'kunalekare02@gmail.com';
              const studentName = selectedMarksheet?.studentInfo?.name || 'Student';
              const subject = `Evaluation Marksheet - ${studentName} | ${selectedMarksheet?.studentInfo?.paperName || 'Exam'}`;
              
              // Create professional email body
              const evaluationRows = selectedMarksheet?.evaluations?.map(item => 
                `   Q${item.questionNumber}:  ${item.score} / ${item.maxMarks}  (${((item.score / item.maxMarks) * 100).toFixed(0)}%)`
              ).join('\n') || '';
              
              const body = 
`Dear ${studentName},

Please find below your evaluation marksheet for the recently conducted examination.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
          EVALUATION MARKSHEET
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STUDENT INFORMATION
──────────────────────────────────────
   Name:        ${selectedMarksheet?.studentInfo?.name}
   Roll No:     ${selectedMarksheet?.studentInfo?.rollNo}
   Class:       ${selectedMarksheet?.studentInfo?.class || 'N/A'}

EXAMINATION DETAILS
──────────────────────────────────────
   Paper:       ${selectedMarksheet?.studentInfo?.paperName}
   Subject:     ${selectedMarksheet?.studentInfo?.subject || 'N/A'}
   Date:        ${selectedMarksheet?.studentInfo?.examDate || 'N/A'}

QUESTION-WISE EVALUATION
──────────────────────────────────────
${evaluationRows}

RESULT SUMMARY
──────────────────────────────────────
   Total Marks:    ${selectedMarksheet?.obtainedMarks} / ${selectedMarksheet?.totalMarks}
   Percentage:     ${selectedMarksheet?.percentage?.toFixed(1)}%
   Grade:          ${selectedMarksheet?.grade}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

This is an official evaluation report generated by the Answer Evaluation System.

If you have any queries regarding this evaluation, please contact your teacher.

Best Regards,
Examination Department`;

              // Open Gmail compose
              const gmailUrl = `https://mail.google.com/mail/?view=cm&fs=1&to=${encodeURIComponent(email)}&su=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
              window.open(gmailUrl, '_blank');
            }}
          >
            Send
          </Button>
          <Button onClick={() => setMarksheetDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
