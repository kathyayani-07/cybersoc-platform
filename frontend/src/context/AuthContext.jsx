import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react';

const AuthContext = createContext(null);
const API_URL = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '');
const apiUrl = (path) => `${API_URL}${path}`;
function storedUser() {
  try {
    return JSON.parse(localStorage.getItem('cyber_user') || 'null');
  } catch {
    localStorage.removeItem('cyber_user');
    return null;
  }
}

export function AuthProvider({ children }) {
  const [token, setToken] = useState(localStorage.getItem('cyber_token') || '');
  const [user, setUser] = useState(storedUser);
  const [isInitializing, setIsInitializing] = useState(true);
  const refreshPromise = useRef(null);

  useEffect(() => {
    if (token) {
      localStorage.setItem('cyber_token', token);
    } else {
      localStorage.removeItem('cyber_token');
    }
  }, [token]);

  useEffect(() => {
    if (user) {
      localStorage.setItem('cyber_user', JSON.stringify(user));
    } else {
      localStorage.removeItem('cyber_user');
    }
  }, [user]);

  const clearSession = useCallback(() => {
    setToken('');
    setUser(null);
    localStorage.removeItem('cyber_token');
    localStorage.removeItem('cyber_user');
  }, []);

  const refreshSession = useCallback(() => {
    if (!refreshPromise.current) {
      const currentToken = token || localStorage.getItem('cyber_token') || '';
      refreshPromise.current = (async () => {
        const headers = new Headers();
        if (currentToken) headers.set('Authorization', `Bearer ${currentToken}`);
        const response = await fetch(apiUrl('/api/auth/refresh'), {
          method: 'POST',
          headers,
          credentials: 'include',
        });
        if (response.status === 401) {
          clearSession();
          return null;
        }
        if (!response.ok) throw new Error('Unable to restore the current session.');
        const session = await response.json();
        setToken(session.access_token);
        setUser(session.user);
        localStorage.setItem('cyber_token', session.access_token);
        localStorage.setItem('cyber_user', JSON.stringify(session.user));
        return session;
      })().catch(() => null).finally(() => {
        refreshPromise.current = null;
      });
    }
    return refreshPromise.current;
  }, [clearSession, token]);

  useEffect(() => {
    let active = true;
    refreshSession().finally(() => {
      if (active) setIsInitializing(false);
    });
    return () => {
      active = false;
    };
  }, []);

  const apiFetch = useCallback(async (input, init = {}) => {
    const send = (accessToken) => {
      const headers = new Headers(init.headers);
      if (accessToken) headers.set('Authorization', `Bearer ${accessToken}`);
      return fetch(apiUrl(input), { ...init, headers, credentials: 'include' });
    };
    const response = await send(token || localStorage.getItem('cyber_token') || '');
    if (response.status !== 401) return response;

    const session = await refreshSession();
    if (!session) return response;
    const retry = await send(session.access_token);
    if (retry.status === 401) {
      clearSession();
    }
    return retry;
  }, [clearSession, refreshSession, token]);

  const logout = useCallback(async () => {
    const headers = new Headers();
    if (token) headers.set('Authorization', `Bearer ${token}`);
    try {
      await fetch(apiUrl('/api/auth/logout'), { method: 'POST', headers, credentials: 'include' });
    } finally {
      clearSession();
    }
  }, [clearSession, token]);

  const value = useMemo(
    () => ({
      token,
      setToken,
      user,
      setUser,
      isInitializing,
      apiFetch,
      logout,
    }),
    [token, user, isInitializing, apiFetch, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  return useContext(AuthContext);
}
