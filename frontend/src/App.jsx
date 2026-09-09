import React, { useState } from 'react';
import WelcomePage from './components/WelcomePage';
import CompilerInterface from './components/CompilerInterface';

export default function App() {
  const [page, setPage] = useState('welcome'); // 'welcome' | 'interface'
  const [initialCode, setInitialCode] = useState('');
  const [theme, setTheme] = useState('dark');

  const toggleTheme = () => {
    setTheme(prev => (prev === 'dark' ? 'light' : 'dark'));
  };

  const handleSelectOption = (code) => {
    setInitialCode(code);
    setPage('interface');
  };

  return (
    <div data-theme={theme} style={{ minHeight: '100vh', background: 'var(--bg-primary)' }}>
      {page === 'welcome' ? (
        <WelcomePage 
          onSelectOption={handleSelectOption} 
          theme={theme} 
          toggleTheme={toggleTheme} 
        />
      ) : (
        <CompilerInterface 
          initialCode={initialCode} 
          onBackToWelcome={() => setPage('welcome')} 
          theme={theme} 
          toggleTheme={toggleTheme} 
        />
      )}
    </div>
  );
}
