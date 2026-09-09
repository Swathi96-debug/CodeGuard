import React from 'react';
import { ShieldAlert, AlertTriangle, Info, CheckCircle2 } from 'lucide-react';

export default function AnomaliesTab({ anomalies, onSelectLine }) {
  return (
    <div>
      <div className="tab-toolbar" style={{ marginBottom: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <ShieldAlert size={18} color="var(--status-error)" />
          <h3 style={{ fontSize: '14px', fontWeight: 600 }}>Anomaly Center</h3>
        </div>
        <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
          {anomalies?.length || 0} Total Anomalies Logged
        </span>
      </div>

      {!anomalies || anomalies.length === 0 ? (
        <div className="card-item" style={{ textAlign: 'center', padding: '24px', borderColor: 'var(--status-safe)' }}>
          <CheckCircle2 size={32} color="var(--status-safe)" style={{ margin: '0 auto 8px auto' }} />
          <h4 style={{ color: 'var(--status-safe)', fontWeight: 600 }}>Zero Anomalies Detected</h4>
          <p style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
            No syntax errors, semantic flaws, memory leaks, or code duplications were found.
          </p>
        </div>
      ) : (
        anomalies.map((anom) => (
          <div 
            key={anom.id} 
            className="card-item clickable"
            style={{ 
              borderLeft: `4px solid ${
                anom.severity === 'error' ? 'var(--status-error)' :
                anom.severity === 'warning' ? 'var(--status-warning)' : 'var(--status-info)'
              }` 
            }}
            onClick={() => onSelectLine(anom.line)}
          >
            <div className="card-item-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                {anom.severity === 'error' && <AlertTriangle size={16} color="var(--status-error)" />}
                {anom.severity === 'warning' && <AlertTriangle size={16} color="var(--status-warning)" />}
                {anom.severity === 'info' && <Info size={16} color="var(--status-info)" />}
                <span className="card-item-title">{anom.message}</span>
              </div>
              <span className={`badge badge-${anom.severity === 'error' ? 'error' : anom.severity === 'warning' ? 'warning' : 'info'}`}>
                {anom.issue_type} — Line {anom.line}
              </span>
            </div>

            <div style={{ margin: '8px 0', fontSize: '12px', color: 'var(--text-secondary)' }}>
              <strong style={{ color: 'var(--text-primary)' }}>Why it matters:</strong> {anom.why_it_matters}
            </div>

            <div className="card-code-block" style={{ borderLeft: '3px solid var(--accent-blue)' }}>
              <strong>Rule Suggestion:</strong> {anom.suggestion}
            </div>

            <div style={{ marginTop: '8px', fontSize: '11px', color: 'var(--text-muted)' }}>
              Click to jump & highlight Line {anom.line} in left editor panel
            </div>
          </div>
        ))
      )}
    </div>
  );
}
