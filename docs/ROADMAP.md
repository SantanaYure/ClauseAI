# E — Roadmap de implementação do MVP

Sequência recomendada para uma pessoa. Cada fase só avança quando sua definição de pronto é verificável. “Mockável” indica o que não deve bloquear o desenvolvimento; “seguros” indica decisões que não devem ser inventadas.

## Fase 1 — Fundação

- **Objetivo:** preparar repositório, convenções, ambientes e qualidade mínima.
- **Dependências:** nenhuma.
- **Entregável:** estrutura backend/frontend/docs, configuração tipada, lint, format, testes e README de execução.
- **Definition of Done:** projeto inicia localmente; segredos não estão no repositório; teste vazio roda.
- **Pode ser mockado:** Firebase, providers, Storage e Event Bus.
- **Equipe de seguros:** nenhuma, além de contato responsável.

## Fase 2 — Specs e ADRs

- **Objetivo:** congelar contratos antes do código.
- **Dependências:** Fase 1.
- **Entregável:** esta documentação revisada, schemas, catálogo de erros e perguntas abertas.
- **Definition of Done:** cada feature tem spec, critérios e teste planejado; decisões relevantes têm ADR.
- **Pode ser mockado:** exemplos de apólice e evidências.
- **Equipe de seguros:** validar vocabulário, campos prioritários e limites de interpretação.

## Fase 3 — Contratos e mocks

- **Objetivo:** testar fluxo sem dependências externas.
- **Dependências:** Fase 2.
- **Entregável:** interfaces, fakes de repositories/Storage/AI/Event Bus, fixtures e schemas de API.
- **Definition of Done:** casos de uso principais passam com fakes e falhas são classificadas.
- **Pode ser mockado:** Gemini, Groq, Firestore, Storage e relógio.
- **Equipe de seguros:** fornecer 2–5 documentos anonimizados e expected fields.

## Fase 4 — Backend base

- **Objetivo:** montar Clean Architecture, composition root, FastAPI e tratamento de erros.
- **Dependências:** Fases 1–3.
- **Entregável:** health check, rotas vazias tipadas, DI simples, logger e catálogo de erros.
- **Definition of Done:** servidor sobe sem provider configurado em modo fake; testes de contrato rodam.
- **Pode ser mockado:** tudo externo.
- **Equipe de seguros:** nenhuma.

## Fase 5 — Upload e armazenamento

- **Objetivo:** implementar RF-01/RF-02 com Firebase adapters.
- **Dependências:** Fase 4 e credenciais de ambiente.
- **Entregável:** `POST /documents`, lista/detalhe, Storage e metadados Firestore.
- **Definition of Done:** upload válido retorna `202`, original recuperável e limites/erros testados.
- **Pode ser mockado:** Firebase Emulator ou fakes.
- **Equipe de seguros:** política de retenção e dados sensíveis.

## Fase 6 — Event Bus

- **Objetivo:** iniciar o pipeline orientado a eventos.
- **Dependências:** Fase 5.
- **Entregável:** envelope, Event Bus em memória, registry, worker e handlers de documento.
- **Definition of Done:** `DocumentUploaded` percorre processamento inicial e é observável.
- **Pode ser mockado:** fila/worker em testes síncronos.
- **Equipe de seguros:** nenhuma.

## Fase 7 — Extração com IA

- **Objetivo:** obter JSON rastreável de documentos reais.
- **Dependências:** Fases 3, 5 e 6; acesso aos providers.
- **Entregável:** AI Orchestrator, Gemini adapter, prompts versionados, schema v1, retries e `ExtractionResult`.
- **Definition of Done:** golden fixtures produzem payload validado ou falha explícita; injection e ausência cobertas.
- **Pode ser mockado:** Gemini em unit/integration; respostas reais só em testes controlados.
- **Equipe de seguros:** taxonomia inicial e revisão de campos/trechos.

## Fase 8 — Persistência estruturada

- **Objetivo:** transformar extração validada em `Policy` consultável.
- **Dependências:** Fase 7.
- **Entregável:** `PolicyStored`, repository, `GET /policies`, evidências e idempotência.
- **Definition of Done:** extração repetida não duplica; policy pronta é consultável e auditável.
- **Pode ser mockado:** Firestore emulator.
- **Equipe de seguros:** validar mapeamento de campos e estados de ausência.

## Fase 9 — Comparação determinística

- **Objetivo:** gerar fatos reproduzíveis para duas policies.
- **Dependências:** Fase 8.
- **Entregável:** `POST /comparisons`, `ComparisonService`, itens e status parcial.
- **Definition of Done:** tabela de casos cobre valores, listas, datas, nulos e incompatibilidade; idempotência passa.
- **Pode ser mockado:** policies fixture e Firestore.
- **Equipe de seguros:** confirmar chaves de correspondência e unidades; sem isso usar `UNKNOWN`.

## Fase 10 — Comparação semântica

- **Objetivo:** explicar diferenças sem ultrapassar evidências.
- **Dependências:** Fase 9, acesso Groq e revisão de prompt.
- **Entregável:** Groq adapter, prompt semântico, schema de interpretação, disclaimer e falha parcial.
- **Definition of Done:** resultado semântico referencia itens, separa fatos/interpretação e rejeita saída inválida.
- **Pode ser mockado:** Groq para maioria dos testes; smoke test real controlado.
- **Equipe de seguros:** revisar linguagem, perguntas pendentes e risco de interpretação.

## Fase 11 — Frontend

- **Objetivo:** entregar fluxo completo para usuário.
- **Dependências:** endpoints estáveis das Fases 5, 8–10.
- **Entregável:** upload, lista/status, detalhe de policy, seleção de duas, comparação e erros.
- **Definition of Done:** fluxo navegável com fixtures; estados loading/partial/failed acessíveis.
- **Pode ser mockado:** API com fixtures/MSW.
- **Equipe de seguros:** validar legibilidade e ordem de informações.

## Fase 12 — Integração

- **Objetivo:** conectar componentes e ambiente Firebase/providers.
- **Dependências:** Fases 1–11.
- **Entregável:** configuração de staging acadêmico, worker, índices e smoke tests.
- **Definition of Done:** upload real autorizado percorre até comparação; logs correlacionados.
- **Pode ser mockado:** provider durante desenvolvimento local; não no smoke test final.
- **Equipe de seguros:** executar revisão funcional com documentos controlados.

## Fase 13 — Testes

- **Objetivo:** comprovar contratos, resiliência e regressão de IA.
- **Dependências:** Fase 12.
- **Entregável:** unit, integration, contract, end-to-end, golden datasets e prompt regression.
- **Definition of Done:** critérios das specs passam; falhas conhecidas têm issue e decisão explícita.
- **Pode ser mockado:** dependências externas em unit/integration; E2E deve ter cenário real controlado.
- **Equipe de seguros:** avaliar expected outputs e falsos positivos/negativos.

## Fase 14 — Estabilização do MVP

- **Objetivo:** reduzir risco de demo e preparar manutenção.
- **Dependências:** Fase 13.
- **Entregável:** checklist de release, documentação de operação, limites, dados de demonstração e backlog futuro.
- **Definition of Done:** instalação reproduzível; nenhum segredo em logs; estados de falha demonstráveis; known issues documentadas.
- **Pode ser mockado:** cenários de falha para a apresentação.
- **Equipe de seguros:** aceite do escopo acadêmico e disclaimer final.

## Priorização de backlog futuro

1. fila durável/executor externo se o volume exigir;
2. autenticação e autorização;
3. revisão humana e correção assistida;
4. múltiplas apólices/documento e versionamento;
5. taxonomia de D&O validada e regras de impacto;
6. exportação e auditoria avançada;
7. circuit breaker, tracing distribuído e escala horizontal.
