// src/App.js
import React from "react";
import { HashRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import { ThemeProvider } from '@mui/material/styles';
import { CssBaseline } from '@mui/material';
import HomePage from "./components/HomePage";
import LoginPage from "./components/LoginPage";
import RegisterPage from "./components/RegisterPage";
import ProfilePage from "./components/ProfilePage";
import MainCanvas from "./components/MainCanvas";
import Layout from "./components/Layout";
import { ProtectedRoute, PublicRoute } from './components/ProtectedRoute';
import theme from './theme';
import './styles/App.css';

const App = () => {
  const isMock = (() => {
    try {
      const envFlag = (typeof process !== 'undefined' && process && process.env && process.env.REACT_APP_MOCK);
      const winFlag = (typeof window !== 'undefined' && window.REACT_APP_MOCK);
      return String(envFlag || winFlag || 'true').toLowerCase() === 'true';
    } catch (e) { return true; }
  })();
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={isMock ? (
              <ProtectedRoute>
                <MainCanvas />
              </ProtectedRoute>
            ) : (
              <HomePage />
            )} />
            <Route path="login" element={
              <PublicRoute>
                <LoginPage />
              </PublicRoute>
            } />
            <Route path="register" element={
              <PublicRoute>
                <RegisterPage />
              </PublicRoute>
            } />
            <Route path="main" element={
              <ProtectedRoute>
                <MainCanvas />
              </ProtectedRoute>
            } />
            <Route path="profile" element={
              <ProtectedRoute>
                <ProfilePage />
              </ProtectedRoute>
            } />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </Router>
    </ThemeProvider>
  );
};

export default App;
