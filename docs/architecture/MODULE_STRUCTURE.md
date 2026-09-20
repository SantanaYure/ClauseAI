# A2 — Estrutura de módulos

## 1. Estrutura proposta

```text
ClauseAI/
├── backend/
│   ├── app/
│   │   ├── domain/
│   │   │   ├── entities/
│   │   │   ├── value_objects/
│   │   │   ├── services/
│   │   │   └── interfaces/
│   │   ├── application/
│   │   │   ├── commands/
│   │   │   ├── queries/
│   │   │   ├── use_cases/
│   │   │   ├── dto/
│   │   │   └── handlers/
│   │   ├── infrastructure/
│   │   │   ├── firebase/
│   │   │   ├── repositories/
│   │   │   ├── storage/
│   │   │   ├── ai/
│   │   │   │   ├── gemini/
│   │   │   │   ├── groq/
│   │   │   │   └── prompts/
│   │   │   └── event_bus/
│   │   ├── presentation/
│   │   │   └── api/
│   │   │       ├── routes/
│   │   │       ├── schemas/
│   │   │       └── error_handlers/
│   │   └── shared/
│   │       ├── config/
│   │       ├── errors/
│   │       ├── logging/
│   │       ├── clock/
│   │       └── ids/
│   ├── tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   ├── contract/
│   │   └── fixtures/
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   ├── features/
│   │   │   ├── documents/
│   │   │   ├── policies/
│   │   │   └── comparisons/
│   │   ├── services/
│   │   ├── types/
│   │   ├── styles/
│   │   └── shared/
│   ├── tests/
│   └── package.json
├── docs/
└── README.md
```

## 2. Camadas do backend

### `domain`

Contém entidades, value objects, invariantes e serviços puros. Não importa FastAPI, Pydantic de entrada, Firebase, SDKs de IA ou variáveis de ambiente. Pydantic pode ser usado apenas se o contrato não acoplar o domínio à camada HTTP; caso contrário, usar dataclasses/tipos de domínio e DTOs separados.

### `application`

Implementa casos de uso e coordena portas. Commands representam intenção de mudança; queries representam leitura; handlers consomem eventos. Essa camada decide a ordem das chamadas e os estados, mas não conhece detalhes do SDK.

### `infrastructure`

Implementa contratos com Firebase, Storage, Gemini, Groq e Event Bus. Conversões entre modelos externos e modelos internos ficam aqui. Cada provider registra nome, versão e métricas sem vazar resposta bruta para o domínio.

### `presentation`

Mapeia HTTP para commands/queries e resultados para schemas de resposta. Os endpoints não devem conter loops de comparação, prompts ou regras de transição de processamento.

### `shared`

Utilitários transversais pequenos: configuração tipada, erros, logger, relógio injetável e gerador de IDs. Não deve se tornar um “módulo de tudo”.

## 3. Portas mínimas

```text
BlobStorage
  put(stream, content_type, metadata) -> StorageObject
  get(storage_key) -> BinaryStream

DocumentRepository
  create(document)
  get(document_id)
  update_status(document_id, status, reason?)

PolicyRepository
  upsert(policy)
  get(policy_id)
  list(filters)

ComparisonRepository
  create(comparison)
  update(comparison)
  get(comparison_id)

AIOrchestrator
  extract_policy(document_context) -> ExtractionResult
  compare_policies(deterministic_result, policies) -> SemanticResult
  explain_comparison(comparison) -> Explanation

EventBus
  publish(event)
  subscribe(event_type, handler)

Clock
  now_utc()
```

Evitar criar interfaces para classes puras, formatadores locais ou componentes sem uma segunda implementação provável. Interfaces acima existem porque isolam infraestrutura externa, efeitos colaterais ou execução assíncrona.

## 4. Handlers

Cada handler recebe um evento, carrega o mínimo necessário, executa uma ação e publica o próximo evento. Deve ser pequeno, idempotente e observável.

| Handler | Ação |
|---|---|
| `StartDocumentProcessingHandler` | valida disponibilidade do arquivo, cria `ProcessingJob` e publica início/extração |
| `ExtractPolicyHandler` | lê arquivo, chama `AIOrchestrator.extract_policy`, grava resultado bruto |
| `ValidateExtractionHandler` | valida schema, normaliza valores e gera `PolicyStructured` ou falha |
| `PersistPolicyHandler` | faz upsert idempotente da apólice e publica `PolicyStored` |
| `RunDeterministicComparisonHandler` | carrega duas apólices e gera fatos comparáveis |
| `RunSemanticComparisonHandler` | envia fatos e evidências ao Groq e grava interpretação |
| `CompleteComparisonHandler` | consolida estados e publica `ComparisonCompleted` |
| `ProcessingFailureHandler` | registra erro, tentativa e estado final/retry agendável |

## 5. Frontend

- `features/documents`: upload, lista, status e polling controlado.
- `features/policies`: leitura de dados estruturados e evidências.
- `features/comparisons`: seleção de exatamente duas apólices, tabela factual e explicação semântica.
- `services/api-client`: único ponto de comunicação com REST.
- `types`: tipos derivados dos contratos públicos, sem replicar regras de domínio.
- `components`: componentes de apresentação reutilizáveis sem chamadas de API ocultas.

O frontend não chama Firebase, Gemini ou Groq. Polling de status deve parar em `COMPLETED` ou `FAILED`, ter intervalo limitado e exibir `correlation_id` quando houver erro.

## 6. Regras de dependência

1. `domain` não importa nenhum módulo externo de infraestrutura.
2. `application` depende de interfaces do domínio, nunca de implementações concretas.
3. `presentation` depende de application DTOs e schemas próprios.
4. `infrastructure` é conectada no composition root.
5. Providers externos só são instanciados no composition root/configuração.
6. Um módulo não acessa coleção Firestore diretamente fora do adapter/repository.
7. Não adicionar um “utils.py” global para contornar desenho de módulos.

## 7. Composition root

Um módulo de inicialização monta configurações, clientes Firebase, repositories, providers, orchestrator, Event Bus, handlers e rotas. Testes substituem essas dependências por fakes/mocks. A configuração deve falhar cedo quando uma credencial obrigatória estiver ausente, sem incluir o valor no erro ou log.
