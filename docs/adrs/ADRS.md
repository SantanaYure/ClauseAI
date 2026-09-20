# D — Architecture Decision Records

Status permitido: `Accepted`, `Proposed`, `Superseded`. ADRs registram decisões técnicas, não regras de seguros.

## ADR-001 — Monólito modular

- **Status:** Accepted
- **Contexto/problema:** MVP acadêmico, um programador, processamento e domínio ainda em descoberta.
- **Decisão:** uma aplicação com módulos internos e worker, separada por portas e camadas.
- **Alternativas:** microserviços; serverless fragmentado.
- **Consequências:** deploy/operação simples; limites de escala e isolamento menores.
- **Riscos:** acoplamento acidental; mitigado por regras de dependência e testes de arquitetura.

## ADR-002 — FastAPI

- **Status:** Accepted
- **Contexto/problema:** API Python tipada, assíncrona e adequada ao ecossistema de IA.
- **Decisão:** FastAPI apenas como adapter HTTP e composition root.
- **Alternativas:** Flask; Django REST.
- **Consequências:** validação e OpenAPI rápidas; exige disciplina para não pôr domínio nas rotas.
- **Riscos:** confundir schemas Pydantic com entidades; separar DTOs.

## ADR-003 — React + TypeScript

- **Status:** Accepted
- **Contexto/problema:** UI web para fluxo e comparação com contratos claros.
- **Decisão:** React, TypeScript e SCSS, feature-oriented.
- **Alternativas:** Vue; HTML server-side.
- **Consequências:** componentes reutilizáveis e tipos; build frontend adicional.
- **Riscos:** duplicação de tipos; centralizar contratos de API.

## ADR-004 — Firebase / Firestore / Storage

- **Status:** Accepted
- **Contexto/problema:** persistência documental e armazenamento de binários com baixo overhead operacional.
- **Decisão:** Firestore para metadados/estruturas e Storage para originais.
- **Alternativas:** PostgreSQL + object storage; MongoDB.
- **Consequências:** velocidade de prototipação; necessidade de índices, limites e emuladores.
- **Riscos:** consultas complexas e consistência entre Storage/Firestore; usar repositories e compensação.

## ADR-005 — AI Orchestrator

- **Status:** Accepted
- **Contexto/problema:** provedores, prompts, retries e schemas mudam independentemente do domínio.
- **Decisão:** única camada de orquestração para todas as chamadas de IA.
- **Alternativas:** SDKs chamados pelos services; provider único acoplado.
- **Consequências:** rastreabilidade e substituição facilitadas; pequena camada adicional.
- **Riscos:** orquestrator virar “god object”; separar portas, prompts e métricas.

## ADR-006 — Gemini para extração

- **Status:** Accepted
- **Contexto/problema:** documentos podem ser PDF/imagem e exigem compreensão multimodal.
- **Decisão:** Gemini 3.5 Flash Lite para extração estruturada, sujeito à confirmação de disponibilidade/nome.
- **Alternativas:** OCR + regras; outro LLM multimodal.
- **Consequências:** reduz pipeline inicial; exige schema, evidências e testes de hallucination.
- **Riscos:** saída inconsistente e limites de contexto; retries limitados e golden datasets.

## ADR-007 — Groq/GPT-OSS-120B para comparação

- **Status:** Accepted
- **Contexto/problema:** interpretação de texto requer modelo separado da extração.
- **Decisão:** Groq hospedando GPT-OSS-120B para semântica e explicação, sujeito a validação operacional.
- **Alternativas:** usar Gemini para tudo; comparação apenas por regras.
- **Consequências:** separa funções e permite otimizar custo/latência; adiciona integração externa.
- **Riscos:** interpretação sem base; enviar somente fatos/evidências e validar schema.

## ADR-008 — JSON estruturado

- **Status:** Accepted
- **Contexto/problema:** comparação e persistência exigem dados previsíveis.
- **Decisão:** schema versionado com evidências por campo.
- **Alternativas:** texto livre; JSON sem versão.
- **Consequências:** testabilidade e migração; evolução de schema requer disciplina.
- **Riscos:** falso senso de precisão; preservar incerteza e `confidence` não científica.

## ADR-009 — Comparação determinística + semântica

- **Status:** Accepted
- **Contexto/problema:** LLM não deve ser fonte única de fatos.
- **Decisão:** backend gera comparação factual; IA interpreta depois.
- **Alternativas:** LLM compara PDFs diretamente; regras somente.
- **Consequências:** auditabilidade maior e resultados reproduzíveis; pipeline em duas fases.
- **Riscos:** chaves de matching incompletas; marcar `UNKNOWN`/`PENDING_BUSINESS_VALIDATION`.

## ADR-010 — SOLID

- **Status:** Accepted
- **Contexto/problema:** reduzir acoplamento em projeto evolutivo de uma pessoa.
- **Decisão:** aplicar SOLID pragmaticamente, com interfaces apenas em fronteiras reais.
- **Alternativas:** camada anêmica sem contratos; abstrações genéricas antecipadas.
- **Consequências:** testes e substituição melhores; risco de excesso de indirection.
- **Riscos:** overengineering; cada interface precisa de justificativa concreta.

## ADR-011 — Clean Architecture

- **Status:** Accepted
- **Contexto/problema:** Firebase, FastAPI e providers não devem contaminar domínio.
- **Decisão:** dependências apontam para dentro; adapters na infraestrutura/apresentação.
- **Alternativas:** arquitetura em camadas acoplada a framework; MVC simples.
- **Consequências:** maior independência e testabilidade; exige composition root.
- **Riscos:** boilerplate; manter somente camadas necessárias ao MVP.

## ADR-012 — Orientação a eventos

- **Status:** Accepted
- **Contexto/problema:** PDF/IA/comparação são demorados e desacopláveis.
- **Decisão:** eventos internos para transições de processamento e observabilidade.
- **Alternativas:** request síncrona; broker desde o início.
- **Consequências:** API responsiva; consistência eventual e necessidade de idempotência.
- **Riscos:** evento perdido em memória; persistir estado antes de publicar e permitir reprocessamento.

## ADR-013 — Event Bus interno

- **Status:** Accepted
- **Contexto/problema:** MVP não precisa de operação de broker.
- **Decisão:** `InMemoryEventBus` com interface substituível.
- **Alternativas:** Kafka; RabbitMQ; Cloud Tasks.
- **Consequências:** simples e barato; não durável nem escalável horizontalmente.
- **Riscos:** restart; documentar limitação e criar caminho de evolução.

## ADR-014 — Processamento assíncrono

- **Status:** Accepted
- **Contexto/problema:** upload não pode ficar bloqueado por PDF/modelo.
- **Decisão:** HTTP aceita comando; worker processa eventos; status por consulta.
- **Alternativas:** background task sem job; síncrono.
- **Consequências:** UX melhor e retry explícito; mais estados para testar.
- **Riscos:** worker em processo não sobreviver a deploy; preparar executor substituível.

## ADR-015 — Commands, Queries e Events

- **Status:** Accepted
- **Contexto/problema:** separar intenção de escrita, leitura e fatos ocorridos.
- **Decisão:** usar distinção conceitual e tipos separados, sem CQRS completo.
- **Alternativas:** endpoints chamando services genéricos; CQRS com bases separadas.
- **Consequências:** contratos claros com baixo custo; não há sincronização de modelos duplicados.
- **Riscos:** criar classes vazias; só introduzir command/query quando melhorar teste ou fronteira.

## ADR-016 — Idempotência

- **Status:** Accepted
- **Contexto/problema:** eventos podem ser duplicados e retries são necessários.
- **Decisão:** `event_id`, `processing_id`, upserts por identidade e coleção `processed_events`.
- **Alternativas:** confiar em exactly-once; ignorar duplicatas.
- **Consequências:** reprocessamento seguro; exige transações/controle de concorrência.
- **Riscos:** marcador e efeito divergirem; usar operação atômica quando possível e testes de crash.
