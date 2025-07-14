// src/components/ProfilePage.js
import React, { useState, useEffect } from "react";
import axios from "axios";
import { 
    Box, 
    Container, 
    Paper, 
    Typography, 
    Avatar, 
    Alert,
    CircularProgress,
    useTheme
} from "@mui/material";
import { Person } from '@mui/icons-material';

const ProfilePage = () => {
  const [userData, setUserData] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const theme = useTheme();

  useEffect(() => {
    // Function to get user data
    const fetchUserData = async () => {
      const token = localStorage.getItem("token"); // Get token from localStorage
      if (token) {
        try {
          const response = await axios.get("http://localhost:8000/api/users/profile", {
            headers: { Authorization: `Bearer ${token}` }, // Send token in headers
          });
          setUserData(response.data); // Save user data in state
        } catch (err) {
          setError("Error fetching user data");
        }
      } else {
        setError("No token found");
      }
      setLoading(false);
    };

    fetchUserData(); // Call function to get user data
  }, []);

  if (loading) {
    return (
      <Box sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: theme.palette.background.default
      }}>
        <CircularProgress size={60} />
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: theme.palette.background.default
      }}>
        <Alert severity="error" sx={{ maxWidth: 400 }}>
          {error}
        </Alert>
      </Box>
    );
  }

  return (
    <Box sx={{
      minHeight: '100vh',
      background: `linear-gradient(135deg, 
          rgba(15, 139, 141, 0.1) 0%, 
          rgba(236, 154, 41, 0.1) 50%, 
          rgba(185, 163, 148, 0.1) 100%)`,
      py: 4
    }}>
      <Container maxWidth="md">
        <Paper elevation={8} sx={{
          p: 4,
          borderRadius: 3,
          backgroundColor: 'rgba(255, 255, 255, 0.95)',
          backdropFilter: 'blur(10px)',
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)'
        }}>
          <Box sx={{ textAlign: 'center', mb: 4 }}>
            <Avatar sx={{
              width: 120,
              height: 120,
              mx: 'auto',
              mb: 3,
              backgroundColor: theme.palette.primary.main,
              fontSize: '3rem'
            }}>
              <Person sx={{ fontSize: 60 }} />
            </Avatar>
            <Typography variant="h3" component="h1" sx={{
              fontWeight: 700,
              color: theme.palette.text.primary,
              mb: 2
            }}>
              User Profile
            </Typography>
            <Typography variant="body1" sx={{
              color: theme.palette.text.secondary,
              fontSize: '1.1rem'
            }}>
              Manage your account information
            </Typography>
          </Box>

          <Box sx={{
            display: 'grid',
            gap: 3,
            maxWidth: 600,
            mx: 'auto'
          }}>
            <Paper elevation={2} sx={{
              p: 3,
              borderRadius: 2,
              backgroundColor: theme.palette.background.paper
            }}>
              <Typography variant="h6" sx={{
                color: theme.palette.primary.main,
                fontWeight: 600,
                mb: 2
              }}>
                Personal Information
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Typography variant="body1" sx={{
                  fontWeight: 600,
                  color: theme.palette.text.primary,
                  minWidth: 120
                }}>
                  Name:
                </Typography>
                <Typography variant="body1" sx={{
                  color: theme.palette.text.secondary,
                  ml: 2
                }}>
                  {userData?.name || 'Not provided'}
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Typography variant="body1" sx={{
                  fontWeight: 600,
                  color: theme.palette.text.primary,
                  minWidth: 120
                }}>
                  Email:
                </Typography>
                <Typography variant="body1" sx={{
                  color: theme.palette.text.secondary,
                  ml: 2
                }}>
                  {userData?.email || 'Not provided'}
                </Typography>
              </Box>
            </Paper>

            <Paper elevation={2} sx={{
              p: 3,
              borderRadius: 2,
              backgroundColor: theme.palette.background.paper
            }}>
              <Typography variant="h6" sx={{
                color: theme.palette.secondary.main,
                fontWeight: 600,
                mb: 2
              }}>
                Account Status
              </Typography>
              <Box sx={{
                display: 'inline-flex',
                alignItems: 'center',
                px: 2,
                py: 1,
                borderRadius: 2,
                backgroundColor: theme.palette.success.light,
                color: theme.palette.success.contrastText,
                fontWeight: 600
              }}>
                Active Account
              </Box>
            </Paper>
          </Box>
        </Paper>
      </Container>
    </Box>
  );
};

export default ProfilePage;
