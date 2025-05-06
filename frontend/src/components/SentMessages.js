import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Card,
  CardContent,
  CardMedia,
  Grid,
  Button,
  Chip,
  Divider,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Snackbar,
  Alert,
  CircularProgress
} from '@mui/material';
import VisibilityIcon from '@mui/icons-material/Visibility';
import LaunchIcon from '@mui/icons-material/Launch';
import LinkIcon from '@mui/icons-material/Link';
import ScheduleIcon from '@mui/icons-material/Schedule';
import EventAvailableIcon from '@mui/icons-material/EventAvailable';
import api from '../services/api';

const SentMessages = () => {
  const [sentMessages, setSentMessages] = useState([]);
  const [viewMessage, setViewMessage] = useState(null);
  const [loading, setLoading] = useState(false);
  const [fetchingSentMessages, setFetchingSentMessages] = useState(true);
  const [notification, setNotification] = useState({ open: false, message: '', severity: 'success' });
  
  // Fetch sent messages when component mounts
  useEffect(() => {
    const fetchSentMessages = async () => {
      try {
        setFetchingSentMessages(true);
        const response = await api.get('/api/sent-messages');
        setSentMessages(response.data.messages || []);
      } catch (error) {
        console.error('Error fetching sent messages:', error);
        setNotification({
          open: true,
          message: 'Failed to load sent messages. Please try again later.',
          severity: 'error'
        });
      } finally {
        setFetchingSentMessages(false);
      }
    };

    fetchSentMessages();
  }, []);

  const handleOpenMessage = (message) => {
    setViewMessage(message);
  };

  const handleCloseMessage = () => {
    setViewMessage(null);
  };

  const handleSendMoreMessages = () => {
    setLoading(true);
    
    // Simulate API call
    setTimeout(() => {
      setLoading(false);
      setNotification({
        open: true,
        message: 'Processing approved messages for sending...',
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
            Sent Messages
          </Typography>
          <Typography variant="subtitle1" color="text.secondary">
            Track messages that have been sent and monitor responses
          </Typography>
        </div>
        <Button 
          variant="outlined" 
          startIcon={<LaunchIcon />}
          href="https://drive.google.com/drive/folders/13JI0-50UdrrB3OUoVuddKbmanhe8TYaY?usp=drive_link" 
          target="_blank"
        >
          Open Sent Messages Folder
        </Button>
      </Box>

      {loading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
          <CircularProgress />
        </Box>
      )}

      <Grid container spacing={3}>
        {sentMessages.map((message) => (
          <Grid item xs={12} md={6} key={message.id}>
            <Card variant="outlined">
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                  <Typography variant="h6">
                    {message.participantName}
                    {message.linkedinUrl && (
                      <IconButton 
                        size="small" 
                        href={message.linkedinUrl} 
                        target="_blank" 
                        sx={{ ml: 1 }}
                      >
                        <LinkIcon fontSize="small" />
                      </IconButton>
                    )}
                  </Typography>
                  <Chip 
                    label={message.responseReceived ? 'Response Received' : 'Awaiting Response'} 
                    color={message.responseReceived ? 'success' : 'default'} 
                    size="small"
                    icon={message.responseReceived ? <EventAvailableIcon /> : <ScheduleIcon />}
                  />
                </Box>
                
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  {message.company}
                </Typography>
                
                <Divider sx={{ my: 1.5 }} />
                
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                  <Typography variant="body2">
                    <strong>Sent Date:</strong> {message.sentDate}
                  </Typography>
                  <Typography variant="body2">
                    <strong>Status:</strong> {message.status}
                  </Typography>
                </Box>
                
                {message.responseReceived && (
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="subtitle2" gutterBottom>Response (Received {message.responseDate}):</Typography>
                    <Typography 
                      variant="body2" 
                      paragraph 
                      sx={{ 
                        whiteSpace: 'pre-line',
                        backgroundColor: '#f0f9ff',
                        p: 1.5, 
                        borderRadius: 1,
                        borderLeft: '3px solid #1976d2'
                      }}
                    >
                      {message.responseMessage}
                    </Typography>
                  </Box>
                )}
                
                <Typography variant="subtitle2" gutterBottom>Message Preview:</Typography>
                <Typography 
                  variant="body2" 
                  sx={{ 
                    display: '-webkit-box',
                    WebkitLineClamp: 3,
                    WebkitBoxOrient: 'vertical',
                    overflow: 'hidden',
                    whiteSpace: 'pre-line',
                    mb: 2
                  }}
                >
                  {message.message}
                </Typography>
                
                <CardMedia
                  component="img"
                  height="140"
                  image={message.screenshotUrl}
                  alt="Message Screenshot"
                  sx={{ borderRadius: 1, objectFit: 'cover', mb: 1 }}
                />
                
                <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
                  <Button
                    size="small"
                    startIcon={<VisibilityIcon />}
                    onClick={() => handleOpenMessage(message)}
                  >
                    View Full Message
                  </Button>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
      
      <Box sx={{ mt: 4, display: 'flex', justifyContent: 'center' }}>
        <Button
          variant="contained"
          color="primary"
          onClick={handleSendMoreMessages}
          disabled={loading}
        >
          Send More Approved Messages
        </Button>
      </Box>

      <Dialog 
        open={!!viewMessage} 
        onClose={handleCloseMessage}
        maxWidth="md"
        fullWidth
      >
        {viewMessage && (
          <>
            <DialogTitle>
              Message to {viewMessage.participantName}
              <Typography variant="subtitle2" color="text.secondary">
                {viewMessage.company} • Sent on {viewMessage.sentDate}
              </Typography>
            </DialogTitle>
            <DialogContent dividers>
              <Typography variant="h6" gutterBottom>Message Content:</Typography>
              <Typography 
                variant="body1" 
                component="pre"
                sx={{ 
                  whiteSpace: 'pre-line',
                  fontFamily: '"Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
                  p: 2,
                  backgroundColor: '#f8f9fa',
                  borderRadius: 1,
                  mb: 3
                }}
              >
                {viewMessage.message}
              </Typography>
              
              <Typography variant="h6" gutterBottom>Message Screenshot:</Typography>
              <Box 
                component="img" 
                src={viewMessage.screenshotUrl} 
                alt="Message Screenshot"
                sx={{ 
                  width: '100%',
                  maxHeight: '400px',
                  objectFit: 'contain',
                  mb: 3,
                  borderRadius: 1
                }}
              />
              
              {viewMessage.responseReceived && (
                <>
                  <Typography variant="h6" gutterBottom>Response (Received {viewMessage.responseDate}):</Typography>
                  <Typography 
                    variant="body1" 
                    sx={{ 
                      p: 2,
                      backgroundColor: '#f0f9ff',
                      borderRadius: 1,
                      borderLeft: '3px solid #1976d2',
                      fontFamily: '"Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif'
                    }}
                  >
                    {viewMessage.responseMessage}
                  </Typography>
                </>
              )}
            </DialogContent>
            <DialogActions>
              <Button onClick={handleCloseMessage}>Close</Button>
              {viewMessage.linkedinUrl && (
                <Button 
                  color="primary" 
                  startIcon={<LinkIcon />}
                  href={viewMessage.linkedinUrl}
                  target="_blank"
                >
                  View LinkedIn Profile
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

export default SentMessages;
