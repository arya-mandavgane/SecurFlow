import React, { createContext, useContext, useState, useEffect } from 'react';
import { User } from '../types';
import { apiClient } from '../api/client';

interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    const savedToken = localStorage.getItem('securflow_access_token');
    const savedUser = localStorage.getItem('securflow_user');

    if (savedToken && savedUser) {
      setToken(savedToken);
      setUser(JSON.parse(savedUser));
    }
    setIsLoading(false);
  }, []);

  const login = async (username: string, password: string) => {
    setIsLoading(true);
    try {
      const response = await apiClient.post('/auth/login/', { username, password });
      const { access, refresh, user: userData } = response.data;

      localStorage.setItem('securflow_access_token', access);
      localStorage.setItem('securflow_refresh_token', refresh);
      localStorage.setItem('securflow_user', JSON.stringify(userData));

      setToken(access);
      setUser(userData);
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    try {
      await apiClient.post('/auth/logout/').catch(() => {});
    } finally {
      localStorage.removeItem('securflow_access_token');
      localStorage.removeItem('securflow_refresh_token');
      localStorage.removeItem('securflow_user');
      setToken(null);
      setUser(null);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!token,
        isLoading,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
