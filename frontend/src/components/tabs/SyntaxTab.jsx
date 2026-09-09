import React from 'react';
import { AlertTriangle, CheckCircle2, BookOpen } from 'lucide-react';

export default function SyntaxTab({ syntaxIssues, onSelectLine }) {
  return (
    <div>
      {/* Grammar Supported Badge / Info */}
      <div className="card-item" style={{ borderColor: 'var(--border-highlight)', marginBottom: '20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
          <BookOpen size={18} color="var(--accent-blue)" />
          <h3 style={{ fontSize: '14px', fontWeight: 600 }}>Hand-Written Recursive Descent Parser — Supported C Subset</h3>
        </div>
        <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '10px' }}>
          The hand-written parser supports function declarations, variable declarations, assignments, comparison expressions, additive/multiplicative arithmetic expressions, if-else statements, while loops, and return statements.
        </p>
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          {['program → statement*', 'type → int|float|double|char|void', 'declaration & assignment', 'if / while / return', 'binary math & logic'].map((rule, idx) => (
            <span key={idx} className="badge badge-info" style={{ textTransform: 'none', fontFamily: 'var(--font-mono)' }}>
              {rule}
            </span>
          ))}
        </div>
      </div>

      <h4 style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '12px' }}>
        Syntax Error Analysis ({syntaxIssues?.length || 0} Issues Detected)
      </h4>

      {!syntaxIssues || syntaxIssues.length === 0 ? (
        <div className="card-item" style={{ textAlign: 'center', padding: '24px', borderColor: 'var(--status-safe)' }}>
          <CheckCircle2 size={32} color="var(--status-safe)" style={{ margin: '0 auto 8px auto' }} />
          <h4 style={{ color: 'var(--status-safe)', fontWeight: 600 }}>No Syntax Errors Found</h4>
          <p style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
            The C source code passed the top-down parser grammar validation cleanly.
          </p>
        </div>
      ) : (
        syntaxIssues.map((issue, idx) => (
          <div 
            key={idx} 
            className="card-item clickable"
            style={{ borderLeft: '4px solid var(--status-error)' }}
            onClick={() => onSelectLine(issue.line)}
          >
            <div className="card-item-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <AlertTriangle size={16} color="var(--status-error)" />
                <span className="card-item-title">{issue.message}</span>
              </div>
              <span className="badge badge-error">Line {issue.line} : Col {issue.column}</span>
            </div>

            <div className="card-item-desc" style={{ marginTop: '6px' }}>
              <strong>Fix Suggestion:</strong> {issue.suggestion}
            </div>

            <div style={{ fontSize: '11px', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '4px' }}>
              Click to jump to Line {issue.line} in the code editor
            </div>
          </div>
        ))
      )}
    </div>
  );
}
