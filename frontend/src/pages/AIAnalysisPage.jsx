import { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { formatDateTimeIST } from '../utils/dateTime';

export default function AIAnalysisPage() {
  const { apiFetch } = useAuth();
  const [description, setDescription] = useState('');
  const [logText, setLogText] = useState('');
  const [incidentId, setIncidentId] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const analyze = async () => {
    if (!description.trim() && !logText.trim()) {
      setError('Enter an incident description or a security log excerpt.');
      setResult(null);
      return;
    }

    setLoading(true);
    setError('');
    setResult(null);
    try {
      const response = await apiFetch('/api/ai/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ description, log_text: logText, incident_id: incidentId ? Number(incidentId) : null }),
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(typeof data.detail === 'string' ? data.detail : 'AI analysis failed.');
      }
      setResult(data);
    } catch (analysisError) {
      setError(analysisError.message || 'AI analysis failed. Check your connection and try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page-block">
      <h2>AI incident analysis</h2>
      <div className="panel-grid">
        <div className="panel-card">
          <label>
            Incident description
            <textarea value={description} onChange={(event) => setDescription(event.target.value)} rows="7" placeholder="Describe suspicious activity, alerts, or compromised systems." />
          </label>
          <label>
            Security log excerpt
            <textarea value={logText} onChange={(event) => setLogText(event.target.value)} rows="5" placeholder="Paste relevant security telemetry, logs, or alerts" />
          </label>
          <label>
            Link to incident ID (optional)
            <input value={incidentId} onChange={(event) => setIncidentId(event.target.value)} placeholder="Leave blank for a standalone analysis" />
          </label>
          <button className="primary-button" onClick={analyze} disabled={loading}>
            {loading ? 'Analyzing...' : 'Analyze Incident'}
          </button>
          {error && <div className="error-box" role="alert">{error}</div>}
        </div>

        <div className="panel-card">
          <h3>AI output</h3>
          {!result ? (
            <div className="empty-state">No analysis generated yet.</div>
          ) : (
            <div className="analysis-result">
              <p><strong>Provider:</strong> {result.provider}</p>
              <p><strong>Analyzed:</strong> {formatDateTimeIST(result.timestamp)}</p>
              <p><strong>Classification:</strong> {result.classification}</p>
              <p><strong>Risk severity:</strong> <span className={`badge severity-${result.suggested_severity.toLowerCase()}`}>{result.suggested_severity}</span></p>
              <p><strong>Executive summary:</strong> {result.executive_summary}</p>
              <h4>Suspicious activity</h4>
              <ul>{result.suspicious_activity.map((item) => <li key={item}>{item}</li>)}</ul>
              <h4>Indicators of Compromise (IOCs)</h4>
              <ul>{result.indicators_of_compromise.map((item) => <li key={item}>{item}</li>)}</ul>
              <p><strong>Potential impact:</strong> {result.potential_impact}</p>
              {result.affected_systems.length > 0 && (
                <>
                  <h4>Affected systems</h4>
                  <ul>{result.affected_systems.map((item) => <li key={item}>{item}</li>)}</ul>
                </>
              )}
              {result.investigation_steps.length > 0 && (
                <>
                  <h4>Investigation steps</h4>
                  <ul>{result.investigation_steps.map((item) => <li key={item}>{item}</li>)}</ul>
                </>
              )}
              <h4>Recommended security actions</h4>
              <ul>{result.containment_recommendations.map((item) => <li key={item}>{item}</li>)}</ul>
              {result.remediation_suggestions.length > 0 && (
                <>
                  <h4>Remediation suggestions</h4>
                  <ul>{result.remediation_suggestions.map((item) => <li key={item}>{item}</li>)}</ul>
                </>
              )}
              {result.monitoring_recommendations.length > 0 && (
                <>
                  <h4>Monitoring recommendations</h4>
                  <ul>{result.monitoring_recommendations.map((item) => <li key={item}>{item}</li>)}</ul>
                </>
              )}
              <h4>Rationale</h4>
              <p>{result.rationale}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
