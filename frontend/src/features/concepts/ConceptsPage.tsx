import { useState, type FormEvent } from 'react';
import { paths } from '../../app/router';
import { Badge } from '../../components/Badge';
import { FilterChips } from '../../components/FilterChips';
import { Icon } from '../../components/Icon';
import { PageHeader } from '../../components/PageHeader';
import { EmptyState, ErrorState, LoadingState } from '../../components/StateViews';
import { clauseApi } from '../../services/api/clause-api';
import { IMPORTANCE_LABELS } from '../../shared/labels';
import { normalizeText } from '../../shared/text';
import { importanceTone } from '../../shared/tones';
import { useApiData } from '../../shared/useApiData';
import type { Concept, Importance, QueryAnswer } from '../../types/domain';
import { QueryAnswerCard } from './QueryAnswerCard';

type Filter = 'ALL' | Importance;

const FILTERS: { value: Filter; label: string }[] = [
  { value: 'ALL', label: 'Todos' },
  { value: 'CRITICAL', label: 'Crítica' },
  { value: 'HIGH', label: 'Alta' },
  { value: 'MEDIUM', label: 'Média' },
  { value: 'LOW', label: 'Baixa' },
  { value: 'UNWEIGHTED', label: 'Sem peso' },
];

const SUGGESTIONS = [
  'Quais apólices cobrem multas?',
  'Qual é o LMG?',
  'Retroatividade',
  'Segurado contra segurado',
];

function matchesConcept(concept: Concept, term: string): boolean {
  const normalized = normalizeText(term);
  if (!normalized) return true;
  return [concept.id, concept.name, concept.domain, ...concept.variants].some((value) =>
    normalizeText(value).includes(normalized),
  );
}

export function ConceptsPage({ initialQuery }: { initialQuery?: string }) {
  const state = useApiData('concepts', () => clauseApi.listConcepts());
  const [query, setQuery] = useState(initialQuery ?? '');
  const [filter, setFilter] = useState<Filter>('ALL');
  const [answer, setAnswer] = useState<QueryAnswer | null>(null);
  const [asking, setAsking] = useState(false);

  const ask = async (question: string) => {
    if (!question.trim()) return;
    setAsking(true);
    try {
      setAnswer(await clauseApi.ask(question.trim()));
    } finally {
      setAsking(false);
    }
  };

  const onSubmit = (event: FormEvent) => {
    event.preventDefault();
    void ask(query);
  };

  return (
    <div className="page">
      <PageHeader
        title="Conceitos"
        subtitle="Consulte o catálogo D&O e pergunte sobre as apólices armazenadas. As respostas usam só evidências dos documentos."
      />

      <form className="ask" onSubmit={onSubmit} role="search">
        <label htmlFor="ask-input" className="visually-hidden">
          Pergunte ou busque um conceito
        </label>
        <Icon name="search" size={20} />
        <input
          id="ask-input"
          type="search"
          value={query}
          onChange={(event) => {
            setQuery(event.target.value);
            setAnswer(null);
          }}
          placeholder="Pergunte ou busque um conceito"
        />
        <button
          type="submit"
          className="btn btn--primary btn--compact"
          disabled={!query.trim() || asking}
        >
          <Icon name="send" size={18} />
          <span>Perguntar</span>
        </button>
      </form>

      {!query && (
        <div className="suggestions" aria-label="Sugestões de consulta">
          {SUGGESTIONS.map((suggestion) => (
            <button
              key={suggestion}
              type="button"
              className="chip"
              onClick={() => {
                setQuery(suggestion);
                void ask(suggestion);
              }}
            >
              {suggestion}
            </button>
          ))}
        </div>
      )}

      {asking && <LoadingState label="Consultando evidências…" />}
      {answer && !asking && <QueryAnswerCard answer={answer} />}

      {state.status === 'loading' && <LoadingState label="Carregando catálogo…" />}
      {state.status === 'error' && <ErrorState message={state.message} onRetry={state.reload} />}
      {state.status === 'success' && (
        <Catalog
          concepts={state.data}
          query={answer ? '' : query}
          filter={filter}
          onFilter={setFilter}
        />
      )}
    </div>
  );
}

type CatalogProps = {
  concepts: Concept[];
  query: string;
  filter: Filter;
  onFilter: (filter: Filter) => void;
};

function Catalog({ concepts, query, filter, onFilter }: CatalogProps) {
  const weighted = concepts.filter((concept) => concept.weight !== null);
  const totalWeight = weighted.reduce((sum, concept) => sum + (concept.weight ?? 0), 0);
  const visible = concepts
    .filter(
      (concept) =>
        (filter === 'ALL' || concept.importance === filter) && matchesConcept(concept, query),
    )
    .sort((x, y) => (y.weight ?? 0) - (x.weight ?? 0) || x.id.localeCompare(y.id));

  return (
    <section aria-labelledby="catalog-title" className="stack">
      <div>
        <h2 id="catalog-title" className="section-title">
          Catálogo D&amp;O
        </h2>
        <p className="muted-text">
          {concepts.length} conceitos · {weighted.length} com peso · soma dos pesos {totalWeight}
        </p>
      </div>
      <FilterChips
        label="Filtrar por importância"
        value={filter}
        onChange={onFilter}
        options={FILTERS.map((option) => ({
          ...option,
          count: concepts.filter(
            (concept) => option.value === 'ALL' || concept.importance === option.value,
          ).length,
        }))}
      />
      {visible.length ? (
        <ul className="list">
          {visible.map((concept) => (
            <li key={concept.id}>
              <a className="list-link" href={paths.concept(concept.id)}>
                <span className="list-link__body">
                  <strong>{concept.name}</strong>
                  <small>
                    {concept.id} · {concept.domain}
                    {concept.pendingValidation ? ' · variantes em validação' : ''}
                  </small>
                </span>
                <Badge tone={importanceTone(concept.importance)}>
                  {concept.weight
                    ? `${IMPORTANCE_LABELS[concept.importance]} · ${concept.weight}`
                    : 'Sem peso'}
                </Badge>
                <Icon name="chevronRight" size={18} />
              </a>
            </li>
          ))}
        </ul>
      ) : (
        <EmptyState
          icon="book"
          title="Nenhum conceito encontrado"
          text="Tente um sinônimo ou toque em Perguntar para consultar as apólices."
        />
      )}
    </section>
  );
}
