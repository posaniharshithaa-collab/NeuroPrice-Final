import './LimitationsNote.css';

const LIMITATIONS = [
  'Price elasticity is either user-supplied or a documented segment-level assumption, not an empirically estimated value.',
  'Persuasion-signal scores are heuristic and evidence-gated, not validated behavioral measurements.',
  'Evidence plausibility and grounding checks are heuristic keyword/overlap checks, not semantic verification.',
  'The model does not establish a causal effect between marketing copy and actual buyer behavior.',
  'Competitor response, cross-price effects, and market saturation are not modeled.',
  'The current version models upward pricing scenarios only.',
  'Scenario price bands (current price, +5%, +10%) are fixed modeling assumptions, not derived from the data.',
];

export default function LimitationsNote() {
  return (
    <div className="limitations-note">
      <h2 className="limitations-note__heading">Methodology and limitations</h2>
      <ul className="limitations-note__list">
        {LIMITATIONS.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
      <p className="limitations-note__footer">
        This is a scenario-analysis decision-support tool, not a statistically validated price optimizer.
      </p>
    </div>
  );
}
