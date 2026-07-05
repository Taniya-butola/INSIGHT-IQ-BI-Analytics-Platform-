import { createContext, useContext, useState, useCallback, useMemo } from "react";
import client from "../api/client";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const stored = localStorage.getItem("insightiq_user");
    return stored ? JSON.parse(stored) : null;
  });
  const [loading, setLoading] = useState(false);

  const persist = (token, userObj) => {
    localStorage.setItem("insightiq_token", token);
    localStorage.setItem("insightiq_user", JSON.stringify(userObj));
    setUser(userObj);
  };

  const register = useCallback(async (payload) => {
    setLoading(true);
    try {
      const { data } = await client.post("/auth/register", payload);
      persist(data.access_token, data.user);
      return { ok: true };
    } catch (err) {
      return { ok: false, errors: err.response?.data?.errors || ["Registration failed."] };
    } finally {
      setLoading(false);
    }
  }, []);

  const login = useCallback(async (payload) => {
    setLoading(true);
    try {
      const { data } = await client.post("/auth/login", payload);
      persist(data.access_token, data.user);
      return { ok: true };
    } catch (err) {
      return { ok: false, errors: err.response?.data?.errors || ["Login failed."] };
    } finally {
      setLoading(false);
    }
  }, []);

  const logout = useCallback(async () => {
    try {
      await client.post("/auth/logout");
    } catch {
      // ignore network errors on logout
    }
    localStorage.removeItem("insightiq_token");
    localStorage.removeItem("insightiq_user");
    setUser(null);
  }, []);

  const updateUser = useCallback((userObj) => {
    localStorage.setItem("insightiq_user", JSON.stringify(userObj));
    setUser(userObj);
  }, []);

  const value = useMemo(
    () => ({ user, loading, register, login, logout, updateUser }),
    [user, loading, register, login, logout, updateUser]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
