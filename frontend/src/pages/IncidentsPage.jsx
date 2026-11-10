import { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { formatDateTimeIST } from '../utils/dateTime';

const PAGE_SIZE = 10;
const API_URL = (import.meta.env.VITE_API_URL || 'https://cybersoc-platform-j4h1.onrender.com').replace(/\/$/, '');
export default function IncidentsPage() {
  const { token } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [items, setItems] = useState([]);
  const [query, setQuery] = useState('');
  const [severity, setSeverity] = useState('');
  const [status, setStatus] = useState('');
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [successMessage, setSuccessMessage] = useState(location.state?.successMessage || '');
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  useEffect(() => {
    if (location.state?.successMessage) {
      setSuccessMessage(location.state.successMessage);
      navigate(location.pathname, { replace: true, state: null });
    }
  }, [location.pathname, location.state, navigate]);

  useEffect(() => {
    async function fetchList() {
      const params = new URLSearchParams({ page: String(page), page_size: String(PAGE_SIZE) });
      if (query) params.set('query', query);
      if (severity) params.set('severity', severity);
      if (status) params.set('status', status);
      const response = await fetch(`${API_URL}/api/incidents?${params.toString()}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await response.json();
      setItems(data.items || []);
      setTotal(data.total || 0);
    }
    if (token) fetchList();
  }, [token, query, severity, status, page]);

  return (
    <div className="page-block">
      {successMessage && <div className="success-box" role="status">{successMessage}</div>}
      <div className="toolbar">
        <input
          value={query}
          onChange={(event) => {
            setQuery(event.target.value);
            setPage(1);
          }}
          placeholder="Search incidents"
        />
        <select value={severity} onChange={(event) => {
          setSeverity(event.target.value);
          setPage(1);
        }}>
          <option value="">All severities</option>
          <option value="Critical">Critical</option>
          <option value="High">High</option>
          <option value="Medium">Medium</option>
          <option value="Low">Low</option>
        </select>
        <select value={status} onChange={(event) => {
          setStatus(event.target.value);
          setPage(1);
        }}>
          <option value="">All statuses</option>
          <option value="New">New</option>
          <option value="Acknowledged">Acknowledged</option>
          <option value="Investigating">Investigating</option>
          <option value="Contained">Contained</option>
          <option value="Resolved">Resolved</option>
          <option value="Closed">Closed</option>
        </select>
        <button className="primary-button" onClick={() => navigate('/create-incident')}>New incident</button>
      </div>

      {items.length === 0 ? (
        <div className="empty-state large">No incidents match the current filters.</div>
      ) : (
        <div className="card-table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>No.</th>
                <th>Incident ID</th>
                <th>Title</th>
                <th>Severity</th>
                <th>Status</th>
                <th>Asset</th>
                <th>Assigned</th>
                <th>Updated (IST)</th>
              </tr>
            </thead>
            <tbody>
              {items.map((incident, index) => (
                <tr key={incident.id} onClick={() => navigate(`/incidents/${incident.id}`)} className="table-row-clickable">
                  <td>{(page - 1) * PAGE_SIZE + index + 1}</td>
                  <td>#{incident.id}</td>
                  <td>{incident.title}</td>
                  <td><span className={`badge severity-${incident.severity.toLowerCase()}`}>{incident.severity}</span></td>
                  <td>{incident.status}</td>
                  <td>{incident.affected_asset}</td>
                  <td>{incident.assigned_analyst || 'Unassigned'}</td>
                  <td>{formatDateTimeIST(incident.last_updated)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="pagination">
        <button disabled={page <= 1} onClick={() => setPage((current) => Math.max(1, current - 1))}>Previous</button>
        <span>Page {page} of {totalPages} · {total} incidents</span>
        <button disabled={page >= totalPages} onClick={() => setPage((current) => Math.min(totalPages, current + 1))}>Next</button>
      </div>
    </div>
  );
}
