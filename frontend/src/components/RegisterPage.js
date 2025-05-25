import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Container, TextField, Button, Typography, Box } from "@mui/material";
import "../styles/RegisterPage.css";

const RegisterPage = () => {
    const [userData, setUserData] = useState({
        name: "",
        email: "",
        password: "",
    });
    const [message, setMessage] = useState("");
    const navigate = useNavigate();

    const handleChange = (e) => {
        const { name, value } = e.target;
        setUserData({
            ...userData,
            [name]: value,
        });
    };

    const registerUser = async (e) => {
        e.preventDefault();
        try {
            const response = await fetch("http://localhost:8000/users/register", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(userData),
            });

            const data = await response.json();
            if (response.ok) {
                console.log("User registered successfully:", data);
                setMessage("Usuario registrado exitosamente");
                setTimeout(() => navigate("/login"), 2000);
            } else {
                console.log("Error registering user:", data);
                setMessage(data.detail.map(err => `${err.msg}`).join(', '));
            }
        } catch (error) {
            console.error("Error:", error);
            setMessage("Ocurrió un error al registrar el usuario.");
        }
    };

    return (
        <div className="register-container">
            <Container maxWidth="sm">
                <Box sx={{ 
                    mt: 8,
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    gap: 3
                }}>
                    <Typography variant="h4" component="h1" gutterBottom>
                        Registro
                    </Typography>
                    <form onSubmit={registerUser} style={{ width: '100%' }}>
                        <TextField
                            fullWidth
                            label="Nombre"
                            name="name"
                            value={userData.name}
                            onChange={handleChange}
                            margin="normal"
                            required
                        />
                        <TextField
                            fullWidth
                            label="Email"
                            name="email"
                            type="email"
                            value={userData.email}
                            onChange={handleChange}
                            margin="normal"
                            required
                        />
                        <TextField
                            fullWidth
                            label="Contraseña"
                            name="password"
                            type="password"
                            value={userData.password}
                            onChange={handleChange}
                            margin="normal"
                            required
                        />
                        <Button
                            type="submit"
                            fullWidth
                            variant="contained"
                            color="primary"
                            size="large"
                            sx={{ mt: 3 }}
                        >
                            Registrarse
                        </Button>
                    </form>
                    {message && (
                        <Typography 
                            color={message.includes("exitosamente") ? "success.main" : "error.main"}
                            sx={{ mt: 2 }}
                        >
                            {message}
                        </Typography>
                    )}
                    <Button
                        variant="text"
                        onClick={() => navigate("/login")}
                        sx={{ mt: 2 }}
                    >
                        ¿Ya tienes cuenta? Inicia sesión
                    </Button>
                </Box>
            </Container>
        </div>
    );
};

export default RegisterPage; 