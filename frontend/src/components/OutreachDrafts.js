import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Card,
  CardContent,
  CardActions,
  Button,
  Chip,
  Grid,
  TextField,
  CircularProgress,
  Snackbar,
  Alert,
  Divider,
  IconButton,
  Tooltip
} from '@mui/material';
import EditIcon from '@mui/icons-material/Edit';
import ThumbUpIcon from '@mui/icons-material/ThumbUp';
import ThumbDownIcon from '@mui/icons-material/ThumbDown';
import LinkIcon from '@mui/icons-material/Link';
import LaunchIcon from '@mui/icons-material/Launch';
import api from '../services/api';

const OutreachDrafts = () => {
  const [drafts, setDrafts] = useState([]);
  const [fetchingDrafts, setFetchingDrafts] = useState(true);
  const [editingDraft, setEditingDraft] = useState(null);
  const [editedMessage, setEditedMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [notification, setNotification] = useState({ open: false, message: '', severity: 'success' });
  
  // Fetch drafts when component mounts
  useEffect(() => {
    const fetchDrafts = async () => {
      try {
        setFetchingDrafts(true);
        const response = await api.get('/api/drafts');
        setDrafts(response.data.drafts || []);
      } catch (error) {
        console.error('Error fetching drafts:', error);
        setNotification({
          open: true,
          message: 'Failed to load outreach drafts. Please try again later.',
          severity: 'error'
        });
      } finally {
        setFetchingDrafts(false);
      }
    };

    fetchDrafts();
  }, []);

  const handleEditDraft = (draft) => {
    setEditingDraft(draft);
    setEditedMessage(draft.message);
  };

  const handleSaveEdit = () => {
    setLoading(true);
    
    // Simulate API call
    setTimeout(() => {
      const updatedDrafts = drafts.map((draft) => 
        draft.id === editingDraft.id 
          ? { ...draft, message: editedMessage } 
          : draft
      );
      
      setDrafts(updatedDrafts);
      setEditingDraft(null);
      setLoading(false);
      setNotification({
        open: true,
        message: 'Message updated successfully!',
        severity: 'success',
      });
    }, 1000);
  };

  const handleApprove = (draftId) => {
    setLoading(true);
    
    // Simulate API call
    setTimeout(() => {
      const updatedDrafts = drafts.map((draft) => 
        draft.id === draftId 
          ? { ...draft, status: 'Approved' } 
          : draft
      );
      
      setDrafts(updatedDrafts);
      setLoading(false);
      setNotification({
        open: true,
        message: 'Message approved successfully!',
        severity: 'success',
      });
    }, 1000);
  };

  const handleReject = (draftId) => {
    setLoading(true);
    
    // Simulate API call
    setTimeout(() => {
      const updatedDrafts = drafts.map((draft) => 
        draft.id === draftId 
          ? { ...draft, status: 'Needs Edits' } 
          : draft
      );
      
      setDrafts(updatedDrafts);
      setLoading(false);
      setNotification({
        open: true,
        message: 'Message needs edits',
        severity: 'warning',
      });
    }, 1000);
  };

  const handleGenerateMore = () => {
    setLoading(true);
    
    // Simulate API call
    setTimeout(() => {
      setLoading(false);
      setNotification({
        open: true,
        message: 'Message generation in progress. Check back soon!',
        severity: 'info',
      });
    }, 1500);
  };

  const handleCloseNotification = () => {
    setNotification({ ...notification, open: false });
  };

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <div>
          <Typography variant="h4" gutterBottom>
            Outreach Drafts
          </Typography>
          <Typography variant="subtitle1" color="text.secondary">
            Review and approve generated outreach messages
          </Typography>
        </div>
        <Button 
          variant="outlined" 
          startIcon={<LaunchIcon />}
          href="https://drive.google.com/drive/folders/1BIuI6z70x4uZchaGzBpV9Ax-VwXQJI_k?usp=drive_link" 
          target="_blank"
        >
          Open Outreach Drafts Folder
        </Button>
      </Box>

      {loading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
          <CircularProgress />
        </Box>
      )}

      {editingDraft ? (
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            Edit Message for {editingDraft.participantName}
          </Typography>
          <Typography variant="body2" color="text.secondary" paragraph>
            <strong>Company:</strong> {editingDraft.company} | <strong>Role:</strong> {editingDraft.role}
          </Typography>
          
          <Box sx={{ mb: 2 }}>
            <Typography variant="subtitle2" gutterBottom>Research Notes:</Typography>
            <Typography variant="body2" paragraph sx={{ backgroundColor: '#f5f5f5', p: 2, borderRadius: 1 }}>
              {editingDraft.research}
            </Typography>
          </Box>
          
          <TextField
            fullWidth
            multiline
            rows={10}
            variant="outlined"
            value={editedMessage}
            onChange={(e) => setEditedMessage(e.target.value)}
            margin="normal"
          />
          
          <Box sx={{ mt: 2, display: 'flex', justifyContent: 'flex-end', gap: 2 }}>
            <Button variant="outlined" onClick={() => setEditingDraft(null)}>
              Cancel
            </Button>
            <Button variant="contained" onClick={handleSaveEdit}>
              Save Changes
            </Button>
          </Box>
        </Paper>
      ) : (
        <>
          <Grid container spacing={3}>
            {drafts.map((draft) => (
              <Grid item xs={12} key={draft.id}>
                <Card variant="outlined">
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                      <Typography variant="h6">
                        {draft.participantName} 
                        {draft.linkedinUrl && (
                          <IconButton 
                            size="small" 
                            href={draft.linkedinUrl} 
                            target="_blank" 
                            sx={{ ml: 1 }}
                          >
                            <LinkIcon fontSize="small" />
                          </IconButton>
                        )}
                      </Typography>
                      <Chip 
                        label={draft.status} 
                        color={
                          draft.status === 'Approved' ? 'success' : 
                          draft.status === 'Needs Edits' ? 'error' : 'default'
                        } 
                        size="small" 
                      />
                    </Box>
                    
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      {draft.role} at {draft.company}
                    </Typography>
                    
                    <Divider sx={{ my: 1.5 }} />
                    
                    <Typography variant="subtitle2" gutterBottom>Research Notes:</Typography>
                    <Typography variant="body2" paragraph sx={{ backgroundColor: '#f5f5f5', p: 1.5, borderRadius: 1, mb: 2, fontSize: '0.875rem' }}>
                      {draft.research}
                    </Typography>
                    
                    <Typography variant="subtitle2" gutterBottom>Generated Message:</Typography>
                    <Typography 
                      variant="body2" 
                      sx={{ 
                        whiteSpace: 'pre-line',
                        backgroundColor: '#f8f9fa',
                        p: 2,
                        borderRadius: 1,
                        fontFamily: '"Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
                        fontSize: '0.875rem'
                      }}
                    >
                      {draft.message}
                    </Typography>
                  </CardContent>
                  
                  <CardActions sx={{ justifyContent: 'flex-end', p: 2 }}>
                    <Button 
                      size="small" 
                      startIcon={<EditIcon />}
                      onClick={() => handleEditDraft(draft)}
                    >
                      Edit
                    </Button>
                    <Button 
                      size="small" 
                      color="error" 
                      startIcon={<ThumbDownIcon />}
                      onClick={() => handleReject(draft.id)}
                      disabled={draft.status === 'Needs Edits'}
                    >
                      Needs Edits
                    </Button>
                    <Button 
                      size="small" 
                      color="success" 
                      startIcon={<ThumbUpIcon />}
                      onClick={() => handleApprove(draft.id)}
                      disabled={draft.status === 'Approved'}
                    >
                      Approve
                    </Button>
                  </CardActions>
                </Card>
              </Grid>
            ))}
          </Grid>
          
          <Box sx={{ mt: 4, display: 'flex', justifyContent: 'center' }}>
            <Button
              variant="contained"
              color="primary"
              onClick={handleGenerateMore}
              disabled={loading}
            >
              Generate More Messages
            </Button>
          </Box>
        </>
      )}

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

export default OutreachDrafts;
