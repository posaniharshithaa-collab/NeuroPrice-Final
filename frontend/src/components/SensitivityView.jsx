import './SensitivityView.css';
const winnerClass=w=>`sensitivity-view__winner--${w.toLowerCase()}`;
export default function SensitivityView({sensitivity}){
 if(!sensitivity?.grid?.length)return null;
 const {grid,elasticity_tested:es,psychology_weight_tested:ws,winner_flips:flips=[]}=sensitivity;
 const counts=grid.reduce((a,c)=>{a[c.winner]=(a[c.winner]||0)+1;return a},{});
 const dominant=Object.entries(counts).sort((a,b)=>b[1]-a[1])[0];
 return <section className="sensitivity-view"><div className="sensitivity-head"><div><p className="eyebrow">ROBUSTNESS CHECK</p><h2>Sensitivity map</h2><p>How the modeled winner changes when elasticity and psychology weighting move.</p></div><div className="sensitivity-stat"><strong>{dominant[1]}/{grid.length}</strong><span>{dominant[0]} wins</span></div></div>
  <div className="sensitivity-grid" style={{gridTemplateColumns:`110px repeat(${es.length},1fr)`}}><div className="grid-corner">WEIGHT ↓ / ELASTICITY →</div>{es.map(e=><div className="grid-head" key={e}>{e.toFixed(1)}</div>)}{ws.map(w=><div className="grid-row" key={w}><div className="grid-head">{(w*100).toFixed(0)}%</div>{es.map(e=>{const c=grid.find(x=>x.psychology_weight===w&&x.price_elasticity===e);return <div key={`${w}-${e}`} className={`grid-cell ${c?winnerClass(c.winner):''}`} title={c?`${c.winner} wins at ${w*100}% weight / ${e} elasticity`:''}>{c?c.winner[0]:'—'}</div>})}</div>)}</div>
  <div className="sensitivity-legend"><span><i className="legend-c conservative"/>C Conservative</span><span><i className="legend-c base"/>B Base</span><span><i className="legend-c aggressive"/>A Aggressive</span><span>{flips.length} winner transition{flips.length===1?'':'s'}</span></div>
  <p className="sensitivity-foot">This is a scenario sweep, not a statistical confidence measure or probability estimate.</p>
 </section>
}
