import React from 'react';
import { AlertCircle, CheckCircle2 } from 'lucide-react';

export default function SemanticTab({ semanticIssues, onSelectLine }) {
  return (
    <div>
      <div className="tab-toolbar" style={{ marginBottom: '16px' }}>
        <h4 style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)' }}>
          Semantic Analyzer Results ({semanticIssues?.length || 0} Issues)
        </h4>
      </div>

      {!semanticIssues || semanticIssues.length === 0 ? (
        <div className="card-item" style={{ textAlign: 'center', padding: '24px', borderColor: 'var(--status-safe)' }}>
          <CheckCircle2 size={32} color="var(--status-safe)" style={{ margin: '0 auto 8px auto' }} />
          <h4 style={{ color: 'var(--status-safe)', fontWeight: 600 }}>No Semantic Errors Found</h4>
          <p style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
            All identifiers are properly declared before usage, and variable scopes are consistent.
          </p>
        </div>
      ) : (
        semanticIssues.map((issue, idx) => (
          <div 
            key={idx} 
            className="card-item clickable"
            style={{ borderLeft: '4px solid var(--status-error)' }}
            onClick={() => onSelectLine(issue.line)}
          >
            <div className="card-item-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <AlertCircle size={16} color="var(--status-error)" />
                <span className="card-item-title">{issue.message}</span>
              </div>
              <span className="badge badge-error">{issue.issue_type} — Line {issue.line}</span>
            </div>

            <div className="card-item-desc" style={{ marginTop: '6px' }}>
              <strong>Fix Recommendation:</strong> {issue.suggestion}
            </div>

            <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
              Click to inspect Line {issue.line} in code editor
            </div>
          </div>
        ))
      )}
    </div>
  );
}
