import React from 'react';
import { AppBar, Toolbar, Typography, Button } from '@mui/material';
import { styled } from '@mui/system';

const StyledToolbar = styled(Toolbar)(({ theme }) => ({
  display: 'flex',
  justifyContent: 'space-between',
}));

const Header = () => {
  return (
    <AppBar position="static">
      <StyledToolbar>
        <Typography variant="h6" component="div">
          Conference Networking Automation
        </Typography>
        <div>
          <Button color="inherit" href="https://drive.google.com/drive/folders/1L-J7JVGeMPP0Cw7GGonX-W6EyAOzrq-w?usp=drive_link" target="_blank">
            Conference Outreach Drive
          </Button>
        </div>
      </StyledToolbar>
    </AppBar>
  );
};

export default Header;
