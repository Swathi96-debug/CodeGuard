import React, { useState } from 'react';
import { ChevronRight, ChevronDown, FolderTree, Code2 } from 'lucide-react';

function AstNodeView({ node, onSelectLine }) {
  const [expanded, setExpanded] = useState(true);

  if (!node || typeof node !== 'object') {
    return <span style={{ color: 'var(--text-muted)' }}>{String(node)}</span>;
  }

  const hasChildren = (node.statements && node.statements.length > 0) ||
                      (node.body && typeof node.body === 'object') ||
                      (node.initializer && typeof node.initializer === 'object') ||
                      (node.left && typeof node.left === 'object') ||
                      (node.right && typeof node.right === 'object') ||
                      (node.condition && typeof node.condition === 'object') ||
                      (node.then_branch && typeof node.then_branch === 'object') ||
                      (node.value && typeof node.value === 'object');

  const handleNodeClick = (e) => {
    e.stopPropagation();
    if (node.line) {
      onSelectLine(node.line);
    }
  };

  return (
    <div className="ast-node">
      <div 
        className="ast-node-header"
        onClick={handleNodeClick}
      >
        {hasChildren ? (
          <span onClick={(e) => { e.stopPropagation(); setExpanded(!expanded); }}>
            {expanded ? <ChevronDown size={14} color="var(--text-muted)" /> : <ChevronRight size={14} color="var(--text-muted)" />}
          </span>
        ) : (
          <span style={{ width: '14px' }}></span>
        )}
        
        <Code2 size={13} color="var(--accent-blue)" />
        <span className="ast-node-label">{node.label || node.type}</span>
        <span className="ast-node-type">[{node.type}]</span>
        {node.line && (
          <span style={{ fontSize: '10px', color: 'var(--text-muted)', marginLeft: 'auto' }}>
            Line {node.line}
          </span>
        )}
      </div>

      {expanded && hasChildren && (
        <div style={{ marginLeft: '12px' }}>
          {node.statements && node.statements.map((stmt, idx) => (
            <AstNodeView key={idx} node={stmt} onSelectLine={onSelectLine} />
          ))}

          {node.body && (
            <AstNodeView node={node.body} onSelectLine={onSelectLine} />
          )}

          {node.initializer && (
            <div style={{ marginLeft: '12px', marginTop: '2px' }}>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Initializer:</span>
              <AstNodeView node={node.initializer} onSelectLine={onSelectLine} />
            </div>
          )}

          {node.left && (
            <div style={{ marginLeft: '12px' }}>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Left:</span>
              <AstNodeView node={node.left} onSelectLine={onSelectLine} />
            </div>
          )}

          {node.right && (
            <div style={{ marginLeft: '12px' }}>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Right:</span>
              <AstNodeView node={node.right} onSelectLine={onSelectLine} />
            </div>
          )}

          {node.condition && (
            <div style={{ marginLeft: '12px' }}>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Condition:</span>
              <AstNodeView node={node.condition} onSelectLine={onSelectLine} />
            </div>
          )}

          {node.then_branch && (
            <div style={{ marginLeft: '12px' }}>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Then:</span>
              <AstNodeView node={node.then_branch} onSelectLine={onSelectLine} />
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function AstTab({ ast, onSelectLine }) {
  return (
    <div>
      <div className="tab-toolbar" style={{ marginBottom: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <FolderTree size={18} color="var(--accent-blue)" />
          <span style={{ fontSize: '13px', fontWeight: 600 }}>Abstract Syntax Tree (AST) Visualization</span>
        </div>
        <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
          Click any tree node to highlight its source line on the left.
        </span>
      </div>

      <div className="card-item" style={{ background: 'var(--bg-primary)', padding: '16px', overflowX: 'auto' }}>
        {ast ? (
          <div className="ast-tree">
            <AstNodeView node={ast} onSelectLine={onSelectLine} />
          </div>
        ) : (
          <div style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '20px' }}>
            No AST generated. Run analysis to construct AST.
          </div>
        )}
      </div>
    </div>
  );
}
