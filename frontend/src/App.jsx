import { useState } from 'react';
import AnalyzeForm from './components/AnalyzeForm';
import ScenarioComparison from './components/ScenarioComparison';
import { analyzePricing, NeuroPriceApiError } from './api/neuroprice';
import { formValuesFromRequest } from './lib/formValidation';
import './styles/tokens.css';
import './App.css';

function HeroVisual() {
  return (
    <div
      className="hero-visual"
      aria-hidden="true"
      style={{
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      <div className="hero-visual__glow hero-visual__glow--one" />
      <div className="hero-visual__glow hero-visual__glow--two" />

      <div
        style={{
          position: 'absolute',
          top: '30px',
          left: '32px',
          fontFamily: 'var(--font-mono)',
          fontSize: '10px',
          letterSpacing: '.13em',
          color: 'var(--text-tertiary)',
          textTransform: 'uppercase',
          zIndex: 2,
        }}
      >
        MARKETING SIGNALS → PRICING MODEL
      </div>

      <svg
        className="hero-visual__network"
        viewBox="0 0 620 420"
        fill="none"
        style={{
          position: 'absolute',
          inset: '45px 0 0 0',
          width: '100%',
          height: 'calc(100% - 45px)',
        }}
      >
        {/* Connecting flow lines */}
        <path
          d="M65 275 C125 275 135 205 195 205"
          stroke="currentColor"
          strokeOpacity=".22"
        />

        <path
          d="M195 205 C255 205 260 130 320 130"
          stroke="currentColor"
          strokeOpacity=".22"
        />

        <path
          d="M320 130 C380 130 385 225 445 225"
          stroke="currentColor"
          strokeOpacity=".22"
        />

        <path
          d="M445 225 C505 225 510 155 565 155"
          stroke="currentColor"
          strokeOpacity=".22"
        />

        {/* Secondary analytical lines */}
        <path
          d="M195 205 L250 310 L445 225"
          stroke="currentColor"
          strokeOpacity=".10"
        />

        <path
          d="M320 130 L390 55 L565 155"
          stroke="currentColor"
          strokeOpacity=".10"
        />

        {/* Stage 1 */}
        <circle
          cx="65"
          cy="275"
          r="20"
          stroke="currentColor"
          strokeOpacity=".10"
        />
        <circle
          cx="65"
          cy="275"
          r="5"
          fill="currentColor"
          opacity=".75"
        />

        <text
          x="38"
          y="318"
          fill="currentColor"
          opacity=".45"
          fontSize="9"
          fontFamily="ui-monospace"
          letterSpacing="1"
        >
          COPY
        </text>

        {/* Stage 2 */}
        <circle
          cx="195"
          cy="205"
          r="25"
          stroke="currentColor"
          strokeOpacity=".12"
        />
        <circle
          cx="195"
          cy="205"
          r="6"
          fill="currentColor"
          opacity=".85"
        />

        <text
          x="164"
          y="165"
          fill="currentColor"
          opacity=".55"
          fontSize="9"
          fontFamily="ui-monospace"
          letterSpacing="1"
        >
          SIGNALS
        </text>

        {/* Psychology signal card */}
        <rect
          x="135"
          y="225"
          width="120"
          height="55"
          rx="10"
          fill="rgba(255,255,255,.035)"
          stroke="rgba(255,255,255,.08)"
        />

        <text
          x="151"
          y="246"
          fill="currentColor"
          opacity=".42"
          fontSize="8"
          fontFamily="ui-monospace"
          letterSpacing="1"
        >
          AI SIGNALS
        </text>

        <text
          x="151"
          y="266"
          fill="currentColor"
          opacity=".78"
          fontSize="12"
          fontFamily="ui-monospace"
        >
          8.0 / 10
        </text>

        {/* Stage 3 */}
        <circle
          cx="320"
          cy="130"
          r="27"
          stroke="currentColor"
          strokeOpacity=".13"
        />
        <circle
          cx="320"
          cy="130"
          r="7"
          fill="currentColor"
          opacity=".95"
        />

        <text
          x="282"
          y="92"
          fill="currentColor"
          opacity=".55"
          fontSize="9"
          fontFamily="ui-monospace"
          letterSpacing="1"
        >
          ELASTICITY
        </text>

        {/* Elasticity card */}
        <rect
          x="265"
          y="145"
          width="112"
          height="55"
          rx="10"
          fill="rgba(255,255,255,.035)"
          stroke="rgba(255,255,255,.08)"
        />

        <text
          x="280"
          y="166"
          fill="currentColor"
          opacity=".42"
          fontSize="8"
          fontFamily="ui-monospace"
          letterSpacing="1"
        >
          EFFECTIVE
        </text>

        <text
          x="280"
          y="186"
          fill="currentColor"
          opacity=".78"
          fontSize="12"
          fontFamily="ui-monospace"
        >
          -0.96
        </text>

        {/* Stage 4 */}
        <circle
          cx="445"
          cy="225"
          r="25"
          stroke="currentColor"
          strokeOpacity=".12"
        />
        <circle
          cx="445"
          cy="225"
          r="6"
          fill="currentColor"
          opacity=".85"
        />

        <text
          x="420"
          y="270"
          fill="currentColor"
          opacity=".48"
          fontSize="9"
          fontFamily="ui-monospace"
          letterSpacing="1"
        >
          SCENARIOS
        </text>

        {/* Scenario branches */}
        <line
          x1="445"
          y1="225"
          x2="500"
          y2="95"
          stroke="currentColor"
          strokeOpacity=".16"
        />

        <line
          x1="445"
          y1="225"
          x2="500"
          y2="225"
          stroke="currentColor"
          strokeOpacity=".16"
        />

        <line
          x1="445"
          y1="225"
          x2="500"
          y2="350"
          stroke="currentColor"
          strokeOpacity=".16"
        />

        {/* Scenario nodes */}
        <circle
          cx="500"
          cy="95"
          r="5"
          fill="currentColor"
          opacity=".55"
        />
        <circle
          cx="500"
          cy="225"
          r="6"
          fill="currentColor"
          opacity=".85"
        />
        <circle
          cx="500"
          cy="350"
          r="5"
          fill="currentColor"
          opacity=".55"
        />

        {/* Scenario labels */}
        <text
          x="515"
          y="99"
          fill="currentColor"
          opacity=".42"
          fontSize="8"
          fontFamily="ui-monospace"
          letterSpacing=".8"
        >
          +0% CONSERVATIVE
        </text>

        <text
          x="515"
          y="229"
          fill="currentColor"
          opacity=".75"
          fontSize="8"
          fontFamily="ui-monospace"
          letterSpacing=".8"
        >
          +5% BASE
        </text>

        <text
          x="515"
          y="354"
          fill="currentColor"
          opacity=".42"
          fontSize="8"
          fontFamily="ui-monospace"
          letterSpacing=".8"
        >
          +10% AGGRESSIVE
        </text>

        {/* Bottom model trace */}
        <rect
          x="120"
          y="335"
          width="325"
          height="42"
          rx="9"
          fill="rgba(255,255,255,.025)"
          stroke="rgba(255,255,255,.07)"
        />

        <text
          x="140"
          y="360"
          fill="currentColor"
          opacity=".40"
          fontSize="8"
          fontFamily="ui-monospace"
          letterSpacing="1"
        >
          VALIDATED AI SIGNAL
        </text>

        <text
          x="270"
          y="360"
          fill="currentColor"
          opacity=".65"
          fontSize="8"
          fontFamily="ui-monospace"
        >
          →
        </text>

        <text
          x="292"
          y="360"
          fill="currentColor"
          opacity=".40"
          fontSize="8"
          fontFamily="ui-monospace"
          letterSpacing="1"
        >
          DETERMINISTIC ENGINE
        </text>
      </svg>

      <div
        className="hero-visual__label hero-visual__label--bottom"
        style={{
          right: '28px',
          bottom: '20px',
        }}
      >
        DECISION SUPPORT / V2
      </div>
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
      const message =
        err instanceof NeuroPriceApiError
          ? err.message
          : 'Something went wrong while running the analysis.';

      setError(message);
      setStatus('error');
    }
  }

  function handleRunAnother() {
    if (submittedInputs) {
      setFormInitialValues(
        formValuesFromRequest(submittedInputs)
      );
    }

    setResult(null);
    setSubmittedInputs(null);
    setStatus('idle');
  }

  return (
    <div className="app">

      <header className="topbar">

        <div
          className="brand"
          style={{
            minHeight: '72px',
          }}
        >
          <img
            className="brand__mark brand__logo"
            src="/favicon.png"
            alt="NeuroPrice logo"
          />

          <span
            className="brand__name"
            style={{
              fontSize: '28px',
            }}
          >
            NeuroPrice
          </span>

          <span
            className="brand__tag"
            style={{
              fontSize: '11px',
              letterSpacing: '.16em',
              paddingLeft: '22px',
              marginLeft: '8px',
              borderLeft: '1px solid rgba(255,255,255,.10)',
              minHeight: '42px',
              display: 'flex',
              alignItems: 'flex-start',
              paddingTop: '3px',
            }}
          >
            PRICING INTELLIGENCE
          </span>
        </div>

        <div className="topbar__status">
          <span />
          AI-assisted scenario analysis
        </div>

      </header>

      {status !== 'success' && (
        <main>

          <section className="hero">

            <div className="hero__copy">

              <p className="eyebrow">
                MARKETING SIGNALS × FINANCIAL MODELING
              </p>

              <h1>
                Price with context.
                <br />
                <em>Decide with evidence.</em>
              </h1>

              <p className="hero__lead">
                NeuroPrice translates persuasion signals in your marketing
                copy into a transparent pricing scenario model, then shows
                the financial trade-offs behind each move.
              </p>

              <div className="hero__metrics">

                <div>
                  <strong>01</strong>
                  <span>Signal extraction</span>
                </div>

                <div>
                  <strong>02</strong>
                  <span>Elasticity adjustment</span>
                </div>

                <div>
                  <strong>03</strong>
                  <span>Financial scenarios</span>
                </div>

              </div>

            </div>

            <HeroVisual />

          </section>

          <div className="section-rule">
            <span>BUILD A SCENARIO</span>
            <i />
          </div>

          {status === 'loading' && (
            <div
              className="analysis-state analysis-state--loading"
              role="status"
            >
              <span className="spinner" />
              Reading persuasion signals and running the deterministic
              pricing engine…
            </div>
          )}

          {status === 'error' && error && (
            <div
              className="analysis-state analysis-state--error"
              role="alert"
            >
              <strong>Analysis unavailable</strong>
              <span>{error}</span>
            </div>
          )}

          <AnalyzeForm
            key={
              formInitialValues
                ? JSON.stringify(formInitialValues)
                : 'default'
            }
            onSubmit={handleAnalyze}
            isSubmitting={status === 'loading'}
            initialValues={formInitialValues}
          />

        </main>
      )}

      {status === 'success' && result && (
        <main className="results-main">

          <ScenarioComparison
            inputs={submittedInputs}
            result={result}
          />

          <div className="app__result-actions">

            <button
              type="button"
              className="app__reset-button"
              onClick={handleRunAnother}
            >
              ← Run another analysis
            </button>

          </div>

        </main>
      )}

      <footer className="footer">
        <span>NEUROPRICE</span>
        <span>
          AI-assisted decision support, not a statistically validated
          price optimizer.
        </span>
      </footer>

    </div>
  );
}