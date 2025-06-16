import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import "../styles/LoginPage.css";

const RegisterPage = () => {
    const [userData, setUserData] = useState({
        full_name: "",
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
            const response = await fetch("http://localhost:8000/api/auth/register", {
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
                if (Array.isArray(data.detail)) {
                    setMessage(data.detail.map(err => err.msg).join(', '));
                } else if (typeof data.detail === 'string') {
                    setMessage(data.detail);
                } else {
                    setMessage("Error al registrar el usuario");
                }
            }
        } catch (error) {
            console.error("Error:", error);
            setMessage("Error de conexión. Por favor, intente de nuevo.");
        }
    };

    return (
        <div className="login-container">
            <div className="form-container">
                <h1>Registro</h1>
                <form onSubmit={registerUser}>
                    <div>
                        <label>Nombre completo:</label>
                        <input
                            type="text"
                            name="full_name"
                            value={userData.full_name}
                            onChange={handleChange}
                            required
                        />
                    </div>
                    <div>
                        <label>Email:</label>
                        <input
                            type="email"
                            name="email"
                            value={userData.email}
                            onChange={handleChange}
                            required
                        />
                    </div>
                    <div>
                        <label>Contraseña:</label>
                        <input
                            type="password"
                            name="password"
                            value={userData.password}
                            onChange={handleChange}
                            required
                        />
                    </div>
                    {message && <p style={{ color: message.includes("exitosamente") ? "#4CAF50" : "red" }}>{message}</p>}
                    <button type="submit">Registrarse</button>
                </form>
                <button 
                    onClick={() => navigate("/login")}
                    style={{ marginTop: "10px", backgroundColor: "transparent", border: "none", color: "white" }}
                >
                    ¿Ya tienes cuenta? Inicia sesión
                </button>
            </div>
        </div>
    );
};

export default RegisterPage; 