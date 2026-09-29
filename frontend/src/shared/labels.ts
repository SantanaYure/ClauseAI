// Rótulos em português para as enumerações da base de conhecimento (seção 4).
import type {
  ContractStatus,
  DecisionMode,
  DocumentStatus,
  DocumentType,
  ExtractionMethod,
  FileKind,
  Importance,
  Level,
  PolicyStatus,
  RiskProfile,
  Verdict,
} from '../types/domain';

export const BROKER_GUIDANCE = 'Consulte seu corretor de seguros.';

export const IMPORTANCE_LABELS: Record<Importance, string> = {
  CRITICAL: 'Crítica',
  HIGH: 'Alta',
  MEDIUM: 'Média',
  LOW: 'Baixa',
  UNWEIGHTED: 'Sem peso',
};

export const CONTRACT_STATUS_LABELS: Record<ContractStatus, string> = {
  CONTRACTED: 'Contratada',
  NOT_PROVEN: 'Não comprovado',
  NOT_FOUND: 'Não localizado',
  EXCLUDED: 'Excluído',
  DIVERGENT: 'Divergente',
};

export const VERDICT_LABELS: Record<Verdict, string> = {
  FAVORS_A: 'Favorável à Apólice 01',
  FAVORS_B: 'Favorável à Apólice 02',
  EQUIVALENT: 'Equivalente',
  EQUIVALENT_BOTH_EXCLUDED: 'Equivalente – ambas excluídas',
  INCONCLUSIVE: 'Inconclusivo',
};

export const DOCUMENT_TYPE_LABELS: Record<DocumentType, string> = {
  POLICY: 'Apólice',
  GENERAL_CONDITIONS: 'Condições gerais',
  SPECIAL_CONDITIONS: 'Condições especiais',
  PARTICULAR_CONDITIONS: 'Condições particulares',
  ENDORSEMENT: 'Endosso',
  SPECIFICATION: 'Especificação',
  PROPOSAL: 'Proposta',
  OTHER: 'Outro',
};

export const DOCUMENT_STATUS_LABELS: Record<DocumentStatus, string> = {
  UPLOADED: 'Enviado',
  PROCESSING: 'Na fila',
  EXTRACTING: 'Extraindo',
  VALIDATING: 'Validando',
  COMPLETED: 'Processado',
  FAILED: 'Falhou',
  CANCELLED: 'Cancelado',
};

export const POLICY_STATUS_LABELS: Record<PolicyStatus, string> = {
  READY: 'Pronta para comparar',
  ATTENTION: 'Com alerta',
  PROCESSING: 'Processando',
  FAILED: 'Falhou',
  CANCELLED: 'Cancelada',
};

export const FILE_KIND_LABELS: Record<FileKind, string> = {
  SEARCHABLE_PDF: 'PDF pesquisável',
  SCANNED_PDF: 'PDF digitalizado',
  IMAGE: 'Imagem',
  DOCX: 'Documento Word',
};

export const METHOD_LABELS: Record<ExtractionMethod, string> = {
  NATIVE: 'Leitura nativa',
  OCR: 'OCR',
  MULTIMODAL: 'OCR multimodal',
};

export const LEVEL_LABELS: Record<Level, string> = {
  HIGH: 'Alta',
  MEDIUM: 'Média',
  LOW: 'Baixa',
};

export const PROFILE_LABELS: Record<RiskProfile, string> = {
  BASE: 'Geral (pesos-base)',
  FINANCIAL: 'Financeiro',
  INTERNATIONAL: 'Internacional',
  REGULATORY: 'Regulatório',
  TAIL: 'Cauda',
  LABOR_REPUTATIONAL: 'Trabalhista e reputacional',
};

export const DECISION_MODE_LABELS: Record<DecisionMode, string> = {
  TECHNICAL: 'Resultado técnico',
  CONDITIONED: 'Resultado condicionado',
};

export const POLICY_SLOT_LABELS = { A: 'Apólice 01', B: 'Apólice 02' } as const;
