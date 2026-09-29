// Contratos de dados do frontend, derivados de docs/architecture/PERSISTENCE_AND_API.md
// e das enumerações de docs/domain/DO_KNOWLEDGE_BASE.md (seção 4).

export type ConceptId = `DO-${string}`;

export type Importance = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'UNWEIGHTED';

export type ContractStatus = 'CONTRACTED' | 'NOT_PROVEN' | 'NOT_FOUND' | 'EXCLUDED' | 'DIVERGENT';

export type Verdict =
  'FAVORS_A' | 'FAVORS_B' | 'EQUIVALENT' | 'EQUIVALENT_BOTH_EXCLUDED' | 'INCONCLUSIVE';

export type DocumentType =
  | 'POLICY'
  | 'GENERAL_CONDITIONS'
  | 'SPECIAL_CONDITIONS'
  | 'PARTICULAR_CONDITIONS'
  | 'ENDORSEMENT'
  | 'SPECIFICATION'
  | 'PROPOSAL'
  | 'OTHER';

export type FileKind = 'SEARCHABLE_PDF' | 'SCANNED_PDF' | 'IMAGE';

export type DocumentStatus =
  'UPLOADED' | 'PROCESSING' | 'EXTRACTING' | 'VALIDATING' | 'COMPLETED' | 'FAILED';

export type PolicyStatus = 'READY' | 'ATTENTION' | 'PROCESSING' | 'FAILED';

export type ExtractionMethod = 'NATIVE' | 'OCR' | 'MULTIMODAL';

export type Level = 'HIGH' | 'MEDIUM' | 'LOW';

export type RiskProfile =
  'BASE' | 'FINANCIAL' | 'INTERNATIONAL' | 'REGULATORY' | 'TAIL' | 'LABOR_REPUTATIONAL';

export type DecisionMode = 'TECHNICAL' | 'CONDITIONED';

export type Concept = {
  id: ConceptId;
  domain: string;
  name: string;
  variants: string[];
  importance: Importance;
  weight: number | null;
  justification?: string;
  criterion: string;
  related: ConceptId[];
  humanReview: 'REQUIRED' | 'RECOMMENDED';
  pendingValidation: boolean;
};

export type Evidence = {
  id: string;
  documentId: string;
  documentName: string;
  page: number;
  clause: string;
  text: string;
  method: ExtractionMethod;
  confidence: number;
};

export type PolicyDocument = {
  id: string;
  filename: string;
  type: DocumentType;
  fileKind: FileKind;
  pages: number;
  status: DocumentStatus;
  extractionQuality: Level | null;
  ocrRequired: boolean;
};

export type LimitBasis = 'AGGREGATE' | 'PER_CLAIM' | 'PER_CLAIM_AND_AGGREGATE';

// Ocorrência extraída; Resultado-base e Fator de Ajuste só existem na comparação.
export type ConceptOccurrence = {
  conceptId: ConceptId;
  term: string;
  contractStatus: ContractStatus;
  justification?: string | null;
  evidence: Evidence[];
  confidence: Level;
  limitBasis?: LimitBasis;
  amount?: string;
};

export type PolicySummary = {
  id: string;
  insurer: string;
  name: string;
  number: string | null;
  validity: string | null;
  status: PolicyStatus;
  documents: PolicyDocument[];
  alerts: string[];
};

export type PolicyDetail = PolicySummary & {
  occurrences: ConceptOccurrence[];
};

export type ComparisonSide = {
  term: string;
  contractStatus: ContractStatus;
  baseResult: number;
  adjustmentFactor: number;
  points: number;
  justification?: string;
  evidence: Evidence[];
  sufficientEvidence: boolean;
  amount?: string;
};

export type ComparisonItem = {
  conceptId: ConceptId;
  conceptName: string;
  importance: Importance;
  weight: number;
  a: ComparisonSide;
  b: ComparisonSide;
  mainDifference: string;
  verdict: Verdict;
  confidence: Level;
  guidance: boolean;
};

export type ScoreSummary = {
  raw: number;
  max: number;
  adherence: number;
  documentary: number;
  completeness: number;
  criticalUnconfirmedWeight: number;
  inconclusiveWeight: number;
  favorable: number;
  equivalent: number;
  inconclusive: number;
};

export type ProfileResult = {
  profile: RiskProfile;
  prioritized: ConceptId[];
  multiplier: number;
  a: ScoreSummary;
  b: ScoreSummary;
  winner: 'A' | 'B' | 'TIE';
  decisiveConcepts: string[];
  sensitivity: 'ROBUST' | 'SENSITIVE';
  limitations: string[];
};

export type QualityCheck = {
  id: string;
  label: string;
  passed: boolean;
  detail: string;
};

export type ExecutiveSummary = {
  decisionMode: DecisionMode;
  highestScore: 'A' | 'B' | 'TIE';
  advantagesA: string[];
  advantagesB: string[];
  equivalentCritical: string[];
  highestImpact: string[];
  attentionPoints: string[];
  scoreVsQualitative: string | null;
  conclusion: string;
};

// Estados de docs/architecture/PERSISTENCE_AND_API.md (GET /comparisons/{id}).
export type ComparisonStatus =
  | 'REQUESTED'
  | 'DETERMINISTIC_COMPLETED'
  | 'ASSESSING'
  | 'SCORED'
  | 'SUMMARIZING'
  | 'COMPLETED'
  | 'PARTIAL'
  | 'FAILED';

export type ApiFailure = {
  code: string;
  message: string;
};

export type ComparisonPolicyRef = {
  id: string;
  insurer: string;
  name: string;
};

export type ComparisonResult = {
  id: string;
  createdAt: string;
  status: ComparisonStatus;
  knowledgeBaseVersion: string;
  selectedProfile: RiskProfile;
  policyA: ComparisonPolicyRef;
  policyB: ComparisonPolicyRef;
  items: ComparisonItem[];
  profiles: ProfileResult[];
  summary: ExecutiveSummary | null;
  qualityGate: QualityCheck[];
  failure: ApiFailure | null;
};

export type ComparisonListItem = {
  id: string;
  createdAt: string;
  status: ComparisonStatus;
  policyA: ComparisonPolicyRef;
  policyB: ComparisonPolicyRef;
  adherenceA: number | null;
  adherenceB: number | null;
  decisionMode: DecisionMode | null;
  failureReason?: string;
};

export type ConceptWithOccurrences = Concept & {
  occurrences: { policy: ComparisonPolicyRef; occurrence: ConceptOccurrence }[];
};

export type QueryAnswer = {
  question: string;
  concept: Concept | null;
  answer: string;
  matches: { policy: ComparisonPolicyRef; occurrence: ConceptOccurrence | null }[];
  guidance: boolean;
};

export type UploadFile = {
  file: File;
  type: DocumentType;
};

export type NewPolicyInput = {
  insurer: string;
  name: string;
  files: UploadFile[];
};
