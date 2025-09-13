import React, { useEffect, useState } from 'react';
import { Navigate, useLocation } from 'react-router-dom';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// For routes that require authentication (e.g., /main, /profile)
export const ProtectedRoute = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(null);
  const location = useLocation();

  useEffect(() => {
    const verifyAuth = async () => {
      const token = localStorage.getItem('token');
      console.log('Token in ProtectedRoute:', token);

      if (!token) {
        console.log('No token found');
        setIsAuthenticated(false);
        return;
      }

      try {
        const response = await fetch(`${API_URL}/api/auth/me`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });

        console.log('Verification response:', response.status);
        if (response.ok) {
          setIsAuthenticated(true);
        } else {
          console.log('Invalid token, clearing localStorage');
          localStorage.removeItem('token');
          setIsAuthenticated(false);
        }
      } catch (error) {
        console.error('Error verifying authentication:', error);
        localStorage.removeItem('token');
        setIsAuthenticated(false);
      }
    };

    verifyAuth();
  }, [location.pathname]);

  if (isAuthenticated === null) {
    return <div>Verifying authentication...</div>;
  }

  if (!isAuthenticated) {
    console.log('Redirecting to login - Not authenticated');
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return children;
};

// For routes that should only be accessible when NOT logged in (e.g., /login, /register)
export const PublicRoute = ({ children }) => {
  const [isChecking, setIsChecking] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const location = useLocation();

  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('token');
      console.log('Token in PublicRoute:', token);

      if (!token) {
        setIsAuthenticated(false);
        setIsChecking(false);
        return;
      }

      try {
        const response = await fetch(`${API_URL}/api/auth/me`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });

        if (response.ok) {
          setIsAuthenticated(true);
        } else {
          console.log('Invalid token in PublicRoute, clearing localStorage');
          localStorage.removeItem('token');
          setIsAuthenticated(false);
        }
      } catch (error) {
        console.error('Error verifying authentication in PublicRoute:', error);
        localStorage.removeItem('token');
        setIsAuthenticated(false);
      }
      setIsChecking(false);
    };

    checkAuth();
  }, [location.pathname]);

  if (isChecking) {
    return <div>Verifying authentication...</div>;
  }

  if (isAuthenticated) {
    console.log('Redirecting to main - Already authenticated');
    return <Navigate to="/main" state={{ from: location }} replace />;
  }

  return children;
}; 