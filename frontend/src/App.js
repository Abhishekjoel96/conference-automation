import React from 'react';
import './App.css';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';

// Import components
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import ParticipantInput from './components/ParticipantInput';
import OutreachDrafts from './components/OutreachDrafts';
import MessageApproval from './components/MessageApproval';
import SentMessages from './components/SentMessages';
import Summary from './components/Summary';

// Create a theme
const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
    background: {
      default: '#f5f5f5',
    },
  },
  typography: {
    fontFamily: [
      '-apple-system',
      'BlinkMacSystemFont',
      '"Segoe UI"',
      'Roboto',
      '"Helvetica Neue"',
      'Arial',
      'sans-serif',
    ].join(','),
  },
});

function App() {
  // Add state for managing the application workflow
  const [eventName, setEventName] = React.useState('');
  const [conferenceUrl, setConferenceUrl] = React.useState('');
  const [userInfo, setUserInfo] = React.useState({
    name: '',
    role: '',
    company: '',
    companyDescription: ''
  });
  const [metrics, setMetrics] = React.useState({
    participants: 0,
    messagesGenerated: 0,
    messagesApproved: 0,
    messagesSent: 0
  });
  // activeStep state removed as it's currently not in use but setActiveStep is passed to child components
  const [, setActiveStep] = React.useState(0);
  const [approvalUrl, setApprovalUrl] = React.useState('');
  
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <div className="app">
          <Header />
          <div className="main-content">
            <Sidebar />
            <div className="content">
              <Routes>
                <Route path="/" element={
                  <ParticipantInput 
                    eventName={eventName} 
                    setEventName={setEventName}
                    conferenceUrl={conferenceUrl}
                    setConferenceUrl={setConferenceUrl}
                    userInfo={userInfo}
                    setUserInfo={setUserInfo}
                    metrics={metrics}
                    setMetrics={setMetrics}
                    setActiveStep={setActiveStep}
                    approvalUrl={approvalUrl}
                    setApprovalUrl={setApprovalUrl}
                  />
                } />
                <Route path="/outreach-drafts" element={<OutreachDrafts />} />
                <Route path="/message-approval" element={<MessageApproval />} />
                <Route path="/sent-messages" element={<SentMessages />} />
                <Route path="/summary" element={<Summary metrics={metrics} />} />
              </Routes>
            </div>
          </div>
        </div>
      </Router>
    </ThemeProvider>
  );
}

export default App;
