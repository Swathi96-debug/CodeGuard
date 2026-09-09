import React, { useRef, useEffect } from 'react';
import Editor from '@monaco-editor/react';

export default function CodeEditor({ code, onChange, activeLine, theme }) {
  const editorRef = useRef(null);
  const decorationsRef = useRef([]);

  const handleEditorDidMount = (editor, monaco) => {
    editorRef.current = editor;
  };

  useEffect(() => {
    if (!editorRef.current || !activeLine) return;

    // Reveal target line and scroll to center
    editorRef.current.revealLineInCenter(activeLine);

    // Apply active line highlight decoration
    const editor = editorRef.current;
    decorationsRef.current = editor.deltaDecorations(decorationsRef.current, [
      {
        range: new window.monaco.Range(activeLine, 1, activeLine, 1),
        options: {
          isWholeLine: true,
          className: 'monaco-highlight-line',
          glyphMarginClassName: 'monaco-highlight-glyph'
        }
      }
    ]);
  }, [activeLine]);

  return (
    <div style={{ width: '100%', height: '100%' }}>
      <style>{`
        .monaco-highlight-line {
          background-color: var(--highlight-line-bg) !important;
        }
        .monaco-highlight-glyph {
          background-color: var(--status-warning) !important;
        }
      `}</style>
      <Editor
        height="100%"
        defaultLanguage="c"
        theme={theme === 'dark' ? 'vs-dark' : 'light'}
        value={code}
        onChange={(val) => onChange(val || '')}
        onMount={handleEditorDidMount}
        options={{
          fontSize: 13,
          fontFamily: "'JetBrains Mono', Consolas, monospace",
          minimap: { enabled: false },
          lineNumbers: 'on',
          scrollBeyondLastLine: false,
          automaticLayout: true,
          tabSize: 4,
          insertSpaces: true,
          cursorBlinking: 'smooth',
          renderLineHighlight: 'all'
        }}
      />
    </div>
  );
}
