import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
const API_URL = (import.meta.env.VITE_API_URL || 'https://cybersoc-platform-j4h1.onrender.com').replace(/\/$/, '');
export default function RegisterPage() {
  const [form, setForm] = useState({
    username: '',
    email: '',
    full_name: '',
    password: '',
  });
  const [message, setMessage] = useState('');
  const { setToken, setUser } = useAuth();
  const navigate = useNavigate();

  const handleChange = (event) => {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    const response = await fetch(`${API_URL}/api/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(form),
    });
    const data = await response.json();
    if (!response.ok) {
      setMessage(data.detail || 'Registration failed');
      return;
    }
    setToken(data.access_token);
    setUser(data.user);
    navigate('/');
  };

  return (
    <div className="auth-screen">
      <div className="auth-card">
        <p className="eyebrow">New Operator</p>
        <h1>Create an account</h1>
        <form onSubmit={handleSubmit} className="auth-form">
          <label>
            Full name
            <input name="full_name" value={form.full_name} onChange={handleChange} />
          </label>
          <label>
            Username
            <input name="username" value={form.username} onChange={handleChange} />
          </label>
          <label>
            Email
            <input type="email" name="email" value={form.email} onChange={handleChange} />
          </label>
          <label>
            Password
            <input type="password" name="password" value={form.password} onChange={handleChange} />
          </label>
          {message && <div className="error-box">{message}</div>}
          <button type="submit" className="primary-button">Register</button>
        </form>
        <p className="auth-switch">
          Already have an account? <Link to="/login">Login</Link>
        </p>
      </div>
    </div>
  );
}
