import React, { createContext, useContext, useState, useEffect } from 'react';
import { authAPI } from '../lib/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('shopply_token');
    const savedUser = localStorage.getItem('shopply_user');
    
    if (token && savedUser) {
      setUser(JSON.parse(savedUser));
      // Verify token is still valid
      authAPI.getMe()
        .then(res => {
          setUser(res.data);
          localStorage.setItem('shopply_user', JSON.stringify(res.data));
        })
        .catch(() => {
          logout();
        })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

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

  const logout = () => {
    localStorage.removeItem('shopply_token');
    localStorage.removeItem('shopply_user');
    setUser(null);
  };

  const updateUser = (userData) => {
    setUser(userData);
    localStorage.setItem('shopply_user', JSON.stringify(userData));
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, updateUser }}>
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
