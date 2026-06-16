import React, { createContext, useContext, useEffect, useMemo, useState } from "react";

import { api } from "../api/client";

const AuthContext = createContext(null);
const AUTH_TOKEN_KEY = "financial_rag_token";
const AUTH_USER_KEY = "financial_rag_user";

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem(AUTH_TOKEN_KEY));
  const [user, setUser] = useState(() => {
    const stored = localStorage.getItem(AUTH_USER_KEY);
    try {
      return stored ? JSON.parse(stored) : null;
    } catch {
      localStorage.removeItem(AUTH_USER_KEY);
      return null;
    }
  });

  function clearAuth() {
    localStorage.removeItem(AUTH_TOKEN_KEY);
    localStorage.removeItem(AUTH_USER_KEY);
    setToken(null);
    setUser(null);
  }

  useEffect(() => {
    window.addEventListener("financial-rag-auth-expired", clearAuth);
    return () => window.removeEventListener("financial-rag-auth-expired", clearAuth);
  }, []);

  async function login(payload) {
    const data = await api.login(payload);
    localStorage.setItem(AUTH_TOKEN_KEY, data.access_token);
    localStorage.setItem(AUTH_USER_KEY, JSON.stringify(data.user));
    setToken(data.access_token);
    setUser(data.user);
  }

  async function register(payload) {
    const data = await api.register(payload);
    localStorage.setItem(AUTH_TOKEN_KEY, data.access_token);
    localStorage.setItem(AUTH_USER_KEY, JSON.stringify(data.user));
    setToken(data.access_token);
    setUser(data.user);
  }

  function logout() {
    clearAuth();
  }

  const value = useMemo(
    () => ({ isAuthenticated: Boolean(token), login, logout, register, token, user }),
    [token, user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider");
  }
  return context;
}
