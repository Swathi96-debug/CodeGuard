import React, { useRef, useEffect } from 'react';
import Editor from '@monaco-editor/react';

export default function CodeEditor({ code, onChange, activeLine, theme, analysisResult }) {
  const editorRef = useRef(null);
  const monacoRef = useRef(null);
  const decorationsRef = useRef([]);

  const handleEditorDidMount = (editor, monaco) => {
    editorRef.current = editor;
    monacoRef.current = monaco;

    // Enforce consistent LF line endings to prevent CRLF/LF discrepancies
    const model = editor.getModel();
    if (model) {
      model.setEOL(monaco.editor.EndOfLineSequence.LF);
    }

    updateMarkers(editor, monaco, analysisResult);
  };

  const updateMarkers = (editor, monaco, result) => {
    if (!editor || !monaco) return;
    const model = editor.getModel();
    if (!model) return;

    if (!result || !result.anomalies || result.anomalies.length === 0) {
      monaco.editor.setModelMarkers(model, 'codeguard', []);
      return;
    }

    const markers = result.anomalies.map((anom) => {
      const lineNum = Math.max(1, Math.min(model.getLineCount(), anom.line || 1));
      const colNum = Math.max(1, anom.column || 1);
      const lineLength = model.getLineLength(lineNum) || 20;

      let severity = monaco.MarkerSeverity.Info;
      if (anom.severity === 'error') {
        severity = monaco.MarkerSeverity.Error;
      } else if (anom.severity === 'warning') {
        severity = monaco.MarkerSeverity.Warning;
      }

      return {
        severity,
        startLineNumber: lineNum,
        startColumn: colNum,
        endLineNumber: lineNum,
        endColumn: Math.max(colNum + 1, lineLength + 1),
        message: `[${anom.issue_type}] ${anom.message}\n• Why it matters: ${anom.why_it_matters}\n• Fix: ${anom.suggestion}`,
        source: 'CodeGuard'
      };
    });

    monaco.editor.setModelMarkers(model, 'codeguard', markers);
  };

  // Sync Monaco diagnostic markers when analysisResult updates
  useEffect(() => {
    if (editorRef.current && monacoRef.current) {
      updateMarkers(editorRef.current, monacoRef.current, analysisResult);
    }
  }, [analysisResult]);

  // Jump to and highlight line when activeLine is triggered
  useEffect(() => {
    if (!editorRef.current || !activeLine) return;

    const editor = editorRef.current;
    const targetLine = typeof activeLine === 'object' && activeLine !== null ? activeLine.line : activeLine;
    if (!targetLine) return;

    // Scroll into view & focus cursor
    editor.revealLineInCenter(targetLine);
    editor.setPosition({ lineNumber: targetLine, column: 1 });
    editor.focus();

    // Apply active line highlight decoration with pulse animation
    const monaco = monacoRef.current || window.monaco;
    if (monaco) {
      decorationsRef.current = editor.deltaDecorations(decorationsRef.current, [
        {
          range: new monaco.Range(targetLine, 1, targetLine, 1),
          options: {
            isWholeLine: true,
            className: 'monaco-highlight-line',
            glyphMarginClassName: 'monaco-highlight-glyph'
          }
        }
      ]);
    }
  }, [activeLine]);

  return (
    <div style={{ width: '100%', height: '100%' }}>
      <style>{`
        .monaco-highlight-line {
          background-color: var(--highlight-line-bg) !important;
          border-left: 3px solid var(--status-warning) !important;
          animation: linePulse 1.2s ease-in-out;
        }
        .monaco-highlight-glyph {
          background-color: var(--status-warning) !important;
        }
        @keyframes linePulse {
          0% { background-color: rgba(245, 158, 11, 0.5); }
          50% { background-color: var(--highlight-line-bg); }
          100% { background-color: var(--highlight-line-bg); }
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
          renderLineHighlight: 'all',
          glyphMargin: true,
          editContext: false
        }}
      />
    </div>
  );
}
