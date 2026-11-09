import { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { formatDateTimeIST } from '../utils/dateTime';

function CountCards({ title, counts }) {
  return (
    <section>
      <h3>{title}</h3>
      <div className="summary-cards">
        {Object.entries(counts || {}).map(([label, count]) => (
          <div className="mini-card" key={label}>
            <span>{label}</span>
            <strong>{count}</strong>
          </div>
        ))}
      </div>
    </section>
  );
}

export default function ReportsPage() {
  const { token } = useAuth();
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError('');
      try {
        const response = await fetch('/api/reports', {
          headers: { Authorization: `Bearer ${token}` },
        });
        const data = await response.json();
        if (!response.ok) {
          throw new Error(typeof data.detail === 'string' ? data.detail : 'Unable to load incident reports.');
        }
        setReport(data);
      } catch (loadError) {
        console.error('Unable to load incident reports:', loadError);
        setError(loadError.message || 'Unable to load incident reports. Check that the backend is running.');
      } finally {
        setLoading(false);
      }
    }
    if (token) load();
  }, [token]);

  const exportCsv = async () => {
    setExporting(true);
    setError('');
    try {
      const response = await fetch('/api/incidents/export/csv', {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) {
        const data = await response.json().catch(() => null);
        throw new Error(typeof data?.detail === 'string' ? data.detail : 'Unable to export incidents. Please try again.');
      }

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = 'incident_export.csv';
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (exportError) {
      console.error('Unable to export incidents:', exportError);
      setError(exportError.message || 'Unable to export incidents. Check that the backend is running.');
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="page-block">
      <div className="toolbar spaced">
        <h2>Incident reports</h2>
        <button className="primary-button" onClick={exportCsv} disabled={exporting}>
          {exporting ? 'Exporting...' : 'Export CSV'}
        </button>
      </div>
      {error && <div className="error-box" role="alert">{error}</div>}
      {loading ? (
        <div className="loader">Loading incident reports...</div>
      ) : report ? (
        <>
          <div className="summary-cards">
            <div className="mini-card">
              <span>All incidents</span>
              <strong>{report.total_incidents}</strong>
            </div>
          </div>
          <CountCards title="Incidents by status" counts={report.status_counts} />
          <CountCards title="Incidents by severity" counts={report.severity_counts} />
          <CountCards title="Incidents by priority" counts={report.priority_counts} />
          <div className="card-table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Title</th>
                  <th>Category</th>
                  <th>Severity</th>
                  <th>Priority</th>
                  <th>Status</th>
                  <th>Asset</th>
                  <th>Recorded (IST)</th>
                  <th>Updated (IST)</th>
                </tr>
              </thead>
              <tbody>
                {report.items.map((incident) => (
                  <tr key={incident.id}>
                    <td>#{incident.id}</td>
                    <td>{incident.title}</td>
                    <td>{incident.category}</td>
                    <td><span className={`badge severity-${incident.severity.toLowerCase()}`}>{incident.severity}</span></td>
                    <td>{incident.priority}</td>
                    <td>{incident.status}</td>
                    <td>{incident.affected_asset}</td>
                    <td>{formatDateTimeIST(incident.detection_timestamp)}</td>
                    <td>{formatDateTimeIST(incident.last_updated)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      ) : null}
    </div>
  );
}
