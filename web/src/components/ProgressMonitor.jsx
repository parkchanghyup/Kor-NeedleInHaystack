import { useEffect } from 'react';
import { motion } from 'framer-motion';
import { Loader2, CheckCircle2 } from 'lucide-react';

export default function ProgressMonitor({ taskId, status, setStatus, setMessage, setResults, message }) {

  useEffect(() => {
    let intervalId;

    const checkStatus = async () => {
      try {
        // 폴링 엔드포인트 호출
        const res = await fetch(`${import.meta.env.VITE_API_BASE || ''}/api/test/status/${taskId}`);
        if (!res.ok) throw new Error('Network error');

        const data = await res.json();
        setStatus(data.status);
        setMessage(data.message);

        // 작업이 완료되었거나 실패한 경우 폴링 중단 및 결과 fetch 시도
        if (data.status === 'completed' || data.status === 'failed') {
          clearInterval(intervalId);

          if (data.status === 'completed') {
            fetchResults();
          }
        }
      } catch (error) {
        console.error("Status Check Error:", error);
      }
    };

    const fetchResults = async () => {
      try {
        const res = await fetch(`${import.meta.env.VITE_API_BASE || ''}/api/test/results/${taskId}`);
        const data = await res.json();
        if (data.results) {
          setResults(data);
        }
      } catch (error) {
        console.error("Result Fetch Error:", error);
      }
    }

    // 2초 간격 폴링
    if (status === 'queued' || status === 'running') {
      intervalId = setInterval(checkStatus, 2000);
      checkStatus(); // 즉시 한 번 실행
    }

    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [taskId, status, setStatus, setMessage, setResults]);

  return (
    <div className="glass-panel" style={{ padding: '3rem', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '400px', height: '100%', position: 'relative', overflow: 'hidden' }}>

      {/* Background Pulse Effect */}
      <motion.div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          background: 'radial-gradient(circle, rgba(0, 240, 181, 0.05) 0%, transparent 70%)',
          zIndex: 0
        }}
        animate={{ scale: [1, 1.2, 1], opacity: [0.5, 1, 0.5] }}
        transition={{ repeat: Infinity, duration: 4, ease: "easeInOut" }}
      />

      <div style={{ position: 'relative', zIndex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '2rem' }}>

        <div style={{ position: 'relative', width: '80px', height: '80px', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
          {status === 'running' || status === 'queued' ? (
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ repeat: Infinity, duration: 2, ease: "linear" }}
            >
              <Loader2 size={48} color="var(--accent-primary)" />
            </motion.div>
          ) : status === 'completed' ? (
            <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ type: "spring" }}>
              <CheckCircle2 size={56} color="var(--accent-primary)" />
            </motion.div>
          ) : null}

          {/* Outer Rotating Ring */}
          {(status === 'running' || status === 'queued') && (
            <motion.svg
              width="100" height="100"
              viewBox="0 0 100 100"
              style={{ position: 'absolute', top: '-10px', left: '-10px' }}
              animate={{ rotate: -360 }}
              transition={{ repeat: Infinity, duration: 8, ease: "linear" }}
            >
              <circle cx="50" cy="50" r="45" fill="none" stroke="var(--border-glass)" strokeWidth="1" strokeDasharray="4 8" />
            </motion.svg>
          )}
        </div>

        <div style={{ textAlign: 'center' }}>
          <h2 className="mono" style={{ fontSize: '1.5rem', marginBottom: '0.5rem', letterSpacing: '0.1em' }}>
            STATUS: <span style={{ color: status === 'completed' ? 'var(--accent-primary)' : '#fff', textTransform: 'uppercase' }}>{status}</span>
          </h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '1.1rem' }}>
            {message || "Initializing inference engine..."}
          </p>
        </div>

        <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
          <span className="title-badge" style={{ margin: 0 }}>TASK ID: {taskId.split('-')[0]}...</span>
        </div>
      </div>
    </div>
  );
}
