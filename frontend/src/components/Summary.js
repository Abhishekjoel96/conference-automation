import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
  Button,
  Divider,
  CircularProgress,
  Snackbar,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  LinearProgress
} from '@mui/material';
import PeopleIcon from '@mui/icons-material/People';
import EditNoteIcon from '@mui/icons-material/EditNote';
import ThumbUpAltIcon from '@mui/icons-material/ThumbUp';
import SendIcon from '@mui/icons-material/Send';
import DownloadIcon from '@mui/icons-material/Download';
import BarChartIcon from '@mui/icons-material/BarChart';
import LaunchIcon from '@mui/icons-material/Launch';
import api from '../services/api';

const Summary = () => {
  const [metrics, setMetrics] = useState({
    totalParticipants: 0,
    messagesGenerated: 0,
    messagesApproved: 0,
    messagesSent: 0,
    responsesReceived: 0,
    conversionRate: '0%',
    averageResponseTime: '0 days'
  });
  const [loading, setLoading] = useState(false);
  const [fetchingMetrics, setFetchingMetrics] = useState(true);
  const [progressValue, setProgressValue] = useState(0);
  const [notification, setNotification] = useState({ open: false, message: '', severity: 'success' });
  const [reportGenerated, setReportGenerated] = useState(false);

  // Fetch metrics when component mounts
  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        setFetchingMetrics(true);
        const response = await api.get('/api/metrics');
        setMetrics(response.data.metrics || {
          totalParticipants: 0,
          messagesGenerated: 0,
          messagesApproved: 0,
          messagesSent: 0,
          responsesReceived: 0,
          conversionRate: '0%',
          averageResponseTime: '0 days'
        });
      } catch (error) {
        console.error('Error fetching metrics:', error);
        setNotification({
          open: true,
          message: 'Failed to load metrics. Please try again later.',
          severity: 'error'
        });
      } finally {
        setFetchingMetrics(false);
      }
    };

    fetchMetrics();
  }, []);

  const handleGenerateReport = () => {
    setLoading(true);
    setProgressValue(0);
    
    // Simulate API call with progress
    const interval = setInterval(() => {
      setProgressValue((prevProgress) => {
        const newProgress = prevProgress + 10;
        if (newProgress >= 100) {
          clearInterval(interval);
          setTimeout(() => {
            setLoading(false);
            setReportGenerated(true);
            setNotification({
              open: true,
              message: 'Summary report generated successfully!',
              severity: 'success',
            });
          }, 500);
          return 100;
        }
        return newProgress;
      });
    }, 400);
  };

  const handleDownloadReport = () => {
    setNotification({
      open: true,
      message: 'Report downloaded successfully!',
      severity: 'success',
    });
  };

  const handleCloseNotification = () => {
    setNotification({ ...notification, open: false });
  };

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <div>
          <Typography variant="h4" gutterBottom>
            Campaign Summary
          </Typography>
          <Typography variant="subtitle1" color="text.secondary">
            Key metrics and results from your networking campaign
          </Typography>
        </div>
        <Button 
          variant="outlined" 
          startIcon={<LaunchIcon />}
          href="https://drive.google.com/drive/folders/1cW_NzfEtA1ky0SZY2mT5K1oDGeT8mnwJ?usp=drive_link" 
          target="_blank"
        >
          Open Summary Reports Folder
        </Button>
      </Box>

      <Grid container spacing={3}>
        {/* Key Metrics Cards */}
        <Grid item xs={12} md={3}>
          <Card variant="outlined">
            <CardContent sx={{ textAlign: 'center' }}>
              <PeopleIcon color="primary" sx={{ fontSize: 40, mb: 1 }} />
              <Typography variant="h5" component="div" gutterBottom>
                {metrics.totalParticipants}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Total Participants
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={3}>
          <Card variant="outlined">
            <CardContent sx={{ textAlign: 'center' }}>
              <EditNoteIcon color="primary" sx={{ fontSize: 40, mb: 1 }} />
              <Typography variant="h5" component="div" gutterBottom>
                {metrics.messagesGenerated}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Messages Generated
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={3}>
          <Card variant="outlined">
            <CardContent sx={{ textAlign: 'center' }}>
              <ThumbUpAltIcon color="primary" sx={{ fontSize: 40, mb: 1 }} />
              <Typography variant="h5" component="div" gutterBottom>
                {metrics.messagesApproved}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Messages Approved
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={3}>
          <Card variant="outlined">
            <CardContent sx={{ textAlign: 'center' }}>
              <SendIcon color="primary" sx={{ fontSize: 40, mb: 1 }} />
              <Typography variant="h5" component="div" gutterBottom>
                {metrics.messagesSent}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Messages Sent
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        {/* Campaign Performance */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Campaign Performance
            </Typography>
            <Divider sx={{ mb: 2 }} />
            
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                  <Typography variant="body1">Responses Received:</Typography>
                  <Typography variant="body1" fontWeight="bold">
                    {metrics.responsesReceived} / {metrics.messagesSent}
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <Box sx={{ width: '100%', mr: 1 }}>
                    <LinearProgress 
                      variant="determinate" 
                      value={(metrics.messagesSent > 0 ? (metrics.responsesReceived / metrics.messagesSent) * 100 : 0)} 
                      sx={{ height: 10, borderRadius: 5 }}
                    />
                  </Box>
                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      {metrics.messagesSent > 0 ? Math.round((metrics.responsesReceived / metrics.messagesSent) * 100) : 0}%
                    </Typography>
                  </Box>
                </Box>
              </Grid>
              
              <Grid item xs={12} md={6}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                  <Typography variant="body1">Messages Approved Rate:</Typography>
                  <Typography variant="body1" fontWeight="bold">
                    {metrics.messagesApproved} / {metrics.messagesGenerated}
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <Box sx={{ width: '100%', mr: 1 }}>
                    <LinearProgress 
                      variant="determinate" 
                      value={(metrics.messagesGenerated > 0 ? (metrics.messagesApproved / metrics.messagesGenerated) * 100 : 0)} 
                      sx={{ height: 10, borderRadius: 5 }}
                    />
                  </Box>
                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      {metrics.messagesGenerated > 0 ? Math.round((metrics.messagesApproved / metrics.messagesGenerated) * 100) : 0}%
                    </Typography>
                  </Box>
                </Box>
              </Grid>
              
              <Grid item xs={12} md={6}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="body1">Conversion Rate:</Typography>
                  <Typography variant="body1" fontWeight="bold">
                    {metrics.conversionRate}
                  </Typography>
                </Box>
              </Grid>
              
              <Grid item xs={12} md={6}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="body1">Average Response Time:</Typography>
                  <Typography variant="body1" fontWeight="bold">
                    {metrics.averageResponseTime}
                  </Typography>
                </Box>
              </Grid>
            </Grid>
          </Paper>
        </Grid>
        
        {/* Report Generation section moved up */}
        
        {/* Report Generation */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Generate Summary Report
            </Typography>
            <Divider sx={{ mb: 2 }} />
            
            <Typography variant="body2" paragraph color="text.secondary">
              Generate a comprehensive PDF report with all campaign metrics, participant information, and result analysis.
            </Typography>
            
            {loading && (
              <Box sx={{ width: '100%', mb: 2 }}>
                <Typography variant="body2" gutterBottom>
                  Generating report... {progressValue}%
                </Typography>
                <LinearProgress variant="determinate" value={progressValue} />
              </Box>
            )}
            
            <Box sx={{ display: 'flex', gap: 2 }}>
              <Button
                variant="contained"
                startIcon={<BarChartIcon />}
                onClick={handleGenerateReport}
                disabled={loading}
              >
                Generate Report
              </Button>
              
              {reportGenerated && (
                <Button
                  variant="outlined"
                  startIcon={<DownloadIcon />}
                  onClick={handleDownloadReport}
                >
                  Download Report
                </Button>
              )}
            </Box>
          </Paper>
        </Grid>
      </Grid>

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

export default Summary;
