import React from 'react';
import { ArrowRight, Layers, Cpu, ShieldCheck } from 'lucide-react';

export default function OverviewTab({ statistics, onSwitchTab }) {
  const pipelineStages = [
    { id: 'tokens', name: 'Preprocessing & Lexical', desc: 'Comment stripping & tokenization', targetTab: 'tokens' },
    { id: 'syntax', name: 'Syntax Analysis', desc: 'Recursive descent parsing', targetTab: 'syntax' },
    { id: 'ast', name: 'AST Generation', desc: 'Abstract Syntax Tree tree node building', targetTab: 'ast' },
    { id: 'symbols', name: 'Symbol Table', desc: 'Scoping & variable tracking', targetTab: 'symbols' },
    { id: 'memory', name: 'Static Analysis', desc: 'Memory leak & duplication detection', targetTab: 'memory' },
    { id: 'report', name: 'Report Generation', desc: 'Audit summary & recommendations', targetTab: 'report' },
  ];

  return (
    <div>
      <div className="tab-toolbar" style={{ marginBottom: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Layers size={18} color="var(--accent-blue)" />
          <h3 style={{ fontSize: '14px', fontWeight: 600 }}>Compiler Pipeline Overview</h3>
        </div>
      </div>

      <div className="stats-grid">
        <div className="stat-box">
          <div className="stat-box-num">{statistics?.lines_of_code || 0}</div>
          <div className="stat-box-label">Lines of Code</div>
        </div>
        <div className="stat-box">
          <div className="stat-box-num">{statistics?.tokens_count || 0}</div>
          <div className="stat-box-label">Tokens</div>
        </div>
        <div className="stat-box">
          <div className="stat-box-num">{statistics?.syntax_errors || 0}</div>
          <div className="stat-box-label">Syntax Errors</div>
        </div>
        <div className="stat-box">
          <div className="stat-box-num">{statistics?.semantic_errors || 0}</div>
          <div className="stat-box-label">Semantic Errors</div>
        </div>
        <div className="stat-box">
          <div className="stat-box-num">{statistics?.memory_issues || 0}</div>
          <div className="stat-box-label">Memory Leaks</div>
        </div>
        <div className="stat-box">
          <div className="stat-box-num">{statistics?.duplicate_blocks || 0}</div>
          <div className="stat-box-label">Duplicate Blocks</div>
        </div>
      </div>

      <h4 style={{ fontSize: '13px', fontWeight: 600, margin: '20px 0 12px 0' }}>
        Interactive Compiler Pipeline Execution Flow
      </h4>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
        {pipelineStages.map((stage, idx) => (
          <div 
            key={stage.id} 
            className="card-item clickable"
            style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '14px 18px' }}
            onClick={() => onSwitchTab(stage.targetTab)}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div style={{ 
                width: '28px', height: '28px', borderRadius: '50%', background: 'var(--accent-blue-light)', 
                color: 'var(--accent-blue)', display: 'flex', alignItems: 'center', justifyContent: 'center', 
                fontSize: '12px', fontWeight: 700 
              }}>
                {idx + 1}
              </div>
              <div>
                <div style={{ fontSize: '13px', fontWeight: 600 }}>{stage.name}</div>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{stage.desc}</div>
              </div>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', color: 'var(--accent-blue)' }}>
              Inspect Phase <ArrowRight size={14} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
