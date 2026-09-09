import React from 'react';
import { Lightbulb, Wrench, CheckCircle2 } from 'lucide-react';

export default function SuggestionsTab({ suggestions, onSelectLine, onApplyFix }) {
  return (
    <div>
      <div className="tab-toolbar" style={{ marginBottom: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Lightbulb size={18} color="var(--status-warning)" />
          <h3 style={{ fontSize: '14px', fontWeight: 600 }}>Rule-Based Suggestion Engine</h3>
        </div>
        <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
          {suggestions?.length || 0} Actionable Fixes
        </span>
      </div>

      {!suggestions || suggestions.length === 0 ? (
        <div className="card-item" style={{ textAlign: 'center', padding: '24px', borderColor: 'var(--status-safe)' }}>
          <CheckCircle2 size={32} color="var(--status-safe)" style={{ margin: '0 auto 8px auto' }} />
          <h4 style={{ color: 'var(--status-safe)', fontWeight: 600 }}>No Suggestions Needed</h4>
          <p style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
            Code is clean with no deterministic static analysis warnings.
          </p>
        </div>
      ) : (
        suggestions.map((sugg) => (
          <div key={sugg.id} className="card-item">
            <div className="card-item-header">
              <span className="card-item-title">{sugg.title} (Line {sugg.line})</span>
              <span className="badge badge-info">{sugg.category}</span>
            </div>

            <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '8px' }}>
              {sugg.message}
            </p>

            <div className="card-code-block" style={{ marginBottom: '12px' }}>
              <strong>Recommended Action:</strong> {sugg.suggestion}
            </div>

            <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
              <button 
                className="btn-action" 
                onClick={() => onSelectLine(sugg.line)}
              >
                View in Editor (Line {sugg.line})
              </button>

              {sugg.safe_fix && (
                <button 
                  className="btn-action btn-primary"
                  onClick={() => onApplyFix(sugg)}
                  style={{ gap: '6px' }}
                >
                  <Wrench size={13} />
                  Apply Safe Fix
                </button>
              )}
            </div>
          </div>
        ))
      )}
    </div>
  );
}
