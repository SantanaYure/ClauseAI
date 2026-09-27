import { BrokerNotice } from '../../components/BrokerNotice';
import { Icon } from '../../components/Icon';
import type { ComparisonResult } from '../../types/domain';

/** Checklist de controle de qualidade (prompt 16, SPEC-019). */
export function QualityPanel({ comparison }: { comparison: ComparisonResult }) {
  const failed = comparison.qualityGate.filter((check) => !check.passed);
  return (
    <div className="stack">
      <p className="muted-text">
        {failed.length
          ? `${failed.length} verificação(ões) com limitação. O resultado continua visível, com as limitações declaradas.`
          : 'Todas as verificações passaram.'}
      </p>
      <ul className="checklist">
        {comparison.qualityGate.map((check) => (
          <li
            key={check.id}
            className={`checklist__item${check.passed ? '' : ' checklist__item--warn'}`}
          >
            <Icon name={check.passed ? 'checkCircle' : 'alert'} size={20} />
            <div>
              <p className="checklist__label">
                {check.label}
                <span className="visually-hidden">{check.passed ? ' — ok' : ' — limitação'}</span>
              </p>
              <p className="muted-text">{check.detail}</p>
            </div>
          </li>
        ))}
      </ul>
      {failed.length > 0 && (
        <BrokerNotice reason="Há limitações no processamento desta comparação." />
      )}
      <p className="footnote">
        Base de conhecimento D&amp;O versão {comparison.knowledgeBaseVersion}.
      </p>
    </div>
  );
}
