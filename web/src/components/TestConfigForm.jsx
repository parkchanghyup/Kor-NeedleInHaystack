import { useState } from 'react';
import { motion } from 'framer-motion';
import { Play } from 'lucide-react';

export default function TestConfigForm({ onStart, isPending }) {
  const [config, setConfig] = useState({
    provider: 'openai',
    evaluator: 'openai',
    model_name: 'gpt-4o-mini',
    evaluator_model_name: 'gpt-4o-mini',
    multi_needle: false,
    context_lengths_min: 1000,
    context_lengths_max: 8000,
    context_lengths_num_intervals: 3,
    document_depth_percent_min: 0,
    document_depth_percent_max: 100,
    document_depth_percent_intervals: 3,
  });

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setConfig(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : (type === 'number' ? Number(value) : value)
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onStart(config);
  };

  return (
    <form onSubmit={handleSubmit} style={{ width: '100%' }}>
      {/* 1. General Configuration */}
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.1 }}>
        <fieldset style={{ border: 'none', marginBottom: '2rem' }}>
          <legend className="mono" style={{ color: 'var(--accent-primary)', marginBottom: '1rem', borderBottom: '1px solid var(--border-glass)', paddingBottom: '0.5rem', width: '100%' }}>
            [1.0] PROVIDER CONFIG
          </legend>

          <div className="form-group">
            <label className="form-label" htmlFor="provider">Target Provider</label>
            <select
              className="form-select"
              id="provider"
              name="provider"
              value={config.provider}
              onChange={handleChange}
              disabled={isPending}
            >
              <option value="openai">OpenAI</option>
              <option value="anthropic">Anthropic</option>
              <option value="gemini">Google Gemini</option>
              <option value="openrouter">OpenRouter</option>
              <option value="vllm">vLLM</option>
            </select>
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="model_name">Target Model Name</label>
            <input
              type="text"
              className="form-input"
              id="model_name"
              name="model_name"
              value={config.model_name}
              onChange={handleChange}
              disabled={isPending}
              placeholder="e.g. gpt-4o-mini"
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="evaluator">Evaluator Provider</label>
            <select
              className="form-select"
              id="evaluator"
              name="evaluator"
              value={config.evaluator}
              onChange={handleChange}
              disabled={isPending}
            >
              <option value="openai">OpenAI</option>
              <option value="gemini">Google Gemini</option>
              <option value="openrouter">OpenRouter</option>
            </select>
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="evaluator_model_name">Evaluator Model Name</label>
            <input
              type="text"
              className="form-input"
              id="evaluator_model_name"
              name="evaluator_model_name"
              value={config.evaluator_model_name}
              onChange={handleChange}
              disabled={isPending}
              placeholder="e.g. gpt-4o-mini"
            />
          </div>

          <div className="form-group">
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
              <input
                type="checkbox"
                name="multi_needle"
                checked={config.multi_needle}
                onChange={handleChange}
                disabled={isPending}
                style={{ width: '1rem', height: '1rem', accentColor: 'var(--accent-primary)' }}
              />
              <span className="form-label" style={{ margin: 0, color: config.multi_needle ? 'var(--accent-primary)' : 'var(--text-muted)' }}>
                Enable Multi-Needle Test
              </span>
            </label>
          </div>
        </fieldset>
      </motion.div>

      {/* 2. Context Testing Range */}
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.2 }}>
        <fieldset style={{ border: 'none', marginBottom: '2rem' }}>
          <legend className="mono" style={{ color: 'var(--accent-secondary)', marginBottom: '1rem', borderBottom: '1px solid var(--border-glass)', paddingBottom: '0.5rem', width: '100%' }}>
            [2.0] CONTEXT LENGTH RANGE
          </legend>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div className="form-group">
              <label className="form-label" htmlFor="context_lengths_min">MIN TOKENS</label>
              <input
                type="number"
                className="form-input"
                id="context_lengths_min"
                name="context_lengths_min"
                value={config.context_lengths_min}
                onChange={handleChange}
                disabled={isPending}
              />
            </div>
            <div className="form-group">
              <label className="form-label" htmlFor="context_lengths_max">MAX TOKENS</label>
              <input
                type="number"
                className="form-input"
                id="context_lengths_max"
                name="context_lengths_max"
                value={config.context_lengths_max}
                onChange={handleChange}
                disabled={isPending}
              />
            </div>
          </div>
          <div className="form-group">
            <label className="form-label" htmlFor="context_lengths_num_intervals">TEST INTERVALS (X-Axis)</label>
            <input
              type="number"
              className="form-input"
              id="context_lengths_num_intervals"
              name="context_lengths_num_intervals"
              value={config.context_lengths_num_intervals}
              onChange={handleChange}
              disabled={isPending}
              min="1" max="25"
            />
          </div>
        </fieldset>
      </motion.div>

       {/* 3. Document Depth Range */}
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.3 }}>
        <fieldset style={{ border: 'none', marginBottom: '1rem' }}>
          <legend className="mono" style={{ color: '#fff', marginBottom: '1rem', borderBottom: '1px solid var(--border-glass)', paddingBottom: '0.5rem', width: '100%' }}>
            [3.0] DOCUMENT DEPTH RANGE
          </legend>
          <div className="form-group">
            <label className="form-label" htmlFor="document_depth_percent_intervals">TEST INTERVALS (Y-Axis)</label>
            <input
              type="number"
              className="form-input"
              id="document_depth_percent_intervals"
              name="document_depth_percent_intervals"
              value={config.document_depth_percent_intervals}
              onChange={handleChange}
              disabled={isPending}
              min="1" max="25"
            />
          </div>
        </fieldset>
      </motion.div>

      <motion.button 
        type="submit" 
        className="btn-primary" 
        disabled={isPending}
        whileTap={{ scale: 0.98 }}
        style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}
      >
        <Play size={20} fill="#000" />
        {isPending ? 'SYSTEM BUSY...' : 'INITIALIZE TEST SEQUENCE'}
      </motion.button>
    </form>
  );
}
