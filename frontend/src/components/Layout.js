// src/components/Layout.js
import React from "react";
import { useNavigate } from "react-router-dom";
import { Avatar, IconButton } from "@mui/material";
import PersonIcon from '@mui/icons-material/Person';

const Layout = ({ children }) => {
  const navigate = useNavigate();
  const isLoggedIn = !!localStorage.getItem("token");

  const handleProfileClick = () => {
    if (isLoggedIn) {
      navigate("/profile"); 
    } else {
      navigate("/login"); 
    }
  };

  return (
    <div className="layout">
      <header className="header">
        <IconButton 
          onClick={handleProfileClick}
          sx={{
            backgroundColor: 'rgba(255, 255, 255, 0.9)',
            '&:hover': {
              backgroundColor: 'rgba(255, 255, 255, 1)',
            }
          }}
        >
          <PersonIcon sx={{ fontSize: 30, color: '#4CAF50' }} />
        </IconButton>
      </header>
      <main>{children}</main>
    </div>
  );
};

export default Layout;
