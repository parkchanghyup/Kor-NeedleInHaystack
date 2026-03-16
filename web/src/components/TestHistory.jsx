import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Clock, Trash2, Eye, RefreshCw, ChevronLeft,
  CheckSquare, XSquare, Target, Zap, Layers,
  AlertTriangle, Database
} from 'lucide-react';

// 시간 포맷 헬퍼
function formatTimestamp(isoStr) {
  if (!isoStr) return '-';
  try {
    const d = new Date(isoStr);
    const pad = (n) => String(n).padStart(2, '0');
    return `${d.getFullYear()}.${pad(d.getMonth() + 1)}.${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
  } catch {
    return isoStr;
  }
}

// 정확도에 따른 색상 (라이트 테마용)
function getAccuracyColor(accuracy) {
  if (accuracy >= 80) return '#059669';
  if (accuracy >= 50) return '#D97706';
  return '#DC2626';
}

// Provider 표시명
function providerLabel(provider) {
  const map = { openai: 'OpenAI', anthropic: 'Anthropic', gemini: 'Gemini', openrouter: 'OpenRouter', vllm: 'vLLM' };
  return map[provider] || provider;
}

export default function TestHistory() {
  const [historyList, setHistoryList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedDetail, setSelectedDetail] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState(null);

  const fetchHistory = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`${import.meta.env.VITE_API_BASE || ''}/api/test/history`);
      const data = await res.json();
      setHistoryList(data.history || []);
    } catch (err) {
      console.error('이력 로드 실패:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchHistory();
  }, [fetchHistory]);

  const viewDetail = async (id) => {
    setDetailLoading(true);
    try {
      const res = await fetch(`${import.meta.env.VITE_API_BASE || ''}/api/test/history/${id}`);
      const data = await res.json();
      setSelectedDetail(data);
    } catch (err) {
      console.error('상세 조회 실패:', err);
    } finally {
      setDetailLoading(false);
    }
  };

  const deleteEntry = async (id) => {
    try {
      await fetch(`${import.meta.env.VITE_API_BASE || ''}/api/test/history/${id}`, { method: 'DELETE' });
      setDeleteConfirm(null);
      fetchHistory();
      if (selectedDetail?.id === id) setSelectedDetail(null);
    } catch (err) {
      console.error('삭제 실패:', err);
    }
  };

  if (selectedDetail) {
    return <DetailView detail={selectedDetail} onBack={() => setSelectedDetail(null)} loading={detailLoading} />;
  }

  return (
    <div className="glass-panel" style={{ padding: '2rem', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* 헤더 */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--border-glass)', paddingBottom: '1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <Database size={22} color="var(--accent-primary)" />
          <h2 className="mono" style={{ fontSize: '1.2rem', margin: 0, color: 'var(--text-main)', letterSpacing: '0.05em' }}>
            TEST HISTORY
          </h2>
          <span className="title-badge" style={{ margin: 0 }}>{historyList.length} RECORDS</span>
        </div>
        <motion.button
          onClick={fetchHistory}
          className="btn-icon"
          whileHover={{ rotate: 180 }}
          whileTap={{ scale: 0.9 }}
          transition={{ duration: 0.4 }}
          title="새로고침"
        >
          <RefreshCw size={18} />
        </motion.button>
      </div>

      {loading && (
        <div style={{ display: 'flex', justifyContent: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
          <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 1.5, ease: 'linear' }}>
            <RefreshCw size={24} />
          </motion.div>
        </div>
      )}

      {!loading && historyList.length === 0 && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          style={{
            display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
            padding: '4rem 2rem', color: 'var(--text-muted)', textAlign: 'center'
          }}
        >
          <Layers size={48} strokeWidth={1} style={{ marginBottom: '1rem', opacity: 0.4 }} />
          <p className="mono" style={{ fontSize: '0.9rem' }}>NO TEST RECORDS FOUND</p>
          <p style={{ fontSize: '0.85rem', marginTop: '0.5rem', opacity: 0.6 }}>테스트를 실행하면 이력이 자동으로 저장됩니다.</p>
        </motion.div>
      )}

      {!loading && historyList.length > 0 && (
        <div className="history-list">
          <AnimatePresence>
            {historyList.map((item, idx) => (
              <motion.div
                key={item.id}
                className="history-card"
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, x: -30 }}
                transition={{ delay: idx * 0.04, duration: 0.3 }}
              >
                <div className="history-card__accent" style={{ background: getAccuracyColor(item.accuracy) }} />
                <div className="history-card__body">
                  <div className="history-card__top">
                    <div className="history-card__model">
                      <span className="mono" style={{ color: 'var(--text-main)', fontSize: '1rem', fontWeight: 700 }}>
                        {item.model_name}
                      </span>
                      <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.3rem', flexWrap: 'wrap' }}>
                        <span className="history-tag">{providerLabel(item.provider)}</span>
                        {item.multi_needle && <span className="history-tag history-tag--accent">Multi-Needle</span>}
                      </div>
                    </div>
                    <div className="history-card__stats">
                      <div className="history-stat">
                        <span className="history-stat__value" style={{ color: getAccuracyColor(item.accuracy) }}>
                          {item.accuracy}%
                        </span>
                        <span className="history-stat__label">정확도</span>
                      </div>
                      <div className="history-stat">
                        <span className="history-stat__value">{item.total_tests}</span>
                        <span className="history-stat__label">테스트</span>
                      </div>
                      <div className="history-stat">
                        <span className="history-stat__value">{item.time_elapsed.toFixed(1)}s</span>
                        <span className="history-stat__label">소요시간</span>
                      </div>
                    </div>
                  </div>
                  <div className="history-card__bottom">
                    <span className="mono" style={{ color: 'var(--text-muted)', fontSize: '0.78rem' }}>
                      <Clock size={12} style={{ verticalAlign: 'middle', marginRight: '0.3rem' }} />
                      {formatTimestamp(item.timestamp)}
                    </span>
                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                      <motion.button
                        className="btn-icon btn-icon--sm"
                        onClick={() => viewDetail(item.id)}
                        whileHover={{ scale: 1.1 }}
                        whileTap={{ scale: 0.95 }}
                        title="상세 보기"
                      >
                        <Eye size={15} />
                      </motion.button>
                      {deleteConfirm === item.id ? (
                        <motion.div
                          initial={{ opacity: 0, scale: 0.9 }}
                          animate={{ opacity: 1, scale: 1 }}
                          style={{ display: 'flex', gap: '0.3rem', alignItems: 'center' }}
                        >
                          <motion.button className="btn-icon btn-icon--sm btn-icon--danger" onClick={() => deleteEntry(item.id)} whileTap={{ scale: 0.9 }} title="삭제 확인">
                            <CheckSquare size={14} />
                          </motion.button>
                          <motion.button className="btn-icon btn-icon--sm" onClick={() => setDeleteConfirm(null)} whileTap={{ scale: 0.9 }} title="취소">
                            <XSquare size={14} />
                          </motion.button>
                        </motion.div>
                      ) : (
                        <motion.button className="btn-icon btn-icon--sm" onClick={() => setDeleteConfirm(item.id)} whileHover={{ scale: 1.1 }} whileTap={{ scale: 0.95 }} title="삭제">
                          <Trash2 size={15} />
                        </motion.button>
                      )}
                    </div>
                  </div>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      )}
    </div>
  );
}


function DetailView({ detail, onBack, loading }) {
  if (loading || !detail) {
    return (
      <div className="glass-panel" style={{ padding: '3rem', display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '400px' }}>
        <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 1.5, ease: 'linear' }}>
          <RefreshCw size={32} color="var(--accent-primary)" />
        </motion.div>
      </div>
    );
  }

  const { config, results, time_elapsed, timestamp } = detail;
  const dataArray = results || [];
  const totalTests = dataArray.length;
  const perfectScores = dataArray.filter(r => r.score >= 10).length;
  const accuracy = totalTests > 0 ? Math.round((perfectScores / totalTests) * 100) : 0;

  return (
    <motion.div
      className="glass-panel"
      style={{ padding: '2rem', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}
      initial={{ opacity: 0, x: 30 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.35 }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--border-glass)', paddingBottom: '1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <motion.button className="btn-icon" onClick={onBack} whileHover={{ x: -3 }} whileTap={{ scale: 0.9 }}>
            <ChevronLeft size={22} />
          </motion.button>
          <div>
            <h2 className="mono" style={{ fontSize: '1.2rem', color: 'var(--text-main)', margin: 0 }}>{config?.model_name}</h2>
            <span className="mono" style={{ color: 'var(--text-muted)', fontSize: '0.78rem' }}>
              {formatTimestamp(timestamp)} · {providerLabel(config?.provider)}
            </span>
          </div>
        </div>
        <span className="title-badge" style={{ margin: 0 }}>
          {config?.multi_needle ? 'MULTI-NEEDLE' : 'SINGLE-NEEDLE'}
        </span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '0.75rem' }}>
        <ConfigCard label="EVALUATOR" value={providerLabel(config?.evaluator)} sublabel={config?.evaluator_model_name} />
        <ConfigCard label="CONTEXT RANGE" value={`${config?.context_lengths_min} - ${config?.context_lengths_max}`} />
        <ConfigCard label="INTERVALS" value={`${config?.context_lengths_num_intervals} × ${config?.document_depth_percent_intervals}`} />
        <ConfigCard label="DEPTH RANGE" value={`${config?.document_depth_percent_min}% - ${config?.document_depth_percent_max}%`} />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem' }}>
        <motion.div className="glass-panel" style={{ padding: '1.2rem', background: '#fff', borderLeft: '4px solid var(--accent-primary)' }}
          initial={{ y: 15, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: 'var(--text-muted)' }}>
            <Clock size={14} /> <span className="mono" style={{ fontSize: '0.75rem' }}>소요 시간</span>
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: 700, color: 'var(--text-main)', marginTop: '0.3rem' }}>
            {time_elapsed.toFixed(1)}<span style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>s</span>
          </div>
        </motion.div>

        <motion.div className="glass-panel" style={{ padding: '1.2rem', background: '#fff', borderLeft: '4px solid var(--accent-primary)' }}
          initial={{ y: 15, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.15 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: 'var(--text-muted)' }}>
            <Target size={14} /> <span className="mono" style={{ fontSize: '0.75rem' }}>테스트 수</span>
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: 700, color: 'var(--text-main)', marginTop: '0.3rem' }}>
            {totalTests}<span style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}> runs</span>
          </div>
        </motion.div>

        <motion.div className="glass-panel" style={{ padding: '1.2rem', background: '#fff', borderLeft: `4px solid ${getAccuracyColor(accuracy)}` }}
          initial={{ y: 15, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.2 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: 'var(--text-muted)' }}>
            <CheckSquare size={14} /> <span className="mono" style={{ fontSize: '0.75rem' }}>정확도</span>
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: 700, color: getAccuracyColor(accuracy), marginTop: '0.3rem' }}>
            {accuracy}<span style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>%</span>
          </div>
        </motion.div>
      </div>

      <div>
        <h3 className="mono" style={{ fontSize: '0.95rem', marginBottom: '0.75rem', borderBottom: '1px solid var(--border-glass)', paddingBottom: '0.5rem' }}>
          RAW DATA OUTPUT
        </h3>
        <div style={{
          background: 'rgba(0,0,0,0.02)',
          borderRadius: 'var(--radius-md)',
          padding: '0.75rem',
          maxHeight: '400px',
          overflowY: 'auto',
          border: '1px solid var(--border-glass)',
          fontFamily: 'Space Mono, monospace',
          fontSize: '0.82rem'
        }}>
          {dataArray.map((r, idx) => (
            <motion.div
              key={idx}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.1 + (idx * 0.03) }}
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                padding: '0.65rem 0.5rem',
                borderBottom: idx === dataArray.length - 1 ? 'none' : '1px solid rgba(0,0,0,0.06)'
              }}
            >
              <div style={{ display: 'flex', gap: '1rem', color: 'var(--text-muted)' }}>
                <span style={{ width: '30px' }}>#{idx + 1}</span>
                <span style={{ width: '100px', color: 'var(--text-main)' }}>Len: {r.context_length}</span>
                <span style={{ width: '80px', color: 'var(--text-main)' }}>Dep: {r.depth_percent}%</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span style={{ width: '60px', textAlign: 'right', color: r.score >= 10 ? '#059669' : (r.score >= 5 ? '#D97706' : '#DC2626') }}>
                  Score: {r.score}
                </span>
                {r.score >= 10 ? <CheckSquare size={14} color="#059669" /> : <XSquare size={14} color="#DC2626" />}
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </motion.div>
  );
}


function ConfigCard({ label, value, sublabel }) {
  return (
    <div style={{
      background: 'rgba(0,0,0,0.02)',
      borderRadius: 'var(--radius-md)',
      padding: '0.75rem',
      border: '1px solid var(--border-glass)',
    }}>
      <span className="mono" style={{ fontSize: '0.65rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
        {label}
      </span>
      <div style={{ color: 'var(--text-main)', fontSize: '0.85rem', fontWeight: 600, marginTop: '0.2rem' }}>
        {value}
      </div>
      {sublabel && (
        <div style={{ color: 'var(--text-muted)', fontSize: '0.72rem', marginTop: '0.15rem' }}>
          {sublabel}
        </div>
      )}
    </div>
  );
}
