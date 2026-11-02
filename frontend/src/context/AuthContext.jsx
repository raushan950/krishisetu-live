import React, { createContext, useCallback, useContext, useState, useEffect } from 'react';
import axiosClient from '../api/axiosClient';
import { extractErrorMessage } from '../utils/authErrors';

const AuthContext = createContext(null);

export { extractErrorMessage };

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('access_token') || null);
  const [loading, setLoading] = useState(true);
  const [authError, setAuthError] = useState(null);

  const logout = useCallback(() => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user_info');
    setToken(null);
    setUser(null);
  }, []);

  // Synchronize state with background token refresh and expiry events
  useEffect(() => {
    const handleTokenRefreshed = (e) => {
      if (e.detail?.access) {
        setToken(e.detail.access);
      }
    };

    const handleSessionExpired = () => {
      setUser(null);
      setToken(null);
    };

    window.addEventListener('auth:token-refreshed', handleTokenRefreshed);
    window.addEventListener('auth:session-expired', handleSessionExpired);

    return () => {
      window.removeEventListener('auth:token-refreshed', handleTokenRefreshed);
      window.removeEventListener('auth:session-expired', handleSessionExpired);
    };
  }, []);

  // Initialize and verify user session on first load
  useEffect(() => {
    const initializeAuth = async () => {
      const storedToken = localStorage.getItem('access_token');
      const storedUser = localStorage.getItem('user_info');

      if (storedToken && storedUser) {
        try {
          const parsedUser = JSON.parse(storedUser);
          setUser(parsedUser);
          setToken(storedToken);

          // Verify and synchronize with backend in background
          const res = await axiosClient.get('/auth/me/');
          setUser(res.data);
          localStorage.setItem('user_info', JSON.stringify(res.data));
        } catch (err) {
          console.warn("Session background verification warning:", err);
          // Only destroy the session if the backend explicitly rejected the token (401 Unauthorized)
          // Do NOT log out on temporary network issues, Render cold starts, or 5xx server errors
          if (err.response && err.response.status === 401) {
            logout();
          }
        }
      }
      setLoading(false);
    };

    initializeAuth();
  }, [logout]);

  const login = async (email, password) => {
    setAuthError(null);
    try {
      const res = await axiosClient.post('/auth/login/', {
        email: email.trim().toLowerCase(),
        password,
      });
      const { access, refresh, user: userData } = res.data;

      localStorage.setItem('access_token', access);
      localStorage.setItem('refresh_token', refresh);
      localStorage.setItem('user_info', JSON.stringify(userData));

      setToken(access);
      setUser(userData);
      return { success: true, user: userData };
    } catch (err) {
      const msg = extractErrorMessage(err, "Invalid email or password. Please verify your credentials.");
      setAuthError(msg);
      return { success: false, error: msg };
    }
  };

  const register = async (formData) => {
    setAuthError(null);
    try {
      const res = await axiosClient.post('/auth/register/', formData);
      const access = res.data.access || res.data.tokens?.access;
      const refresh = res.data.refresh || res.data.tokens?.refresh;
      const userData = res.data.user;

      if (access) localStorage.setItem('access_token', access);
      if (refresh) localStorage.setItem('refresh_token', refresh);
      if (userData) localStorage.setItem('user_info', JSON.stringify(userData));

      setToken(access || null);
      setUser(userData || null);
      return { success: true, user: userData };
    } catch (err) {
      const msg = extractErrorMessage(err, "Registration failed. Please check form inputs.");
      setAuthError(msg);
      return { success: false, error: msg };
    }
  };

  const value = {
    user,
    token,
    role: user?.role || null,
    isAuthenticated: !!token && !!user,
    isFarmer: user?.role === 'FARMER',
    isBuyer: user?.role === 'BUYER',
    isAdmin: user?.role === 'ADMIN',
    loading,
    authError,
    login,
    register,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
