import { useState } from 'react';
import { validateForm, buildAnalyzeRequest, DEFAULT_FORM_VALUES } from '../lib/formValidation';
import './AnalyzeForm.css';

export default function AnalyzeForm({ onSubmit, isSubmitting, initialValues }) {
  const [values, setValues] = useState(initialValues || DEFAULT_FORM_VALUES);
  const [touched, setTouched] = useState({});
  const { errors, isValid } = validateForm(values);
  const update = (field, value) => setValues((prev) => ({ ...prev, [field]: value }));
  const markTouched = (field) => setTouched((prev) => ({ ...prev, [field]: true }));
  const showError = (field) => touched[field] && errors[field];
  function handleSubmit(e) {
    e.preventDefault();
    setTouched({ marketing_copy:true, current_price:true, variable_cost:true, conversion_rate_pct:true, estimated_market_size:true, price_elasticity:true, customer_segment:true, psychology_weight_pct:true });
    if (!isValid || isSubmitting) return;
    onSubmit(buildAnalyzeRequest(values));
  }
  return (
    <form className="analyze-form" onSubmit={handleSubmit} noValidate>
      <div className="form-heading"><div><p className="form-heading__kicker">INPUTS</p><h2>Build your pricing scenario</h2></div><span className="form-heading__badge">DECISION MODEL</span></div>
      <div className="form-layout">
        <div className="copy-panel">
          <label className="field-label" htmlFor="marketing_copy">Marketing copy</label>
          <p className="field-helper">Paste the message customers will actually see. The AI only evaluates persuasion signals.</p>
          <textarea id="marketing_copy" className={`field-textarea ${showError('marketing_copy') ? 'field--error' : ''}`} value={values.marketing_copy} onChange={(e)=>update('marketing_copy',e.target.value)} onBlur={()=>markTouched('marketing_copy')} maxLength={2000} placeholder="e.g. Only 5 seats remaining. Join 50,000+ customers who already trust our premium solution." />
          <div className="copy-meta"><span>{values.marketing_copy.length}/2000</span><span>Signal extraction is evidence-gated</span></div>
          {showError('marketing_copy') && <p className="field-error">{errors.marketing_copy}</p>}
        </div>
        <div className="economics-panel">
          <div className="panel-title">Product economics</div>
          <div className="input-grid">
            <Field id="current_price" label="Current price" prefix="₹" value={values.current_price} update={update} blur={markTouched} error={showError('current_price')} type="number" step="0.01" />
            <Field id="variable_cost" label="Variable cost" prefix="₹" value={values.variable_cost} update={update} blur={markTouched} error={showError('variable_cost')} type="number" step="0.01" />
            <Field id="conversion_rate_pct" label="Conversion rate" suffix="%" value={values.conversion_rate_pct} update={update} blur={markTouched} error={showError('conversion_rate_pct')} type="number" step="0.1" />
            <Field id="estimated_market_size" label="Market size" value={values.estimated_market_size} update={update} blur={markTouched} error={showError('estimated_market_size')} type="number" step="1" />
          </div>
          <div className="panel-title panel-title--spaced">Elasticity assumption</div>
          <div className="segmented">
            <button type="button" className={values.elasticity_mode==='segment'?'active':''} onClick={()=>update('elasticity_mode','segment')}>Segment default</button>
            <button type="button" className={values.elasticity_mode==='manual'?'active':''} onClick={()=>update('elasticity_mode','manual')}>Manual</button>
          </div>
          {values.elasticity_mode === 'segment' ? (
            <select id="customer_segment" className="field-select" value={values.customer_segment} onChange={(e)=>update('customer_segment',e.target.value)} onBlur={()=>markTouched('customer_segment')}>
              <option value="price_sensitive">Price sensitive · −1.8</option><option value="neutral">Neutral · −1.0</option><option value="price_insensitive">Price insensitive · −0.5</option>
            </select>
          ) : <Field id="price_elasticity" label="Price elasticity" value={values.price_elasticity} update={update} blur={markTouched} error={showError('price_elasticity')} type="number" step="0.1" placeholder="e.g. -1.2" />}
          {showError('price_elasticity') && <p className="field-error">{errors.price_elasticity}</p>}
          <div className="weight-row"><div><span className="field-label">Psychology weighting</span><p className="field-helper">Maximum elasticity dampening</p></div><div className="weight-control"><input type="range" min="0" max="100" step="1" value={values.psychology_weight_pct} onChange={(e)=>update('psychology_weight_pct',e.target.value)} /><strong>{values.psychology_weight_pct}%</strong></div></div>
          {showError('psychology_weight_pct') && <p className="field-error">{errors.psychology_weight_pct}</p>}
        </div>
      </div>
      <div className="form-submit-row"><p><span>Fixed scenario bands</span> Current · +5% · +10% &nbsp; / &nbsp; Psychology affects elasticity, not the price band.</p><button type="submit" className="analyze-form__submit" disabled={isSubmitting || !isValid}><span>{isSubmitting ? 'Running model' : 'Run analysis'}</span><b>↗</b></button></div>
    </form>
  );
}

function Field({id,label,prefix,suffix,value,update,blur,error,type='text',step,placeholder}) {
  return <div className="field"><label className="field-label" htmlFor={id}>{label}</label><div className={`input-shell ${error?'field--error':''}`}>{prefix&&<span>{prefix}</span>}<input id={id} type={type} step={step} placeholder={placeholder} value={value} onChange={(e)=>update(id,e.target.value)} onBlur={()=>blur(id)} />{suffix&&<span>{suffix}</span>}</div>{error&&<p className="field-error">{error}</p>}</div>;
}
