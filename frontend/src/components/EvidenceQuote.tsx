import { evidenceLocation, useDocumentKinds } from '../shared/evidenceLocation';
import { METHOD_LABELS } from '../shared/labels';
import type { Evidence } from '../types/domain';

type EvidenceQuoteProps = {
  evidence: Evidence;
};

/** Trecho literal com fonte, cláusula, página (ou bloco, em DOCX), método de extração e confiança. */
export function EvidenceQuote({ evidence }: EvidenceQuoteProps) {
  const kinds = useDocumentKinds();
  const lowConfidence = evidence.confidence < 0.8;
  return (
    <figure className="evidence">
      <blockquote className="evidence__text">“{evidence.text}”</blockquote>
      <figcaption className="evidence__source">
        <span>{evidence.documentName}</span>
        <span>{evidence.clause}</span>
        <span>{evidenceLocation(evidence, kinds)}</span>
        <span className={lowConfidence ? 'evidence__confidence--low' : undefined}>
          {METHOD_LABELS[evidence.method]} · confiança {evidence.confidence.toLocaleString('pt-BR')}
        </span>
      </figcaption>
    </figure>
  );
}
