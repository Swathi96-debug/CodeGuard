import React from 'react';
import { Wrench, X, Check, AlertTriangle, ShieldCheck, ArrowRight, FileCode } from 'lucide-react';

export default function FixPreviewModal({
  isOpen,
  suggestion,
  currentCode,
  codeSnapshot,
  onClose,
  onConfirm
}) {
  if (!isOpen || !suggestion) return null;

  const normalize = (s) => (s || '').replace(/\r\n/g, '\n');
  const snapshot = suggestion.sourceSnapshot || codeSnapshot || '';
  const isInvalidated = Boolean(
    snapshot !== undefined &&
    currentCode !== undefined &&
    normalize(currentCode) !== normalize(snapshot)
  );

  const targetLine = suggestion.target_line || suggestion.line || 1;
  const fixType = suggestion.fix_type || 'replace';
  const originalSnippet = suggestion.original_snippet ?? '';
  const fixedSnippet = suggestion.fixed_snippet || suggestion.safe_fix || '';
  const explanation = suggestion.fix_explanation || suggestion.suggestion;

  // Compute context lines from the snapshot code
  const snapshotLines = (snapshot || '').split('\n');
  const contextStart = Math.max(0, targetLine - 3);
  const contextEnd = Math.min(snapshotLines.length, targetLine + 2);

  // Build original and preview line slices from snapshot
  const originalContext = snapshotLines.slice(contextStart, contextEnd);

  let previewLines = [...snapshotLines];
  if (fixType === 'replace') {
    if (targetLine - 1 < previewLines.length) {
      previewLines[targetLine - 1] = fixedSnippet;
    }
  } else if (fixType === 'insert') {
    previewLines.splice(targetLine - 1, 0, fixedSnippet);
  }
  const previewContext = previewLines.slice(
    contextStart,
    Math.min(previewLines.length, contextEnd + (fixType === 'insert' ? 1 : 0))
  );

  return (
    <div className="modal-backdrop">
      <div 
        className="modal-container"
        role="dialog"
        aria-modal="true"
        aria-labelledby="fix-modal-title"
      >
        {/* MODAL HEADER */}
        <div className="modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div className="modal-icon-badge">
              <Wrench size={18} color="var(--accent-blue)" />
            </div>
            <div>
              <h3 id="fix-modal-title" className="modal-title">
                {suggestion.title || 'Review Safe Fix'}
              </h3>
              <div style={{ display: 'flex', gap: '8px', alignItems: 'center', marginTop: '2px' }}>
                <span className="badge badge-info">{suggestion.category || 'COMPILER'}</span>
                <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                  Target: Line {targetLine} ({fixType === 'insert' ? 'Insert' : 'Replace'})
                </span>
                {isInvalidated && (
                  <span className="badge badge-error">STALE PREVIEW</span>
                )}
              </div>
            </div>
          </div>
          <button 
            className="btn-action" 
            onClick={onClose} 
            title="Cancel and Close"
            aria-label="Close modal"
          >
            <X size={18} />
          </button>
        </div>

        {/* MODAL CONTENT */}
        <div className="modal-body">
          {/* Prominent Invalidation Alert if code changed */}
          {isInvalidated && (
            <div 
              className="invalidation-banner" 
              id="fix-invalidation-warning"
              style={{ marginBottom: '16px' }}
            >
              <AlertTriangle size={20} color="var(--status-error)" style={{ flexShrink: 0 }} />
              <div>
                <strong style={{ color: 'var(--status-error)', fontSize: '13px' }}>
                  Source Code Modified — Fix Preview Invalidated
                </strong>
                <p style={{ fontSize: '12px', marginTop: '3px', color: 'var(--text-primary)' }}>
                  The editor source code differs from the snapshot taken when this preview was opened. To prevent applying stale or incorrect changes, this fix has been disabled.
                </p>
                <p style={{ fontSize: '11px', marginTop: '4px', color: 'var(--text-muted)' }}>
                  Please click <strong>Cancel</strong>, then re-run analysis to preview a fresh fix for your updated code.
                </p>
              </div>
            </div>
          )}

          {/* Finding & Rationale Box */}
          <div className="fix-info-box">
            <div style={{ marginBottom: '8px' }}>
              <strong style={{ color: 'var(--text-primary)', fontSize: '13px' }}>Issue Detected:</strong>
              <p style={{ color: 'var(--text-secondary)', fontSize: '12px', marginTop: '2px' }}>
                {suggestion.message}
              </p>
            </div>
            <div>
              <strong style={{ color: 'var(--text-primary)', fontSize: '13px' }}>Proposed Safe Fix:</strong>
              <p style={{ color: 'var(--accent-blue)', fontSize: '12px', marginTop: '2px', fontWeight: 500 }}>
                {explanation}
              </p>
            </div>
          </div>

          {/* DIFF PREVIEW */}
          <div style={{ marginTop: '16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary)' }}>
                DIFF PREVIEW (SOURCE RANGE: LINES {contextStart + 1}–{contextEnd})
              </span>
              <span style={{ fontSize: '11px', color: isInvalidated ? 'var(--status-error)' : 'var(--text-muted)' }}>
                {isInvalidated ? 'Diff is stale (source was modified)' : 'Original vs Proposed'}
              </span>
            </div>

            <div className="diff-columns" style={{ opacity: isInvalidated ? 0.6 : 1 }}>
              {/* CURRENT / ORIGINAL */}
              <div className="diff-column">
                <div className="diff-column-header">Snapshot Source</div>
                <div className="diff-code-area">
                  {originalContext.map((lineText, idx) => {
                    const lineNo = contextStart + idx + 1;
                    const isTarget = lineNo === targetLine && fixType === 'replace';
                    return (
                      <div 
                        key={idx} 
                        className={`diff-line ${isTarget ? 'diff-line-removed' : ''}`}
                      >
                        <span className="diff-line-num">{lineNo}</span>
                        <span className="diff-line-prefix">{isTarget ? '-' : ' '}</span>
                        <span className="diff-line-code">{lineText || ' '}</span>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* PROPOSED FIX */}
              <div className="diff-column">
                <div className="diff-column-header proposed">Proposed Fix</div>
                <div className="diff-code-area">
                  {previewContext.map((lineText, idx) => {
                    const lineNo = contextStart + idx + 1;
                    const isFixed = (fixType === 'replace' && lineNo === targetLine) ||
                                    (fixType === 'insert' && lineNo === targetLine);
                    return (
                      <div 
                        key={idx} 
                        className={`diff-line ${isFixed ? 'diff-line-added' : ''}`}
                      >
                        <span className="diff-line-num">{lineNo}</span>
                        <span className="diff-line-prefix">{isFixed ? '+' : ' '}</span>
                        <span className="diff-line-code">{lineText || ' '}</span>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* MODAL FOOTER */}
        <div className="modal-footer">
          <div style={{ fontSize: '11px', color: isInvalidated ? 'var(--status-error)' : 'var(--text-muted)' }}>
            {isInvalidated ? (
              <strong>⚠️ Preview invalidated: Apply button disabled. Please close and re-analyze.</strong>
            ) : (
              'Changes will not be applied to source code until you confirm.'
            )}
          </div>
          <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
            <button 
              className="btn-action" 
              onClick={onClose} 
              id="btn-fix-cancel"
            >
              Cancel
            </button>
            <button 
              className="btn-action btn-primary" 
              onClick={() => onConfirm(suggestion)}
              disabled={isInvalidated}
              id="btn-fix-confirm"
              title={isInvalidated ? 'Source code was modified; please close and re-analyze' : 'Apply fix to source code'}
              style={{
                opacity: isInvalidated ? 0.35 : 1,
                cursor: isInvalidated ? 'not-allowed' : 'pointer'
              }}
            >
              <Check size={14} />
              Confirm & Apply Fix
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
