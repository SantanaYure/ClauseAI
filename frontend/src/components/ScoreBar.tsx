import { formatPercent } from '../shared/format';

type ScoreBarProps = {
  label: string;
  value: number;
  variant?: 'primary' | 'secondary';
};

/** Barra horizontal com o valor sempre escrito ao lado. */
export function ScoreBar({ label, value, variant = 'primary' }: ScoreBarProps) {
  const percent = Math.round(Math.min(Math.max(value, 0), 1) * 1000) / 10;
  return (
    <div className="score-bar">
      <div className="score-bar__header">
        <span>{label}</span>
        <strong>{formatPercent(value)}</strong>
      </div>
      <div
        className={`score-bar__track score-bar__track--${variant}`}
        role="meter"
        aria-label={label}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={percent}
        aria-valuetext={formatPercent(value)}
      >
        <span className="score-bar__fill" style={{ width: `${percent}%` }} />
      </div>
    </div>
  );
}
