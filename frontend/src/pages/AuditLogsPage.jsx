import { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { formatDateTimeIST } from '../utils/dateTime';

export default function AuditLogsPage() {
  const { apiFetch } = useAuth();
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;
    async function loadLogs() {
      setLoading(true);
      setError('');
      try {
        const response = await apiFetch('/api/admin/audit-logs');
        const data = await response.json();
        if (!response.ok) {
          throw new Error(typeof data.detail === 'string' ? data.detail : 'Unable to load audit logs.');
        }
        if (active) setLogs(data.items);
      } catch (loadError) {
        if (active) setError(loadError.message || 'Unable to load audit logs. Check that the backend is running.');
      } finally {
        if (active) setLoading(false);
      }
    }
    loadLogs();
    return () => {
      active = false;
    };
  }, [apiFetch]);

  return (
    <div className="page-block">
      <h2>Audit logs</h2>
      {error && <div className="error-box" role="alert">{error}</div>}
      <div className="card-table-wrap">
        <table className="data-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Action</th>
              <th>Details</th>
              <th>Created</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan="4">Loading audit logs...</td></tr>
            ) : logs.map((log) => (
              <tr key={log.id}>
                <td>{log.id}</td>
                <td>{log.action}</td>
                <td>{log.details}</td>
                <td>{formatDateTimeIST(log.created_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
