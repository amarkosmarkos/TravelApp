import React, { useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import { 
    Box, 
    Container, 
    Paper, 
    TextField, 
    Button, 
    Typography, 
    Alert,
    CircularProgress,
    useTheme
} from "@mui/material";
import { LockOutlined } from '@mui/icons-material';
import '../styles/LoginPage.css';

const API_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

// Configure axios with timeout and default headers
axios.defaults.timeout = 10000; // 10 seconds
axios.defaults.headers.common['Content-Type'] = 'application/x-www-form-urlencoded';

const LoginPage = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();
  const theme = useTheme();

  const handleLogin = async (e) => {
    e.preventDefault();
    setError("");
    setIsLoading(true);

    try {
      console.log("Attempting login with:", { email });
      
      // Create login data object
      const loginData = new URLSearchParams();
      loginData.append('username', email);
      loginData.append('password', password);

      // Perform login request
      const response = await axios.post(
        `${API_URL}/api/auth/token`,
        loginData.toString(),
        {
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
          validateStatus: function (status) {
            return status < 500; // Resolve only if status is less than 500
          }
        }
      );

      console.log("Server response:", response.data);

      if (response.status === 200) {
        const { access_token } = response.data;
        localStorage.setItem("token", access_token);
        
        // Verify that the token was saved correctly
        const savedToken = localStorage.getItem("token");
        if (!savedToken) {
          throw new Error("Could not save token");
        }
        
        // Verify that the token is valid by making a test request
        try {
          const testResponse = await axios.get(`${API_URL}/api/auth/me`, {
            headers: {
              'Authorization': `Bearer ${savedToken}`
            }
          });
          
          if (testResponse.status === 200) {
            console.log("Authentication test successful:", testResponse.data);
            navigate("/main", { replace: true });
          } else {
            throw new Error("Token verification error");
          }
        } catch (testError) {
          console.error("Authentication test error:", testError);
          localStorage.removeItem("token");
          throw new Error("Error verifying authentication");
        }
      } else {
        throw new Error(response.data.detail || "Login error");
      }
    } catch (err) {
      console.error("Complete error:", err);
      if (err.response) {
        console.error("Error response:", err.response.data);
        setError(err.response.data.detail || "Login error");
      } else if (err.message) {
        setError(err.message);
      } else {
        setError("Connection error. Please try again.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Box sx={{
      minHeight: '100vh',
      background: `linear-gradient(135deg, 
          rgba(15, 139, 141, 0.9) 0%, 
          rgba(236, 154, 41, 0.8) 50%, 
          rgba(185, 163, 148, 0.7) 100%)`,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      p: 2
    }}>
      <Container maxWidth="sm">
        <Paper elevation={8} sx={{
          p: 4,
          borderRadius: 3,
          backgroundColor: 'rgba(255, 255, 255, 0.95)',
          backdropFilter: 'blur(10px)',
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)'
        }}>
          <Box sx={{ textAlign: 'center', mb: 4 }}>
            <Box sx={{
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: 64,
              height: 64,
              borderRadius: '50%',
              backgroundColor: theme.palette.primary.main,
              color: 'white',
              mb: 2
            }}>
              <LockOutlined sx={{ fontSize: 32 }} />
            </Box>
            <Typography variant="h4" component="h1" sx={{
              fontWeight: 700,
              color: theme.palette.text.primary,
              mb: 1
            }}>
              Welcome Back
            </Typography>
            <Typography variant="body1" sx={{
              color: theme.palette.text.secondary
            }}>
              Sign in to your account to continue
            </Typography>
          </Box>

          <form onSubmit={handleLogin}>
            <TextField
              fullWidth
              label="Email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              disabled={isLoading}
              sx={{ mb: 3 }}
              variant="outlined"
            />
            <TextField
              fullWidth
              label="Password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              disabled={isLoading}
              sx={{ mb: 3 }}
              variant="outlined"
            />
            
            {error && (
              <Alert severity="error" sx={{ mb: 3 }}>
                {error}
              </Alert>
            )}
            
            <Button
              type="submit"
              fullWidth
              variant="contained"
              disabled={isLoading}
              sx={{
                py: 1.5,
                fontSize: '1.1rem',
                fontWeight: 600,
                backgroundColor: theme.palette.primary.main,
                '&:hover': {
                  backgroundColor: theme.palette.primary.dark,
                }
              }}
            >
              {isLoading ? (
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <CircularProgress size={20} color="inherit" />
                  Signing in...
                </Box>
              ) : (
                'Sign In'
              )}
            </Button>
          </form>

          <Box sx={{ textAlign: 'center', mt: 3 }}>
            <Typography variant="body2" sx={{ color: theme.palette.text.secondary }}>
              Don't have an account?{' '}
              <Button
                onClick={() => navigate("/register")}
                sx={{
                  color: theme.palette.primary.main,
                  textTransform: 'none',
                  fontWeight: 600,
                  '&:hover': {
                    textDecoration: 'underline'
                  }
                }}
              >
                Sign up here
              </Button>
            </Typography>
          </Box>
        </Paper>
      </Container>
    </Box>
  );
};

export default LoginPage;
