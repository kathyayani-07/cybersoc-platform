import { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { formatDateTimeIST } from '../utils/dateTime';

export default function AlertsPage() {
  const { token } = useAuth();
  const [alerts, setAlerts] = useState([]);

  useEffect(() => {
    async function fetchAlerts() {
      const response = await fetch('/api/dashboard/overview', {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await response.json();
      setAlerts(data.recent_alerts || []);
    }
    if (token) fetchAlerts();
  }, [token]);

  return (
    <div className="page-block">
      <h2>Alerts and threat indicators</h2>
      {alerts.length === 0 ? (
        <div className="empty-state large">No alerts available.</div>
      ) : (
        <div className="alert-list">
          {alerts.map((alert) => (
            <div key={alert.id} className="alert-card">
              <div className="alert-header">
                <span className={`badge severity-${alert.severity.toLowerCase()}`}>{alert.severity}</span>
                <strong>{alert.title}</strong>
              </div>
              <p>{alert.status}</p>
              <small>{formatDateTimeIST(alert.last_updated)}</small>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
