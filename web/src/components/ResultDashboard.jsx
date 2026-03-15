import { motion } from 'framer-motion';
import { RefreshCw, Clock, CheckSquare, XSquare, Target } from 'lucide-react';

export default function ResultDashboard({ results, onReset }) {
  if (!results || !results.results) return null;

  const { time_elapsed, results: dataArray } = results;
  const totalTests = dataArray.length;
  
  // 성공 여부 기준 단순 집계
  const perfectScores = dataArray.filter(r => r.score >= 10).length;
  const partialScores = dataArray.filter(r => r.score >= 5 && r.score < 10).length;
  const failedScores = totalTests - perfectScores - partialScores;

  return (
    <div className="glass-panel" style={{ padding: '2rem', display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--border-glass)', paddingBottom: '1rem' }}>
        <div>
          <h2 className="title-glow" style={{ fontSize: '1.5rem', margin: 0 }}>MISSION COMPLETE</h2>
          <span className="mono" style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>
            {dataArray[0]?.model || 'UNKNOWN_MODEL'}
          </span>
        </div>
        <button 
          onClick={onReset}
          className="btn-primary" 
          style={{ width: 'auto', padding: '0.5rem 1rem', marginTop: 0, background: 'rgba(255,255,255,0.1)', color: '#fff' }}
        >
          <RefreshCw size={16} /> NEW TEST
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem' }}>
        
        <motion.div 
          className="glass-panel" 
          style={{ padding: '1.5rem', background: 'rgba(0, 0, 0, 0.4)', borderLeft: '4px solid var(--accent-primary)' }}
          initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.1 }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-muted)' }}>
            <Clock size={16} /> <span className="mono" style={{ fontSize: '0.8rem' }}>EXECUTION TIME</span>
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 700, color: '#fff', marginTop: '0.5rem' }}>
            {time_elapsed.toFixed(1)}<span style={{ fontSize: '1rem', color: 'var(--text-muted)' }}>s</span>
          </div>
        </motion.div>

        <motion.div 
          className="glass-panel" 
          style={{ padding: '1.5rem', background: 'rgba(0, 0, 0, 0.4)', borderLeft: '4px solid var(--accent-primary)' }}
          initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.2 }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-muted)' }}>
             <Target size={16} /> <span className="mono" style={{ fontSize: '0.8rem' }}>TOTAL METRICS</span>
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 700, color: '#fff', marginTop: '0.5rem' }}>
            {totalTests}<span style={{ fontSize: '1rem', color: 'var(--text-muted)' }}> runs</span>
          </div>
        </motion.div>

        <motion.div 
          className="glass-panel" 
          style={{ padding: '1.5rem', background: 'rgba(0, 0, 0, 0.4)', borderLeft: `4px solid ${perfectScores > 0 ? '#00f0b5' : '#f82572'}` }}
          initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.3 }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-muted)' }}>
             <CheckSquare size={16} /> <span className="mono" style={{ fontSize: '0.8rem' }}>ACCURACY INDEX</span>
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 700, color: '#fff', marginTop: '0.5rem' }}>
            {((perfectScores / totalTests) * 100).toFixed(0)}<span style={{ fontSize: '1rem', color: 'var(--text-muted)' }}>%</span>
          </div>
        </motion.div>

      </div>

      <div style={{ marginTop: '1rem' }}>
        <h3 className="mono" style={{ fontSize: '1rem', marginBottom: '1rem', borderBottom: '1px solid var(--border-glass)', paddingBottom: '0.5rem' }}>
          RAW DATA OUTPUT
        </h3>
        
        <div style={{ 
          background: 'rgba(0,0,0,0.6)', 
          borderRadius: 'var(--radius-md)', 
          padding: '1rem',
          maxHeight: '400px',
          overflowY: 'auto',
          border: '1px solid var(--border-glass)',
          fontFamily: 'Space Mono, monospace',
          fontSize: '0.85rem'
        }}>
          {dataArray.map((r, idx) => (
             <motion.div 
                key={idx} 
                initial={{ opacity: 0, x: -10 }} 
                animate={{ opacity: 1, x: 0 }} 
                transition={{ delay: 0.4 + (idx * 0.05) }}
                style={{ 
                  display: 'flex', 
                  justifyContent: 'space-between',
                  padding: '0.8rem', 
                  borderBottom: idx === dataArray.length - 1 ? 'none' : '1px solid rgba(255,255,255,0.05)'
                }}
             >
                <div style={{ display: 'flex', gap: '1rem', color: 'var(--text-muted)' }}>
                  <span style={{ width: '30px' }}>#{idx+1}</span>
                  <span style={{ width: '100px', color: '#fff' }}>Len: {r.context_length}</span>
                  <span style={{ width: '80px', color: '#fff' }}>Dep: {r.depth_percent}%</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <span style={{ width: '60px', textAlign: 'right', color: r.score >= 10 ? '#00f0b5' : (r.score >= 5 ? '#f5a623' : '#f82572') }}>
                    Score: {r.score}
                  </span>
                  {r.score >= 10 ? <CheckSquare size={14} color="#00f0b5" /> : <XSquare size={14} color="#f82572" />}
                </div>
             </motion.div>
          ))}
        </div>
      </div>

    </div>
  );
}
