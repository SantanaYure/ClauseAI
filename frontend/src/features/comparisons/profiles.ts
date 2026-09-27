import type { RiskProfile } from '../../types/domain';

/** Descrições dos perfis de risco (base de conhecimento, seção 7.1). */
export const PROFILE_DESCRIPTIONS: Record<RiskProfile, string> = {
  BASE: 'Usa os pesos-base da matriz, sem priorização.',
  FINANCIAL: 'Prioriza LMG, Garantia A, Garantia B e Custos de Defesa.',
  INTERNATIONAL:
    'Prioriza Territorialidade, Processos no Exterior, Retroatividade e prazos pós-vigência.',
  REGULATORY:
    'Prioriza Investigação, Multas e Penalidades, Responsabilidade Tributária e Ambiental.',
  TAIL: 'Prioriza Retroatividade, Cláusula de Notificação, Prazo Complementar e Suplementar.',
  LABOR_REPUTATIONAL:
    'Prioriza Práticas Trabalhistas, Danos Morais, Proteção de Imagem, Gerenciamento de Crise e Custos de Defesa.',
};

export const PROFILE_ORDER: RiskProfile[] = [
  'BASE',
  'FINANCIAL',
  'INTERNATIONAL',
  'REGULATORY',
  'TAIL',
  'LABOR_REPUTATIONAL',
];
