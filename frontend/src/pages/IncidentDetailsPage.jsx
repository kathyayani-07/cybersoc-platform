import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { formatDateTimeIST } from '../utils/dateTime';

export default function IncidentDetailsPage() {
  const { token } = useAuth();
  const { incidentId } = useParams();
  const [incident, setIncident] = useState(null);
  const [note, setNote] = useState('');
  const [message, setMessage] = useState('');

  const fetchIncident = async () => {
    const response = await fetch(`/api/incidents/${incidentId}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    const data = await response.json();
    setIncident(data);
  };

  useEffect(() => {
    if (token) fetchIncident();
  }, [token, incidentId]);

  const handleChange = (event) => {
    const { name, value } = event.target;
    setIncident((current) => ({ ...current, [name]: value }));
  };

  const handleSave = async () => {
    const response = await fetch(`/api/incidents/${incidentId}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(incident),
    });
    const data = await response.json();
    if (!response.ok) {
      setMessage(data.detail || 'Failed to update incident');
      return;
    }
    setMessage('Incident updated successfully');
  };

  const handleNote = async () => {
    const response = await fetch(`/api/incidents/${incidentId}/notes?note=${encodeURIComponent(note)}`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
    });
    if (response.ok) {
      setNote('');
      fetchIncident();
    }
  };

  if (!incident) {
    return <div className="loader">Loading incident…</div>;
  }

  return (
    <div className="page-block">
      <h2>Incident #{incident.id}: {incident.title}</h2>
      {message && <div className="success-box">{message}</div>}
      <div className="panel-card">
        <p><strong>Recorded:</strong> {formatDateTimeIST(incident.detection_timestamp)}</p>
        <p><strong>Last updated:</strong> {formatDateTimeIST(incident.last_updated)}</p>
        {incident.resolution_timestamp && (
          <p><strong>Resolved:</strong> {formatDateTimeIST(incident.resolution_timestamp)}</p>
        )}
      </div>
      <div className="form-grid">
        <label>
          Title
          <input name="title" value={incident.title} onChange={handleChange} />
        </label>
        <label>
          Category
          <input name="category" value={incident.category} onChange={handleChange} />
        </label>
        <label>
          Severity
          <select name="severity" value={incident.severity} onChange={handleChange}>
            <option>Critical</option>
            <option>High</option>
            <option>Medium</option>
            <option>Low</option>
          </select>
        </label>
        <label>
          Status
          <select name="status" value={incident.status} onChange={handleChange}>
            <option>New</option>
            <option>Acknowledged</option>
            <option>Investigating</option>
            <option>Contained</option>
            <option>Resolved</option>
            <option>Closed</option>
          </select>
        </label>
        <label>
          Affected asset
          <input name="affected_asset" value={incident.affected_asset} onChange={handleChange} />
        </label>
        <label>
          Assigned analyst
          <input name="assigned_analyst" value={incident.assigned_analyst || ''} onChange={handleChange} />
        </label>
      </div>

      <label>
        Description
        <textarea name="description" value={incident.description} rows="5" onChange={handleChange} />
      </label>
      <label>
        Investigation notes
        <textarea name="investigation_notes" value={incident.investigation_notes || ''} rows="4" onChange={handleChange} />
      </label>
      <label>
        Recommended response actions
        <textarea name="recommended_response_actions" value={incident.recommended_response_actions || ''} rows="3" onChange={handleChange} />
      </label>

      <div className="button-row">
        <button className="primary-button" onClick={handleSave}>Save changes</button>
      </div>

      <div className="note-panel">
        <h3>Investigation notes</h3>
        <textarea value={note} onChange={(e) => setNote(e.target.value)} rows="3" placeholder="Add a note" />
        <button className="secondary-button" onClick={handleNote}>Add note</button>
      </div>
    </div>
  );
}
