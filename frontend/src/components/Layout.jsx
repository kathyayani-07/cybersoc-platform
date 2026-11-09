import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const navItems = [
  { to: '/', label: 'Dashboard' },
  { to: '/incidents', label: 'Incidents' },
  { to: '/create-incident', label: 'Create Incident' },
  { to: '/ai-analysis', label: 'AI Analysis' },
  { to: '/alerts', label: 'Alerts' },
  { to: '/reports', label: 'Reports' },
  { to: '/users', label: 'Users' },
  { to: '/audit', label: 'Audit Logs' },
  { to: '/settings', label: 'Settings' },
];

export default function Layout({ children }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand-block">
          <div className="brand-mark">SOC</div>
          <div>
            <h2>CyberSOC</h2>
            <small>Incident Response</small>
          </div>
        </div>

        <nav className="nav-menu">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) => (isActive ? 'nav-item active' : 'nav-item')}
            >
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-footer">
          <span className="role-pill">{user?.role || 'Viewer'}</span>
          <button className="ghost-button" onClick={handleLogout}>Logout</button>
        </div>
      </aside>

      <main className="main-panel">
        <header className="topbar">
          <div>
            <p className="eyebrow">Operations Center</p>
            <h1>Security Response Console</h1>
          </div>
          <div className="topbar-user">
            <strong>{user?.full_name || user?.username || 'User'}</strong>
            <span>{user?.email || 'security@cybersoc.local'}</span>
          </div>
        </header>

        <div className="page-content">{children}</div>
      </main>
    </div>
  );
}
