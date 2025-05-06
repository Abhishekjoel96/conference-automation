import React, { useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  Button,
  CircularProgress,
  Snackbar,
  Alert,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  Chip
} from '@mui/material';
import DownloadIcon from '@mui/icons-material/Download';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import api from '../services/api';

const ReportGeneration = () => {
  const [loading, setLoading] = useState(false);
  const [notification, setNotification] = useState({ open: false, message: '', severity: 'success' });
  const [reportOptions, setReportOptions] = useState({
    format: 'excel',
    includeApproved: true,
    includePending: true,
    includeRejected: false,
  });
  const [reportUrl, setReportUrl] = useState(null);

  const handleReportOptionChange = (event) => {
    const { name, value, checked } = event.target;
    setReportOptions(prev => ({
      ...prev,
      [name]: name === 'format' ? value : checked
    }));
  };

  const generateReport = async () => {
    setLoading(true);
    try {
      const response = await api.post('/api/reports', reportOptions);
      setReportUrl(response.data.reportUrl);
      setNotification({
        open: true,
        message: 'Report generated successfully!',
        severity: 'success'
      });
    } catch (error) {
      console.error('Error generating report:', error);
      setNotification({
        open: true,
        message: 'Failed to generate report. Please try again.',
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
    <Paper elevation={3} sx={{ p: 3, height: '100%' }}>
      <Typography variant="h5" gutterBottom>
        Generate Reports
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        Create reports of your outreach messages and export them for your records or to share with your team.
      </Typography>

      <Box sx={{ my: 3 }}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <FormControl fullWidth>
              <InputLabel id="format-label">Report Format</InputLabel>
              <Select
                labelId="format-label"
                name="format"
                value={reportOptions.format}
                label="Report Format"
                onChange={handleReportOptionChange}
              >
                <MenuItem value="excel">Excel (.xlsx)</MenuItem>
                <MenuItem value="csv">CSV</MenuItem>
                <MenuItem value="pdf">PDF</MenuItem>
                <MenuItem value="google_sheet">Google Sheet</MenuItem>
              </Select>
            </FormControl>
          </Grid>

          <Grid item xs={12}>
            <Typography variant="subtitle1" gutterBottom>
              Include Messages:
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
              <Chip 
                label="Approved" 
                color={reportOptions.includeApproved ? "success" : "default"}
                onClick={() => setReportOptions(prev => ({ ...prev, includeApproved: !prev.includeApproved }))}
              />
              <Chip 
                label="Pending" 
                color={reportOptions.includePending ? "primary" : "default"}
                onClick={() => setReportOptions(prev => ({ ...prev, includePending: !prev.includePending }))}
              />
              <Chip 
                label="Needs Edits" 
                color={reportOptions.includeRejected ? "warning" : "default"}
                onClick={() => setReportOptions(prev => ({ ...prev, includeRejected: !prev.includeRejected }))}
              />
            </Box>
          </Grid>
        </Grid>
      </Box>

      {reportUrl && (
        <Box sx={{ mt: 2, p: 2, bgcolor: 'background.paper', borderRadius: 1 }}>
          <Typography variant="subtitle1" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
            <CheckCircleIcon color="success" sx={{ mr: 1 }} />
            Report Ready
          </Typography>
          <Button
            variant="outlined"
            color="primary"
            startIcon={<DownloadIcon />}
            href={reportUrl}
            target="_blank"
            rel="noopener noreferrer"
          >
            Download Report
          </Button>
        </Box>
      )}

      <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
        <Button
          variant="contained"
          color="primary"
          disabled={loading}
          onClick={generateReport}
          startIcon={loading ? <CircularProgress size={20} color="inherit" /> : null}
        >
          {loading ? 'Generating...' : 'Generate Report'}
        </Button>
      </Box>

      <Snackbar open={notification.open} autoHideDuration={6000} onClose={handleCloseNotification}>
        <Alert onClose={handleCloseNotification} severity={notification.severity} sx={{ width: '100%' }}>
          {notification.message}
        </Alert>
      </Snackbar>
    </Paper>
  );
};

export default ReportGeneration;
