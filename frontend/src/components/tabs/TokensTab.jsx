import React, { useState } from 'react';

export default function TokensTab({ tokens, tokenStats, onSelectLine }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedType, setSelectedType] = useState('ALL');
  const [sortBy, setSortBy] = useState('id');

  const filteredTokens = (tokens || []).filter((tok) => {
    const matchesSearch = tok.lexeme.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          tok.token_type.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesType = selectedType === 'ALL' || tok.token_type === selectedType;
    return matchesSearch && matchesType;
  }).sort((a, b) => {
    if (sortBy === 'lexeme') return a.lexeme.localeCompare(b.lexeme);
    if (sortBy === 'token_type') return a.token_type.localeCompare(b.token_type);
    if (sortBy === 'line') return a.line - b.line;
    return a.id - b.id;
  });

  return (
    <div>
      <div className="stats-grid">
        <div className="stat-box">
          <div className="stat-box-num">{tokenStats?.keywords || 0}</div>
          <div className="stat-box-label">Keywords</div>
        </div>
        <div className="stat-box">
          <div className="stat-box-num">{tokenStats?.identifiers || 0}</div>
          <div className="stat-box-label">Identifiers</div>
        </div>
        <div className="stat-box">
          <div className="stat-box-num">{tokenStats?.constants || 0}</div>
          <div className="stat-box-label">Constants</div>
        </div>
        <div className="stat-box">
          <div className="stat-box-num">{tokenStats?.operators || 0}</div>
          <div className="stat-box-label">Operators</div>
        </div>
        <div className="stat-box">
          <div className="stat-box-num">{tokenStats?.separators || 0}</div>
          <div className="stat-box-label">Separators</div>
        </div>
        <div className="stat-box">
          <div className="stat-box-num">{tokenStats?.strings || 0}</div>
          <div className="stat-box-label">Strings</div>
        </div>
      </div>

      <div className="tab-toolbar">
        <input 
          type="text" 
          placeholder="Search lexeme or type..." 
          className="search-input"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          style={{ width: '200px' }}
        />

        <select 
          className="search-input" 
          value={selectedType}
          onChange={(e) => setSelectedType(e.target.value)}
        >
          <option value="ALL">All Token Types</option>
          <option value="KEYWORD">Keyword</option>
          <option value="IDENTIFIER">Identifier</option>
          <option value="INT_CONSTANT">Int Constant</option>
          <option value="FLOAT_CONSTANT">Float Constant</option>
          <option value="STRING_LITERAL">String Literal</option>
          <option value="OPERATOR">Operator</option>
          <option value="SEPARATOR">Separator</option>
        </select>

        <select 
          className="search-input" 
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value)}
        >
          <option value="id">Sort by Token #</option>
          <option value="line">Sort by Line</option>
          <option value="lexeme">Sort by Lexeme</option>
          <option value="token_type">Sort by Type</option>
        </select>

        <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
          Showing {filteredTokens.length} of {tokens?.length || 0} tokens
        </span>
      </div>

      <div className="data-table-container">
        <table className="data-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Lexeme</th>
              <th>Token Type</th>
              <th>Line</th>
              <th>Column</th>
            </tr>
          </thead>
          <tbody>
            {filteredTokens.length === 0 ? (
              <tr>
                <td colSpan={5} style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '20px' }}>
                  No matching tokens found.
                </td>
              </tr>
            ) : (
              filteredTokens.map((tok) => (
                <tr 
                  key={tok.id} 
                  className="clickable"
                  onClick={() => onSelectLine(tok.line)}
                >
                  <td style={{ color: 'var(--text-muted)' }}>{tok.id}</td>
                  <td style={{ fontWeight: 600, color: 'var(--accent-blue)' }}>{tok.lexeme}</td>
                  <td>
                    <span className="badge badge-info">{tok.token_type}</span>
                  </td>
                  <td>Line {tok.line}</td>
                  <td>Col {tok.column}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
