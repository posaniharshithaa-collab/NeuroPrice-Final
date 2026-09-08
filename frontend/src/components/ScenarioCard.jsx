import { formatMargin } from '../lib/scenarioInsights';
import './ScenarioCard.css';
const money=v=>new Intl.NumberFormat('en-IN',{style:'currency',currency:'INR',maximumFractionDigits:0}).format(v);
const pct=v=>`${(v*100).toFixed(1)}%`;
export default function ScenarioCard({scenario,isRecommended,tradeoff}){const margin=formatMargin(scenario);return <article className={`scenario-card ${isRecommended?'scenario-card--recommended':''}`}>
  <div className="scenario-card__top"><span>{scenario.name}</span>{isRecommended&&<b>RECOMMENDED</b>}</div>
  <strong className="scenario-card__price">{money(scenario.price)}</strong>
  <p className="scenario-card__lift">{scenario.adjustment_level} adjustment · {scenario.name==='Conservative'?'0':scenario.name==='Base'?'5':'10'}% price lift</p>
  <div className="scenario-card__stats"><div><small>Demand</small><strong>{scenario.demand.toLocaleString()}</strong></div><div><small>Conversion</small><strong>{pct(scenario.conversion)}</strong></div><div><small>Contribution</small><strong>{money(scenario.contribution)}</strong></div></div>
  <div className="scenario-card__footer"><span>{tradeoff}</span><span>Margin {margin!==null?`${margin.toFixed(1)}%`:'—'}</span></div>
</article>}
