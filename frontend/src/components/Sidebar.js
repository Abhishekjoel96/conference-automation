import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  Box, 
  List, 
  ListItem, 
  ListItemIcon, 
  ListItemText,
  Paper,
  styled
} from '@mui/material';
import PersonAddIcon from '@mui/icons-material/PersonAdd';
import EditNoteIcon from '@mui/icons-material/EditNote';
import ThumbUpAltIcon from '@mui/icons-material/ThumbUpAlt';
import SendIcon from '@mui/icons-material/Send';
import SummarizeIcon from '@mui/icons-material/Summarize';

const StyledSidebar = styled(Paper)(({ theme }) => ({
  width: '250px',
  height: 'calc(100vh - 64px)',
  position: 'sticky',
  top: '64px',
  padding: theme.spacing(2),
  borderRadius: 0,
}));

const StyledListItem = styled(ListItem)(({ theme, active }) => ({
  borderRadius: theme.spacing(1),
  marginBottom: theme.spacing(1),
  backgroundColor: active ? 'rgba(25, 118, 210, 0.08)' : 'transparent',
  '&:hover': {
    backgroundColor: 'rgba(25, 118, 210, 0.12)',
  },
}));

const Sidebar = () => {
  const location = useLocation();
  
  const menuItems = [
    { text: 'Participant Input', icon: <PersonAddIcon />, path: '/' },
    { text: 'Outreach Drafts', icon: <EditNoteIcon />, path: '/outreach-drafts' },
    { text: 'Message Approval', icon: <ThumbUpAltIcon />, path: '/message-approval' },
    { text: 'Sent Messages', icon: <SendIcon />, path: '/sent-messages' },
    { text: 'Summary', icon: <SummarizeIcon />, path: '/summary' },
  ];

  return (
    <StyledSidebar elevation={2}>
      <List>
        {menuItems.map((item) => (
          <StyledListItem 
            button 
            component={Link} 
            to={item.path} 
            key={item.text}
            active={location.pathname === item.path ? 1 : 0}
          >
            <ListItemIcon>{item.icon}</ListItemIcon>
            <ListItemText primary={item.text} />
          </StyledListItem>
        ))}
      </List>
    </StyledSidebar>
  );
};

export default Sidebar;
