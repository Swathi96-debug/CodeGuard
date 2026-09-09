import React from 'react';
import { Database } from 'lucide-react';

export default function SymbolTableTab({ symbolTable, onSelectLine }) {
  return (
    <div>
      <div className="tab-toolbar" style={{ marginBottom: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Database size={18} color="var(--accent-blue)" />
          <span style={{ fontSize: '13px', fontWeight: 600 }}>Symbol Table & Scope Registry</span>
        </div>
        <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
          {symbolTable?.length || 0} Symbols Registered
        </span>
      </div>

      <div className="data-table-container">
        <table className="data-table">
          <thead>
            <tr>
              <th>Variable Name</th>
              <th>Data Type</th>
              <th>Scope Level</th>
              <th>Declaration Line</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {!symbolTable || symbolTable.length === 0 ? (
              <tr>
                <td colSpan={5} style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '20px' }}>
                  No variable declarations found in symbol table.
                </td>
              </tr>
            ) : (
              symbolTable.map((sym, idx) => (
                <tr 
                  key={idx} 
                  className="clickable"
                  onClick={() => onSelectLine(sym.line)}
                >
                  <td style={{ fontWeight: 600, color: 'var(--accent-blue)' }}>{sym.name}</td>
                  <td>
                    <span className="badge badge-info">{sym.type}</span>
                  </td>
                  <td>{sym.scope}</td>
                  <td>Line {sym.line}</td>
                  <td>
                    {sym.status.includes('Error') ? (
                      <span className="badge badge-error">{sym.status}</span>
                    ) : (
                      <span className="badge badge-safe">{sym.status}</span>
                    )}
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
