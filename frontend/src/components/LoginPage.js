import React, { useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import '../styles/LoginPage.css'; // Importa el archivo CSS

const LoginPage = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setError("");

    try {
      console.log("Intentando login con:", { email, password });
      
      const formData = new URLSearchParams();
      formData.append('username', email);
      formData.append('password', password);

      const response = await axios.post(
        "http://localhost:8000/users/login",
        formData,
        {
          headers: {
            "Content-Type": "application/x-www-form-urlencoded",
          },
        }
      );

      console.log("Respuesta del servidor:", response.data);

      const { access_token } = response.data;
      localStorage.setItem("token", access_token);
      
      navigate("/main", { replace: true });
    } catch (err) {
      console.error("Error completo:", err);
      if (err.response) {
        console.error("Respuesta de error:", err.response.data);
        setError(err.response.data.detail || "Error al iniciar sesión");
      } else {
        setError("Error de conexión. Por favor, intenta de nuevo.");
      }
    }
  };

  return (
    <div className="login-container">
      <div className="form-container">
        <h1>Login</h1>
        <form onSubmit={handleLogin}>
          <div>
            <label>Email:</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          <div>
            <label>Password:</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          {error && <p style={{ color: "red" }}>{error}</p>}
          <button type="submit">Login</button>
        </form>
      </div>
    </div>
  );
};

export default LoginPage;
