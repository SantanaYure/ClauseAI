# A1 — Architecture Overview

## 1. Objetivo e escopo

O ClauseAI recebe documentos de apólice D&O, armazena o original, extrai evidências com leitura nativa de PDF, leitura local de DOCX ou OCR/IA multimodal (imagem e PDF digitalizado), normaliza essas evidências contra o catálogo de conceitos D&O, persiste dados estruturados, compara duas apólices conceito a conceito, calcula pontuação ponderada e apresenta um resumo executivo condicionado e rastreável. As regras de domínio vêm de [`domain/DO_KNOWLEDGE_BASE.md`](../domain/DO_KNOWLEDGE_BASE.md). O MVP privilegia execução local simples, baixa acoplagem e capacidade de substituir provedores externos sem alterar o domínio.

### Requisitos funcionais

| ID | Requisito |
|---|---|
| RF-01 | Aceitar PDF, imagens (JPG, PNG) e DOCX, com o tipo detectado pelo conteúdo, e registrar tipo de documento, seguradora, versão e vigência. |
| RF-02 | Armazenar original, metadados, status e histórico de processamento. |
| RF-03 | Processar fora do ciclo da requisição de upload. |
| RF-04 | Extrair conteúdo por leitura nativa (PDF, DOCX) ou OCR (imagem, PDF digitalizado), com evidências literais (página ou seção/bloco, cláusula, confiança). DOCX nunca usa OCR. |
| RF-05 | Normalizar evidências contra o catálogo D&O, classificando tipo de ocorrência, relação terminológica e status. |
| RF-06 | Consultar documentos, apólices e evidências por conceito, variante, seguradora, cláusula, página, peso e status. |
| RF-07 | Comparar exatamente duas apólices com os mesmos conceitos, critérios e pesos. |
| RF-08 | Calcular Pontos Ponderados, Score de Aderência, Score Documental e Índice de Completude. |
| RF-09 | Calcular decisão por perfil de risco com pesos ajustados, preservando os pesos-base. |
| RF-10 | Gerar resumo executivo condicionado, separado da análise documental. |
| RF-11 | Exibir evidência, avaliação, pontuação e recomendação em camadas distintas, com alertas e “Consulte seu corretor de seguros.” |
| RF-12 | Expor falhas recuperáveis, correlação e status do processamento. |

### Requisitos não funcionais

- **Simplicidade:** monólito modular, uma base de código, Event Bus em memória e um processo de worker no MVP.
- **Rastreabilidade:** cada valor extraído referencia documento, página, trecho, modelo e prompt.
- **Explicabilidade:** resultados não suportados por evidência ficam nulos ou marcados como ambíguos; toda pontuação diferente de 1,00 tem justificativa.
- **Reprodutibilidade:** mesma entrada, mesma versão da base de conhecimento e mesmas avaliações produzem os mesmos scores.
- **Resiliência:** timeout, retry limitado e estado `FAILED` explícito.
- **Segurança:** segredos apenas em variáveis de ambiente/secret manager; arquivos tratados como dados não confiáveis.
- **Testabilidade:** interfaces para storage, repositórios, relógio, IDs, IA e Event Bus.
- **Evolução:** providers, storage e barramento externo podem ser adicionados por adaptadores.

## 2. Visão de contexto

```mermaid
flowchart LR
    U[Usuário / Analista] --> FE[Web app React]
    FE --> API[FastAPI]
    API --> APP[Application Layer]
    APP --> DOM[Domain Layer]
    APP --> BUS[Event Bus interno]
    BUS --> WORKER[Worker assíncrono do monólito]
    WORKER --> KB[Catálogo D&O / pesos]
    WORKER --> SCORE[Scoring Service]
    WORKER --> AI[AI Orchestrator]
    AI --> GEM[Gemini 3.5 Flash Lite: extração, avaliação e conclusão]
    WORKER --> REPO[Repositories]
    REPO --> FS[(Firestore)]
    REPO --> ST[(Firebase Storage)]
    APP --> OBS[Logs / métricas]
```

## 3. Componentes e responsabilidades

| Componente | Responsabilidade | Não deve fazer |
|---|---|---|
| React UI | Interação, estado de tela e renderização | Acessar Firebase ou providers de IA diretamente |
| FastAPI | Serializar entrada/saída, autenticar no futuro, mapear erros | Executar regra de negócio ou chamada longa de IA |
| Application | Orquestrar casos de uso, transações lógicas e publicação de eventos | Conhecer detalhes de HTTP, Firestore ou SDKs de IA |
| Domain | Entidades, value objects, invariantes e comparação determinística | Importar FastAPI, Firebase ou Gemini |
| Document Service (agente de recepção) | Validar arquivo, classificar tipo de documento, persistir original e iniciar processamento | Interpretar cláusulas |
| Extraction Service (agente de OCR/extração) | Leitura nativa de PDF, leitura local de DOCX (sem OCR), OCR multimodal, parsing e validação de evidências | Completar texto ilegível por inferência |
| Normalization Service (agente de cláusulas) | Vincular evidências a conceitos do catálogo e classificar ocorrência/relação/status | Unir conceitos distintos ou declarar equivalência automática |
| Policy Service (agente de estruturação) | Construir e persistir estrutura de apólice e ocorrências | Fazer chamadas externas diretamente |
| Knowledge Base | Fornecer catálogo, variantes, pesos, escalas e perfis versionados | Ser alterada pela IA |
| Comparison Service (agente comparador) | Comparação determinística e avaliação por conceito via IA | Ocultar diferenças factuais |
| Scoring Service | Calcular pontos, scores, completude, pareceres e perfis de forma determinística | Chamar LLM ou alterar pesos silenciosamente |
| Report Service (agente de relatório) | Montar resumo executivo e tabela final com números já calculados | Criar fatos ou números novos |
| Quality Gate | Executar o checklist do prompt 16 antes de marcar a comparação como concluída | Esconder limitações |
| AI Orchestrator | Roteamento, prompts, schemas, timeout, retry, logs e providers | Ser fonte de regra de negócio |
| Repositories | Persistência por contratos pequenos | Vazar objetos do SDK para domínio |
| Event Bus | Publicar e consumir eventos internos | Ser banco de dados ou garantir entrega durável |
| Worker | Consumir eventos e executar operações demoradas | Misturar handlers ou assumir contexto global mutável |

## 4. Dependências e direção

```text
presentation -> application -> domain
infrastructure -> application/domain interfaces
shared -> usado transversalmente, sem regra de negócio
```

O domínio depende apenas de tipos e interfaces próprias. A infraestrutura implementa `DocumentRepository`, `PolicyRepository`, `ComparisonRepository`, `BlobStorage`, `AIProvider` e `EventBus`. FastAPI é um adaptador de entrada/saída.

## 5. Fluxo de processamento de apólice

```mermaid
sequenceDiagram
    actor User as Usuário
    participant UI as React
    participant API as FastAPI
    participant App as UploadDocumentUseCase
    participant Blob as Firebase Storage
    participant Bus as Event Bus
    participant Worker as Worker
    participant AI as AI Orchestrator
    participant DB as Firestore

    User->>UI: Seleciona PDF, imagem ou DOCX
    UI->>API: POST /documents
    API->>App: UploadDocumentCommand
    App->>Blob: grava original
    App->>DB: metadados/status=UPLOADED
    App->>Bus: DocumentUploaded
    API-->>UI: 202 document_id/status
    Bus->>Worker: StartDocumentProcessingHandler
    Worker->>DB: status=PROCESSING/EXTRACTING
    Worker->>AI: extract_policy(document)
    AI-->>Worker: ExtractionResult + evidências
    Worker->>DB: raw result + política validada
    Worker->>Bus: PolicyStored ou ProcessingFailed
    UI->>API: GET /documents/{id}/status
    API-->>UI: estado atual + erro opcional
```

## 6. Fluxo de comparação

```mermaid
sequenceDiagram
    actor User as Usuário
    participant UI as React
    participant API as FastAPI
    participant App as ComparePoliciesUseCase
    participant Bus as Event Bus
    participant Det as ComparisonService
    participant AI as AI Orchestrator
    participant DB as Firestore

    User->>UI: Seleciona policy_a e policy_b
    UI->>API: POST /comparisons
    API->>App: ComparePoliciesCommand
    App->>DB: cria Comparison/PROCESSING
    App->>Bus: ComparisonRequested
    API-->>UI: 202 comparison_id
    Bus->>Det: RunDeterministicComparisonHandler
    Det->>DB: grava itens determinísticos
    Det->>Bus: DeterministicComparisonCompleted
    Bus->>AI: AssessConceptsHandler (P-ASSESS-001)
    AI-->>Bus: Resultado-base, Fator de Ajuste e justificativas por conceito
    Bus->>DB: grava avaliações validadas
    Bus->>Det: CalculateScoresHandler (ScoringService)
    Det->>DB: pontos, scores, completude, pareceres e perfis
    Bus->>AI: GenerateExecutiveSummaryHandler (P-EXECUTIVE-001)
    AI-->>Bus: resumo executivo condicionado
    Bus->>DB: Quality Gate + status=COMPLETED
    UI->>API: GET /comparisons/{id}
    API-->>UI: fatos, avaliações, scores e resumo
```

## 7. Eventos do MVP

Todos implementam o envelope comum:

```json
{
  "event_id": "evt_01",
  "event_type": "DocumentUploaded",
  "event_version": 1,
  "occurred_at": "2026-09-20T12:00:00Z",
  "correlation_id": "cor_01",
  "entity_id": "doc_01",
  "payload": {}
}
```

| Evento | Produtor | Consumidor principal | Payload mínimo |
|---|---|---|---|
| `DocumentUploaded` | Upload use case | `StartDocumentProcessingHandler` | `document_id`, `storage_key`, `content_type` |
| `DocumentValidated` | Document handler | próximo passo do pipeline | `document_id`, `validation` |
| `DocumentProcessingStarted` | Processing handler | observabilidade/UI | `document_id`, `processing_id` |
| `ExtractionRequested` | Processing handler | `ExtractPolicyHandler` | `document_id`, `processing_id` |
| `ExtractionCompleted` | Extraction handler | `PersistPolicyHandler` | `document_id`, `extraction_result_id` |
| `ExtractionFailed` | Extraction handler | falha/retentativa | `document_id`, `error_code`, `retryable` |
| `PolicyStructured` | Validation handler | persistência | `policy_id`, `document_id`, `schema_version` |
| `PolicyStored` | Policy handler | UI/observabilidade | `policy_id`, `document_id` |
| `ComparisonRequested` | Comparison use case | determinístico | `comparison_id`, `policy_ids[2]` |
| `EvidenceNormalized` | Normalization handler | persistência | `policy_id`, `occurrence_count`, `knowledge_base_version` |
| `DeterministicComparisonCompleted` | Comparison handler | avaliação | `comparison_id`, `item_count` |
| `ConceptAssessmentCompleted` | Assessment handler | pontuação | `comparison_id`, `assessed_count`, `inconclusive_count` |
| `ScoringCompleted` | Scoring handler | resumo executivo | `comparison_id`, `score_a`, `score_b`, `completeness_a`, `completeness_b` |
| `ExecutiveSummaryCompleted` | Report handler | finalização | `comparison_id`, `summary_id` |
| `ComparisonCompleted` | Finalização | UI/observabilidade | `comparison_id` |
| `ProcessingFailed` | qualquer handler | UI/observabilidade | `entity_type`, `entity_id`, `error_code` |

O contrato detalhado, incluindo versionamento e idempotência, está em [`specs/SDD_SPECIFICATIONS.md`](../specs/SDD_SPECIFICATIONS.md).

## 8. Assíncrono no monólito

O endpoint devolve `202 Accepted` depois de persistir o documento e publicar `DocumentUploaded`. Um worker no mesmo repositório consome o `InMemoryEventBus`. A implementação pode começar com `asyncio.Queue` e uma tarefa de ciclo de vida do processo; a interface não deve impedir a substituição por Cloud Tasks ou outro executor no futuro.

O Event Bus em memória não é durável. Portanto, o estado mínimo é persistido antes de publicar e cada handler deve poder ser reexecutado com segurança. Se o processo cair entre publicação e consumo, um comando administrativo ou uma rotina futura poderá reenfileirar jobs `UPLOADED`/`PROCESSING`.

## 9. Decisões principais

- Monólito modular para reduzir operação e permitir desenvolvimento por uma pessoa.
- Firestore como persistência documental simples e Storage para binários.
- IA isolada por `AIOrchestrator` e portas `ExtractionProvider`/`ComparisonProvider`.
- Comparação determinística antes da avaliação por IA para separar fatos de interpretação.
- IA propõe Resultado-base e Fator de Ajuste dentro de escalas fechadas; o backend calcula todos os números.
- Catálogo, pesos e perfis versionados como base de conhecimento, fora do código e dos prompts.
- Arquitetura multiagente sugerida pelo desafio mapeada em serviços do monólito, não em processos separados.
- Eventos internos apenas onde há trabalho demorado ou desacoplamento real.
- Pontos não definidos pelas bases continuam `PENDING_BUSINESS_VALIDATION`.

Ver detalhes em [`adrs/ADRS.md`](../adrs/ADRS.md).
