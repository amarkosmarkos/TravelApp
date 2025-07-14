import React from "react";
import { useNavigate } from "react-router-dom";
import { 
    Button, 
    Container, 
    Typography, 
    Box, 
    Card, 
    CardContent,
    Grid,
    Paper,
    useTheme
} from "@mui/material";
import { 
    FlightTakeoff, 
    Explore, 
    Favorite,
    ArrowForward 
} from '@mui/icons-material';
import AnimatedBackground from './AnimatedBackground';
import "../styles/HomePage.css";

const HomePage = () => {
    const navigate = useNavigate();
    const theme = useTheme();

    const features = [
        {
            icon: <FlightTakeoff sx={{ fontSize: 40, color: theme.palette.primary.main }} />,
            title: "Plan Your Trip",
            description: "Create personalized itineraries with our intelligent tools"
        },
        {
            icon: <Explore sx={{ fontSize: 40, color: theme.palette.secondary.main }} />,
            title: "Explore Destinations",
            description: "Discover amazing places with personalized recommendations"
        },
        {
            icon: <Favorite sx={{ fontSize: 40, color: theme.palette.neutral.main }} />,
            title: "Save Favorites",
            description: "Organize and save your favorite destinations for future trips"
        }
    ];

    return (
        <div className="home-container">
            {/* Hero Section */}
            <Box 
                sx={{
                    minHeight: '100vh',
                    background: `linear-gradient(135deg, 
                        rgba(15, 139, 141, 0.9) 0%, 
                        rgba(236, 154, 41, 0.8) 50%, 
                        rgba(185, 163, 148, 0.7) 100%)`,
                    display: 'flex',
                    alignItems: 'center',
                    position: 'relative',
                    overflow: 'hidden'
                }}
            >
                {/* Animated Background */}
                <AnimatedBackground />
                
                <Container maxWidth="lg" sx={{ position: 'relative', zIndex: 3 }}>
                    <Grid container spacing={4} alignItems="center">
                        {/* Left Column - Main Content */}
                        <Grid item xs={12} md={6}>
                            <Box sx={{ textAlign: { xs: 'center', md: 'left' } }}>
                                <Typography 
                                    variant="h1" 
                                    component="h1" 
                                    gutterBottom
                                    sx={{
                                        color: 'white',
                                        fontWeight: 700,
                                        fontSize: { xs: '2.5rem', md: '3.5rem' },
                                        textShadow: '2px 2px 4px rgba(0, 0, 0, 0.3)',
                                        mb: 2,
                                        animation: 'fadeInUp 1s ease-out'
                                    }}
                                >
                                    Welcome to TravelApp
                                </Typography>
                                
                                <Typography 
                                    variant="h4" 
                                    component="h2" 
                                    gutterBottom
                                    sx={{
                                        color: 'white',
                                        fontWeight: 400,
                                        mb: 4,
                                        textShadow: '1px 1px 2px rgba(0, 0, 0, 0.3)',
                                        opacity: 0.9,
                                        animation: 'fadeInUp 1s ease-out 0.2s both'
                                    }}
                                >
                                    Your perfect travel companion
                                </Typography>
                                
                                <Typography 
                                    variant="body1" 
                                    sx={{
                                        color: 'white',
                                        fontSize: '1.1rem',
                                        mb: 4,
                                        opacity: 0.8,
                                        lineHeight: 1.6,
                                        animation: 'fadeInUp 1s ease-out 0.4s both'
                                    }}
                                >
                                    Discover amazing destinations, plan unique itineraries and 
                                    create unforgettable memories with our intelligent platform.
                                </Typography>
                                
                                <Box sx={{ 
                                    display: 'flex', 
                                    gap: 2, 
                                    flexDirection: { xs: 'column', sm: 'row' },
                                    justifyContent: { xs: 'center', md: 'flex-start' },
                                    animation: 'fadeInUp 1s ease-out 0.6s both'
                                }}>
                                    <Button 
                                        variant="contained" 
                                        size="large"
                                        onClick={() => navigate("/register")}
                                        sx={{
                                            backgroundColor: theme.palette.primary.main,
                                            '&:hover': {
                                                backgroundColor: theme.palette.primary.dark,
                                                transform: 'translateY(-2px)',
                                            },
                                            px: 4,
                                            py: 1.5,
                                            fontSize: '1.1rem',
                                            boxShadow: '0 4px 12px rgba(15, 139, 141, 0.3)',
                                        }}
                                        endIcon={<ArrowForward />}
                                    >
                                        Get Started
                                    </Button>
                                    <Button 
                                        variant="outlined" 
                                        size="large"
                                        onClick={() => navigate("/login")}
                                        sx={{
                                            borderColor: 'white',
                                            color: 'white',
                                            '&:hover': {
                                                borderColor: 'white',
                                                backgroundColor: 'rgba(255, 255, 255, 0.1)',
                                                transform: 'translateY(-2px)',
                                            },
                                            px: 4,
                                            py: 1.5,
                                            fontSize: '1.1rem'
                                        }}
                                    >
                                        Sign In
                                    </Button>
                                </Box>
                            </Box>
                        </Grid>
                        
                        {/* Right Column - Features Cards */}
                        <Grid item xs={12} md={6}>
                            <Grid container spacing={3}>
                                {features.map((feature, index) => (
                                    <Grid item xs={12} sm={6} md={12} key={index}>
                                        <Card 
                                            sx={{
                                                backgroundColor: 'rgba(255, 255, 255, 0.95)',
                                                backdropFilter: 'blur(10px)',
                                                borderRadius: 3,
                                                boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
                                                transition: 'transform 0.3s ease, box-shadow 0.3s ease',
                                                '&:hover': {
                                                    transform: 'translateY(-5px)',
                                                    boxShadow: '0 12px 40px rgba(0, 0, 0, 0.15)',
                                                },
                                                animation: `fadeInUp 1s ease-out ${0.8 + index * 0.2}s both`
                                            }}
                                        >
                                            <CardContent sx={{ p: 3 }}>
                                                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                                                    {feature.icon}
                                                </Box>
                                                <Typography 
                                                    variant="h6" 
                                                    component="h3" 
                                                    gutterBottom
                                                    sx={{ 
                                                        fontWeight: 600,
                                                        color: theme.palette.text.primary
                                                    }}
                                                >
                                                    {feature.title}
                                                </Typography>
                                                <Typography 
                                                    variant="body2" 
                                                    sx={{ 
                                                        color: theme.palette.text.secondary,
                                                        lineHeight: 1.6
                                                    }}
                                                >
                                                    {feature.description}
                                                </Typography>
                                            </CardContent>
                                        </Card>
                                    </Grid>
                                ))}
                            </Grid>
                        </Grid>
                    </Grid>
                </Container>
            </Box>
        </div>
    );
};

export default HomePage;
