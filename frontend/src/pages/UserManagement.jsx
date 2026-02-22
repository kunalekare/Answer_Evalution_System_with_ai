/**
 * User Management Page
 * =====================
 * For admins to manage both teachers and students.
 * Features: CRUD operations, view details, manage status.
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
  AdminPanelSettings as AdminIcon,
  Refresh as RefreshIcon,
  Close as CloseIcon,
  PersonAdd as PersonAddIcon,
  Badge as BadgeIcon,
  Email as EmailIcon,
  Phone as PhoneIcon,
  Work as WorkIcon,
} from '@mui/icons-material';
import { toast } from 'react-hot-toast';
import { useAuth, ROLES } from '../context/AuthContext';
import {
  getTeachers,
  createTeacher,
  updateTeacher,
  deleteTeacher,
  getStudents,
  createStudent,
  updateStudent,
  deleteStudent,
  getClasses,
} from '../services/api';

const initialTeacherForm = {
  name: '',
  email: '',
  password: '',
  phone: '',
  employee_id: '',
  department: '',
  designation: '',
};

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

export default function UserManagement() {
  const { user, hasRole } = useAuth();
  const [activeTab, setActiveTab] = useState(0); // 0: Teachers, 1: Students
  const [loading, setLoading] = useState(true);
  
  // Teachers state
  const [teachers, setTeachers] = useState([]);
  const [totalTeachers, setTotalTeachers] = useState(0);
  const [teacherPage, setTeacherPage] = useState(0);
  const [teacherRowsPerPage, setTeacherRowsPerPage] = useState(10);
  const [teacherSearch, setTeacherSearch] = useState('');
  
  // Students state
  const [students, setStudents] = useState([]);
  const [totalStudents, setTotalStudents] = useState(0);
  const [studentPage, setStudentPage] = useState(0);
  const [studentRowsPerPage, setStudentRowsPerPage] = useState(10);
  const [studentSearch, setStudentSearch] = useState('');
  const [filterClass, setFilterClass] = useState('');
  const [classes, setClasses] = useState([]);
  
  // Dialog states
  const [openAddTeacherDialog, setOpenAddTeacherDialog] = useState(false);
  const [openEditTeacherDialog, setOpenEditTeacherDialog] = useState(false);
  const [openAddStudentDialog, setOpenAddStudentDialog] = useState(false);
  const [openEditStudentDialog, setOpenEditStudentDialog] = useState(false);
  const [openViewDialog, setOpenViewDialog] = useState(false);
  
  const [selectedTeacher, setSelectedTeacher] = useState(null);
  const [selectedStudent, setSelectedStudent] = useState(null);
  const [teacherForm, setTeacherForm] = useState(initialTeacherForm);
  const [studentForm, setStudentForm] = useState(initialStudentForm);

  // Fetch teachers
  const fetchTeachers = useCallback(async () => {
    try {
      setLoading(true);
      const response = await getTeachers(teacherPage + 1, teacherRowsPerPage, teacherSearch);
      if (response.success && response.data) {
        setTeachers(response.data.teachers || response.data || []);
        setTotalTeachers(response.data.pagination?.total || response.total || 0);
      }
    } catch (error) {
      console.error('Error fetching teachers:', error);
      toast.error('Failed to load teachers');
    } finally {
      setLoading(false);
    }
  }, [teacherPage, teacherRowsPerPage, teacherSearch]);

  // Fetch students
  const fetchStudents = useCallback(async () => {
    try {
      setLoading(true);
      const response = await getStudents(studentPage + 1, studentRowsPerPage, studentSearch, filterClass);
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
  }, [studentPage, studentRowsPerPage, studentSearch, filterClass]);

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
    if (activeTab === 0) {
      fetchTeachers();
    } else {
      fetchStudents();
    }
  }, [activeTab, fetchTeachers, fetchStudents]);

  useEffect(() => {
    fetchClasses();
  }, [fetchClasses]);

  // Teacher handlers
  const handleAddTeacher = async () => {
    if (!teacherForm.name || !teacherForm.email || !teacherForm.password) {
      toast.error('Name, email and password are required');
      return;
    }
    try {
      const response = await createTeacher(teacherForm);
      if (response.success) {
        toast.success('Teacher added successfully');
        setOpenAddTeacherDialog(false);
        setTeacherForm(initialTeacherForm);
        fetchTeachers();
      }
    } catch (error) {
      console.error('Error adding teacher:', error);
      toast.error(error.message || 'Failed to add teacher');
    }
  };

  const handleUpdateTeacher = async () => {
    if (!selectedTeacher) return;
    try {
      const response = await updateTeacher(selectedTeacher.teacher_id, teacherForm);
      if (response.success) {
        toast.success('Teacher updated successfully');
        setOpenEditTeacherDialog(false);
        setSelectedTeacher(null);
        setTeacherForm(initialTeacherForm);
        fetchTeachers();
      }
    } catch (error) {
      console.error('Error updating teacher:', error);
      toast.error(error.message || 'Failed to update teacher');
    }
  };

  const handleDeleteTeacher = async (teacher) => {
    if (!window.confirm(`Are you sure you want to delete ${teacher.name}?`)) return;
    try {
      const response = await deleteTeacher(teacher.teacher_id);
      if (response.success) {
        toast.success('Teacher deleted successfully');
        fetchTeachers();
      }
    } catch (error) {
      console.error('Error deleting teacher:', error);
      toast.error(error.message || 'Failed to delete teacher');
    }
  };

  const handleEditTeacher = (teacher) => {
    setSelectedTeacher(teacher);
    setTeacherForm({
      name: teacher.name || '',
      email: teacher.email || '',
      password: '',
      phone: teacher.phone || '',
      employee_id: teacher.employee_id || '',
      department: teacher.department || '',
      designation: teacher.designation || '',
    });
    setOpenEditTeacherDialog(true);
  };

  // Student handlers
  const handleAddStudent = async () => {
    if (!studentForm.roll_no || !studentForm.name) {
      toast.error('Roll number and name are required');
      return;
    }
    try {
      const response = await createStudent(studentForm);
      if (response.success) {
        toast.success('Student added successfully');
        setOpenAddStudentDialog(false);
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
        setOpenEditStudentDialog(false);
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
    setOpenEditStudentDialog(true);
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'active': return 'success';
      case 'inactive': return 'default';
      case 'suspended': return 'error';
      default: return 'default';
    }
  };

  return (
    <Box sx={{ p: { xs: 1.5, sm: 2, md: 3 } }}>
      {/* Header */}
      <Box sx={{ display: 'flex', flexDirection: { xs: 'column', sm: 'row' }, justifyContent: 'space-between', alignItems: { xs: 'flex-start', sm: 'center' }, gap: { xs: 1, sm: 0 }, mb: { xs: 2, md: 3 } }}>
        <Box>
          <Typography variant="h4" fontWeight={700} gutterBottom sx={{ fontSize: { xs: '1.5rem', sm: '1.75rem', md: '2.125rem' } }}>
            User Management
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ fontSize: { xs: '0.875rem', md: '1rem' } }}>
            Manage teachers and students in the system
          </Typography>
        </Box>
      </Box>

      {/* Stats Cards */}
      <Grid container spacing={{ xs: 1.5, sm: 2, md: 3 }} sx={{ mb: { xs: 2, md: 3 } }}>
        <Grid item xs={6} sm={6} md={3}>
          <Card sx={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', borderRadius: { xs: 2, md: 3 } }}>
            <CardContent sx={{ p: { xs: 1.5, sm: 2, md: 3 }, '&:last-child': { pb: { xs: 1.5, sm: 2, md: 3 } } }}>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.8)', fontSize: { xs: '0.7rem', sm: '0.75rem', md: '0.875rem' } }}>
                    Total Teachers
                  </Typography>
                  <Typography variant="h4" sx={{ color: 'white', fontWeight: 700, fontSize: { xs: '1.25rem', sm: '1.5rem', md: '2rem' } }}>
                    {totalTeachers}
                  </Typography>
                </Box>
                <Avatar sx={{ bgcolor: 'rgba(255,255,255,0.2)', width: { xs: 36, sm: 44, md: 56 }, height: { xs: 36, sm: 44, md: 56 } }}>
                  <BadgeIcon sx={{ fontSize: { xs: 20, sm: 24, md: 32 } }} />
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
                    Total Students
                  </Typography>
                  <Typography variant="h4" sx={{ color: 'white', fontWeight: 700, fontSize: { xs: '1.25rem', sm: '1.5rem', md: '2rem' } }}>
                    {totalStudents}
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
                    Total Classes
                  </Typography>
                  <Typography variant="h4" sx={{ color: 'white', fontWeight: 700, fontSize: { xs: '1.25rem', sm: '1.5rem', md: '2rem' } }}>
                    {classes.length}
                  </Typography>
                </Box>
                <Avatar sx={{ bgcolor: 'rgba(255,255,255,0.2)', width: { xs: 36, sm: 44, md: 56 }, height: { xs: 36, sm: 44, md: 56 } }}>
                  <WorkIcon sx={{ fontSize: { xs: 20, sm: 24, md: 32 } }} />
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
                    Total Users
                  </Typography>
                  <Typography variant="h4" sx={{ color: 'white', fontWeight: 700, fontSize: { xs: '1.25rem', sm: '1.5rem', md: '2rem' } }}>
                    {totalTeachers + totalStudents}
                  </Typography>
                </Box>
                <Avatar sx={{ bgcolor: 'rgba(255,255,255,0.2)', width: { xs: 36, sm: 44, md: 56 }, height: { xs: 36, sm: 44, md: 56 } }}>
                  <PersonIcon sx={{ fontSize: { xs: 20, sm: 24, md: 32 } }} />
                </Avatar>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Tabs */}
      <Paper sx={{ mb: { xs: 2, md: 3 }, borderRadius: { xs: 2, md: 3 } }}>
        <Tabs
          value={activeTab}
          onChange={(_, v) => setActiveTab(v)}
          variant="fullWidth"
          sx={{ 
            borderBottom: 1, 
            borderColor: 'divider',
            '& .MuiTab-root': {
              minHeight: { xs: 48, md: 56 },
              fontSize: { xs: '0.8rem', md: '0.875rem' },
            },
            '& .MuiTab-iconWrapper': {
              fontSize: { xs: 18, md: 22 },
            },
          }}
        >
          <Tab
            icon={<BadgeIcon />}
            label="Teachers"
            iconPosition="start"
          />
          <Tab
            icon={<SchoolIcon />}
            label="Students"
            iconPosition="start"
          />
        </Tabs>
      </Paper>

      {/* Teachers Tab Content */}
      {activeTab === 0 && (
        <>
          {/* Search and Actions */}
          <Paper sx={{ p: { xs: 1.5, sm: 2 }, mb: { xs: 2, md: 3 }, borderRadius: { xs: 2, md: 3 } }}>
            <Grid container spacing={{ xs: 1.5, sm: 2 }} alignItems="center">
              <Grid item xs={12} sm={8} md={8}>
                <TextField
                  fullWidth
                  placeholder="Search by name, email, employee ID..."
                  value={teacherSearch}
                  onChange={(e) => setTeacherSearch(e.target.value)}
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
              <Grid item xs={12} sm={4} md={4}>
                <Button
                  fullWidth
                  variant="contained"
                  startIcon={<PersonAddIcon />}
                  onClick={() => {
                    setTeacherForm(initialTeacherForm);
                    setOpenAddTeacherDialog(true);
                  }}
                  sx={{ py: { xs: 1, md: 1.2 }, fontSize: { xs: '0.8rem', md: '0.875rem' } }}
                >
                  Add Teacher
                </Button>
              </Grid>
            </Grid>
          </Paper>

          {/* Teachers Table */}
          <Paper sx={{ width: '100%', overflow: 'hidden', borderRadius: { xs: 2, md: 3 } }}>
            {loading && <LinearProgress />}
            <TableContainer sx={{ maxHeight: { xs: 400, md: 500 } }}>
              <Table stickyHeader size="small">
                <TableHead>
                  <TableRow>
                    <TableCell sx={{ fontWeight: 700, fontSize: { xs: '0.75rem', md: '0.875rem' }, py: { xs: 1, md: 1.5 }, display: { xs: 'none', sm: 'table-cell' } }}>Employee ID</TableCell>
                    <TableCell sx={{ fontWeight: 700, fontSize: { xs: '0.75rem', md: '0.875rem' }, py: { xs: 1, md: 1.5 } }}>Name</TableCell>
                    <TableCell sx={{ fontWeight: 700, fontSize: { xs: '0.75rem', md: '0.875rem' }, py: { xs: 1, md: 1.5 }, display: { xs: 'none', md: 'table-cell' } }}>Email</TableCell>
                    <TableCell sx={{ fontWeight: 700, fontSize: { xs: '0.75rem', md: '0.875rem' }, py: { xs: 1, md: 1.5 }, display: { xs: 'none', lg: 'table-cell' } }}>Department</TableCell>
                    <TableCell sx={{ fontWeight: 700, fontSize: { xs: '0.75rem', md: '0.875rem' }, py: { xs: 1, md: 1.5 }, display: { xs: 'none', lg: 'table-cell' } }}>Designation</TableCell>
                    <TableCell sx={{ fontWeight: 700, fontSize: { xs: '0.75rem', md: '0.875rem' }, py: { xs: 1, md: 1.5 } }}>Status</TableCell>
                    <TableCell sx={{ fontWeight: 700, fontSize: { xs: '0.75rem', md: '0.875rem' }, py: { xs: 1, md: 1.5 } }} align="center">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {teachers.length === 0 && !loading ? (
                    <TableRow>
                      <TableCell colSpan={7} align="center" sx={{ py: 4 }}>
                        <Typography color="text.secondary">
                          No teachers found. Click "Add Teacher" to add one.
                        </Typography>
                      </TableCell>
                    </TableRow>
                  ) : (
                    teachers.map((teacher) => (
                      <TableRow key={teacher.teacher_id} hover>
                        <TableCell sx={{ py: { xs: 1, md: 1.5 }, display: { xs: 'none', sm: 'table-cell' } }}>
                          <Typography fontWeight={600} sx={{ fontSize: { xs: '0.75rem', md: '0.875rem' } }}>{teacher.employee_id || '-'}</Typography>
                        </TableCell>
                        <TableCell sx={{ py: { xs: 1, md: 1.5 } }}>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: { xs: 0.75, md: 1 } }}>
                            <Avatar
                              src={teacher.profile_image}
                              sx={{ width: { xs: 28, md: 32 }, height: { xs: 28, md: 32 }, bgcolor: 'secondary.main', fontSize: { xs: '0.75rem', md: '0.875rem' } }}
                            >
                              {teacher.name?.charAt(0)}
                            </Avatar>
                            <Box>
                              <Typography sx={{ fontSize: { xs: '0.8rem', md: '0.875rem' } }}>{teacher.name}</Typography>
                              <Typography sx={{ fontSize: '0.7rem', color: 'text.secondary', display: { xs: 'block', md: 'none' } }}>{teacher.email}</Typography>
                            </Box>
                          </Box>
                        </TableCell>
                        <TableCell sx={{ py: { xs: 1, md: 1.5 }, fontSize: { xs: '0.75rem', md: '0.875rem' }, display: { xs: 'none', md: 'table-cell' } }}>{teacher.email}</TableCell>
                        <TableCell sx={{ py: { xs: 1, md: 1.5 }, fontSize: { xs: '0.75rem', md: '0.875rem' }, display: { xs: 'none', lg: 'table-cell' } }}>{teacher.department || '-'}</TableCell>
                        <TableCell sx={{ py: { xs: 1, md: 1.5 }, fontSize: { xs: '0.75rem', md: '0.875rem' }, display: { xs: 'none', lg: 'table-cell' } }}>{teacher.designation || '-'}</TableCell>
                        <TableCell sx={{ py: { xs: 1, md: 1.5 } }}>
                          <Chip
                            label={teacher.status || 'active'}
                            color={getStatusColor(teacher.status)}
                            size="small"
                            sx={{ fontSize: { xs: '0.65rem', md: '0.75rem' }, height: { xs: 20, md: 24 } }}
                          />
                        </TableCell>
                        <TableCell align="center" sx={{ py: { xs: 1, md: 1.5 } }}>
                          <Tooltip title="Edit">
                            <IconButton
                              size="small"
                              color="info"
                              onClick={() => handleEditTeacher(teacher)}
                              sx={{ p: { xs: 0.5, md: 1 } }}
                            >
                              <EditIcon sx={{ fontSize: { xs: 18, md: 20 } }} />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Delete">
                            <IconButton
                              size="small"
                              color="error"
                              onClick={() => handleDeleteTeacher(teacher)}
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
              rowsPerPageOptions={[5, 10, 25]}
              component="div"
              count={totalTeachers}
              rowsPerPage={teacherRowsPerPage}
              page={teacherPage}
              onPageChange={(_, newPage) => setTeacherPage(newPage)}
              onRowsPerPageChange={(e) => {
                setTeacherRowsPerPage(parseInt(e.target.value, 10));
                setTeacherPage(0);
              }}
              sx={{ 
                '& .MuiTablePagination-selectLabel, & .MuiTablePagination-displayedRows': { 
                  fontSize: { xs: '0.75rem', md: '0.875rem' } 
                },
                '& .MuiTablePagination-select': { fontSize: { xs: '0.75rem', md: '0.875rem' } },
              }}
            />
          </Paper>
        </>
      )}

      {/* Students Tab Content */}
      {activeTab === 1 && (
        <>
          {/* Search and Filter */}
          <Paper sx={{ p: { xs: 1.5, sm: 2 }, mb: { xs: 2, md: 3 }, borderRadius: { xs: 2, md: 3 } }}>
            <Grid container spacing={{ xs: 1.5, sm: 2 }} alignItems="center">
              <Grid item xs={12} sm={6} md={5}>
                <TextField
                  fullWidth
                  placeholder="Search by name, roll no, email..."
                  value={studentSearch}
                  onChange={(e) => setStudentSearch(e.target.value)}
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
              <Grid item xs={6} sm={6} md={3}>
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
              <Grid item xs={6} sm={12} md={4}>
                <Button
                  fullWidth
                  variant="contained"
                  startIcon={<PersonAddIcon />}
                  onClick={() => {
                    setStudentForm(initialStudentForm);
                    setOpenAddStudentDialog(true);
                  }}
                  sx={{ py: { xs: 1, md: 1.2 }, fontSize: { xs: '0.8rem', md: '0.875rem' } }}
                >
                  Add Student
                </Button>
              </Grid>
            </Grid>
          </Paper>

          {/* Students Table */}
          <Paper sx={{ width: '100%', overflow: 'hidden', borderRadius: { xs: 2, md: 3 } }}>
            {loading && <LinearProgress />}
            <TableContainer sx={{ maxHeight: { xs: 400, md: 500 } }}>
              <Table stickyHeader size="small">
                <TableHead>
                  <TableRow>
                    <TableCell sx={{ fontWeight: 700, fontSize: { xs: '0.75rem', md: '0.875rem' }, py: { xs: 1, md: 1.5 } }}>Roll No</TableCell>
                    <TableCell sx={{ fontWeight: 700, fontSize: { xs: '0.75rem', md: '0.875rem' }, py: { xs: 1, md: 1.5 } }}>Name</TableCell>
                    <TableCell sx={{ fontWeight: 700, fontSize: { xs: '0.75rem', md: '0.875rem' }, py: { xs: 1, md: 1.5 }, display: { xs: 'none', md: 'table-cell' } }}>Email</TableCell>
                    <TableCell sx={{ fontWeight: 700, fontSize: { xs: '0.75rem', md: '0.875rem' }, py: { xs: 1, md: 1.5 }, display: { xs: 'none', sm: 'table-cell' } }}>Class</TableCell>
                    <TableCell sx={{ fontWeight: 700, fontSize: { xs: '0.75rem', md: '0.875rem' }, py: { xs: 1, md: 1.5 } }}>Status</TableCell>
                    <TableCell sx={{ fontWeight: 700, fontSize: { xs: '0.75rem', md: '0.875rem' }, py: { xs: 1, md: 1.5 } }} align="center">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {students.length === 0 && !loading ? (
                    <TableRow>
                      <TableCell colSpan={6} align="center" sx={{ py: 4 }}>
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
                        <TableCell align="center" sx={{ py: { xs: 1, md: 1.5 } }}>
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
              rowsPerPage={studentRowsPerPage}
              page={studentPage}
              onPageChange={(_, newPage) => setStudentPage(newPage)}
              onRowsPerPageChange={(e) => {
                setStudentRowsPerPage(parseInt(e.target.value, 10));
                setStudentPage(0);
              }}
              sx={{ 
                '& .MuiTablePagination-selectLabel, & .MuiTablePagination-displayedRows': { 
                  fontSize: { xs: '0.75rem', md: '0.875rem' } 
                },
                '& .MuiTablePagination-select': { fontSize: { xs: '0.75rem', md: '0.875rem' } },
              }}
            />
          </Paper>
        </>
      )}

      {/* Add Teacher Dialog */}
      <Dialog open={openAddTeacherDialog} onClose={() => setOpenAddTeacherDialog(false)} maxWidth="md" fullWidth fullScreen={window.innerWidth < 600}>
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <PersonAddIcon color="primary" />
            Add New Teacher
          </Box>
        </DialogTitle>
        <DialogContent dividers>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Full Name"
                value={teacherForm.name}
                onChange={(e) => setTeacherForm({ ...teacherForm, name: e.target.value })}
                required
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Email"
                type="email"
                value={teacherForm.email}
                onChange={(e) => setTeacherForm({ ...teacherForm, email: e.target.value })}
                required
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Password"
                type="password"
                value={teacherForm.password}
                onChange={(e) => setTeacherForm({ ...teacherForm, password: e.target.value })}
                required
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Phone"
                value={teacherForm.phone}
                onChange={(e) => setTeacherForm({ ...teacherForm, phone: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Employee ID"
                value={teacherForm.employee_id}
                onChange={(e) => setTeacherForm({ ...teacherForm, employee_id: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Department"
                value={teacherForm.department}
                onChange={(e) => setTeacherForm({ ...teacherForm, department: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Designation"
                value={teacherForm.designation}
                onChange={(e) => setTeacherForm({ ...teacherForm, designation: e.target.value })}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenAddTeacherDialog(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleAddTeacher}>Add Teacher</Button>
        </DialogActions>
      </Dialog>

      {/* Edit Teacher Dialog */}
      <Dialog open={openEditTeacherDialog} onClose={() => setOpenEditTeacherDialog(false)} maxWidth="md" fullWidth fullScreen={window.innerWidth < 600}>
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <EditIcon color="primary" />
            Edit Teacher
          </Box>
        </DialogTitle>
        <DialogContent dividers>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Full Name"
                value={teacherForm.name}
                onChange={(e) => setTeacherForm({ ...teacherForm, name: e.target.value })}
                required
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Email"
                type="email"
                value={teacherForm.email}
                onChange={(e) => setTeacherForm({ ...teacherForm, email: e.target.value })}
                required
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Phone"
                value={teacherForm.phone}
                onChange={(e) => setTeacherForm({ ...teacherForm, phone: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Employee ID"
                value={teacherForm.employee_id}
                onChange={(e) => setTeacherForm({ ...teacherForm, employee_id: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Department"
                value={teacherForm.department}
                onChange={(e) => setTeacherForm({ ...teacherForm, department: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Designation"
                value={teacherForm.designation}
                onChange={(e) => setTeacherForm({ ...teacherForm, designation: e.target.value })}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenEditTeacherDialog(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleUpdateTeacher}>Save Changes</Button>
        </DialogActions>
      </Dialog>

      {/* Add Student Dialog */}
      <Dialog open={openAddStudentDialog} onClose={() => setOpenAddStudentDialog(false)} maxWidth="md" fullWidth fullScreen={window.innerWidth < 600}>
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <PersonAddIcon color="primary" />
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
          <Button onClick={() => setOpenAddStudentDialog(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleAddStudent}>Add Student</Button>
        </DialogActions>
      </Dialog>

      {/* Edit Student Dialog */}
      <Dialog open={openEditStudentDialog} onClose={() => setOpenEditStudentDialog(false)} maxWidth="md" fullWidth fullScreen={window.innerWidth < 600}>
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
          <Button onClick={() => setOpenEditStudentDialog(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleUpdateStudent}>Save Changes</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
