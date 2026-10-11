import React from 'react';
import { Lightbulb, Wrench, CheckCircle2, Eye, Info, AlertTriangle } from 'lucide-react';

export default function SuggestionsTab({ suggestions, currentCode, analyzedCode, onSelectLine, onPreviewFix }) {
  const normalize = (s) => (s || '').replace(/\r\n/g, '\n');
  const isSourceDrifted = Boolean(
    analyzedCode &&
    currentCode !== undefined &&
    normalize(currentCode) !== normalize(analyzedCode)
  );

  return (
    <div>
      <div className="tab-toolbar" style={{ marginBottom: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Lightbulb size={18} color="var(--status-warning)" />
          <h3 style={{ fontSize: '14px', fontWeight: 600 }}>Rule-Based Suggestion Engine</h3>
        </div>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          {isSourceDrifted && (
            <span className="badge badge-error">SOURCE MODIFIED</span>
          )}
          <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
            {suggestions?.length || 0} Actionable Items
          </span>
        </div>
      </div>

      {isSourceDrifted && (
        <div className="invalidation-banner" style={{ marginBottom: '16px' }}>
          <AlertTriangle size={16} color="var(--status-error)" style={{ flexShrink: 0 }} />
          <div>
            <strong style={{ color: 'var(--status-error)', fontSize: '12px' }}>
              Source code has changed since last analysis
            </strong>
            <p style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '2px' }}>
              The suggestions below were generated for an earlier version of your code. Click <strong>Analyze</strong> to refresh suggestions.
            </p>
          </div>
        </div>
      )}

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
              <span className={`badge ${sugg.safe_fix ? 'badge-safe' : 'badge-info'}`}>
                {sugg.safe_fix ? 'SAFE FIX AVAILABLE' : sugg.category}
              </span>
            </div>

            <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '8px' }}>
              {sugg.message}
            </p>

            <div className="card-code-block" style={{ marginBottom: '12px' }}>
              <strong>Recommended Action:</strong> {sugg.suggestion}
            </div>

            <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
              <button 
                className="btn-action" 
                onClick={() => onSelectLine(sugg.line)}
                title={`Jump to line ${sugg.line} in code editor`}
              >
                <Eye size={13} />
                View in Editor (Line {sugg.line})
              </button>

              {sugg.safe_fix ? (
                <button 
                  className="btn-action btn-primary"
                  onClick={() => onPreviewFix(sugg)}
                  style={{ gap: '6px' }}
                  title="Review diff and confirm fix before applying"
                  id={`btn-review-fix-${sugg.id}`}
                >
                  <Wrench size={13} />
                  Review & Apply Fix
                </button>
              ) : (
                <div style={{ fontSize: '11px', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <Info size={12} />
                  <span>Manual review recommended (safe automated fix unavailable)</span>
                </div>
              )}
            </div>
          </div>
        ))
      )}
    </div>
  );
}
