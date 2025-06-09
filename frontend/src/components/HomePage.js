import React from "react";
import { useNavigate } from "react-router-dom";
import { Button, Container, Typography, Box } from "@mui/material";
import "../styles/HomePage.css";

const HomePage = () => {
    const navigate = useNavigate();

    return (
        <div className="home-container">
            <Container maxWidth="sm">
                <Box sx={{ 
                    mt: 8,
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    gap: 3
                }}>
                    <Typography variant="h2" component="h1" gutterBottom>
                        Bienvenido a TravelApp
                    </Typography>
                    <Typography variant="h5" component="h2" gutterBottom>
                        Tu compañero de viaje perfecto
                    </Typography>
                    <Box sx={{ display: 'flex', gap: 2, mt: 4 }}>
                        <Button 
                            variant="contained" 
                            color="primary" 
                            size="large"
                            onClick={() => navigate("/register")}
                        >
                            Registrarse
                        </Button>
                        <Button 
                            variant="contained" 
                            color="secondary" 
                            size="large"
                            onClick={() => navigate("/login")}
                        >
                            Iniciar Sesión
                        </Button>
                    </Box>
                </Box>
            </Container>
        </div>
    );
};

export default HomePage;
