import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Button,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Snackbar,
  Alert,
  CircularProgress
} from '@mui/material';
import VisibilityIcon from '@mui/icons-material/Visibility';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import CancelIcon from '@mui/icons-material/Cancel';
import LaunchIcon from '@mui/icons-material/Launch';
import LinkIcon from '@mui/icons-material/Link';

import api from '../services/api';

// Message approval component for reviewing and approving/rejecting outreach messages

const MessageApproval = () => {
  const [approvals, setApprovals] = useState([]);
  const [viewMessage, setViewMessage] = useState(null);
  const [feedback, setFeedback] = useState('');
  const [loading, setLoading] = useState(false);
  const [notification, setNotification] = useState({ open: false, message: '', severity: 'success' });
  const [fetchingApprovals, setFetchingApprovals] = useState(true);

  // Fetch approvals from API when component mounts
  useEffect(() => {
    const fetchApprovals = async () => {
      try {
        setFetchingApprovals(true);
        const response = await api.get('/api/messages');
        setApprovals(response.data.messages || []);
      } catch (error) {
        console.error('Error fetching approvals:', error);
        setNotification({
          open: true,
          message: 'Failed to load messages. Please try again later.',
          severity: 'error'
        });
      } finally {
        setFetchingApprovals(false);
      }
    };

    fetchApprovals();
  }, []);

  const handleOpenMessage = (message) => {
    setViewMessage(message);
    setFeedback(message.feedback || '');
  };

  const handleCloseMessage = () => {
    setViewMessage(null);
  };

  const handleApproveMessage = async (id) => {
    setLoading(true);
    try {
      await api.put(`/api/messages/${id}/approve`);
      
      // Update local state
      setApprovals(prevApprovals => 
        prevApprovals.map(msg => 
          msg.id === id ? { ...msg, status: 'Approved', dateApproved: new Date().toISOString().split('T')[0] } : msg
        )
      );
      
      setNotification({
        open: true,
        message: 'Message approved successfully!',
        severity: 'success'
      });
      
      handleCloseMessage();
    } catch (error) {
      console.error('Error approving message:', error);
      setNotification({
        open: true,
        message: 'Failed to approve message. Please try again.',
        severity: 'error'
      });
    } finally {
      setLoading(false);
    }
  };
  
  const handleRejectMessage = async (id) => {
    if (!feedback.trim() && viewMessage && viewMessage.id === id) {
      setNotification({
        open: true,
        message: 'Please provide feedback before rejecting',
        severity: 'error',
      });
      return;
    }
    
    setLoading(true);
    try {
      await api.put(`/api/messages/${id}/reject`, { feedback });
      
      // Update local state
      setApprovals(prevApprovals => 
        prevApprovals.map(msg => 
          msg.id === id ? { ...msg, status: 'Needs Edits', feedback } : msg
        )
      );
      
      if (viewMessage && viewMessage.id === id) {
        setViewMessage({
          ...viewMessage,
          status: 'Needs Edits',
          feedback
        });
      }
      
      setNotification({
        open: true,
        message: 'Feedback submitted successfully',
        severity: 'success',
      });
      
      handleCloseMessage();
    } catch (error) {
      console.error('Error rejecting message:', error);
      setNotification({
        open: true,
        message: 'Failed to submit feedback. Please try again.',
        severity: 'error'
      });
    } finally {
      setLoading(false);
    }
  };
  
  const handleEditMessage = async (id, updatedMessage) => {
    setLoading(true);
    try {
      await api.put(`/api/messages/${id}/edit`, { updatedMessage });
      
      // Update local state
      setApprovals(prevApprovals => 
        prevApprovals.map(msg => 
          msg.id === id ? { ...msg, message: updatedMessage, status: 'Pending' } : msg
        )
      );
      
      setNotification({
        open: true,
        message: 'Message updated successfully',
        severity: 'success',
      });
      
      handleCloseMessage();
    } catch (error) {
      console.error('Error updating message:', error);
      setNotification({
        open: true,
        message: 'Failed to update message. Please try again.',
        severity: 'error'
      });
    } finally {
      setLoading(false);
    }
  };

  const handleCloseNotification = () => {
    setNotification({ ...notification, open: false });
  };

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <div>
          <Typography variant="h4" gutterBottom>
            Message Approval
          </Typography>
          <Typography variant="subtitle1" color="text.secondary">
            Review and approve messages before sending
          </Typography>
        </div>
        <Button 
          variant="outlined" 
          startIcon={<LaunchIcon />}
          href="https://docs.google.com/spreadsheets/d/1UxhwA4y1jarysB5QGbpj0esPi_pI9gqQkqefIhYDhBM/edit?usp=drive_link" 
          target="_blank"
        >
          Open Message Approval Tracker
        </Button>
      </Box>

      {loading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
          <CircularProgress />
        </Box>
      )}

      <Paper sx={{ width: '100%', overflow: 'hidden' }}>
        <TableContainer sx={{ maxHeight: 'calc(100vh - 240px)' }}>
          <Table stickyHeader>
            <TableHead>
              <TableRow>
                <TableCell>Participant</TableCell>
                <TableCell>Company</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Date Submitted</TableCell>
                <TableCell>Date Approved</TableCell>
                <TableCell align="center">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {approvals.map((approval) => (
                <TableRow key={approval.id} hover>
                  <TableCell>
                    {approval.participantName}
                    {approval.linkedinUrl && (
                      <IconButton 
                        size="small" 
                        href={approval.linkedinUrl} 
                        target="_blank"
                        sx={{ ml: 1 }}
                      >
                        <LinkIcon fontSize="small" />
                      </IconButton>
                    )}
                  </TableCell>
                  <TableCell>{approval.company}</TableCell>
                  <TableCell>
                    <Chip 
                      label={approval.status} 
                      color={
                        approval.status === 'Approved' ? 'success' : 
                        approval.status === 'Needs Edits' ? 'error' : 'default'
                      }
                      size="small" 
                    />
                  </TableCell>
                  <TableCell>{approval.dateSubmitted}</TableCell>
                  <TableCell>{approval.dateApproved || '—'}</TableCell>
                  <TableCell align="center">
                    <IconButton 
                      color="primary" 
                      onClick={() => handleOpenMessage(approval)}
                      size="small"
                    >
                      <VisibilityIcon />
                    </IconButton>
                    {approval.status !== 'Approved' && (
                      <IconButton 
                        color="success" 
                        onClick={() => handleApproveMessage(approval.id)}
                        size="small"
                      >
                        <CheckCircleIcon />
                      </IconButton>
                    )}
                    {approval.status !== 'Needs Edits' && (
                      <IconButton 
                        color="error" 
                        onClick={() => handleOpenMessage(approval)}
                        size="small"
                      >
                        <CancelIcon />
                      </IconButton>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>

      <Dialog 
        open={!!viewMessage} 
        onClose={handleCloseMessage}
        maxWidth="md"
        fullWidth
      >
        {viewMessage && (
          <>
            <DialogTitle>
              Message for {viewMessage.participantName}
              <Typography variant="subtitle2" color="text.secondary">
                {viewMessage.company} • Status: {' '}
                <Chip 
                  label={viewMessage.status} 
                  color={
                    viewMessage.status === 'Approved' ? 'success' : 
                    viewMessage.status === 'Needs Edits' ? 'error' : 'default'
                  }
                  size="small" 
                />
              </Typography>
            </DialogTitle>
            <DialogContent dividers>
              <Typography 
                variant="body1" 
                component="pre"
                sx={{ 
                  whiteSpace: 'pre-line',
                  fontFamily: '"Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
                  p: 2,
                  backgroundColor: '#f8f9fa',
                  borderRadius: 1
                }}
              >
                {viewMessage.message}
              </Typography>
              
              <Box sx={{ mt: 3 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Feedback (required for rejection):
                </Typography>
                <TextField
                  fullWidth
                  multiline
                  rows={3}
                  placeholder="Enter your feedback here..."
                  variant="outlined"
                  value={feedback}
                  onChange={(e) => setFeedback(e.target.value)}
                />
              </Box>
            </DialogContent>
            <DialogActions>
              <Button onClick={handleCloseMessage}>Close</Button>
              {viewMessage.status !== 'Needs Edits' && (
                <Button 
                  color="error" 
                  onClick={() => handleRejectMessage(viewMessage.id)}
                >
                  Needs Edits
                </Button>
              )}
              {viewMessage.status !== 'Approved' && (
                <Button 
                  color="success" 
                  onClick={() => handleApproveMessage(viewMessage.id)}
                >
                  Approve
                </Button>
              )}
            </DialogActions>
          </>
        )}
      </Dialog>

      <Snackbar 
        open={notification.open} 
        autoHideDuration={6000} 
        onClose={handleCloseNotification}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert onClose={handleCloseNotification} severity={notification.severity}>
          {notification.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default MessageApproval;
