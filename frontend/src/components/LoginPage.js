import React, { useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import '../styles/LoginPage.css'; // Importa el archivo CSS

const API_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

// Configurar axios con timeout y headers por defecto
axios.defaults.timeout = 10000; // 10 segundos
axios.defaults.headers.common['Content-Type'] = 'application/x-www-form-urlencoded';

const LoginPage = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setError("");
    setIsLoading(true);

    try {
      console.log("Intentando login con:", { email });
      
      // Crear el objeto de datos para el login
      const loginData = new URLSearchParams();
      loginData.append('username', email);
      loginData.append('password', password);

      // Realizar la petición de login
      const response = await axios.post(
        `${API_URL}/api/auth/token`,
        loginData.toString(),
        {
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
          validateStatus: function (status) {
            return status < 500; // Resolver solo si el status es menor que 500
          }
        }
      );

      console.log("Respuesta del servidor:", response.data);

      if (response.status === 200) {
        const { access_token } = response.data;
        localStorage.setItem("token", access_token);
        
        // Verificar que el token se guardó correctamente
        const savedToken = localStorage.getItem("token");
        if (!savedToken) {
          throw new Error("No se pudo guardar el token");
        }
        
        // Verificar que el token es válido haciendo una petición de prueba
        try {
          const testResponse = await axios.get(`${API_URL}/api/auth/me`, {
            headers: {
              'Authorization': `Bearer ${savedToken}`
            }
          });
          
          if (testResponse.status === 200) {
            console.log("Test de autenticación exitoso:", testResponse.data);
            navigate("/main", { replace: true });
          } else {
            throw new Error("Error en la verificación del token");
          }
        } catch (testError) {
          console.error("Error en test de autenticación:", testError);
          localStorage.removeItem("token");
          throw new Error("Error al verificar la autenticación");
        }
      } else {
        throw new Error(response.data.detail || "Error al iniciar sesión");
      }
    } catch (err) {
      console.error("Error completo:", err);
      if (err.response) {
        console.error("Respuesta de error:", err.response.data);
        setError(err.response.data.detail || "Error al iniciar sesión");
      } else if (err.message) {
        setError(err.message);
      } else {
        setError("Error de conexión. Por favor, intenta de nuevo.");
      }
    } finally {
      setIsLoading(false);
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
              disabled={isLoading}
            />
          </div>
          <div>
            <label>Password:</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              disabled={isLoading}
            />
          </div>
          {error && <p className="error-message">{error}</p>}
          <button type="submit" disabled={isLoading}>
            {isLoading ? "Iniciando sesión..." : "Login"}
          </button>
        </form>
      </div>
    </div>
  );
};

export default LoginPage;
