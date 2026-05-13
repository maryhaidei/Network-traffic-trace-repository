import React, { createContext, useContext, useEffect, useState } from "react";
import { getMeApi, loginApi, logoutApi } from "../api/client";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem("token"));
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(false);

  const isAuthenticated = !!token;
  const isAdmin = user?.role === "admin";

  useEffect(() => {
    if (token) localStorage.setItem("token", token);
    else localStorage.removeItem("token");
  }, [token]);

  useEffect(() => {
    let cancelled = false;

    async function loadMe() {
      if (!token) {
        setUser(null);
        return;
      }

      try {
        const me = await getMeApi();
        if (!cancelled) setUser(me);
      } catch {
        if (!cancelled) {
          logoutApi();
          setToken(null);
          setUser(null);
        }
      }
    }

    loadMe();

    return () => {
      cancelled = true;
    };
  }, [token]);

  async function login(login, password) {
    setLoading(true);
    try {
      await loginApi(login, password);
      const freshToken = localStorage.getItem("token");
      setToken(freshToken);
      const me = await getMeApi();
      setUser(me);
      return me;
    } finally {
      setLoading(false);
    }
  }

  function logout() {
    logoutApi();
    setToken(null);
    setUser(null);
  }

  return (
    <AuthContext.Provider
      value={{
        token,
        user,
        loading,
        isAuthenticated,
        isAdmin,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}