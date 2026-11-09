import { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';

export default function UserManagementPage() {
  const { apiFetch } = useAuth();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;
    async function loadUsers() {
      setLoading(true);
      setError('');
      try {
        const response = await apiFetch('/api/admin/users');
        const data = await response.json();
        if (!response.ok) {
          throw new Error(typeof data.detail === 'string' ? data.detail : 'Unable to load users.');
        }
        if (active) setUsers(data.items);
      } catch (loadError) {
        if (active) setError(loadError.message || 'Unable to load users. Check that the backend is running.');
      } finally {
        if (active) setLoading(false);
      }
    }
    loadUsers();
    return () => {
      active = false;
    };
  }, [apiFetch]);

  const changeRole = async (userId, role) => {
    setError('');
    try {
      const response = await apiFetch(`/api/admin/users/${userId}/role?role=${encodeURIComponent(role)}`, {
        method: 'PUT',
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(typeof data.detail === 'string' ? data.detail : 'Unable to update the user role.');
      }
      setUsers((current) => current.map((user) => (user.id === userId ? data.user : user)));
    } catch (changeError) {
      setError(changeError.message || 'Unable to update the user role.');
    }
  };

  return (
    <div className="page-block">
      <h2>User and role management</h2>
      {error && <div className="error-box" role="alert">{error}</div>}
      <div className="card-table-wrap">
        <table className="data-table">
          <thead>
            <tr>
              <th>Username</th>
              <th>Email</th>
              <th>Role</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan="4">Loading users...</td></tr>
            ) : users.map((user) => (
              <tr key={user.id}>
                <td>{user.username}</td>
                <td>{user.email}</td>
                <td>{user.role}</td>
                <td>
                  <select value={user.role} onChange={(event) => changeRole(user.id, event.target.value)}>
                    <option value="viewer">Viewer</option>
                    <option value="incident_responder">Incident Responder</option>
                    <option value="security_analyst">Security Analyst</option>
                    <option value="admin">Admin</option>
                  </select>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
