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
        {/* IMPLEMENTED FEATURES (PHASES 3A–3E) */}
        <div className="card-item" style={{ borderTop: '4px solid var(--status-safe)' }}>
          <div style={{ display: 'flex', alignItems: 'center', marginBottom: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <CheckCircle size={18} color="var(--status-safe)" />
              <h4 style={{ fontSize: '14px', fontWeight: 700, color: 'var(--status-safe)' }}>IMPLEMENTED FEATURES (PHASES 3A–3E)</h4>
            </div>
          </div>
          <ul style={{ fontSize: '12px', color: 'var(--text-secondary)', paddingLeft: '18px', lineHeight: '1.8' }}>
            <li><strong>Preprocessing & Lexing:</strong> Strips single/multi-line comments while preserving line mappings; tokenizes keywords, identifiers, constants, strings, operators, and separators.</li>
            <li><strong>Syntax Parsing & AST:</strong> Recursive descent parser for the supported C subset; dynamic AST tree visualization with node-to-code navigation.</li>
            <li><strong>Symbol Table & Semantics:</strong> Scoped variable registry (Global, Function, Block); checks for undeclared identifiers and variable redeclarations.</li>
            <li><strong>Memory Safety Analysis:</strong> Provenance tracking for <code>malloc</code>, <code>calloc</code>, <code>realloc</code>, and <code>free</code>; classifies definite vs. possible leaks; detects invalid frees (stack, global, string literal, interior pointers), use-after-free, and path-sensitive double-frees.</li>
            <li><strong>Interprocedural Summaries:</strong> Function-level summaries tracking heap memory escapes via return, parameter deallocation, and alias propagation.</li>
            <li><strong>Multi-Hop Pointer Aliasing:</strong> Tracks ownership propagation through pointer assignments and multi-hop alias chains.</li>
            <li><strong>Duplicate Code Detection:</strong> Normalized token clone detector identifying Type 1 (exact) and Type 2 (structural/renamed) duplicates with boilerplate filtering.</li>
            <li><strong>Complexity Metrics:</strong> McCabe Cyclomatic Complexity with logical operator decision points, statement counting, and peak nesting depth.</li>
            <li><strong>Safe-Fix & Stale-Preview Engine:</strong> Conservative automated fixes for semicolons and local unescaped leaks with snapshot drift detection and invalidation protection.</li>
          </ul>
        </div>

        {/* ARCHITECTURAL SCOPE & LIMITATIONS */}
        <div className="card-item" style={{ borderTop: '4px solid var(--status-info)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
            <Clock size={18} color="var(--status-info)" />
            <h4 style={{ fontSize: '14px', fontWeight: 700, color: 'var(--status-info)' }}>ARCHITECTURAL SCOPE & LIMITATIONS</h4>
          </div>
          <ul style={{ fontSize: '12px', color: 'var(--text-secondary)', paddingLeft: '18px', lineHeight: '1.8' }}>
            <li><strong>Supported C Grammar:</strong> Tailored for core imperative C constructs (primitive types, 1D pointers, conditionals, loops, functions). Does not parse full ISO C11/C17 grammars (unions, bitfields, function pointers, variable-length arrays).</li>
            <li><strong>Field-Insensitive Tracking:</strong> Heap allocations assigned to struct members (e.g. <code>node-&gt;data</code>) are not tracked with field sensitivity.</li>
            <li><strong>Single Translation Unit:</strong> Analyzes a single source file without multi-file linker or external header library expansion.</li>
            <li><strong>Bounded Loop Simulation:</strong> Loops are unrolled up to 2 iterations to capture loop-carried double frees and immediate overwrite leaks; unbounded loop invariants are not solved.</li>
            <li><strong>Conservative Fix Policy:</strong> Automatic fixes are restricted to deterministic syntax and local leak patterns. Semantic conflicts and multi-branch memory anomalies require manual review by design.</li>
          </ul>
        </div>
      </div>

      <div className="card-item" style={{ background: 'var(--bg-primary)' }}>
        <h4 style={{ fontSize: '13px', fontWeight: 600, marginBottom: '6px' }}>Static Analysis Methodology</h4>
        <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
          CodeGuard combines compiler front-end techniques (lexing, parsing, symbol tables) with deterministic path-sensitive abstract interpretation to identify common C programming hazards without running code in a sandbox.
        </p>
      </div>
    </div>
  );
}
