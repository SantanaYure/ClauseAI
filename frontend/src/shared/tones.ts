// Regras visuais da base de conhecimento (seção 8). Só mapeiam dados já calculados para cores;
// nenhuma regra de pontuação vive na interface.
import type { Tone } from '../components/Badge';
import type {
  ComparisonItem,
  ContractStatus,
  DocumentStatus,
  Importance,
  PolicyStatus,
} from '../types/domain';

/** Cor da linha do conceito conforme a importância da diferença. */
export function differenceTone(item: ComparisonItem): Tone {
  const sides = [item.a, item.b];
  if (sides.some((side) => side.contractStatus === 'EXCLUDED')) return 'danger';
  if (sides.every((side) => side.contractStatus === 'NOT_FOUND')) return 'muted';
  if (item.verdict === 'EQUIVALENT') return 'success';
  if (item.importance === 'CRITICAL') return 'danger';
  if (item.importance === 'HIGH') return 'high';
  return 'medium';
}

export const DIFFERENCE_TONE_LABELS: Record<Tone, string> = {
  danger: 'Diferença crítica, exclusão ou ausência relevante',
  high: 'Diferença de alta importância',
  medium: 'Diferença de média ou baixa importância',
  success: 'Equivalência ou vantagem documental comprovada',
  muted: 'Informação não localizada',
  info: '',
  neutral: '',
};

/** Verde só para contratação comprovada; menção sem contrato nunca fica verde. */
export function contractTone(status: ContractStatus): Tone {
  switch (status) {
    case 'CONTRACTED':
      return 'success';
    case 'EXCLUDED':
      return 'danger';
    case 'NOT_FOUND':
      return 'muted';
    case 'DIVERGENT':
      return 'medium';
    case 'NOT_PROVEN':
      return 'neutral';
  }
}

export function importanceTone(importance: Importance): Tone {
  switch (importance) {
    case 'CRITICAL':
      return 'danger';
    case 'HIGH':
      return 'high';
    case 'MEDIUM':
    case 'LOW':
      return 'medium';
    case 'UNWEIGHTED':
      return 'muted';
  }
}

export function policyStatusTone(status: PolicyStatus): Tone {
  switch (status) {
    case 'READY':
      return 'success';
    case 'ATTENTION':
      return 'medium';
    case 'PROCESSING':
      return 'info';
    case 'FAILED':
      return 'danger';
  }
}

export function documentStatusTone(status: DocumentStatus): Tone {
  if (status === 'COMPLETED') return 'success';
  if (status === 'FAILED') return 'danger';
  return 'info';
}
