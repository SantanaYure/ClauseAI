// Regras visuais da base de conhecimento (seção 8). Só mapeiam dados já calculados para cores;
// nenhuma regra de pontuação vive na interface.
import type { Tone } from '../components/Badge';
import type { IconName } from '../components/Icon';
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

// Status de processamento usam só azul ou neutro (SPEC-010); verde, amarelo, laranja e vermelho
// ficam reservados aos resultados da comparação. O ícone e o texto carregam o significado.
export function policyStatusTone(status: PolicyStatus): Tone {
  return status === 'READY' || status === 'PROCESSING' ? 'info' : 'neutral';
}

export function policyStatusIcon(status: PolicyStatus): IconName | undefined {
  switch (status) {
    case 'READY':
      return 'checkCircle';
    case 'ATTENTION':
    case 'FAILED':
      return 'alert';
    case 'CANCELLED':
      return 'x';
    case 'PROCESSING':
      return undefined;
  }
}

export function documentStatusTone(status: DocumentStatus): Tone {
  return status === 'FAILED' || status === 'CANCELLED' ? 'neutral' : 'info';
}

export function documentStatusIcon(status: DocumentStatus): IconName | undefined {
  if (status === 'COMPLETED') return 'checkCircle';
  if (status === 'FAILED') return 'alert';
  if (status === 'CANCELLED') return 'x';
  return undefined;
}
