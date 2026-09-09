import React from 'react';
import { Copy, CheckCircle2, RefreshCw } from 'lucide-react';

export default function DuplicationTab({ duplication, onSelectLine }) {
  const maxSimilarity = duplication && duplication.length > 0 
    ? Math.max(...duplication.map(d => d.similarity_percentage))
    : 0;

  return (
    <div>
      <div className="stats-grid">
        <div className="stat-box">
          <div className="stat-box-num">{duplication?.length || 0}</div>
          <div className="stat-box-label">Duplicated Blocks</div>
        </div>
        <div className="stat-box">
          <div className="stat-box-num">{maxSimilarity.toFixed(1)}%</div>
          <div className="stat-box-label">Peak Similarity</div>
        </div>
        <div className="stat-box">
          <div className="stat-box-num">
            {duplication ? duplication.reduce((acc, curr) => acc + (curr.block_a_lines[1] - curr.block_a_lines[0] + 1) * 2, 0) : 0}
          </div>
          <div className="stat-box-label">Affected Lines</div>
        </div>
      </div>

      {!duplication || duplication.length === 0 ? (
        <div className="card-item" style={{ textAlign: 'center', padding: '24px', borderColor: 'var(--status-safe)' }}>
          <CheckCircle2 size={32} color="var(--status-safe)" style={{ margin: '0 auto 8px auto' }} />
          <h4 style={{ color: 'var(--status-safe)', fontWeight: 600 }}>No Code Duplication Detected</h4>
          <p style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
            The C source code has no redundant structural token sequences or identical statement blocks.
          </p>
        </div>
      ) : (
        duplication.map((dup, idx) => (
          <div 
            key={idx} 
            className="card-item clickable"
            onClick={() => onSelectLine(dup.block_b_lines[0])}
          >
            <div className="card-item-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Copy size={16} color="var(--status-warning)" />
                <span className="card-item-title">
                  Duplicate Pair #{idx + 1} — Similarity {dup.similarity_percentage}%
                </span>
              </div>
              <span className="badge badge-warning">STRUCTURAL CLONE</span>
            </div>

            <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '8px' }}>
              <strong>Reason:</strong> {dup.reason}
            </p>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginBottom: '10px' }}>
              <div>
                <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-muted)' }}>
                  Block A (Line {dup.block_a_lines[0]}):
                </div>
                <div className="card-code-block">{dup.code_snippet_a}</div>
              </div>
              <div>
                <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-muted)' }}>
                  Block B (Line {dup.block_b_lines[0]}):
                </div>
                <div className="card-code-block">{dup.code_snippet_b}</div>
              </div>
            </div>

            <div style={{ fontSize: '12px', color: 'var(--accent-blue)', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <RefreshCw size={13} />
              <strong>Recommendation:</strong> {dup.suggestion}
            </div>
          </div>
        ))
      )}
    </div>
  );
}
