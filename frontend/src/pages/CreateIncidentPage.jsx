import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const initialState = {
  title: '',
  description: '',
  category: 'Malware',
  severity: 'High',
  priority: 'High',
  status: 'New',
  detection_source: 'EDR',
  affected_asset: '',
  reported_by: 'SOC Analyst',
  assigned_analyst: '',
  investigation_notes: '',
  evidence_references: '',
  recommended_response_actions: '',
};

export default function CreateIncidentPage() {
  const { token, logout } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState(initialState);
  const [message, setMessage] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleChange = (event) => {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setMessage('');
    setSubmitting(true);

    try {
      const response = await fetch('/api/incidents', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          ...form,
          assigned_analyst: form.assigned_analyst.trim() || null,
        }),
      });

      const data = await response.json().catch(() => null);
      if (response.status === 401) {
        logout();
        navigate('/login', {
          replace: true,
          state: { message: 'Your session has expired. Please sign in again before creating an incident.' },
        });
        return;
      }

      if (!response.ok) {
        const detail = data?.detail;
        const errorMessage = response.status === 403
          ? 'Your account cannot create incidents. Contact an administrator if you need additional access.'
          : Array.isArray(detail)
            ? detail.map((error) => `${error.loc?.at(-1) || 'Incident'}: ${error.msg}`).join(' ')
            : typeof detail === 'string'
              ? detail
              : 'Unable to create incident. Check the required fields and try again.';
        setMessage(errorMessage);
        return;
      }

      if (!Number.isInteger(data?.id)) {
        setMessage('The incident service returned an invalid response. Please refresh the incident list before retrying.');
        return;
      }

      navigate('/incidents', {
        state: { successMessage: `Incident "${data.title}" was created successfully.` },
      });
    } catch (error) {
      console.error('Incident creation request failed:', error);
      setMessage('Unable to reach the incident service. Check that the backend is running and try again.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="page-block">
      <h2>Create incident</h2>
      <form className="stack-form" onSubmit={handleSubmit}>
        <div className="form-row">
          <label>
            Title
            <input name="title" value={form.title} onChange={handleChange} required />
          </label>
          <label>
            Category
            <input name="category" value={form.category} onChange={handleChange} required />
          </label>
        </div>
        <div className="form-row">
          <label>
            Severity
            <select name="severity" value={form.severity} onChange={handleChange}>
              <option>Critical</option>
              <option>High</option>
              <option>Medium</option>
              <option>Low</option>
            </select>
          </label>
          <label>
            Priority
            <select name="priority" value={form.priority} onChange={handleChange}>
              <option>High</option>
              <option>Medium</option>
              <option>Low</option>
            </select>
          </label>
          <label>
            Status
            <select name="status" value={form.status} onChange={handleChange}>
              <option>New</option>
              <option>Acknowledged</option>
              <option>Investigating</option>
              <option>Contained</option>
              <option>Resolved</option>
              <option>Closed</option>
            </select>
          </label>
        </div>
        <div className="form-row">
          <label>
            Detection source
            <input name="detection_source" value={form.detection_source} onChange={handleChange} />
          </label>
          <label>
            Affected asset
            <input name="affected_asset" value={form.affected_asset} onChange={handleChange} required />
          </label>
        </div>
        <div className="form-row">
          <label>
            Reported by
            <input name="reported_by" value={form.reported_by} onChange={handleChange} />
          </label>
          <label>
            Assigned analyst (optional)
            <input name="assigned_analyst" value={form.assigned_analyst} onChange={handleChange} />
          </label>
        </div>
        <label>
          Description
          <textarea name="description" value={form.description} onChange={handleChange} rows="5" required />
        </label>
        <label>
          Investigation notes
          <textarea name="investigation_notes" value={form.investigation_notes} onChange={handleChange} rows="3" />
        </label>
        <label>
          Evidence references
          <textarea name="evidence_references" value={form.evidence_references} onChange={handleChange} rows="2" />
        </label>
        <label>
          Recommended response actions
          <textarea name="recommended_response_actions" value={form.recommended_response_actions} onChange={handleChange} rows="2" />
        </label>
        {message && <div className="error-box" role="alert" aria-live="polite">{message}</div>}
        <button type="submit" className="primary-button" disabled={submitting}>
          {submitting ? 'Creating incident...' : 'Create incident'}
        </button>
      </form>
    </div>
  );
}
