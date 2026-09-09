import React, { useRef } from 'react';
import { Code2, Upload, Play, Shield, FileCode } from 'lucide-react';
import { SAMPLE_PROGRAMS } from '../data/samplePrograms';

export default function WelcomePage({ onSelectOption, theme, toggleTheme }) {
  const fileInputRef = useRef(null);

  const handleFileUpload = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.name.endsWith('.c')) {
      alert('Invalid file format. Please upload a C source file (.c extension).');
      return;
    }

    const reader = new FileReader();
    reader.onload = (event) => {
      const code = event.target?.result || '';
      onSelectOption(code);
    };
    reader.readAsText(file);
  };

  return (
    <div className="welcome-container" data-theme={theme}>
      <div className="welcome-header">
        <div style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', marginBottom: '12px', background: 'var(--bg-secondary)', padding: '6px 14px', borderRadius: '20px', border: '1px solid var(--border-color)' }}>
          <Shield size={16} color="var(--accent-blue)" />
          <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary)' }}>Compiler Design Project</span>
        </div>
        <h1 className="welcome-title">CodeGuard</h1>
        <h2 className="welcome-subtitle">C Code Analysis & Memory Safety Tool</h2>
        <p className="welcome-desc">
          Analyze C source code using manual lexical analysis, syntax parsing, AST construction, symbol-table tracking, memory leak detection, and structural duplication analysis.
        </p>
      </div>

      <div className="welcome-cards">
        {/* OPTION 1 — ENTER C CODE */}
        <div className="input-card">
          <div className="card-icon">
            <Code2 size={24} />
          </div>
          <h3 className="card-title">Enter C Code</h3>
          <p className="card-desc">
            Write or paste your C source code directly into the interactive compiler editor.
          </p>
          <button 
            className="btn-action btn-primary" 
            style={{ width: '100%', justifyContent: 'center' }}
            onClick={() => onSelectOption('')}
          >
            Open Code Editor
          </button>
        </div>

        {/* OPTION 2 — UPLOAD C FILE */}
        <div className="input-card">
          <div className="card-icon">
            <Upload size={24} />
          </div>
          <h3 className="card-title">Upload C File</h3>
          <p className="card-desc">
            Upload a .c source file from your device for immediate static compiler analysis.
          </p>
          <input 
            type="file" 
            ref={fileInputRef} 
            accept=".c" 
            style={{ display: 'none' }} 
            onChange={handleFileUpload}
          />
          <button 
            className="btn-action btn-primary" 
            style={{ width: '100%', justifyContent: 'center' }}
            onClick={() => fileInputRef.current?.click()}
          >
            Choose .c File
          </button>
        </div>
      </div>

      {/* SAMPLE PROGRAMS */}
      <div className="samples-section">
        <div className="samples-title">Or try a sample C program</div>
        <div className="samples-grid">
          {SAMPLE_PROGRAMS.map((sample) => (
            <button 
              key={sample.id} 
              className="sample-chip"
              onClick={() => onSelectOption(sample.code)}
            >
              <div className="sample-chip-name">{sample.name}</div>
              <div className="sample-chip-desc">{sample.description}</div>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
