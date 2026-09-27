import { paths } from '../../app/router';
import { Badge } from '../../components/Badge';
import { BrokerNotice } from '../../components/BrokerNotice';
import { EvidenceQuote } from '../../components/EvidenceQuote';
import { CONTRACT_STATUS_LABELS, IMPORTANCE_LABELS } from '../../shared/labels';
import { contractTone } from '../../shared/tones';
import type { QueryAnswer } from '../../types/domain';

/** Resposta à consulta (SPEC-018): só evidências armazenadas, com fonte e orientação. */
export function QueryAnswerCard({ answer }: { answer: QueryAnswer }) {
  const { concept } = answer;
  return (
    <section className="card answer" aria-live="polite" aria-labelledby="answer-title">
      <p className="muted-text">Pergunta: “{answer.question}”</p>
      <h2 id="answer-title" className="section-title">
        {concept ? concept.name : 'Sem correspondência na base'}
      </h2>
      {concept && (
        <p className="muted-text">
          {concept.id} · {IMPORTANCE_LABELS[concept.importance]}
          {concept.weight ? ` · peso ${concept.weight}` : ''} ·{' '}
          <a href={paths.concept(concept.id)}>ver conceito</a>
        </p>
      )}

      {answer.matches.length > 0 && (
        <ul className="stack">
          {answer.matches.map(({ policy, occurrence }) => (
            <li key={policy.id} className="answer__match">
              <div className="occurrence__header">
                <a href={paths.policy(policy.id)}>
                  <strong>{policy.insurer}</strong>
                </a>
                <Badge tone={occurrence ? contractTone(occurrence.contractStatus) : 'muted'}>
                  {occurrence
                    ? CONTRACT_STATUS_LABELS[occurrence.contractStatus]
                    : 'Não localizado'}
                </Badge>
              </div>
              {occurrence ? (
                <>
                  <p>
                    <span className="muted-text">Termo: </span>
                    {occurrence.term}
                  </p>
                  {occurrence.justification && (
                    <p className="muted-text">{occurrence.justification}</p>
                  )}
                  {occurrence.evidence.map((evidence) => (
                    <EvidenceQuote key={evidence.id} evidence={evidence} />
                  ))}
                </>
              ) : (
                <p className="muted-text">Não localizado não significa excluído.</p>
              )}
            </li>
          ))}
        </ul>
      )}

      {answer.guidance ? (
        <BrokerNotice
          reason={
            concept
              ? 'Há ausência, menção sem contratação ou exclusão em pelo menos uma apólice.'
              : 'A consulta não pôde ser respondida com as evidências armazenadas.'
          }
        />
      ) : (
        <p className="muted-text">Contratação comprovada nas apólices consultadas.</p>
      )}
    </section>
  );
}
