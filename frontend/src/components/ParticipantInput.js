import React, { useState, useEffect } from 'react';
import api from '../services/api';
import {
  Box,
  Typography,
  TextField,
  Button,
  Grid,
  Paper,
  Alert,
  Snackbar,
  Tab,
  Tabs,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  LinearProgress,
  CircularProgress,
  IconButton
} from '@mui/material';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import PersonAddIcon from '@mui/icons-material/PersonAdd';
import LinkIcon from '@mui/icons-material/Link';
import LaunchIcon from '@mui/icons-material/Launch';
import RefreshIcon from '@mui/icons-material/Refresh';

// Participant input component for both manual entry and loading from conference websites

const ParticipantInput = ({ eventName, setEventName, conferenceUrl, setConferenceUrl, userInfo, setUserInfo, metrics, setMetrics, setActiveStep, approvalUrl, setApprovalUrl }) => {
  const [tabValue, setTabValue] = useState(0);
  const [loginCredentials, setLoginCredentials] = useState({ username: '', password: '' });
  
  // Add state variables for job tracking
  const [jobId, setJobId] = useState(null);
  const [jobStatus, setJobStatus] = useState(null);
  const [jobProgress, setJobProgress] = useState(0);
  const [jobMessage, setJobMessage] = useState('');
  const [jobPollingInterval, setJobPollingInterval] = useState(null);
  const [manualParticipant, setManualParticipant] = useState({
    name: '',
    role: '',
    company: '',
    country: '',
    linkedin_url: '',
    notes: '',
  });
  const [participants, setParticipants] = useState([]);
  const [loading, setLoading] = useState(false);
  const [notification, setNotification] = useState({ open: false, message: '', severity: 'success' });

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  const handleUserInfoChange = (e) => {
    const { name, value } = e.target;
    setUserInfo({ ...userInfo, [name]: value });
  };

  const handleManualParticipantChange = (e) => {
    const { name, value } = e.target;
    setManualParticipant({ ...manualParticipant, [name]: value });
  };

  const handleManualAdd = (e) => {
    e.preventDefault();
    if (manualParticipant.name && manualParticipant.company) {
      setParticipants([...participants, manualParticipant]);
      setManualParticipant({
        name: '',
        role: '',
        company: '',
        country: '',
        linkedin_url: '',
        notes: '',
      });
      setNotification({
        open: true,
        message: 'Participant added successfully!',
        severity: 'success',
      });
    } else {
      setNotification({
        open: true,
        message: 'Name and Company are required fields',
        severity: 'error',
      });
    }
  };

  const handleCloseNotification = () => {
    setNotification({ ...notification, open: false });
  };

  // Function to scrape participants from conference URL
  const handleScrapeConference = async () => {
    if (!eventName || !conferenceUrl) {
      setNotification({
        open: true,
        message: 'Event name and conference URL are required',
        severity: 'error',
      });
      return;
    }
    
    if (!userInfo.name || !userInfo.company) {
      setNotification({
        open: true,
        message: 'Please complete your information before scraping participants',
        severity: 'warning',
      });
      return;
    }
    
    setLoading(true);
    setNotification({
      open: true,
      message: 'Scraping participants from conference website. This may take up to 15 minutes for large conferences...',
      severity: 'info',
    });
    
    try {
      console.log('Attempting to scrape from:', conferenceUrl);
      
      // Prepare login credentials if provided
      const credentials = (loginCredentials.username && loginCredentials.password) ? {
        username: loginCredentials.username,
        password: loginCredentials.password
      } : null;
      
      // First get the configured phantom ID from the backend
      const healthCheck = await api.get('/api/health');
      console.log('Health check response:', healthCheck.data);
      
      // Get the phantom ID from the backend health check
      const phantomId = healthCheck.data.config.phantom_conference_scraper_id;
      console.log('Using phantom ID from backend:', phantomId);
      
      // Call the API to scrape participants with increased timeout
      const response = await api.post('/scrape', {
        event_name: eventName,
        conference_url: conferenceUrl,
        phantom_id: phantomId,  // Use the configured phantom ID
        login_credentials: credentials
      }, { timeout: 950000 }); // Set almost 16 minutes timeout on client side
      
      console.log('Scrape response:', response.data);
      
      if (response.data.status === 'success' && response.data.participants) {
        // Check if any participants were returned
        if (response.data.participants.length === 0) {
          setNotification({
            open: true,
            message: 'No participants found. The conference website structure may not be compatible with automatic scraping. Try adding participants manually.',
            severity: 'warning',
          });
          setLoading(false);
          return;
        }
        
        // Add the scraped participants to our state with all available data
        const scrapedParticipants = response.data.participants.map(p => ({
          name: p.name,
          role: p.role || '',
          company: p.company,
          country: p.country || '',
          linkedin_url: p.linkedin_url || '',
          notes: p.bio || ''
        }));
        
        setParticipants([...participants, ...scrapedParticipants]);
        
        // Show success message
        setNotification({
          open: true,
          message: `Successfully scraped ${scrapedParticipants.length} participants from the conference website.`,
          severity: 'success',
        });
        
        // If we have participants, automatically start the workflow to process them
        if (scrapedParticipants.length > 0) {
          setTabValue(1);
          
          // Ask user if they want to start the automated workflow
          const startWorkflow = window.confirm(`Successfully scraped ${scrapedParticipants.length} participants. Do you want to start processing them through the LLM pipeline now?`);
          
          if (startWorkflow) {
            // Small delay before starting workflow
            setTimeout(() => {
              handleGenerateMessages();
            }, 1000);
          }
        }
      } else {
        throw new Error(response.data.message || 'Failed to scrape participants');
      }
    } catch (error) {
      console.error('Scraping error:', error);
      
      // Handle timeout error specifically
      if (error.message && (error.message.includes('timeout') || error.code === 'ECONNABORTED')) {
        setNotification({
          open: true,
          message: 'Error scraping conference: timeout exceeded. The conference website may be too large. Try adding key participants manually or reduce the scraping scope.',
          severity: 'error',
        });
      } else {
        setNotification({
          open: true,
          message: `Error scraping conference: ${error.message || 'Unknown error'}. You can add participants manually.`,
          severity: 'error',
        });
      }
    } finally {
      setLoading(false);
    }
  };
  
  // Function to check job status
  const checkJobStatus = async (id) => {
    try {
      const response = await api.get(`/workflow/status/${id}`);
      console.log('Job status:', response.data);
      
      setJobStatus(response.data.status);
      setJobProgress(response.data.progress * 100); // Convert to percentage
      setJobMessage(response.data.message);
      
      // If job is completed or failed, stop polling
      if (response.data.status === 'completed') {
        clearInterval(jobPollingInterval);
        setJobPollingInterval(null);
        setLoading(false);
        
        // Update metrics if available
        if (response.data.result && response.data.result.metrics) {
          setMetrics(response.data.result.metrics);
        }
        
        // Set approval URL if available
        if (response.data.result && response.data.result.approval_url) {
          setApprovalUrl(response.data.result.approval_url);
        }
        
        setNotification({
          open: true,
          message: 'Process completed successfully! Check the approval dashboard.',
          severity: 'success',
        });
        
        // Navigate to approval
        setActiveStep(2);
      } else if (response.data.status === 'failed') {
        clearInterval(jobPollingInterval);
        setJobPollingInterval(null);
        setLoading(false);
        
        setNotification({
          open: true,
          message: `Error: ${response.data.message}`,
          severity: 'error',
        });
      }
    } catch (error) {
      console.error('Error checking job status:', error);
    }
  };
  
  // Clean up polling interval on component unmount
  useEffect(() => {
    return () => {
      if (jobPollingInterval) {
        clearInterval(jobPollingInterval);
      }
    };
  }, [jobPollingInterval]);
  
  // Function to generate messages for participants
  const handleGenerateMessages = async () => {
    if (participants.length === 0) {
      setNotification({
        open: true,
        message: 'Please add at least one participant',
        severity: 'error',
      });
      return;
    }

    if (!eventName || !userInfo.name || !userInfo.company || !userInfo.role) {
      setNotification({
        open: true,
        message: 'Event name, your name, company, and role are required',
        severity: 'error',
      });
      return;
    }
    
    setLoading(true);
    setNotification({
      open: true,
      message: 'Starting background process to research participants and generate messages...',
      severity: 'info',
    });

    try {
      // Ask if user wants to skip the research phase (which is time consuming)
      const skipResearch = window.confirm(
        'The research phase can take a long time. Would you like to skip detailed research and proceed with basic information only? (Recommended for testing or when you have many participants)'
      );
      
      // Format the participant data for the API
      const participantsForApi = participants.map(p => ({
        name: p.name,
        role: p.role || '',
        company: p.company,
        country: p.country || '',
        linkedin_url: p.linkedin_url || '',
        notes: p.notes || ''
      }));
      
      // Call the workflow API endpoint to start background processing
      const response = await api.post('/workflow/start', {
        event_name: eventName,
        conference_url: conferenceUrl,
        login_credentials: (loginCredentials.username && loginCredentials.password) ? {
          username: loginCredentials.username,
          password: loginCredentials.password
        } : null,
        user_name: userInfo.name,
        user_role: userInfo.role,
        user_company_name: userInfo.company,
        user_company_description: userInfo.companyDescription,
        participants: participantsForApi,
        skip_research: skipResearch // Add option to skip research phase
      });
      
      console.log('Workflow API response:', response.data);
      
      if (response.data.status === 'success') {
        // Store the job ID
        setJobId(response.data.job_id);
        
        setNotification({
          open: true,
          message: 'Background process started! You can navigate to other tabs while processing continues.',
          severity: 'success',
        });
        
        // Start polling for job status
        const intervalId = setInterval(() => {
          checkJobStatus(response.data.job_id);
        }, 5000); // Check every 5 seconds
        
        setJobPollingInterval(intervalId);
      } else {
        throw new Error(response.data.message || 'Unknown error');
      }
    } catch (error) {
      console.error('Workflow error:', error);
      setLoading(false);
      
      setNotification({
        open: true,
        message: `Error starting workflow: ${error.message || 'Unknown error'}`,
        severity: 'error',
      });
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <div>
          <Typography variant="h4" gutterBottom>
            Participant Input
          </Typography>
          <Typography variant="subtitle1" color="text.secondary">
            Add conference participants to generate personalized outreach messages
          </Typography>
        </div>
        <Button 
          variant="outlined" 
          startIcon={<LaunchIcon />}
          href="https://docs.google.com/spreadsheets/d/1-81K4OzYWm4u2pjW7irq23kxXes6PjSKP9YiGGCzyiE/edit?usp=drive_link" 
          target="_blank"
        >
          Open Participants List
        </Button>
      </Box>
      
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>Event Information</Typography>
        <Typography variant="body2" color="text.secondary" paragraph>
          Enter the conference details and URL to automatically scrape participant information.
        </Typography>
        <Grid container spacing={2}>
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Event Name"
              name="eventName"
              variant="outlined"
              value={eventName}
              onChange={(e) => setEventName(e.target.value)}
              required
              margin="normal"
            />
          </Grid>
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Conference URL"
              name="conferenceUrl"
              variant="outlined"
              value={conferenceUrl}
              onChange={(e) => setConferenceUrl(e.target.value)}
              required
              margin="normal"
              helperText="URL of the conference website with participant/speaker information"
            />
          </Grid>
        </Grid>
        <Typography variant="subtitle1" gutterBottom sx={{ mt: 2 }}>
          Login Credentials (Optional - only if the conference website requires login)
        </Typography>
        <Grid container spacing={2}>
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Username/Email"
              name="username"
              variant="outlined"
              value={loginCredentials.username}
              onChange={(e) => setLoginCredentials({ ...loginCredentials, username: e.target.value })}
              margin="normal"
              helperText="Optional - only needed for password-protected websites"
            />
          </Grid>
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Password"
              name="password"
              type="password"
              variant="outlined"
              value={loginCredentials.password}
              onChange={(e) => setLoginCredentials({ ...loginCredentials, password: e.target.value })}
              margin="normal"
              helperText="Optional - only needed for password-protected websites"
            />
          </Grid>
        </Grid>
        <Box sx={{ mt: 2, display: 'flex', justifyContent: 'flex-end' }}>
          <Button
            variant="contained"
            color="primary"
            onClick={handleScrapeConference}
            disabled={loading || !eventName || !conferenceUrl}
            startIcon={<CloudUploadIcon />}
          >
            Scrape Conference Participants
          </Button>
        </Box>
      </Paper>
      
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>Your Information</Typography>
        <Grid container spacing={2}>
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Your Name"
              name="name"
              variant="outlined"
              value={userInfo.name}
              onChange={handleUserInfoChange}
              required
              margin="normal"
            />
          </Grid>
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Your Role"
              name="role"
              variant="outlined"
              value={userInfo.role}
              onChange={handleUserInfoChange}
              required
              margin="normal"
            />
          </Grid>
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Your Company"
              name="company"
              variant="outlined"
              value={userInfo.company}
              onChange={handleUserInfoChange}
              required
              margin="normal"
            />
          </Grid>
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Company Description"
              name="companyDescription"
              variant="outlined"
              value={userInfo.companyDescription}
              onChange={handleUserInfoChange}
              multiline
              rows={3}
              margin="normal"
            />
          </Grid>
        </Grid>
      </Paper>

      <Paper sx={{ p: 3 }}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}>
          <Tabs value={tabValue} onChange={handleTabChange}>
            <Tab label="Manual Input" />
            <Tab label="Current Participants" />
          </Tabs>
        </Box>
        
        {tabValue === 0 && (
          <Box component="form" onSubmit={handleManualAdd}>
            <Typography variant="body1" paragraph>
              Add conference participants you want to connect with. After adding participants, click "Start Automated Workflow" to research them and generate personalized messages.
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Name"
                  name="name"
                  variant="outlined"
                  value={manualParticipant.name}
                  onChange={handleManualParticipantChange}
                  required
                  margin="normal"
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Role"
                  name="role"
                  variant="outlined"
                  value={manualParticipant.role}
                  onChange={handleManualParticipantChange}
                  margin="normal"
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Company"
                  name="company"
                  variant="outlined"
                  value={manualParticipant.company}
                  onChange={handleManualParticipantChange}
                  required
                  margin="normal"
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Country"
                  name="country"
                  variant="outlined"
                  value={manualParticipant.country}
                  onChange={handleManualParticipantChange}
                  margin="normal"
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="LinkedIn URL"
                  name="linkedin_url"
                  variant="outlined"
                  value={manualParticipant.linkedin_url}
                  onChange={handleManualParticipantChange}
                  margin="normal"
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Notes"
                  name="notes"
                  variant="outlined"
                  value={manualParticipant.notes}
                  onChange={handleManualParticipantChange}
                  multiline
                  rows={2}
                  margin="normal"
                />
              </Grid>
              <Grid item xs={12}>
                <Button
                  type="submit"
                  variant="contained"
                  startIcon={<PersonAddIcon />}
                  sx={{ mt: 2 }}
                >
                  Add Participant
                </Button>
              </Grid>
            </Grid>
          </Box>
        )}
        
        {tabValue === 1 && (
          <Box>
            <Typography variant="body1" paragraph>
              Current list of participants ({participants.length})
            </Typography>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Name</TableCell>
                    <TableCell>Role</TableCell>
                    <TableCell>Company</TableCell>
                    <TableCell>Country</TableCell>
                    <TableCell>LinkedIn</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {participants.map((participant, index) => (
                    <TableRow key={index}>
                      <TableCell>{participant.name}</TableCell>
                      <TableCell>{participant.role}</TableCell>
                      <TableCell>{participant.company}</TableCell>
                      <TableCell>{participant.country}</TableCell>
                      <TableCell>
                        {participant.linkedin_url && (
                          <Button 
                            size="small" 
                            startIcon={<LinkIcon />}
                            href={participant.linkedin_url.startsWith('http') ? participant.linkedin_url : `https://${participant.linkedin_url}`}
                            target="_blank"
                          >
                            View
                          </Button>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Box>
        )}
      </Paper>

      <Paper sx={{ p: 3, mt: 4, bgcolor: '#f8f9fa' }}>
        <Typography variant="h6" gutterBottom>
          Generate Personalized Messages
        </Typography>
        <Typography variant="body2" color="text.secondary" paragraph>
          Ready to start the automated workflow? This will research all participants, gather company information, and generate personalized outreach messages.
        </Typography>
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
          <Button
            variant="contained"
            color="primary"
            onClick={handleGenerateMessages}
            disabled={loading || participants.length === 0}
            fullWidth
            sx={{ mt: 2 }}
          >
            {loading ? <CircularProgress size={24} color="inherit" /> : 'Start Automated Workflow'}
          </Button>
          {/* Display job status if a job is running */}
          {jobId && jobStatus && (
            <Paper elevation={2} sx={{ p: 2, mt: 2 }}>
              <Box sx={{ width: '100%' }}>
                <Typography variant="h6">Background Process Status</Typography>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  {jobMessage}
                </Typography>
                
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <Box sx={{ width: '100%', mr: 1 }}>
                    <LinearProgress variant="determinate" value={jobProgress} />
                  </Box>
                  <Box sx={{ minWidth: 35 }}>
                    <Typography variant="body2" color="text.secondary">
                      {`${Math.round(jobProgress)}%`}
                    </Typography>
                  </Box>
                  <IconButton 
                    size="small" 
                    onClick={() => checkJobStatus(jobId)}
                    title="Refresh status"
                  >
                    <RefreshIcon />
                  </IconButton>
                </Box>
                
                <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                  Status: {jobStatus.charAt(0).toUpperCase() + jobStatus.slice(1)}
                </Typography>
              </Box>
            </Paper>
          )}
        </Box>
        {loading && (
          <Box sx={{ mt: 2, textAlign: 'center' }}>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
              Processing... This will research participants and generate personalized messages.
            </Typography>
            <LinearProgress color="primary" />
          </Box>
        )}
      </Paper>

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

export default ParticipantInput;
