import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { authAPI } from '../lib/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const checkAuth = useCallback(async () => {
    // CRITICAL: If returning from OAuth callback, skip the /me check.
    // AuthCallback will exchange the session_id and establish the session first.
    if (window.location.hash?.includes('session_id=')) {
      setLoading(false);
      return;
    }

    const token = localStorage.getItem('shopply_token');
    const savedUser = localStorage.getItem('shopply_user');

    if (token && savedUser) {
      setUser(JSON.parse(savedUser));
      try {
        const res = await authAPI.getMe();
        setUser(res.data);
        localStorage.setItem('shopply_user', JSON.stringify(res.data));
      } catch {
        // Token invalid, clean up
        localStorage.removeItem('shopply_token');
        localStorage.removeItem('shopply_user');
        setUser(null);
      }
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  const login = async (email, password) => {
    const res = await authAPI.login({ email, password });
    const { access_token, user: userData } = res.data;
    localStorage.setItem('shopply_token', access_token);
    localStorage.setItem('shopply_user', JSON.stringify(userData));
    setUser(userData);
    return userData;
  };

  const register = async (email, password, nome, referralCode = null) => {
    const res = await authAPI.register({ email, password, nome, referral_code: referralCode });
    const { access_token, user: userData } = res.data;
    localStorage.setItem('shopply_token', access_token);
    localStorage.setItem('shopply_user', JSON.stringify(userData));
    setUser(userData);
    return userData;
  };

  const loginWithGoogle = (userData) => {
    localStorage.setItem('shopply_user', JSON.stringify(userData));
    setUser(userData);
  };

  const logout = async () => {
    try {
      await authAPI.googleLogout();
    } catch {
      // Ignore
    }
    localStorage.removeItem('shopply_token');
    localStorage.removeItem('shopply_user');
    setUser(null);
  };

  const updateUser = (userData) => {
    setUser(userData);
    localStorage.setItem('shopply_user', JSON.stringify(userData));
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, loginWithGoogle, logout, updateUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
