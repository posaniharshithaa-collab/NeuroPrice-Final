import { useState } from 'react';
import AnalyzeForm from './components/AnalyzeForm';
import ScenarioComparison from './components/ScenarioComparison';
import { analyzePricing, NeuroPriceApiError } from './api/neuroprice';
import { formValuesFromRequest } from './lib/formValidation';
import './styles/tokens.css';
import './App.css';

function HeroVisual() {
  return (
    <div className="hero-visual" aria-hidden="true">
      <div className="hero-visual__glow hero-visual__glow--one" />
      <div className="hero-visual__glow hero-visual__glow--two" />
      <svg className="hero-visual__network" viewBox="0 0 520 360" fill="none">
        <path d="M80 270L180 178L276 232L364 112L456 166" stroke="currentColor" strokeOpacity=".32" />
        <path d="M180 178L220 84L364 112L414 42" stroke="currentColor" strokeOpacity=".2" />
        <path d="M276 232L330 300L456 166" stroke="currentColor" strokeOpacity=".18" />
        {[['80', '270', '3'], ['180', '178', '5'], ['276', '232', '4'], ['364', '112', '6'], ['456', '166', '4'], ['220', '84', '3'], ['414', '42', '3'], ['330', '300', '3']].map(([cx, cy, r], i) => (
          <g key={i}>
            <circle cx={cx} cy={cy} r={Number(r) * 2.6} stroke="currentColor" strokeOpacity=".09" />
            <circle cx={cx} cy={cy} r={r} fill="currentColor" opacity={i === 3 ? '.95' : '.6'} />
          </g>
        ))}
        <rect x="306" y="74" width="130" height="58" rx="10" fill="rgba(255,255,255,.045)" stroke="rgba(255,255,255,.1)" />
        <text x="322" y="97" fill="currentColor" opacity=".55" fontSize="10" fontFamily="ui-monospace">MODEL SIGNAL</text>
        <text x="322" y="117" fill="currentColor" opacity=".95" fontSize="18" fontFamily="ui-monospace">+10.0%</text>
      </svg>
      <div className="hero-visual__label hero-visual__label--top">PSYCHOLOGY → ELASTICITY</div>
      <div className="hero-visual__label hero-visual__label--bottom">SCENARIO ENGINE / v2</div>
    </div>
  );
}

export default function App() {
  const [status, setStatus] = useState('idle');
  const [result, setResult] = useState(null);
  const [submittedInputs, setSubmittedInputs] = useState(null);
  const [formInitialValues, setFormInitialValues] = useState(undefined);
  const [error, setError] = useState(null);

  async function handleAnalyze(payload) {
    if (status === 'loading') return;
    setStatus('loading');
    setError(null);
    try {
      const apiResult = await analyzePricing(payload);
      setSubmittedInputs(payload);
      setResult(apiResult);
      setStatus('success');
    } catch (err) {
      const message = err instanceof NeuroPriceApiError
        ? err.message
        : 'Something went wrong while running the analysis.';
      setError(message);
      setStatus('error');
    }
  }

  function handleRunAnother() {
    if (submittedInputs) setFormInitialValues(formValuesFromRequest(submittedInputs));
    setResult(null);
    setSubmittedInputs(null);
    setStatus('idle');
  }

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <span className="brand__mark">N</span>
          <span className="brand__name">NeuroPrice</span>
          <span className="brand__tag">PRICING INTELLIGENCE</span>
        </div>
        <div className="topbar__status"><span /> AI-assisted scenario analysis</div>
      </header>

      {status !== 'success' && (
        <main>
          <section className="hero">
            <div className="hero__copy">
              <p className="eyebrow">MARKETING SIGNALS × FINANCIAL MODELING</p>
              <h1>Price with context.<br /><em>Decide with evidence.</em></h1>
              <p className="hero__lead">
                NeuroPrice translates persuasion signals in your marketing copy into a transparent pricing scenario model, then shows the financial trade-offs behind each move.
              </p>
              <div className="hero__metrics">
                <div><strong>01</strong><span>Signal extraction</span></div>
                <div><strong>02</strong><span>Elasticity adjustment</span></div>
                <div><strong>03</strong><span>Financial scenarios</span></div>
              </div>
            </div>
            <HeroVisual />
          </section>

          <div className="section-rule"><span>BUILD A SCENARIO</span><i /></div>
          {status === 'loading' && (
            <div className="analysis-state analysis-state--loading" role="status">
              <span className="spinner" /> Reading persuasion signals and running the deterministic pricing engine…
            </div>
          )}
          {status === 'error' && error && (
            <div className="analysis-state analysis-state--error" role="alert">
              <strong>Analysis unavailable</strong><span>{error}</span>
            </div>
          )}
          <AnalyzeForm
            key={formInitialValues ? JSON.stringify(formInitialValues) : 'default'}
            onSubmit={handleAnalyze}
            isSubmitting={status === 'loading'}
            initialValues={formInitialValues}
          />
        </main>
      )}

      {status === 'success' && result && (
        <main className="results-main">
          <ScenarioComparison inputs={submittedInputs} result={result} />
          <div className="app__result-actions">
            <button type="button" className="app__reset-button" onClick={handleRunAnother}>← Run another analysis</button>
          </div>
        </main>
      )}

      <footer className="footer"><span>NEUROPRICE</span><span>AI-assisted decision support, not a statistically validated price optimizer.</span></footer>
    </div>
  );
}
