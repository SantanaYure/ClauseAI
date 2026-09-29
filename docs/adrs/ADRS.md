# D — Architecture Decision Records

Status permitido: `Accepted`, `Proposed`, `Superseded`. ADRs registram decisões técnicas; regras de seguros ficam na [base de conhecimento D&O](../domain/DO_KNOWLEDGE_BASE.md).

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
- **Decisão:** Firestore para metadados/estruturas e Storage para originais. Atualizado pelo ADR-022: os originais ficam em pasta local por padrão.
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
- **Consequências:** reduz pipeline inicial; exige schema, evidências e testes de hallucination. Complementado pelo ADR-019 (leitura nativa + OCR).
- **Riscos:** saída inconsistente e limites de contexto; retries limitados e golden datasets.

## ADR-007 — Groq/GPT-OSS-120B para comparação

- **Status:** Superseded pelo ADR-023
- **Contexto/problema:** interpretação de texto requer modelo separado da extração.
- **Decisão:** Groq hospedando GPT-OSS-120B para avaliação por conceito e resumo executivo, sujeito a validação operacional (ver ADR-018).
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

## ADR-009 — Comparação determinística + avaliação por IA

- **Status:** Accepted
- **Contexto/problema:** LLM não deve ser fonte única de fatos.
- **Decisão:** backend gera comparação factual; IA avalia depois dentro de escalas fechadas; backend calcula a pontuação (ADR-018).
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

## ADR-017 — Base de conhecimento D&O versionada

- **Status:** Accepted
- **Contexto/problema:** o dicionário D&O, a matriz de pesos e os prompts do agente comparador são a base do produto e mudam com a validação da equipe de seguros.
- **Decisão:** manter os arquivos-fonte em `docs/domain/sources/`, consolidá-los em `DO_KNOWLEDGE_BASE.md` e carregá-los por seed versionado (`knowledge_base_version`) atrás da porta `ConceptCatalog`. Prompts leem o catálogo; não o duplicam.
- **Alternativas:** conceitos e pesos embutidos em prompts; constantes no código.
- **Consequências:** regras auditáveis e reproduzíveis por versão; exige comando de seed e testes de consistência entre fonte e catálogo.
- **Riscos:** fonte e catálogo divergirem; teste compara contagem de conceitos, pesos e total 207.

## ADR-018 — Pontuação ponderada determinística com avaliação por IA

- **Status:** Accepted
- **Contexto/problema:** o desafio pede apoio à decisão e as bases definem pesos, Resultado-base, Fator de Ajuste, scores e perfis; LLMs erram cálculos e não são reproduzíveis.
- **Decisão:** a IA escolhe Resultado-base e Fator de Ajuste em escalas fechadas, com justificativa e evidência; o `ScoringService` do domínio calcula pontos, scores, completude, pareceres e perfis com `Decimal`. Substitui a restrição anterior de “sem pontuação” da SPEC-008.
- **Alternativas:** LLM calcula tudo; comparação apenas factual sem pontuação.
- **Consequências:** decisão explicável e reproduzível; dois pontos de validação (schema da IA e regras do domínio).
- **Riscos:** score lido como verdade absoluta; mitigado por Índice de Completude, decisão `CONDITIONED`, separação entre análise e recomendação e “Consulte seu corretor de seguros.”

## ADR-019 — Leitura nativa de PDF com OCR multimodal

- **Status:** Accepted
- **Contexto/problema:** o desafio exige PDF e imagem; os prompts exigem leitura nativa quando houver camada de texto e OCR quando não houver, com confiança por evidência.
- **Decisão:** biblioteca de PDF na infraestrutura para texto nativo; Gemini multimodal como OCR para PDF digitalizado e imagem; porta `PdfTextReader` permite acrescentar OCR dedicado (Tesseract ou serviço gerenciado) se os golden datasets exigirem.
- **Alternativas:** apenas multimodal; OCR dedicado desde o início.
- **Consequências:** menos erro em PDFs pesquisáveis e rastreabilidade do método de extração; mais um adapter.
- **Riscos:** divergência entre texto nativo e leitura do modelo; preservar ambos e marcar conflito.

## ADR-020 — Agentes especializados como serviços do monólito

- **Status:** Accepted
- **Contexto/problema:** o desafio sugere agentes de recepção, OCR/extração, identificação de cláusulas, estruturação, comparação e relatório.
- **Decisão:** cada agente é um serviço de aplicação com handler, prompt versionado e contrato próprio, orquestrado pelo Event Bus interno (ver arquitetura, seção 3).
- **Alternativas:** framework multiagente externo; um único prompt monolítico.
- **Consequências:** atende à sugestão do desafio sem operar processos separados; responsabilidades testáveis isoladamente.
- **Riscos:** acoplamento entre agentes; comunicação só por eventos e DTOs.

## ADR-021 — Worker em fila e adaptador de persistência em memória

- **Status:** Accepted
- **Contexto/problema:** o HTTP precisa responder `202` sem esperar o Gemini, e os testes automatizados não devem depender do Firebase nem das chaves de IA.
- **Decisão:** `QueuedEventBus` envolve o `InMemoryEventBus` com uma `asyncio.Queue` e workers iniciados no ciclo de vida do FastAPI (`WORKER_CONCURRENCY`). `PERSISTENCE_BACKEND=memory` troca Firestore/Storage por repositórios em memória e pasta local, sem nenhum dado pré-carregado; o padrão é `firebase`.
- **Alternativas:** `BackgroundTasks` do FastAPI; fila externa desde o início; Firebase Emulator nos testes.
- **Consequências:** API responsiva e testes rápidos e determinísticos; o modo memória perde dados ao reiniciar.
- **Riscos:** evento na fila perdido se o processo cair; o estado é gravado antes de publicar e a comparação pode ser repetida pela UI (Histórico → “Tentar novamente”).

## ADR-022 — Arquivos originais em pasta local por padrão

- **Status:** Accepted (complementa o ADR-004)
- **Contexto/problema:** projetos novos do Firebase só ativam o Storage no plano Blaze (pago conforme o uso). O MVP acadêmico roda localmente e deve funcionar no plano gratuito Spark.
- **Decisão:** `STORAGE_BACKEND=local` (padrão) grava os originais em `backend/.data/uploads`, fora do Git; os dados continuam no Firestore. `STORAGE_BACKEND=firebase` reativa o Firebase Storage sem mudar código, pela mesma porta `BlobStorage`.
- **Alternativas:** exigir o plano Blaze; não guardar os originais.
- **Consequências:** custo zero e configuração mais simples; os originais existem só na máquina do backend.
- **Riscos:** perder a pasta impede reprocessar documentos (apólices e comparações continuam no Firestore); para publicar o backend na nuvem é preciso usar `STORAGE_BACKEND=firebase` ou outro armazenamento de objetos.

## ADR-023 — Gemini 3.5 Flash Lite em todas as etapas de IA

- **Status:** Accepted (substitui o ADR-007)
- **Contexto/problema:** o plano gratuito do Groq limita a 8.000 tokens por minuto, e uma comparação completa precisa de dezenas de milhares; na prática, as comparações falhavam por limite de uso (HTTP 429) ou levavam vários minutos. Manter dois provedores também exige duas chaves e duas integrações.
- **Decisão:** usar o Gemini 3.5 Flash Lite para extração, avaliação por conceito (`P-ASSESS-001`) e conclusão (`P-EXECUTIVE-001`), com um único `GeminiClient` compartilhado. As travas determinísticas e o `ScoringService` não mudam: a IA continua só propondo Resultado-base e Fator de Ajuste.
- **Alternativas:** Groq no plano pago (Dev Tier); outro provedor para a avaliação.
- **Consequências:** uma chave, uma integração e comparações mais rápidas; perde-se a separação entre o modelo que extrai e o que avalia.
- **Riscos:** o mesmo modelo lê e avalia, e pode repetir um erro de leitura na avaliação. Mitigado pelas travas determinísticas, pela exigência de evidência literal e pelo Quality Gate. O limite de uso do Gemini segue tratado com espera pelo tempo pedido (HTTP 429).
