import { useEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { motion } from 'framer-motion';
import { ChevronDown, ChevronUp, Play } from 'lucide-react';

const DEFAULT_MULTI_NEEDLE_COUNT = 5;
const TOOLTIP_GAP = 8;
const TOOLTIP_VIEWPORT_PADDING = 12;
const TOOLTIP_MIN_WIDTH = 120;
const TOOLTIP_MAX_WIDTH = 260;

function SectionHeader({ title, tone, isOpen, onToggle, summary }) {
  return (
    <div className="section-header">
      <button type="button" className="section-toggle" onClick={onToggle} aria-expanded={isOpen}>
        <span className={`mono section-title ${tone}`}>{title}</span>
        <span className="section-toggle__icon">{isOpen ? <ChevronUp size={18} /> : <ChevronDown size={18} />}</span>
      </button>
      <p className="section-description">{summary}</p>
    </div>
  );
}

function HelpIconTooltip({ label, help }) {
  const triggerRef = useRef(null);
  const [isOpen, setIsOpen] = useState(false);
  const [tooltipStyle, setTooltipStyle] = useState({
    left: 0,
    top: 0,
    width: TOOLTIP_MAX_WIDTH,
    placement: 'bottom',
  });

  const updateTooltipPosition = () => {
    if (!triggerRef.current) {
      return;
    }

    const triggerRect = triggerRef.current.getBoundingClientRect();
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;
    const availableWidth = Math.max(120, viewportWidth - TOOLTIP_VIEWPORT_PADDING * 2);
    const contentBasedWidth = Math.round(help.length * 7.4 + 24);
    const tooltipWidth = Math.min(
      availableWidth,
      Math.min(TOOLTIP_MAX_WIDTH, Math.max(TOOLTIP_MIN_WIDTH, contentBasedWidth))
    );

    const halfWidth = tooltipWidth / 2;
    const minCenter = TOOLTIP_VIEWPORT_PADDING + halfWidth;
    const maxCenter = viewportWidth - TOOLTIP_VIEWPORT_PADDING - halfWidth;
    const centerX = Math.min(maxCenter, Math.max(minCenter, triggerRect.left + triggerRect.width / 2));

    const estimatedHeight = 64;
    const canOpenBelow = triggerRect.bottom + TOOLTIP_GAP + estimatedHeight <= viewportHeight - TOOLTIP_VIEWPORT_PADDING;
    const canOpenAbove = triggerRect.top - TOOLTIP_GAP - estimatedHeight >= TOOLTIP_VIEWPORT_PADDING;
    const placement = canOpenBelow || !canOpenAbove ? 'bottom' : 'top';
    const top = placement === 'bottom'
      ? triggerRect.bottom + TOOLTIP_GAP
      : triggerRect.top - TOOLTIP_GAP;

    setTooltipStyle({
      left: centerX,
      top,
      width: tooltipWidth,
      placement,
    });
  };

  useEffect(() => {
    if (!isOpen) {
      return;
    }

    updateTooltipPosition();

    const handleReposition = () => {
      updateTooltipPosition();
    };

    window.addEventListener('resize', handleReposition);
    window.addEventListener('scroll', handleReposition, true);

    return () => {
      window.removeEventListener('resize', handleReposition);
      window.removeEventListener('scroll', handleReposition, true);
    };
  }, [isOpen]);

  return (
    <span
      ref={triggerRef}
      className="help-wrap"
      tabIndex={0}
      role="note"
      aria-label={`${label} 도움말`}
      onMouseEnter={() => setIsOpen(true)}
      onMouseLeave={() => setIsOpen(false)}
      onFocus={() => setIsOpen(true)}
      onBlur={() => setIsOpen(false)}
    >
      <span className="help-dot">?</span>
      {isOpen && createPortal(
        <span
          className={`help-tooltip help-tooltip--portal help-tooltip--${tooltipStyle.placement}`}
          style={{ left: `${tooltipStyle.left}px`, top: `${tooltipStyle.top}px`, width: `${tooltipStyle.width}px` }}
        >
          {help}
        </span>,
        document.body
      )}
    </span>
  );
}

function LabelWithHelp({ htmlFor, label, help }) {
  return (
    <label className="form-label label-with-help" htmlFor={htmlFor}>
      <span>{label}</span>
      <HelpIconTooltip label={label} help={help} />
    </label>
  );
}

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
  const [openSections, setOpenSections] = useState({
    provider: true,
    context: true,
    depth: true,
  });
  const wasPendingRef = useRef(false);

  const expectedTests = config.context_lengths_num_intervals * config.document_depth_percent_intervals;

  useEffect(() => {
    if (isPending && !wasPendingRef.current) {
      setOpenSections({
        provider: false,
        context: false,
        depth: false,
      });
    }

    wasPendingRef.current = isPending;
  }, [isPending]);

  const toggleSection = (key) => {
    setOpenSections((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setConfig((prev) => ({
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
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.1 }}>
        <fieldset className="config-section config-section--primary">
          <SectionHeader
            title="PROVIDER CONFIG"
            tone="section-title--primary"
            isOpen={openSections.provider}
            onToggle={() => toggleSection('provider')}
            summary="테스트 모델과 평가 모델을 선택합니다."
          />

          <motion.div
            className="section-collapse"
            initial={false}
            animate={openSections.provider ? 'open' : 'collapsed'}
            variants={{
              open: { height: 'auto', opacity: 1 },
              collapsed: { height: 0, opacity: 0 }
            }}
            transition={{ duration: 0.24, ease: [0.22, 1, 0.36, 1] }}
          >
            <div className="section-body">
              <div className="form-group">
                <LabelWithHelp htmlFor="provider" label="테스트 대상 프로바이더" help="실제 성능을 측정할 모델 제공사입니다." />
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
                <LabelWithHelp htmlFor="model_name" label="테스트 대상 모델명" help="호출할 실제 모델 이름을 입력합니다." />
                <input
                  type="text"
                  className="form-input"
                  id="model_name"
                  name="model_name"
                  value={config.model_name}
                  onChange={handleChange}
                  disabled={isPending}
                  placeholder="예: gpt-4o-mini"
                />
              </div>

              <div className="form-group">
                <LabelWithHelp htmlFor="evaluator" label="평가 프로바이더" help="응답 정답 여부를 채점할 모델 제공사입니다." />
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
                <LabelWithHelp htmlFor="evaluator_model_name" label="평가 모델명" help="채점에 사용할 모델 이름입니다." />
                <input
                  type="text"
                  className="form-input"
                  id="evaluator_model_name"
                  name="evaluator_model_name"
                  value={config.evaluator_model_name}
                  onChange={handleChange}
                  disabled={isPending}
                  placeholder="예: gpt-4o-mini"
                />
              </div>

              <div className="mode-card">
                <label className="mode-toggle">
                  <input
                    type="checkbox"
                    name="multi_needle"
                    checked={config.multi_needle}
                    onChange={handleChange}
                    disabled={isPending}
                    style={{ width: '1rem', height: '1rem', accentColor: 'var(--accent-primary)' }}
                  />
                  <span className="form-label label-with-help" style={{ margin: 0, color: config.multi_needle ? 'var(--accent-primary)' : 'var(--text-main)' }}>
                    <span>멀티 needle 테스트 사용</span>
                    <HelpIconTooltip
                      label="멀티 needle"
                      help={`현재 기본값으로 한 문서에 ${DEFAULT_MULTI_NEEDLE_COUNT}개 needle을 함께 넣어 테스트합니다.`}
                    />
                  </span>
                </label>
                <p className="mode-copy">needle 여러 개를 동시에 찾는 시나리오를 검사합니다.</p>
              </div>
            </div>
          </motion.div>
        </fieldset>
      </motion.div>

      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.2 }}>
        <fieldset className="config-section config-section--secondary">
          <SectionHeader
            title="CONTEXT LENGTH RANGE"
            tone="section-title--secondary"
            isOpen={openSections.context}
            onToggle={() => toggleSection('context')}
            summary="문서 길이 범위를 설정합니다."
          />

          <motion.div
            className="section-collapse"
            initial={false}
            animate={openSections.context ? 'open' : 'collapsed'}
            variants={{
              open: { height: 'auto', opacity: 1 },
              collapsed: { height: 0, opacity: 0 }
            }}
            transition={{ duration: 0.24, ease: [0.22, 1, 0.36, 1] }}
          >
            <div className="section-body">
              <div className="range-grid">
                <div className="form-group">
                  <LabelWithHelp htmlFor="context_lengths_min" label="최소 토큰 수" help="테스트할 문서 길이의 시작값입니다." />
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
                  <LabelWithHelp htmlFor="context_lengths_max" label="최대 토큰 수" help="테스트할 문서 길이의 끝값입니다." />
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
                <LabelWithHelp htmlFor="context_lengths_num_intervals" label="길이 구간 수 (X축)" help="최소~최대 사이를 몇 단계로 나눌지 설정합니다." />
                <input
                  type="number"
                  className="form-input"
                  id="context_lengths_num_intervals"
                  name="context_lengths_num_intervals"
                  value={config.context_lengths_num_intervals}
                  onChange={handleChange}
                  disabled={isPending}
                  min="1"
                  max="25"
                />
              </div>
            </div>
          </motion.div>
        </fieldset>
      </motion.div>

      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.3 }}>
        <fieldset className="config-section config-section--neutral">
          <SectionHeader
            title="DOCUMENT DEPTH RANGE"
            tone="section-title--neutral"
            isOpen={openSections.depth}
            onToggle={() => toggleSection('depth')}
            summary="needle 삽입 위치 범위를 설정합니다."
          />

          <motion.div
            className="section-collapse"
            initial={false}
            animate={openSections.depth ? 'open' : 'collapsed'}
            variants={{
              open: { height: 'auto', opacity: 1 },
              collapsed: { height: 0, opacity: 0 }
            }}
            transition={{ duration: 0.24, ease: [0.22, 1, 0.36, 1] }}
          >
            <div className="section-body">
              <div className="range-grid">
                <div className="form-group">
                  <LabelWithHelp htmlFor="document_depth_percent_min" label="최소 깊이 (%)" help="문서 앞쪽 기준 삽입 시작 위치입니다." />
                  <input
                    type="number"
                    className="form-input"
                    id="document_depth_percent_min"
                    name="document_depth_percent_min"
                    value={config.document_depth_percent_min}
                    onChange={handleChange}
                    disabled={isPending}
                    min="0"
                    max="100"
                  />
                </div>
                <div className="form-group">
                  <LabelWithHelp htmlFor="document_depth_percent_max" label="최대 깊이 (%)" help="문서 뒤쪽 기준 삽입 끝 위치입니다." />
                  <input
                    type="number"
                    className="form-input"
                    id="document_depth_percent_max"
                    name="document_depth_percent_max"
                    value={config.document_depth_percent_max}
                    onChange={handleChange}
                    disabled={isPending}
                    min="0"
                    max="100"
                  />
                </div>
              </div>

              <div className="form-group">
                <LabelWithHelp htmlFor="document_depth_percent_intervals" label="깊이 구간 수 (Y축)" help="삽입 위치를 몇 단계로 나눌지 설정합니다." />
                <input
                  type="number"
                  className="form-input"
                  id="document_depth_percent_intervals"
                  name="document_depth_percent_intervals"
                  value={config.document_depth_percent_intervals}
                  onChange={handleChange}
                  disabled={isPending}
                  min="1"
                  max="25"
                />
              </div>
            </div>
          </motion.div>
        </fieldset>
      </motion.div>

      <div className="estimate-card">
        <span className="estimate-card__label">예상 테스트 수</span>
        <strong className="estimate-card__value">{expectedTests}회</strong>
        <span className="estimate-card__meta">
          {config.context_lengths_num_intervals}개 길이 구간 × {config.document_depth_percent_intervals}개 깊이 구간
        </span>
      </div>

      <motion.button
        type="submit"
        className="btn-primary"
        disabled={isPending}
        whileTap={{ scale: 0.98 }}
        style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}
      >
        <Play size={20} fill="#000" />
        {isPending ? '테스트 실행 중...' : '테스트 시작'}
      </motion.button>
    </form>
  );
}
