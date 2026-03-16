import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Activity, Database, Zap, FileText } from 'lucide-react';
import TestConfigForm from './components/TestConfigForm';
import ProgressMonitor from './components/ProgressMonitor';
import ResultDashboard from './components/ResultDashboard';

function App() {
  const [taskId, setTaskId] = useState(null);
  const [taskStatus, setTaskStatus] = useState('idle'); // idle, queued, running, completed, failed
  const [taskMessage, setTaskMessage] = useState('');
  const [testResults, setTestResults] = useState(null);

  const handleStartTest = async (config) => {
    try {
      setTaskStatus('queued');
      const response = await fetch(`${import.meta.env.VITE_API_BASE || ''}/api/test/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
      });

      const data = await response.json();
      if (data.task_id) {
        setTaskId(data.task_id);
      }
    } catch (error) {
      console.error('API Error:', error);
      setTaskStatus('failed');
      setTaskMessage('Failed to connect to the backend server.');
    }
  };

  const resetTest = () => {
    setTaskId(null);
    setTaskStatus('idle');
    setTaskMessage('');
    setTestResults(null);
  };

  return (
    <>
      <header>
        <div>
          <h1 className="title-glow">N.I.H. Kor</h1>
          <span className="title-badge">Terminal v1.0</span>
        </div>
        <div style={{ display: 'flex', gap: '1rem', color: 'var(--text-muted)' }}>
          <Database size={20} />
          <Activity size={20} />
          <Zap size={20} color="var(--accent-primary)" />
        </div>
      </header>

      <main>
        {/* Left Sidebar: Config Form */}
        <motion.section
          className="glass-panel"
          style={{ padding: '2rem', height: 'fit-content' }}
          initial={{ opacity: 0, x: -50 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5 }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '2rem' }}>
            <FileText size={20} color="var(--accent-secondary)" />
            <h2 style={{ fontSize: '1.2rem', color: '#fff' }}>Test Parameters</h2>
          </div>

          <TestConfigForm
            onStart={handleStartTest}
            isPending={taskStatus === 'queued' || taskStatus === 'running'}
          />
        </motion.section>

        {/* Right Content: Monitor & Results */}
        <section style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          <AnimatePresence mode="wait">
            {taskId && taskStatus !== 'completed' && taskStatus !== 'failed' && (
              <motion.div
                key="monitor"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.95 }}
                transition={{ duration: 0.4 }}
              >
                <ProgressMonitor
                  taskId={taskId}
                  status={taskStatus}
                  setStatus={setTaskStatus}
                  setMessage={setTaskMessage}
                  setResults={setTestResults}
                  message={taskMessage}
                />
              </motion.div>
            )}

            {taskStatus === 'completed' && testResults && (
              <motion.div
                key="results"
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.5, type: 'spring' }}
              >
                <ResultDashboard results={testResults} onReset={resetTest} />
              </motion.div>
            )}

            {taskStatus === 'failed' && (
              <motion.div
                key="error"
                className="glass-panel"
                style={{ padding: '2rem', border: '1px solid var(--accent-secondary)' }}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
              >
                <h3 style={{ color: 'var(--accent-secondary)', marginBottom: '1rem' }}>Test Execution Failed</h3>
                <p className="mono">{taskMessage}</p>
                <button onClick={resetTest} className="btn-primary" style={{ marginTop: '2rem', background: '#333', color: '#fff' }}>
                  Reset & Try Again
                </button>
              </motion.div>
            )}

            {taskStatus === 'idle' && (
              <motion.div
                key="idle"
                className="glass-panel"
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  height: '100%',
                  minHeight: '400px',
                  opacity: 0.5
                }}
                initial={{ opacity: 0 }}
                animate={{ opacity: 0.4 }}
                exit={{ opacity: 0 }}
              >
                <Activity size={48} strokeWidth={1} style={{ marginBottom: '1rem', color: 'var(--text-muted)' }} />
                <p className="mono" style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                  AWAITING TEST INITIALIZATION...
                </p>
              </motion.div>
            )}
          </AnimatePresence>
        </section>
      </main>
    </>
  );
}

export default App;
