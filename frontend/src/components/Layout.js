// src/components/Layout.js
import React from 'react';
import { useNavigate, useLocation, Outlet } from 'react-router-dom';
import { AppBar, Toolbar, Button, Typography, Box } from '@mui/material';
import LogoutIcon from '@mui/icons-material/Logout';
import AccountCircleIcon from '@mui/icons-material/AccountCircle';
import '../styles/Layout.css';

const Layout = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const isAuthenticated = !!localStorage.getItem("token");

  const handleLogout = () => {
    localStorage.removeItem("token");
    navigate('/');
  };

  const handleProfile = () => {
    navigate('/profile');
  };

  const handleLogoClick = () => {
    if (isAuthenticated) {
      navigate('/main');
    } else {
      navigate('/');
    }
  };

  return (
    <div className="layout">
      <AppBar position="fixed" className="header" sx={{ zIndex: 1200 }}>
        <Toolbar sx={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center',
          minHeight: '64px !important',
          padding: '0 24px'
        }}>
          <Box sx={{ width: 120 }} /> {/* Espacio izquierdo */}
          
          <Typography
            variant="h4"
            component="div"
            sx={{
              fontFamily: 'Playfair Display, serif',
              fontWeight: 700,
              color: '#111',
              cursor: 'pointer',
              flex: 1,
              textAlign: 'center'
            }}
            onClick={handleLogoClick}
          >
            Voasis
          </Typography>

          <Box sx={{ 
            width: 120,
            display: 'flex',
            justifyContent: 'flex-end',
            gap: 5
          }}>
            {isAuthenticated && (
              <>
                <Button
                  onClick={handleProfile}
                  startIcon={<AccountCircleIcon />}
                  sx={{
                    color: '#111',
                    '&:hover': {
                      backgroundColor: 'rgba(0, 0, 0, 0.04)',
                    },
                  }}
                >
                  Profile
                </Button>
                <Button
                  onClick={handleLogout}
                  startIcon={<LogoutIcon />}
                  sx={{
                    color: '#111',
                    '&:hover': {
                      backgroundColor: 'rgba(0, 0, 0, 0.04)',
                    },
                  }}
                >
                  Logout
                </Button>
              </>
            )}
          </Box>
        </Toolbar>
      </AppBar>

      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
};

export default Layout;
