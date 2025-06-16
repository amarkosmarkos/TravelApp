import React, { useEffect, useState } from 'react';
import { Navigate, useLocation } from 'react-router-dom';

// Para rutas que requieren autenticación (ej: /main, /profile)
export const ProtectedRoute = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(null);
  const location = useLocation();

  useEffect(() => {
    const verifyAuth = async () => {
      const token = localStorage.getItem('token');
      console.log('Token en ProtectedRoute:', token);

      if (!token) {
        console.log('No hay token');
        setIsAuthenticated(false);
        return;
      }

      try {
        const response = await fetch('http://localhost:8000/api/auth/me', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });

        console.log('Respuesta de verificación:', response.status);
        if (response.ok) {
          setIsAuthenticated(true);
        } else {
          console.log('Token inválido, limpiando localStorage');
          localStorage.removeItem('token');
          setIsAuthenticated(false);
        }
      } catch (error) {
        console.error('Error verificando autenticación:', error);
        localStorage.removeItem('token');
        setIsAuthenticated(false);
      }
    };

    verifyAuth();
  }, [location.pathname]);

  if (isAuthenticated === null) {
    return <div>Verificando autenticación...</div>;
  }

  if (!isAuthenticated) {
    console.log('Redirigiendo a login - No autenticado');
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return children;
};

// Para rutas que solo deben ser accesibles cuando NO hay sesión (ej: /login, /register)
export const PublicRoute = ({ children }) => {
  const [isChecking, setIsChecking] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const location = useLocation();

  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('token');
      console.log('Token en PublicRoute:', token);

      if (!token) {
        setIsAuthenticated(false);
        setIsChecking(false);
        return;
      }

      try {
        const response = await fetch('http://localhost:8000/api/auth/me', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });

        if (response.ok) {
          setIsAuthenticated(true);
        } else {
          console.log('Token inválido en PublicRoute, limpiando localStorage');
          localStorage.removeItem('token');
          setIsAuthenticated(false);
        }
      } catch (error) {
        console.error('Error verificando autenticación en PublicRoute:', error);
        localStorage.removeItem('token');
        setIsAuthenticated(false);
      }
      setIsChecking(false);
    };

    checkAuth();
  }, [location.pathname]);

  if (isChecking) {
    return <div>Verificando autenticación...</div>;
  }

  if (isAuthenticated) {
    console.log('Redirigiendo a main - Ya autenticado');
    return <Navigate to="/main" state={{ from: location }} replace />;
  }

  return children;
}; 