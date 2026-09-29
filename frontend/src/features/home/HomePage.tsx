import { paths } from '../../app/router';
import { Badge } from '../../components/Badge';
import { BrokerNotice } from '../../components/BrokerNotice';
import { Icon, type IconName } from '../../components/Icon';
import { clauseApi } from '../../services/api/clause-api';
import { formatDateTime } from '../../shared/format';
import { DECISION_MODE_LABELS } from '../../shared/labels';
import { hasBusyComparison, isComparisonBusy, PROCESSING_POLL_MS } from '../../shared/processing';
import { useApiData } from '../../shared/useApiData';

const STEPS: { icon: IconName; title: string; text: string }[] = [
  {
    icon: 'upload',
    title: 'Enviar documentos',
    text: 'Apólice, condições gerais e especificação em PDF ou imagem.',
  },
  {
    icon: 'file',
    title: 'Extrair informações',
    text: 'Leitura do PDF e OCR identificam cláusulas e coberturas.',
  },
  {
    icon: 'search',
    title: 'Revisar evidências',
    text: 'Cada informação mostra o trecho, a cláusula e a página.',
  },
  {
    icon: 'chart',
    title: 'Comparar resultados',
    text: 'Scores por conceito, perfis de risco e resumo executivo.',
  },
];

const PRINCIPLES: { icon: IconName; title: string; text: string }[] = [
  {
    icon: 'quote',
    title: 'Trechos e páginas da fonte',
    text: 'Nada é afirmado sem o trecho literal, a cláusula e a página.',
  },
  {
    icon: 'shield',
    title: 'Contratação separada de menção',
    text: 'Previsto nas condições gerais não é o mesmo que contratado.',
  },
  {
    icon: 'chart',
    title: 'Pontuação explicável',
    text: 'Peso × resultado × ajuste, com justificativa para cada redução.',
  },
];

function LatestComparison() {
  const state = useApiData('comparisons', () => clauseApi.listComparisons(), {
    pollMs: PROCESSING_POLL_MS,
    shouldPoll: hasBusyComparison,
  });
  if (state.status !== 'success') return null;
  const latest = state.data.find((comparison) => comparison.status !== 'FAILED');
  if (!latest) return null;

  return (
    <section className="card card--muted" aria-labelledby="continue-title">
      <h2 id="continue-title" className="section-title">
        Continue de onde parou
      </h2>
      <a className="list-link" href={paths.comparison(latest.id)}>
        <Icon name="scale" size={22} />
        <span className="list-link__body">
          <strong>
            {latest.policyA.insurer.replace('Seguradora ', '')} ×{' '}
            {latest.policyB.insurer.replace('Seguradora ', '')}
          </strong>
          <small>{formatDateTime(latest.createdAt)}</small>
          {isComparisonBusy(latest.status) ? (
            <Badge tone="info" busy>
              Em processamento
            </Badge>
          ) : (
            latest.decisionMode && (
              <Badge tone="neutral">{DECISION_MODE_LABELS[latest.decisionMode]}</Badge>
            )
          )}
        </span>
        <Icon name="chevronRight" size={18} />
      </a>
    </section>
  );
}

export function HomePage() {
  return (
    <div className="page page--home">
      <section className="hero">
        <h1 className="hero__title">Compare apólices D&amp;O com clareza</h1>
        <p className="hero__subtitle">
          Envie os documentos, confira as evidências e veja as diferenças com pontuação explicável.
        </p>
        <div className="hero__actions">
          <a className="btn btn--primary btn--block" href={paths.compare()}>
            <Icon name="plus" size={20} />
            Nova comparação
          </a>
          <a className="btn btn--secondary btn--block" href={paths.newPolicy}>
            <Icon name="upload" size={20} />
            Adicionar apólice
          </a>
        </div>
      </section>

      <LatestComparison />

      <section aria-labelledby="how-title">
        <h2 id="how-title" className="section-title">
          Como funciona
        </h2>
        <ol className="steps">
          {STEPS.map((step, index) => (
            <li key={step.title} className="steps__item">
              <span className="steps__number" aria-hidden="true">
                {index + 1}
              </span>
              <Icon name={step.icon} size={24} className="steps__icon" />
              <div>
                <p className="steps__title">{step.title}</p>
                <p className="steps__text">{step.text}</p>
              </div>
            </li>
          ))}
        </ol>
      </section>

      <section aria-labelledby="principles-title">
        <h2 id="principles-title" className="section-title">
          Como o ClauseAI decide
        </h2>
        <ul className="principles">
          {PRINCIPLES.map((principle) => (
            <li key={principle.title} className="principles__item">
              <Icon name={principle.icon} size={22} />
              <div>
                <p className="principles__title">{principle.title}</p>
                <p className="principles__text">{principle.text}</p>
              </div>
            </li>
          ))}
        </ul>
      </section>

      <BrokerNotice reason="A análise depende dos documentos enviados e não é aconselhamento jurídico. Em caso de dúvida:" />
    </div>
  );
}
