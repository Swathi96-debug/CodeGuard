import React from 'react';
import { BookOpen, CheckCircle, Clock } from 'lucide-react';

export default function DocumentationTab() {
  return (
    <div>
      <div className="card-item" style={{ borderColor: 'var(--accent-blue)', marginBottom: '20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
          <BookOpen size={20} color="var(--accent-blue)" />
          <h3 style={{ fontSize: '15px', fontWeight: 700 }}>CodeGuard Technical Documentation & Scope Breakdown</h3>
        </div>
        <p style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
          CodeGuard is built as a CS Compiler Design demonstration tool. The pipeline highlights front-end compilation phases alongside targeted static security and memory analysis.
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '24px' }}>
        {/* CURRENT IMPLEMENTATION — 40% */}
        <div className="card-item" style={{ borderTop: '4px solid var(--status-safe)' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyBetween: 'space-between', marginBottom: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <CheckCircle size={18} color="var(--status-safe)" />
              <h4 style={{ fontSize: '14px', fontWeight: 700, color: 'var(--status-safe)' }}>CURRENT IMPLEMENTATION — 40%</h4>
            </div>
          </div>
          <ul style={{ fontSize: '12px', color: 'var(--text-secondary)', paddingLeft: '18px', lineHeight: '1.8' }}>
            <li><strong>Preprocessing:</strong> Single (<code>//</code>) and multi-line (<code>/* */</code>) comment removal while preserving line count.</li>
            <li><strong>Lexical Analysis:</strong> Hand-written scanner recognizing keywords, identifiers, numeric constants, strings, operators, and separators.</li>
            <li><strong>Syntax Parsing:</strong> Recursive descent parser enforcing supported C subset grammar and detecting syntax errors (missing semicolons, unmatched parens/braces).</li>
            <li><strong>AST Generation:</strong> Dynamic Abstract Syntax Tree construction with interactive node inspection.</li>
            <li><strong>Symbol Table:</strong> Multi-scope variable registry tracking global, function, and block declarations and redeclaration conflicts.</li>
            <li><strong>Semantic Analysis:</strong> Scope validation, undeclared variable detection, and simple type checking.</li>
            <li><strong>Memory Analysis:</strong> Static tracking of <code>malloc</code>, <code>calloc</code>, <code>realloc</code>, and <code>free</code> for leaks and double-frees.</li>
            <li><strong>Code Duplication:</strong> Normalized token structural similarity detector.</li>
          </ul>
        </div>

        {/* FUTURE SCOPE — 60% */}
        <div className="card-item" style={{ borderTop: '4px solid var(--status-info)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
            <Clock size={18} color="var(--status-info)" />
            <h4 style={{ fontSize: '14px', fontWeight: 700, color: 'var(--status-info)' }}>FUTURE SCOPE — 60%</h4>
          </div>
          <ul style={{ fontSize: '12px', color: 'var(--text-secondary)', paddingLeft: '18px', lineHeight: '1.8' }}>
            <li>Full ISO C11/C17 standard grammar parsing.</li>
            <li>Control-Flow Graph (CFG) & Data-Flow Analysis.</li>
            <li>Interprocedural pointer alias analysis across multiple files.</li>
            <li>Industrial AST-based clone detection (Rabin-Karp / PDG hashing).</li>
            <li>Automatic code refactoring & LLVM IR code generation.</li>
            <li>Path-sensitive symbolic execution for deep null-pointer dereference detection.</li>
          </ul>
        </div>
      </div>

      <div className="card-item" style={{ background: 'var(--bg-primary)' }}>
        <h4 style={{ fontSize: '13px', fontWeight: 600, marginBottom: '6px' }}>Technical Limitations Disclaimer</h4>
        <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
          This tool implements a <strong>Supported C Subset</strong> and <strong>Basic Static Memory Analysis</strong>. It is designed specifically for academic compiler design presentation and static safety analysis demonstration.
        </p>
      </div>
    </div>
  );
}
