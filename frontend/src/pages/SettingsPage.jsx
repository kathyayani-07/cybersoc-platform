import { useAuth } from '../context/AuthContext';

export default function SettingsPage() {
  const { user } = useAuth();

  return (
    <div className="page-block">
      <h2>Settings</h2>
      <div className="settings-grid">
        <div className="panel-card">
          <h3>Account</h3>
          <p><strong>Name:</strong> {user?.full_name}</p>
          <p><strong>Username:</strong> {user?.username}</p>
          <p><strong>Role:</strong> {user?.role}</p>
        </div>
        <div className="panel-card">
          <h3>Security controls</h3>
          <ul>
            <li>JWT authentication enabled</li>
            <li>Role-based access control enforced</li>
            <li>Passwords hashed before storage</li>
            <li>Demo AI mode available when API keys are absent</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
