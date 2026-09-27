import { useState } from 'react';
import { Badge } from '../../components/Badge';
import { FilterChips } from '../../components/FilterChips';
import { EmptyState } from '../../components/StateViews';
import { DIFFERENCE_TONE_LABELS } from '../../shared/tones';
import type { Tone } from '../../components/Badge';
import type { ComparisonResult, Importance } from '../../types/domain';
import { ConceptComparisonCard } from './ConceptComparisonCard';

type ImportanceFilter = 'ALL' | Exclude<Importance, 'UNWEIGHTED'>;

const FILTERS: { value: ImportanceFilter; label: string }[] = [
  { value: 'ALL', label: 'Todos' },
  { value: 'CRITICAL', label: 'Crítica · 10' },
  { value: 'HIGH', label: 'Alta · 7' },
  { value: 'MEDIUM', label: 'Média · 4' },
  { value: 'LOW', label: 'Baixa · 2' },
];

const LEGEND: Tone[] = ['danger', 'high', 'medium', 'success', 'muted'];
const LEGEND_SHORT: Partial<Record<Tone, string>> = {
  danger: 'Crítica ou exclusão',
  high: 'Alta',
  medium: 'Média/baixa',
  success: 'Equivalente',
  muted: 'Não localizado',
};

export function ConceptsPanel({ comparison }: { comparison: ComparisonResult }) {
  const [filter, setFilter] = useState<ImportanceFilter>('ALL');
  const [onlyDifferences, setOnlyDifferences] = useState(false);

  const visible = comparison.items.filter(
    (item) =>
      (filter === 'ALL' || item.importance === filter) &&
      (!onlyDifferences || !item.verdict.startsWith('EQUIVALENT')),
  );

  return (
    <div className="stack">
      <FilterChips
        label="Filtrar por nível de importância"
        value={filter}
        onChange={setFilter}
        options={FILTERS.map((option) => ({
          ...option,
          count: comparison.items.filter(
            (item) => option.value === 'ALL' || item.importance === option.value,
          ).length,
        }))}
      />
      <label className="toggle">
        <input
          type="checkbox"
          checked={onlyDifferences}
          onChange={(event) => setOnlyDifferences(event.target.checked)}
        />
        Mostrar só diferenças e inconclusivos
      </label>

      <details className="legend">
        <summary>Legenda de cores</summary>
        <ul>
          {LEGEND.map((tone) => (
            <li key={tone}>
              <Badge tone={tone}>{LEGEND_SHORT[tone]}</Badge>
              <span>{DIFFERENCE_TONE_LABELS[tone]}</span>
            </li>
          ))}
        </ul>
        <p className="muted-text">
          “Não comprovado” nunca aparece em verde: menção nas condições gerais não é contratação.
        </p>
      </details>

      {visible.length ? (
        <ul className="stack" aria-label="Comparação por conceito">
          {visible.map((item) => (
            <ConceptComparisonCard
              key={item.conceptId}
              item={item}
              insurerA={comparison.policyA.insurer}
              insurerB={comparison.policyB.insurer}
            />
          ))}
        </ul>
      ) : (
        <EmptyState
          icon="search"
          title="Nenhum conceito neste filtro"
          text="Altere o nível de importância ou mostre todos os conceitos."
        />
      )}
    </div>
  );
}
