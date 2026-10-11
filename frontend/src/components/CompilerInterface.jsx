import React, { useState } from 'react';
import { 
  Play, Trash2, Upload, FileCode, Sun, Moon, ArrowLeft,
  Layers, Code2, AlertTriangle, FolderTree, Database, AlertCircle,
  Cpu, Copy, ShieldAlert, Lightbulb, FileText, BookOpen, Wand2
} from 'lucide-react';
import CodeEditor from './CodeEditor';
import FixPreviewModal from './FixPreviewModal';
import TokensTab from './tabs/TokensTab';
import SyntaxTab from './tabs/SyntaxTab';
import AstTab from './tabs/AstTab';
import SymbolTableTab from './tabs/SymbolTableTab';
import SemanticTab from './tabs/SemanticTab';
import MemoryTab from './tabs/MemoryTab';
import DuplicationTab from './tabs/DuplicationTab';
import AnomaliesTab from './tabs/AnomaliesTab';
import SuggestionsTab from './tabs/SuggestionsTab';
import ReportTab from './tabs/ReportTab';
import OverviewTab from './tabs/OverviewTab';
import DocumentationTab from './tabs/DocumentationTab';
import { SAMPLE_PROGRAMS } from '../data/samplePrograms';

export default function CompilerInterface({ initialCode, onBackToWelcome, theme, toggleTheme }) {
  const [code, setCode] = useState(initialCode || '');
  const [activeTab, setActiveTab] = useState('overview');
  const [activeLine, setActiveLine] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [progressStage, setProgressStage] = useState('');
  const [analysisResult, setAnalysisResult] = useState(null);
  const [previewSuggestion, setPreviewSuggestion] = useState(null);
  const [codeSnapshot, setCodeSnapshot] = useState('');
  const [analyzedCode, setAnalyzedCode] = useState('');

  const stages = [
    "Preprocessing...",
    "Generating tokens...",
    "Parsing...",
    "Building AST...",
    "Building symbol table...",
    "Analyzing semantics...",
    "Analyzing memory...",
    "Checking duplication...",
    "Generating suggestions...",
    "Generating report..."
  ];

  const handleAnalyze = async (codeToAnalyze = null) => {
    const source = typeof codeToAnalyze === 'string' ? codeToAnalyze : code;
    if (!source.trim()) {
      alert('Please enter or upload C source code before analyzing.');
      return;
    }

    setIsAnalyzing(true);

    // Progress stage simulation for user feedback
    for (let i = 0; i < stages.length; i++) {
      setProgressStage(stages[i]);
      await new Promise(resolve => setTimeout(resolve, 60));
    }

    try {
      const apiUrl = window.location.origin.includes('5173')
        ? 'http://127.0.0.1:8000/analyze'
        : '/analyze';

      const response = await fetch(apiUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code: source })
      });

      if (!response.ok) {
        throw new Error(`Server returned error status ${response.status}`);
      }

      const data = await response.json();
      // Attach the exact source snapshot used to generate these suggestions:
      if (data && data.suggestions) {
        data.suggestions = data.suggestions.map(s => ({
          ...s,
          sourceSnapshot: source
        }));
      }
      setAnalysisResult(data);
      setAnalyzedCode(source);
    } catch (err) {
      alert(`Unable to connect to analysis server: ${err.message}. Please ensure the backend is running.`);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleClear = () => {
    setCode('');
    setAnalysisResult(null);
    setAnalyzedCode('');
    setActiveLine(null);
    setPreviewSuggestion(null);
  };

  const handleSelectLine = (line) => {
    if (line) {
      setActiveLine({ line, ts: Date.now() });
    }
  };

  const handleLoadSample = (e) => {
    const sampleId = e.target.value;
    if (!sampleId) return;
    const sample = SAMPLE_PROGRAMS.find(s => s.id === sampleId);
    if (sample) {
      setCode(sample.code);
      setAnalysisResult(null);
      setAnalyzedCode('');
      setActiveLine(null);
      setPreviewSuggestion(null);
    }
  };

  const handleFileUpload = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.name.endsWith('.c')) {
      alert('Invalid file format. Please upload a C file (.c extension).');
      return;
    }

    const reader = new FileReader();
    reader.onload = (evt) => {
      setCode(evt.target?.result || '');
      setAnalysisResult(null);
      setAnalyzedCode('');
      setActiveLine(null);
      setPreviewSuggestion(null);
    };
    reader.readAsText(file);
  };

  const handleFormat = () => {
    // Basic automatic C code formatter (indentation adjustment)
    const lines = code.split('\n');
    let indentLevel = 0;
    const formatted = lines.map(line => {
      let trimmed = line.trim();
      if (trimmed.startsWith('}')) {
        indentLevel = Math.max(0, indentLevel - 1);
      }
      const indentedLine = '    '.repeat(indentLevel) + trimmed;
      if (trimmed.endsWith('{') && !trimmed.startsWith('//')) {
        indentLevel++;
      }
      return indentedLine;
    }).join('\n');
    setCode(formatted);
  };

  const handleOpenPreview = (sugg) => {
    // Retain the immutable source snapshot used when this suggestion was generated
    const immutableSnapshot = sugg.sourceSnapshot || analyzedCode || code;
    setPreviewSuggestion({ ...sugg, sourceSnapshot: immutableSnapshot });
    setCodeSnapshot(immutableSnapshot);
  };

  const handleClosePreview = () => {
    setPreviewSuggestion(null);
  };

  const handleConfirmFix = (sugg) => {
    if (!sugg || (!sugg.safe_fix && !sugg.fixed_snippet)) return;
    const normalize = (s) => (s || '').replace(/\r\n/g, '\n');
    const snapshot = sugg.sourceSnapshot || codeSnapshot || analyzedCode;
    
    // Guard 1: Verify current source matches the exact snapshot used when preview was generated
    if (normalize(code) !== normalize(snapshot)) {
      alert('Cannot apply fix: source code has changed since preview was generated. Please close and re-analyze.');
      return;
    }

    const lines = normalize(code).split('\n');
    const targetLine = sugg.target_line || sugg.line;
    const idx = targetLine - 1;

    // Guard 2: Line-level content check to ensure target line has not drifted
    if (sugg.fix_type === 'replace' && sugg.original_snippet !== undefined && sugg.original_snippet !== null) {
      if (lines[idx] !== sugg.original_snippet && lines[idx]?.trim() !== sugg.original_snippet?.trim()) {
        alert('Cannot apply fix: target line content has changed since preview was generated. Please close and re-analyze.');
        return;
      }
    }

    let newCode = code;

    if (sugg.fix_type === 'replace') {
      if (0 <= idx && idx < lines.length) {
        lines[idx] = sugg.fixed_snippet || sugg.safe_fix;
        newCode = lines.join('\n');
      }
    } else if (sugg.fix_type === 'insert') {
      if (0 <= idx && idx <= lines.length) {
        lines.splice(idx, 0, sugg.fixed_snippet || sugg.safe_fix);
        newCode = lines.join('\n');
      }
    } else {
      // Fallback
      if (sugg.category === 'SYNTAX' && sugg.message.includes('semicolon')) {
        lines[idx] = sugg.safe_fix;
      } else {
        lines.splice(targetLine, 0, `    ${sugg.safe_fix}`);
      }
      newCode = lines.join('\n');
    }

    setCode(newCode);
    setPreviewSuggestion(null);

    // Automatically re-analyze with updated code
    handleAnalyze(newCode);
  };

  return (
    <div className="compiler-layout" data-theme={theme}>
      {/* TOP BAR */}
      <header className="top-header">
        <div className="brand-section">
          <button className="btn-action" onClick={onBackToWelcome} title="Back to Welcome Page">
            <ArrowLeft size={16} />
          </button>
          <div className="brand-title">
            <span>CodeGuard</span>
            <span className="brand-badge">C Compiler Analysis IDE</span>
          </div>
        </div>

        <div className="header-actions">
          <button className="btn-action btn-primary" onClick={() => handleAnalyze()}>
            <Play size={14} />
            Analyze
          </button>

          <button className="btn-action" onClick={handleClear}>
            <Trash2 size={14} />
            Clear
          </button>

          <select className="btn-action" onChange={handleLoadSample} defaultValue="">
            <option value="" disabled>Load Sample...</option>
            {SAMPLE_PROGRAMS.map(s => (
              <option key={s.id} value={s.id}>{s.name}</option>
            ))}
          </select>

          <label className="btn-action" style={{ cursor: 'pointer' }}>
            <Upload size={14} />
            Upload .c
            <input type="file" accept=".c" style={{ display: 'none' }} onChange={handleFileUpload} />
          </label>

          <button className="btn-action" onClick={handleFormat} title="Format C Source Code">
            <Wand2 size={14} />
            Format
          </button>

          <button className="btn-action" onClick={toggleTheme}>
            {theme === 'dark' ? <Sun size={14} /> : <Moon size={14} />}
            {theme === 'dark' ? 'Light' : 'Dark'}
          </button>
        </div>
      </header>

      {/* TWO PANEL LAYOUT */}
      <div className="panels-wrapper">
        {/* LEFT PANEL — SOURCE CODE EDITOR */}
        <div className="left-panel">
          <div className="panel-header">
            <span>C SOURCE CODE EDITOR</span>
            <span>{code.split('\n').length} Lines</span>
          </div>
          <div className="editor-container">
            <CodeEditor 
              code={code} 
              onChange={setCode} 
              activeLine={activeLine} 
              theme={theme}
              analysisResult={analysisResult}
            />

            {/* Analysis Progress Overlay */}
            {isAnalyzing && (
              <div className="progress-overlay">
                <div className="progress-card">
                  <div className="spinner"></div>
                  <h4 style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '4px' }}>
                    Compiling & Analyzing
                  </h4>
                  <div style={{ fontSize: '12px', color: 'var(--accent-blue)', fontFamily: 'var(--font-mono)' }}>
                    {progressStage}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* RIGHT PANEL — ANALYSIS TABS */}
        <div className="right-panel">
          <nav className="tabs-nav">
            <button className={`tab-btn ${activeTab === 'overview' ? 'active' : ''}`} onClick={() => setActiveTab('overview')}>
              <Layers size={14} /> Overview
            </button>
            <button className={`tab-btn ${activeTab === 'tokens' ? 'active' : ''}`} onClick={() => setActiveTab('tokens')}>
              <Code2 size={14} /> Tokens
              {analysisResult && <span className="tab-badge">{analysisResult.tokens.length}</span>}
            </button>
            <button className={`tab-btn ${activeTab === 'syntax' ? 'active' : ''}`} onClick={() => setActiveTab('syntax')}>
              <AlertTriangle size={14} /> Syntax
              {analysisResult && analysisResult.syntax_issues.length > 0 && (
                <span className="tab-badge" style={{ background: 'var(--status-error-bg)', color: 'var(--status-error)' }}>
                  {analysisResult.syntax_issues.length}
                </span>
              )}
            </button>
            <button className={`tab-btn ${activeTab === 'ast' ? 'active' : ''}`} onClick={() => setActiveTab('ast')}>
              <FolderTree size={14} /> AST
            </button>
            <button className={`tab-btn ${activeTab === 'symbols' ? 'active' : ''}`} onClick={() => setActiveTab('symbols')}>
              <Database size={14} /> Symbol Table
            </button>
            <button className={`tab-btn ${activeTab === 'semantic' ? 'active' : ''}`} onClick={() => setActiveTab('semantic')}>
              <AlertCircle size={14} /> Semantic
            </button>
            <button className={`tab-btn ${activeTab === 'memory' ? 'active' : ''}`} onClick={() => setActiveTab('memory')}>
              <Cpu size={14} /> Memory
            </button>
            <button className={`tab-btn ${activeTab === 'duplication' ? 'active' : ''}`} onClick={() => setActiveTab('duplication')}>
              <Copy size={14} /> Duplication
            </button>
            <button className={`tab-btn ${activeTab === 'anomalies' ? 'active' : ''}`} onClick={() => setActiveTab('anomalies')}>
              <ShieldAlert size={14} /> Anomalies
              {analysisResult && analysisResult.anomalies.length > 0 && (
                <span className="tab-badge" style={{ background: 'var(--status-warning-bg)', color: 'var(--status-warning)' }}>
                  {analysisResult.anomalies.length}
                </span>
              )}
            </button>
            <button className={`tab-btn ${activeTab === 'suggestions' ? 'active' : ''}`} onClick={() => setActiveTab('suggestions')}>
              <Lightbulb size={14} /> Suggestions
            </button>
            <button className={`tab-btn ${activeTab === 'report' ? 'active' : ''}`} onClick={() => setActiveTab('report')}>
              <FileText size={14} /> Report
            </button>
            <button className={`tab-btn ${activeTab === 'docs' ? 'active' : ''}`} onClick={() => setActiveTab('docs')}>
              <BookOpen size={14} /> Docs
            </button>
          </nav>

          <div className="tab-content">
            {activeTab === 'overview' && (
              <OverviewTab statistics={analysisResult?.statistics} onSwitchTab={setActiveTab} />
            )}
            {activeTab === 'tokens' && (
              <TokensTab tokens={analysisResult?.tokens} tokenStats={analysisResult?.token_stats} onSelectLine={handleSelectLine} />
            )}
            {activeTab === 'syntax' && (
              <SyntaxTab syntaxIssues={analysisResult?.syntax_issues} onSelectLine={handleSelectLine} />
            )}
            {activeTab === 'ast' && (
              <AstTab ast={analysisResult?.ast} onSelectLine={handleSelectLine} />
            )}
            {activeTab === 'symbols' && (
              <SymbolTableTab symbolTable={analysisResult?.symbol_table} onSelectLine={handleSelectLine} />
            )}
            {activeTab === 'semantic' && (
              <SemanticTab semanticIssues={analysisResult?.semantic_issues} onSelectLine={handleSelectLine} />
            )}
            {activeTab === 'memory' && (
              <MemoryTab memoryAnalysis={analysisResult?.memory_analysis} onSelectLine={handleSelectLine} />
            )}
            {activeTab === 'duplication' && (
              <DuplicationTab duplication={analysisResult?.duplication} onSelectLine={handleSelectLine} />
            )}
            {activeTab === 'anomalies' && (
              <AnomaliesTab anomalies={analysisResult?.anomalies} onSelectLine={handleSelectLine} />
            )}
            {activeTab === 'suggestions' && (
              <SuggestionsTab 
                suggestions={analysisResult?.suggestions} 
                currentCode={code}
                analyzedCode={analyzedCode}
                onSelectLine={handleSelectLine} 
                onPreviewFix={handleOpenPreview} 
              />
            )}
            {activeTab === 'report' && (
              <ReportTab analysisResult={analysisResult} onAnalyze={() => handleAnalyze()} onClear={handleClear} />
            )}
            {activeTab === 'docs' && (
              <DocumentationTab />
            )}
          </div>
        </div>
      </div>

      {/* FIX PREVIEW MODAL */}
      <FixPreviewModal
        isOpen={Boolean(previewSuggestion)}
        suggestion={previewSuggestion}
        currentCode={code}
        codeSnapshot={codeSnapshot}
        onClose={handleClosePreview}
        onConfirm={handleConfirmFix}
      />
    </div>
  );
}
