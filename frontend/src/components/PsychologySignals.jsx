import { TRIGGER_LABELS } from '../lib/scenarioInsights';
import './PsychologySignals.css';
function score(v){return typeof v==='number'?v:0}
export default function PsychologySignals({psychology}){
 const {scores={},composite_score:compositeScore,dominant_triggers:dominantTriggers=[],evidence=[]}=psychology;
 return <section className="psychology-signals">
  <div className="signal-head"><div><p className="eyebrow">AI SIGNAL LAYER</p><h2>Persuasion signals</h2><p>Evidence-gated signals detected in the submitted marketing copy.</p></div><div className="composite-score"><span>COMPOSITE</span><strong>{typeof compositeScore==='number'?compositeScore.toFixed(1):'—'}</strong><small>/ 10</small></div></div>
  <div className="signal-grid">{Object.keys(TRIGGER_LABELS).map(key=><div className="signal-card" key={key}><div className="signal-card__top"><span>{TRIGGER_LABELS[key]}</span><strong>{score(scores[key]).toFixed(0)}<i>/10</i></strong></div><div className="signal-meter"><span style={{width:`${score(scores[key])*10}%`}} /></div></div>)}</div>
  {dominantTriggers.length>0&&<div className="dominant-row"><span>DOMINANT SIGNALS</span><strong>{dominantTriggers.map(t=>TRIGGER_LABELS[t]||t).join(' · ')}</strong></div>}
  <div className="evidence-block"><div className="evidence-title"><span>EVIDENCE FROM COPY</span><small>{evidence.length} validated item{evidence.length===1?'':'s'}</small></div>{evidence.length?evidence.map((item,i)=><div className="evidence-item" key={`${item.trigger}-${i}`}><b>{TRIGGER_LABELS[item.trigger]||item.trigger}</b><p>{item.reason}</p></div>):<p className="evidence-empty">No supporting evidence was returned for the detected signals.</p>}</div>
 </section>
}
