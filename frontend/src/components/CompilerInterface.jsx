import React, { useState } from 'react';
import { 
  Play, Trash2, Upload, FileCode, Sun, Moon, ArrowLeft,
  Layers, Code2, AlertTriangle, FolderTree, Database, AlertCircle,
  Cpu, Copy, ShieldAlert, Lightbulb, FileText, BookOpen, Wand2
} from 'lucide-react';
import CodeEditor from './CodeEditor';
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

  const handleAnalyze = async () => {
    if (!code.trim()) {
      alert('Please enter or upload C source code before analyzing.');
      return;
    }

    setIsAnalyzing(true);

    // Progress stage simulation for user feedback
    for (let i = 0; i < stages.length; i++) {
      setProgressStage(stages[i]);
      await new Promise(resolve => setTimeout(resolve, 80));
    }

    try {
      const response = await fetch('http://127.0.0.1:8001/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code })
      });

      if (!response.ok) {
        throw new Error(`Server returned error status ${response.status}`);
      }

      const data = await response.json();
      setAnalysisResult(data);
    } catch (err) {
      alert(`Unable to connect to analysis server: ${err.message}. Please ensure the backend is running.`);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleClear = () => {
    setCode('');
    setAnalysisResult(null);
    setActiveLine(null);
  };

  const handleLoadSample = (e) => {
    const sampleId = e.target.value;
    if (!sampleId) return;
    const sample = SAMPLE_PROGRAMS.find(s => s.id === sampleId);
    if (sample) {
      setCode(sample.code);
      setAnalysisResult(null);
      setActiveLine(null);
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
      setActiveLine(null);
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

  const handleApplyFix = (sugg) => {
    if (!sugg.safe_fix) return;
    const lines = code.split('\n');
    if (0 <= sugg.line - 1 && sugg.line - 1 < lines.length) {
      if (sugg.category === 'SYNTAX' && sugg.message.includes('semicolon')) {
        lines[sugg.line - 1] = sugg.safe_fix;
      } else if (sugg.category === 'MEMORY' && sugg.message.includes('not freed')) {
        lines.splice(sugg.line, 0, `    ${sugg.safe_fix}`);
      } else if (sugg.category === 'SEMANTIC' && sugg.message.includes('Undeclared')) {
        lines.splice(sugg.line - 1, 0, `    ${sugg.safe_fix}`);
      }
      setCode(lines.join('\n'));
      alert(`Safe fix applied to line ${sugg.line}. Click 'Analyze' to refresh compiler state.`);
    }
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
          <button className="btn-action btn-primary" onClick={handleAnalyze}>
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
              <TokensTab tokens={analysisResult?.tokens} tokenStats={analysisResult?.token_stats} onSelectLine={setActiveLine} />
            )}
            {activeTab === 'syntax' && (
              <SyntaxTab syntaxIssues={analysisResult?.syntax_issues} onSelectLine={setActiveLine} />
            )}
            {activeTab === 'ast' && (
              <AstTab ast={analysisResult?.ast} onSelectLine={setActiveLine} />
            )}
            {activeTab === 'symbols' && (
              <SymbolTableTab symbolTable={analysisResult?.symbol_table} onSelectLine={setActiveLine} />
            )}
            {activeTab === 'semantic' && (
              <SemanticTab semanticIssues={analysisResult?.semantic_issues} onSelectLine={setActiveLine} />
            )}
            {activeTab === 'memory' && (
              <MemoryTab memoryAnalysis={analysisResult?.memory_analysis} onSelectLine={setActiveLine} />
            )}
            {activeTab === 'duplication' && (
              <DuplicationTab duplication={analysisResult?.duplication} onSelectLine={setActiveLine} />
            )}
            {activeTab === 'anomalies' && (
              <AnomaliesTab anomalies={analysisResult?.anomalies} onSelectLine={setActiveLine} />
            )}
            {activeTab === 'suggestions' && (
              <SuggestionsTab suggestions={analysisResult?.suggestions} onSelectLine={setActiveLine} onApplyFix={handleApplyFix} />
            )}
            {activeTab === 'report' && (
              <ReportTab analysisResult={analysisResult} onAnalyze={handleAnalyze} onClear={handleClear} />
            )}
            {activeTab === 'docs' && (
              <DocumentationTab />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
