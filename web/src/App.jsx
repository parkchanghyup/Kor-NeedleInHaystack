import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Activity, FileText, Clock, Play } from 'lucide-react';
import TestConfigForm from './components/TestConfigForm';
import ProgressMonitor from './components/ProgressMonitor';
import ResultDashboard from './components/ResultDashboard';
import TestHistory from './components/TestHistory';

function App() {
  const [activeTab, setActiveTab] = useState('test'); // 'test' | 'history'
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
        setTaskMessage(
          data.needle_count > 1
            ? `총 ${data.total_tests}개 조합을 검사합니다. 문서마다 ${data.needle_count}개의 needle이 함께 삽입됩니다.`
            : `총 ${data.total_tests}개 조합을 검사합니다.`
        );
      }
    } catch (error) {
      console.error('API Error:', error);
      setTaskStatus('failed');
      setTaskMessage('백엔드 서버에 연결하지 못했습니다.');
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
          <p className="header-copy">긴 문서 속 숨겨진 정보를 모델이 얼마나 잘 찾아내는지 확인하는 Needle In A Haystack 테스트 도구</p>
        </div>

        {/* 탭 네비게이션 */}
        <nav className="header-nav">
          <motion.button
            className={`nav-tab ${activeTab === 'test' ? 'nav-tab--active' : ''}`}
            onClick={() => setActiveTab('test')}
            whileTap={{ scale: 0.97 }}
          >
            <Play size={16} />
            <span>테스트</span>
          </motion.button>
          <motion.button
            className={`nav-tab ${activeTab === 'history' ? 'nav-tab--active' : ''}`}
            onClick={() => setActiveTab('history')}
            whileTap={{ scale: 0.97 }}
          >
            <Clock size={16} />
            <span>이력</span>
          </motion.button>
        </nav>
      </header>

      <AnimatePresence mode="wait">
        {activeTab === 'test' && (
          <motion.main
            key="test-view"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.25 }}
          >
            {/* 왼쪽 사이드바: 테스트 설정 폼 */}
            <motion.section
              className="glass-panel"
              style={{ padding: '2rem', height: 'fit-content' }}
              initial={{ opacity: 0, x: -50 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5 }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '2rem' }}>
                <FileText size={20} color="var(--accent-secondary)" />
                <h2 style={{ fontSize: '1.2rem', color: 'var(--text-main)' }}>테스트 설정</h2>
              </div>

              <TestConfigForm
                onStart={handleStartTest}
                isPending={taskStatus === 'queued' || taskStatus === 'running'}
              />
            </motion.section>

            {/* 오른쪽 컨텐츠: 모니터 & 결과 */}
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
                    <h3 style={{ color: 'var(--accent-secondary)', marginBottom: '1rem' }}>테스트 실행 실패</h3>
                    <p className="mono">{taskMessage}</p>
                    <button onClick={resetTest} className="btn-primary" style={{ marginTop: '2rem', background: 'rgba(0,0,0,0.06)', color: 'var(--text-main)' }}>
                      초기화 후 다시 시도
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
                      테스트 시작을 기다리고 있습니다.
                    </p>
                  </motion.div>
                )}
              </AnimatePresence>
            </section>
          </motion.main>
        )}

        {activeTab === 'history' && (
          <motion.div
            key="history-view"
            className="history-container"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.25 }}
          >
            <TestHistory />
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}

export default App;
