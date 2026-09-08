import ScenarioCard from './ScenarioCard';
import AssumptionsPanel from './AssumptionsPanel';
import PsychologySignals from './PsychologySignals';
import SensitivityView from './SensitivityView';
import LimitationsNote from './LimitationsNote';
import { getScenarioTradeoff, generateWhatMovedText, computeFinancialImpact, formatDelta } from '../lib/scenarioInsights';
import './ScenarioComparison.css';

const money = (v) => new Intl.NumberFormat('en-IN', { style:'currency', currency:'INR', maximumFractionDigits:0 }).format(v);
const pct = (v) => `${(v*100).toFixed(1)}%`;

function BarChart({ title, subtitle, scenarios, metric, format }) {
  const values = scenarios.map(s => Number(s[metric]) || 0);
  const max = Math.max(...values, 1);
  return <div className="data-chart">
    <div className="data-chart__head"><div><h3>{title}</h3><p>{subtitle}</p></div><span>SCENARIO VIEW</span></div>
    <div className="bar-chart">
      {scenarios.map((s, i) => <div className="bar-item" key={s.name}>
        <div className="bar-item__value">{format(s[metric])}</div>
        <div className="bar-item__track"><div className={`bar-item__fill bar-item__fill--${i}`} style={{height:`${Math.max(7,(s[metric]/max)*100)}%`}} /></div>
        <div className="bar-item__label">{s.name}</div><small>{i===0?'Current':i===1?'+5%':' +10%'}</small>
      </div>)}
    </div>
  </div>;
}

function ElasticityFlow({ assumptions, composite }) {
  const base = assumptions.price_elasticity_used;
  const effective = assumptions.effective_elasticity;
  const damp = base !== 0 ? (1 - effective / base) * 100 : 0;
  return <div className="model-flow">
    <div className="model-flow__head"><div><p className="eyebrow">MODEL TRACE</p><h2>How the signal changed the model</h2></div><span>TRANSPARENT CHAIN</span></div>
    <div className="flow-row">
      <div className="flow-node"><small>AI SIGNAL</small><strong>{composite.toFixed(1)}<i>/10</i></strong><span>persuasion score</span></div>
      <b>→</b><div className="flow-node"><small>BASE ELASTICITY</small><strong>{base.toFixed(2)}</strong><span>user / segment assumption</span></div>
      <b>→</b><div className="flow-node flow-node--accent"><small>EFFECTIVE ELASTICITY</small><strong>{effective.toFixed(4)}</strong><span>{damp.toFixed(1)}% magnitude dampening</span></div>
    </div>
    <p className="model-flow__explain">Validated persuasion signals reduced the magnitude of modeled price elasticity, meaning the model assumes less demand sensitivity to the price increase. Psychology does not choose the price band.</p>
  </div>;
}

export default function ScenarioComparison({ inputs, result }) {
  if (!result.ok) return <div className="scenario-comparison"><div className="scenario-comparison__status scenario-comparison__status--error" role="alert">{result.error_message}</div></div>;
  const { financials, psychology } = result;
  const { scenarios } = financials;
  const recommended = scenarios.find(s => s.recommended) || scenarios[0];
  const baseline = scenarios.find(s => s.name === 'Conservative') || scenarios[0];
  const impact = computeFinancialImpact(recommended, baseline);
  const whatMovedText = generateWhatMovedText(psychology, financials, recommended);
  return <div className="scenario-comparison">
    <section className="results-hero">
      <div><p className="eyebrow">ANALYSIS COMPLETE · {result.attempts_used || 1} AI ATTEMPT{result.attempts_used === 1 ? '' : 'S'}</p><h1>Pricing decision <em>decoded.</em></h1><p>One validated signal layer, one deterministic financial model, three explicit scenarios.</p></div>
      <div className="recommendation"><span>RECOMMENDED SCENARIO</span><strong>{recommended.name}</strong><b>{money(recommended.price)}</b><small>Highest modeled contribution under the stated assumptions.</small></div>
    </section>
    <div className="copy-strip"><span>ANALYZED COPY</span><p>“{inputs.marketing_copy}”</p></div>
    <section className="scenario-section"><div className="section-heading"><div><p className="eyebrow">PRICE SCENARIOS</p><h2>Three moves. One trade-off.</h2></div><span>0% / +5% / +10%</span></div><div className="scenario-comparison__grid">{scenarios.map(s=><ScenarioCard key={s.name} scenario={s} isRecommended={s.recommended} tradeoff={getScenarioTradeoff(s, scenarios)} />)}</div></section>
    <ElasticityFlow assumptions={financials.assumptions} composite={psychology.composite_score} />
    <section className="charts-grid">
      <BarChart title="Revenue by scenario" subtitle="Modeled top-line outcome" scenarios={scenarios} metric="revenue" format={money} />
      <BarChart title="Contribution by scenario" subtitle="Modeled contribution after variable cost" scenarios={scenarios} metric="contribution" format={money} />
    </section>
    <section className="impact-panel"><div><p className="eyebrow">FINANCIAL IMPACT</p><h2>What changes if you move?</h2><p>Recommended scenario versus the current-price baseline.</p></div><div className="impact-metrics"><Metric label="Demand" value={formatDelta(impact.demand)} tone="flat" /><Metric label="Revenue" value={formatDelta(impact.revenue)} tone={impact.revenue>0?'up':impact.revenue<0?'down':'flat'} /><Metric label="Contribution" value={formatDelta(impact.contribution)} tone={impact.contribution>0?'up':impact.contribution<0?'down':'flat'} /></div></section>
    <div className="what-moved"><div className="what-moved__icon">↗</div><div><p className="eyebrow">WHAT MOVED THE MODEL</p><h2>The AI signal changed elasticity, not price.</h2><p>{whatMovedText}</p></div></div>
    <PsychologySignals psychology={psychology} />
    <AssumptionsPanel inputs={inputs} assumptions={financials.assumptions} />
    <SensitivityView sensitivity={financials.sensitivity} />
    <LimitationsNote />
  </div>;
}
function Metric({label,value,tone}) { return <div className="impact-metric"><span>{label}</span><strong className={`impact-metric--${tone}`}>{value}</strong></div>; }
