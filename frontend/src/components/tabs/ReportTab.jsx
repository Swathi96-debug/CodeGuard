import React from 'react';
import { FileText, Download, Copy, RefreshCw, Trash2, CheckCircle2, AlertTriangle } from 'lucide-react';

export default function ReportTab({ analysisResult, onAnalyze, onClear }) {
  if (!analysisResult) {
    return (
      <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
        No report generated yet. Click <strong>Analyze</strong> to generate report.
      </div>
    );
  }

  const { statistics, tokens, syntax_issues, symbol_table, semantic_issues, memory_analysis, duplication, suggestions, complexity } = analysisResult;

  const handleDownloadTxt = () => {
    const textContent = `=====================================================
CODEGUARD - C CODE ANALYSIS REPORT
=====================================================
Status: ${statistics.overall_status}
Lines of Code: ${statistics.lines_of_code}
Tokens Generated: ${statistics.tokens_count}
Syntax Errors: ${statistics.syntax_errors}
Semantic Errors: ${statistics.semantic_errors}
Memory Issues: ${statistics.memory_issues}
Duplicate Blocks: ${statistics.duplicate_blocks}
Symbol Table Count: ${statistics.variables_count}
Peak Cyclomatic Complexity: ${statistics.cyclomatic_complexity || 1} (${statistics.complexity_rating || 'LOW'})

-----------------------------------------------------
1. TOKENS SUMMARY
-----------------------------------------------------
Total Tokens: ${tokens?.length || 0}

-----------------------------------------------------
2. SYNTAX ANALYSIS
-----------------------------------------------------
${syntax_issues?.length === 0 ? "No syntax errors found." : syntax_issues.map(s => `Line ${s.line}:${s.column} - ${s.message} (${s.suggestion})`).join('\n')}

-----------------------------------------------------
3. SEMANTIC ANALYSIS
-----------------------------------------------------
${semantic_issues?.length === 0 ? "No semantic errors found." : semantic_issues.map(s => `Line ${s.line} - ${s.message}`).join('\n')}

-----------------------------------------------------
4. MEMORY ANALYSIS
-----------------------------------------------------
${memory_analysis?.length === 0 ? "No heap allocations found." : memory_analysis.map(m => `Pointer '${m.pointer}' (${m.allocation_function} Line ${m.allocation_line}) -> Status: ${m.status}`).join('\n')}

-----------------------------------------------------
5. DUPLICATION ANALYSIS
-----------------------------------------------------
${duplication?.length === 0 ? "No duplication found." : duplication.map(d => `Lines ${d.block_a_lines[0]} & ${d.block_b_lines[0]} -> ${d.similarity_percentage}% similarity`).join('\n')}

-----------------------------------------------------
6. COMPLEXITY METRICS
-----------------------------------------------------
${complexity?.length ? complexity.map(c => `Function '${c.name}' (Line ${c.line}): Cyclomatic Complexity = ${c.cyclomatic_complexity} (${c.rating}), Statements = ${c.statement_count}, Max Nesting = ${c.max_nesting_depth}`).join('\n') : "No functions analyzed."}
`;

    const blob = new Blob([textContent], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'codeguard_analysis_report.txt';
    link.click();
  };

  const handleDownloadJson = () => {
    const jsonStr = JSON.stringify(analysisResult, null, 2);
    const blob = new Blob([jsonStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'codeguard_analysis_report.json';
    link.click();
  };

  const handleCopySummary = () => {
    const summary = `CodeGuard Analysis Result:
Status: ${statistics.overall_status}
LOC: ${statistics.lines_of_code} | Tokens: ${statistics.tokens_count}
Errors: Syntax (${statistics.syntax_errors}), Semantic (${statistics.semantic_errors}), Memory (${statistics.memory_issues})
Duplicate Blocks: ${statistics.duplicate_blocks}
Peak Complexity: CC ${statistics.cyclomatic_complexity || 1} (${statistics.complexity_rating || 'LOW'})`;
    navigator.clipboard.writeText(summary);
    alert('Analysis summary copied to clipboard!');
  };

  return (
    <div>
      <div className="tab-toolbar" style={{ marginBottom: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <FileText size={18} color="var(--accent-blue)" />
          <h3 style={{ fontSize: '14px', fontWeight: 600 }}>Compiler Analysis Summary Report</h3>
        </div>
        <div>
          <span className={`badge badge-${statistics.overall_status === 'CLEAN' ? 'safe' : statistics.overall_status === 'NEEDS ATTENTION' ? 'warning' : 'error'}`}>
            {statistics.overall_status}
          </span>
        </div>
      </div>

      <div className="stats-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))' }}>
        <div className="stat-box">
          <div className="stat-box-num">{statistics.lines_of_code}</div>
          <div className="stat-box-label">Lines of Code</div>
        </div>
        <div className="stat-box">
          <div className="stat-box-num">{statistics.tokens_count}</div>
          <div className="stat-box-label">Tokens</div>
        </div>
        <div className="stat-box">
          <div className="stat-box-num">{statistics.syntax_errors}</div>
          <div className="stat-box-label">Syntax Errors</div>
        </div>
        <div className="stat-box">
          <div className="stat-box-num">{statistics.semantic_errors}</div>
          <div className="stat-box-label">Semantic Errors</div>
        </div>
        <div className="stat-box">
          <div className="stat-box-num">{statistics.memory_issues}</div>
          <div className="stat-box-label">Memory Issues</div>
        </div>
        <div className="stat-box">
          <div className="stat-box-num">{statistics.duplicate_blocks}</div>
          <div className="stat-box-label">Duplicate Blocks</div>
        </div>
        <div className="stat-box">
          <div className="stat-box-num">{statistics.cyclomatic_complexity || 1}</div>
          <div className="stat-box-label">Cyclomatic CC ({statistics.complexity_rating || 'LOW'})</div>
        </div>
      </div>

      <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', margin: '20px 0' }}>
        <button className="btn-action btn-primary" onClick={handleDownloadTxt}>
          <Download size={14} />
          Download TXT
        </button>
        <button className="btn-action" onClick={handleDownloadJson}>
          <Download size={14} />
          Download JSON
        </button>
        <button className="btn-action" onClick={handleCopySummary}>
          <Copy size={14} />
          Copy Summary
        </button>
        <button className="btn-action" onClick={onAnalyze}>
          <RefreshCw size={14} />
          Re-Analyze
        </button>
        <button className="btn-action" onClick={onClear}>
          <Trash2 size={14} />
          Clear
        </button>
      </div>

      {complexity && complexity.length > 0 && (
        <div className="card-item" style={{ marginBottom: '16px' }}>
          <h4 style={{ fontSize: '13px', fontWeight: 600, marginBottom: '10px' }}>Function Complexity Breakdown</h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {complexity.map((c, idx) => (
              <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 12px', background: 'var(--bg-secondary)', borderRadius: '6px' }}>
                <div>
                  <strong style={{ fontSize: '13px' }}>{c.name}()</strong>
                  <span style={{ fontSize: '11px', color: 'var(--text-muted)', marginLeft: '6px' }}>Line {c.line}</span>
                </div>
                <div style={{ display: 'flex', gap: '14px', alignItems: 'center', fontSize: '12px' }}>
                  <span>Cyclomatic Complexity: <strong>{c.cyclomatic_complexity}</strong></span>
                  <span>Statements: <strong>{c.statement_count}</strong></span>
                  <span>Max Nesting: <strong>{c.max_nesting_depth}</strong></span>
                  <span className={`badge badge-${c.rating === 'LOW' ? 'safe' : c.rating === 'MODERATE' ? 'warning' : 'error'}`}>{c.rating} RISK</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="card-item">
        <h4 style={{ fontSize: '13px', fontWeight: 600, marginBottom: '8px' }}>Pipeline Audit Checklist</h4>
        <ul style={{ fontSize: '12px', color: 'var(--text-secondary)', paddingLeft: '20px', lineHeight: '1.8' }}>
          <li>Preprocessor: Stripped comments & preserved line metadata.</li>
          <li>Lexical Analyzer: Tokenized {tokens?.length || 0} valid C lexemes.</li>
          <li>Parser: Constructed AST & checked recursive descent grammar.</li>
          <li>Symbol Table: Registered {symbol_table?.length || 0} variable declarations.</li>
          <li>Memory Analyzer: Inspected heap memory lifecycle ({memory_analysis?.length || 0} pointers tracked).</li>
          <li>Duplication Engine: Scanned normalized token similarity.</li>
          <li>Complexity Metrics: Calculated cyclomatic complexity and nesting depth.</li>
        </ul>
      </div>
    </div>
  );
}
