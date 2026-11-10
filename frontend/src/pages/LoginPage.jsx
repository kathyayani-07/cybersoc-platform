
import { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const API_URL = (import.meta.env.VITE_API_URL || 'https://cybersoc-platform-j4h1.onrender.com').replace(/\/$/, '');

export default function LoginPage() {
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('');
  const location = useLocation();
  const [message, setMessage] = useState(location.state?.message || '');
  const { setToken, setUser } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (event) => {
    event.preventDefault();
    setMessage('');

    try {
      const response = await fetch(`${API_URL}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ username, password }),
      });

      const data = await response.json();

      if (!response.ok) {
        setMessage(data.detail || 'Login failed');
        return;
      }

      setToken(data.access_token);
      setUser(data.user);
      navigate('/');
    } catch (error) {
      setMessage('Cannot connect to the server. Please try again.');
      console.error('Login error:', error);
    }
  };

  return (
    <div className="auth-screen">
      <div className="auth-card">
        <p className="eyebrow">CyberSOC</p>
        <h1>Log in to your console</h1>
        <form onSubmit={handleSubmit} className="auth-form">
          <label>
            Username
            <input value={username} onChange={(e) => setUsername(e.target.value)} />
          </label>
          <label>
            Password
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </label>
          {message && <div className="error-box">{message}</div>}
          <button type="submit" className="primary-button">Login</button>
        </form>
        <p className="auth-switch">
          Need an account? <Link to="/register">Create one</Link>
        </p>
      </div>
    </div>
  );
}


