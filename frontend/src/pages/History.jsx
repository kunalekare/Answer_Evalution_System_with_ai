/**
 * History Page
 * =============
 * View past evaluation results.
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Chip,
  IconButton,
  TextField,
  InputAdornment,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Paper,
  Skeleton,
  Button,
} from '@mui/material';
import {
  Search as SearchIcon,
  Visibility as ViewIcon,
  Delete as DeleteIcon,
  FilterList as FilterIcon,
  Download as DownloadIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';

const gradeColors = {
  excellent: 'success',
  good: 'primary',
  average: 'warning',
  poor: 'error',
};

// Mock data for demonstration
const mockEvaluations = [
  {
    evaluation_id: 'eval-001',
    student_name: 'John Doe',
    subject: 'Biology',
    final_score: 92.5,
    max_marks: 10,
    obtained_marks: 9.25,
    grade: 'excellent',
    timestamp: '2026-01-27T10:30:00Z',
  },
  {
    evaluation_id: 'eval-002',
    student_name: 'Jane Smith',
    subject: 'Physics',
    final_score: 78.3,
    max_marks: 10,
    obtained_marks: 7.83,
    grade: 'good',
    timestamp: '2026-01-27T09:15:00Z',
  },
  {
    evaluation_id: 'eval-003',
    student_name: 'Bob Wilson',
    subject: 'Chemistry',
    final_score: 65.0,
    max_marks: 10,
    obtained_marks: 6.5,
    grade: 'average',
    timestamp: '2026-01-26T14:45:00Z',
  },
  {
    evaluation_id: 'eval-004',
    student_name: 'Alice Brown',
    subject: 'Biology',
    final_score: 88.7,
    max_marks: 10,
    obtained_marks: 8.87,
    grade: 'excellent',
    timestamp: '2026-01-26T11:20:00Z',
  },
  {
    evaluation_id: 'eval-005',
    student_name: 'Charlie Davis',
    subject: 'Mathematics',
    final_score: 45.2,
    max_marks: 10,
    obtained_marks: 4.52,
    grade: 'poor',
    timestamp: '2026-01-25T16:00:00Z',
  },
];

function History() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [evaluations, setEvaluations] = useState([]);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [searchQuery, setSearchQuery] = useState('');
  const [gradeFilter, setGradeFilter] = useState('all');

  useEffect(() => {
    // Simulate API call
    const fetchData = async () => {
      setLoading(true);
      await new Promise((resolve) => setTimeout(resolve, 1000));
      setEvaluations(mockEvaluations);
      setLoading(false);
    };
    fetchData();
  }, []);

  const handleChangePage = (event, newPage) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const handleViewResult = (evaluationId) => {
    navigate(`/results/${evaluationId}`);
  };

  const handleDelete = (evaluationId) => {
    setEvaluations(evaluations.filter((e) => e.evaluation_id !== evaluationId));
  };

  // Filter evaluations
  const filteredEvaluations = evaluations.filter((e) => {
    const matchesSearch =
      e.student_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      e.subject?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      e.evaluation_id.toLowerCase().includes(searchQuery.toLowerCase());
    
    const matchesGrade = gradeFilter === 'all' || e.grade === gradeFilter;
    
    return matchesSearch && matchesGrade;
  });

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <Box>
      <Typography variant="h4" fontWeight={700} gutterBottom sx={{ fontSize: { xs: '1.5rem', md: '2rem' } }}>
        Evaluation History
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: { xs: 2, md: 4 }, fontSize: { xs: '0.875rem', md: '1rem' } }}>
        View and manage past evaluation results.
      </Typography>

      {/* Filters */}
      <Card sx={{ mb: { xs: 2, md: 3 }, borderRadius: { xs: 2, md: 3 } }}>
        <CardContent sx={{ py: { xs: 1.5, md: 2 }, px: { xs: 2, md: 3 } }}>
          <Box sx={{ 
            display: 'flex', 
            gap: { xs: 1.5, md: 2 }, 
            flexWrap: 'wrap', 
            alignItems: 'center',
            flexDirection: { xs: 'column', sm: 'row' },
          }}>
            <TextField
              placeholder="Search by student, subject, or ID..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              size="small"
              sx={{ 
                minWidth: { xs: '100%', sm: 250, md: 300 },
                '& .MuiInputBase-input': {
                  fontSize: { xs: '0.8rem', md: '0.875rem' },
                },
              }}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon sx={{ fontSize: { xs: 18, md: 24 } }} />
                  </InputAdornment>
                ),
              }}
            />
            
            <FormControl size="small" sx={{ minWidth: { xs: '100%', sm: 120, md: 150 } }}>
              <InputLabel sx={{ fontSize: { xs: '0.8rem', md: '0.875rem' } }}>Grade</InputLabel>
              <Select
                value={gradeFilter}
                label="Grade"
                onChange={(e) => setGradeFilter(e.target.value)}
                sx={{ fontSize: { xs: '0.8rem', md: '0.875rem' } }}
              >
                <MenuItem value="all">All Grades</MenuItem>
                <MenuItem value="excellent">Excellent</MenuItem>
                <MenuItem value="good">Good</MenuItem>
                <MenuItem value="average">Average</MenuItem>
                <MenuItem value="poor">Poor</MenuItem>
              </Select>
            </FormControl>

            <Box sx={{ flexGrow: 1, display: { xs: 'none', md: 'block' } }} />

            <Box sx={{ display: 'flex', gap: 1, width: { xs: '100%', sm: 'auto' } }}>
              <Button
                variant="outlined"
                startIcon={<RefreshIcon sx={{ fontSize: { xs: 16, md: 20 } }} />}
                onClick={() => window.location.reload()}
                sx={{ fontSize: { xs: '0.75rem', md: '0.875rem' }, flex: { xs: 1, sm: 'unset' } }}
              >
                Refresh
              </Button>
              <Button 
                variant="outlined" 
                startIcon={<DownloadIcon sx={{ fontSize: { xs: 16, md: 20 } }} />}
                sx={{ fontSize: { xs: '0.75rem', md: '0.875rem' }, flex: { xs: 1, sm: 'unset' } }}
              >
                Export
              </Button>
            </Box>
          </Box>
        </CardContent>
      </Card>

      {/* Results Table */}
      <Card sx={{ borderRadius: { xs: 2, md: 3 } }}>
        {/* Mobile Card View */}
        <Box sx={{ display: { xs: 'block', md: 'none' }, p: 2 }}>
          {loading ? (
            [...Array(3)].map((_, index) => (
              <Paper key={index} elevation={0} sx={{ p: 2, mb: 2, border: '1px solid', borderColor: 'divider', borderRadius: 2 }}>
                <Skeleton animation="wave" height={24} />
                <Skeleton animation="wave" height={20} width="60%" />
                <Skeleton animation="wave" height={32} width="40%" sx={{ mt: 1 }} />
              </Paper>
            ))
          ) : filteredEvaluations.length === 0 ? (
            <Box sx={{ py: 6, textAlign: 'center' }}>
              <Typography variant="body1" color="text.secondary">
                No evaluations found
              </Typography>
            </Box>
          ) : (
            filteredEvaluations
              .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
              .map((evaluation) => (
                <Paper
                  key={evaluation.evaluation_id}
                  elevation={0}
                  sx={{
                    p: 2,
                    mb: 2,
                    border: '1px solid',
                    borderColor: 'divider',
                    borderRadius: 2,
                    '&:last-child': { mb: 0 },
                  }}
                >
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                    <Box>
                      <Typography variant="body2" fontWeight={600}>
                        {evaluation.student_name || 'N/A'}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {evaluation.subject || 'N/A'} • {formatDate(evaluation.timestamp)}
                      </Typography>
                    </Box>
                    <Chip
                      label={evaluation.grade}
                      color={gradeColors[evaluation.grade]}
                      size="small"
                      sx={{ textTransform: 'capitalize', fontSize: '0.65rem', height: 22 }}
                    />
                  </Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 1.5 }}>
                    <Box>
                      <Typography variant="h6" fontWeight={700} color="primary.main" sx={{ fontSize: '1.1rem' }}>
                        {evaluation.final_score.toFixed(1)}%
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {evaluation.obtained_marks} / {evaluation.max_marks} marks
                      </Typography>
                    </Box>
                    <Box>
                      <IconButton
                        size="small"
                        onClick={() => handleViewResult(evaluation.evaluation_id)}
                        sx={{ color: 'primary.main' }}
                      >
                        <ViewIcon fontSize="small" />
                      </IconButton>
                      <IconButton
                        size="small"
                        onClick={() => handleDelete(evaluation.evaluation_id)}
                        sx={{ color: 'error.main' }}
                      >
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </Box>
                  </Box>
                </Paper>
              ))
          )}
        </Box>

        {/* Desktop Table View */}
        <TableContainer sx={{ display: { xs: 'none', md: 'block' } }}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Evaluation ID</TableCell>
                <TableCell>Student</TableCell>
                <TableCell>Subject</TableCell>
                <TableCell align="center">Score</TableCell>
                <TableCell align="center">Marks</TableCell>
                <TableCell align="center">Grade</TableCell>
                <TableCell>Date</TableCell>
                <TableCell align="center">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {loading ? (
                // Loading skeletons
                [...Array(5)].map((_, index) => (
                  <TableRow key={index}>
                    {[...Array(8)].map((_, cellIndex) => (
                      <TableCell key={cellIndex}>
                        <Skeleton animation="wave" />
                      </TableCell>
                    ))}
                  </TableRow>
                ))
              ) : filteredEvaluations.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={8} align="center" sx={{ py: 6 }}>
                    <Typography variant="body1" color="text.secondary">
                      No evaluations found
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                filteredEvaluations
                  .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                  .map((evaluation) => (
                    <TableRow
                      key={evaluation.evaluation_id}
                      hover
                      sx={{ cursor: 'pointer' }}
                    >
                      <TableCell>
                        <Typography
                          variant="body2"
                          fontFamily="monospace"
                          color="text.secondary"
                        >
                          {evaluation.evaluation_id}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" fontWeight={500}>
                          {evaluation.student_name || 'N/A'}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        {evaluation.subject || 'N/A'}
                      </TableCell>
                      <TableCell align="center">
                        <Typography variant="body2" fontWeight={600} color="primary.main">
                          {evaluation.final_score.toFixed(1)}%
                        </Typography>
                      </TableCell>
                      <TableCell align="center">
                        {evaluation.obtained_marks} / {evaluation.max_marks}
                      </TableCell>
                      <TableCell align="center">
                        <Chip
                          label={evaluation.grade}
                          color={gradeColors[evaluation.grade]}
                          size="small"
                          sx={{ textTransform: 'capitalize' }}
                        />
                      </TableCell>
                      <TableCell>
                        <Typography variant="caption" color="text.secondary">
                          {formatDate(evaluation.timestamp)}
                        </Typography>
                      </TableCell>
                      <TableCell align="center">
                        <IconButton
                          size="small"
                          onClick={() => handleViewResult(evaluation.evaluation_id)}
                          title="View Details"
                        >
                          <ViewIcon />
                        </IconButton>
                        <IconButton
                          size="small"
                          onClick={() => handleDelete(evaluation.evaluation_id)}
                          title="Delete"
                        >
                          <DeleteIcon />
                        </IconButton>
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
          count={filteredEvaluations.length}
          rowsPerPage={rowsPerPage}
          page={page}
          onPageChange={handleChangePage}
          onRowsPerPageChange={handleChangeRowsPerPage}
          sx={{
            '& .MuiTablePagination-selectLabel, & .MuiTablePagination-displayedRows': {
              fontSize: { xs: '0.75rem', md: '0.875rem' },
            },
            '& .MuiTablePagination-select': {
              fontSize: { xs: '0.75rem', md: '0.875rem' },
            },
          }}
        />
      </Card>
    </Box>
  );
}

export default History;
