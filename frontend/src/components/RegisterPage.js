import React, { useState } from "react";
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
import { PersonAddOutlined } from '@mui/icons-material';
import "../styles/LoginPage.css";

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const RegisterPage = () => {
    const [userData, setUserData] = useState({
        full_name: "",
        email: "",
        password: "",
    });
    const [message, setMessage] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const navigate = useNavigate();
    const theme = useTheme();

    const handleChange = (e) => {
        const { name, value } = e.target;
        setUserData({
            ...userData,
            [name]: value,
        });
    };

    const registerUser = async (e) => {
        e.preventDefault();
        setIsLoading(true);
        try {
            const response = await fetch(`${API_URL}/api/auth/register`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(userData),
            });

            const data = await response.json();
            
            if (response.ok) {
                console.log("User registered successfully:", data);
                setMessage("User registered successfully");
                setTimeout(() => navigate("/login"), 2000);
            } else {
                console.log("Error registering user:", data);
                if (Array.isArray(data.detail)) {
                    setMessage(data.detail.map(err => err.msg).join(', '));
                } else if (typeof data.detail === 'string') {
                    setMessage(data.detail);
                } else {
                    setMessage("Error registering user");
                }
            }
        } catch (error) {
            console.error("Error:", error);
            setMessage("Connection error. Please try again.");
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
                            backgroundColor: theme.palette.secondary.main,
                            color: 'white',
                            mb: 2
                        }}>
                            <PersonAddOutlined sx={{ fontSize: 32 }} />
                        </Box>
                        <Typography variant="h4" component="h1" sx={{
                            fontWeight: 700,
                            color: theme.palette.text.primary,
                            mb: 1
                        }}>
                            Create Account
                        </Typography>
                        <Typography variant="body1" sx={{
                            color: theme.palette.text.secondary
                        }}>
                            Join us and start planning your next adventure
                        </Typography>
                    </Box>

                    <form onSubmit={registerUser}>
                        <TextField
                            fullWidth
                            label="Full Name"
                            name="full_name"
                            value={userData.full_name}
                            onChange={handleChange}
                            required
                            disabled={isLoading}
                            sx={{ mb: 3 }}
                            variant="outlined"
                        />
                        <TextField
                            fullWidth
                            label="Email"
                            type="email"
                            name="email"
                            value={userData.email}
                            onChange={handleChange}
                            required
                            disabled={isLoading}
                            sx={{ mb: 3 }}
                            variant="outlined"
                        />
                        <TextField
                            fullWidth
                            label="Password"
                            type="password"
                            name="password"
                            value={userData.password}
                            onChange={handleChange}
                            required
                            disabled={isLoading}
                            sx={{ mb: 3 }}
                            variant="outlined"
                        />
                        
                        {message && (
                            <Alert 
                                severity={message.includes("successfully") ? "success" : "error"} 
                                sx={{ mb: 3 }}
                            >
                                {message}
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
                                backgroundColor: theme.palette.secondary.main,
                                '&:hover': {
                                    backgroundColor: theme.palette.secondary.dark,
                                }
                            }}
                        >
                            {isLoading ? (
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                    <CircularProgress size={20} color="inherit" />
                                    Creating account...
                                </Box>
                            ) : (
                                'Create Account'
                            )}
                        </Button>
                    </form>

                    <Box sx={{ textAlign: 'center', mt: 3 }}>
                        <Typography variant="body2" sx={{ color: theme.palette.text.secondary }}>
                            Already have an account?{' '}
                            <Button
                                onClick={() => navigate("/login")}
                                sx={{
                                    color: theme.palette.secondary.main,
                                    textTransform: 'none',
                                    fontWeight: 600,
                                    '&:hover': {
                                        textDecoration: 'underline'
                                    }
                                }}
                            >
                                Sign in here
                            </Button>
                        </Typography>
                    </Box>
                </Paper>
            </Container>
        </Box>
    );
};

export default RegisterPage; 