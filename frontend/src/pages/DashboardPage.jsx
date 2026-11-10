import { useEffect, useMemo, useState } from 'react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { useAuth } from '../context/AuthContext';
import { formatDateTimeIST } from '../utils/dateTime';
const API_URL = (import.meta.env.VITE_API_URL || 'https://cybersoc-platform-j4h1.onrender.com').replace(/\/$/, '');
const severityColors = {
  Critical: '#ef4444',
  High: '#fb7185',
  Medium: '#fbbf24',
  Low: '#38bdf8',
};

export default function DashboardPage() {
  const { token } = useAuth();
  const [metrics, setMetrics] = useState(null);

  useEffect(() => {
    async function fetchData() {
      const response = await fetch(`${API_URL}/api/dashboard/overview`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await response.json();
      setMetrics(data);
    }
    if (token) fetchData();
  }, [token]);

  const trendData = useMemo(() => {
    if (!metrics?.incident_trend) return [];
    const groups = {};
    metrics.incident_trend.forEach((entry) => {
      groups[entry.date] = (groups[entry.date] || 0) + entry.count;
    });
    return Object.entries(groups).map(([date, count]) => ({ date, count }));
  }, [metrics]);

  const pieData = useMemo(
    () => Object.entries(metrics?.severity_distribution || {}).map(([name, value]) => ({ name, value })),
    [metrics],
  );

  if (!metrics) {
    return <div className="loader">Loading dashboard metrics...</div>;
  }

  return (
    <div>
      <div className="stats-grid">
        <div className="stat-card accent">
          <span>Total incidents</span>
          <strong>{metrics.total_incidents}</strong>
        </div>
        <div className="stat-card">
          <span>Open incidents</span>
          <strong>{metrics.open_incidents}</strong>
        </div>
        <div className="stat-card danger">
          <span>Critical</span>
          <strong>{metrics.critical_incidents}</strong>
        </div>
        <div className="stat-card warning">
          <span>High severity</span>
          <strong>{metrics.high_severity_incidents}</strong>
        </div>
        <div className="stat-card">
          <span>Under investigation</span>
          <strong>{metrics.under_investigation}</strong>
        </div>
        <div className="stat-card success">
          <span>Resolved</span>
          <strong>{metrics.resolved_incidents}</strong>
        </div>
      </div>

      <div className="panel-grid">
        <div className="panel-card chart-card">
          <h3>Incident trend</h3>
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={trendData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2a38" />
              <XAxis dataKey="date" stroke="#cbd5e1" />
              <YAxis allowDecimals={false} stroke="#cbd5e1" />
              <Tooltip />
              <Line type="monotone" dataKey="count" stroke="#60a5fa" strokeWidth={3} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="panel-card chart-card">
          <h3>Severity distribution</h3>
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie data={pieData} dataKey="value" nameKey="name" innerRadius={40} outerRadius={80}>
                {pieData.map((entry) => (
                  <Cell key={entry.name} fill={severityColors[entry.name] || '#60a5fa'} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="panel-grid">
        <div className="panel-card">
          <h3>Recent alerts</h3>
          {metrics.recent_alerts.length === 0 ? (
            <div className="empty-state">No alerts found.</div>
          ) : (
            <ul className="list-stack">
              {metrics.recent_alerts.map((item) => (
                <li key={item.id} className="list-item">
                  <span className={`badge severity-${item.severity.toLowerCase()}`}>{item.severity}</span>
                  <strong>{item.title}</strong>
                  <small>{item.status}</small>
                  <small>{formatDateTimeIST(item.last_updated)}</small>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="panel-card">
          <h3>Activity</h3>
          {metrics.recent_activity.length === 0 ? (
            <div className="empty-state">No recent activity.</div>
          ) : (
            <ul className="list-stack">
              {metrics.recent_activity.map((item) => (
                <li key={item.id} className="list-item">
                  <strong>{item.title}</strong>
                  <small>{item.status} • {item.severity}</small>
                  <small>{formatDateTimeIST(item.last_updated)}</small>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      <div className="panel-grid stack-grid">
        <div className="panel-card">
          <h3>Mean time to acknowledge</h3>
          <strong>{metrics.mean_time_to_acknowledge_hours} hrs</strong>
        </div>
        <div className="panel-card">
          <h3>Mean time to resolve</h3>
          <strong>{metrics.mean_time_to_resolve_hours} hrs</strong>
        </div>
      </div>
    </div>
  );
}
