import React from 'react';
import { Cpu, ShieldAlert, CheckCircle2 } from 'lucide-react';

export default function MemoryTab({ memoryAnalysis, onSelectLine }) {
  return (
    <div>
      {/* Notice header */}
      <div className="card-item" style={{ borderColor: 'var(--border-highlight)', marginBottom: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
          <Cpu size={18} color="var(--accent-blue)" />
          <h3 style={{ fontSize: '13px', fontWeight: 600 }}>Basic Static Memory Analysis</h3>
        </div>
        <p style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
          Tracks heap memory allocation primitives (<code>malloc</code>, <code>calloc</code>, <code>realloc</code>) and matches them against <code>free</code> invocations to detect leaks and double-free anomalies.
        </p>
      </div>

      <div className="data-table-container">
        <table className="data-table">
          <thead>
            <tr>
              <th>Pointer</th>
              <th>Allocation</th>
              <th>Alloc Line</th>
              <th>Freed?</th>
              <th>Free Line</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {!memoryAnalysis || memoryAnalysis.length === 0 ? (
              <tr>
                <td colSpan={6} style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '20px' }}>
                  No dynamic memory allocation primitives (malloc/calloc/free) detected in source code.
                </td>
              </tr>
            ) : (
              memoryAnalysis.map((mem, idx) => (
                <tr 
                  key={idx} 
                  className="clickable"
                  onClick={() => onSelectLine(mem.free_line || mem.allocation_line)}
                >
                  <td style={{ fontWeight: 600, color: 'var(--accent-blue)' }}>{mem.pointer}</td>
                  <td><code>{mem.allocation_function}</code></td>
                  <td>Line {mem.allocation_line}</td>
                  <td>{mem.freed ? 'Yes' : 'No'}</td>
                  <td>{mem.free_line ? `Line ${mem.free_line}` : '-'}</td>
                  <td>
                    {mem.status === 'SAFE' && <span className="badge badge-safe">SAFE</span>}
                    {mem.status === 'POSSIBLE LEAK' && <span className="badge badge-warning">POSSIBLE LEAK</span>}
                    {mem.status === 'DOUBLE FREE' && <span className="badge badge-error">DOUBLE FREE</span>}
                    {mem.status === 'INVALID FREE' && <span className="badge badge-error">INVALID FREE</span>}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
