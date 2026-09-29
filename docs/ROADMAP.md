# E — Roadmap de implementação do MVP

Sequência recomendada para uma pessoa. Cada fase só avança quando sua definição de pronto é verificável. “Mockável” indica o que não deve bloquear o desenvolvimento; “seguros” indica decisões que não devem ser inventadas.

**Prazo do Projeto Final:** 06/10/2026, 23h59. Se o tempo apertar, priorizar o fluxo demonstrável ponta a ponta (upload → extração → normalização → comparação ponderada → resumo) sobre recursos opcionais: o desafio valoriza uma solução simples e tecnicamente consistente.

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
- **Equipe de seguros:** dicionário, pesos e prompts já entregues (`docs/domain/sources/`); validar apenas os pontos pendentes da seção 10 da base de conhecimento.

## Fase 3 — Contratos e mocks

- **Objetivo:** testar fluxo sem dependências externas.
- **Dependências:** Fase 2.
- **Entregável:** interfaces, fakes de repositories/Storage/AI/Event Bus, seed da base de conhecimento, fixtures e schemas de API.
- **Definition of Done:** casos de uso principais passam com fakes e falhas são classificadas.
- **Pode ser mockado:** Gemini, Firestore, Storage e relógio.
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
- **Entregável:** AI Orchestrator, leitor de PDF nativo (DOCX em I-01; leitura em faixas de páginas; modo de IA local para desenvolvimento, ADR-026), Gemini adapter (OCR multimodal), `P-INTAKE-001`, `P-EXTRACT-001`, `P-NORMALIZE-001`, schema v1, retries, `ExtractionResult`, `Evidence` e `ConceptOccurrence`.
- **Definition of Done:** golden fixtures produzem payload validado ou falha explícita; PDF pesquisável, PDF digitalizado e imagem cobertos; injection, ausência e Condições Gerais isoladas cobertas; os 31 conceitos ponderados são pesquisados.
- **Pode ser mockado:** Gemini em unit/integration; respostas reais só em testes controlados.
- **Equipe de seguros:** revisar variantes de DO-036 a DO-044.

## Fase 8 — Persistência estruturada

- **Objetivo:** transformar extração validada em `Policy` consultável.
- **Dependências:** Fase 7.
- **Entregável:** `PolicyStored`, repository, `GET /policies`, `GET /concepts`, `GET /concepts/{id}/occurrences`, `GET /search`, evidências versionadas e idempotência.
- **Definition of Done:** extração repetida não duplica; policy pronta é consultável e auditável.
- **Pode ser mockado:** Firestore emulator.
- **Equipe de seguros:** validar mapeamento de campos e estados de ausência.

## Fase 9 — Comparação determinística

- **Objetivo:** gerar fatos reproduzíveis para duas policies.
- **Dependências:** Fase 8.
- **Entregável:** `POST /comparisons`, `ComparisonService`, itens e status parcial.
- **Definition of Done:** tabela de casos cobre valores, listas, datas, nulos e incompatibilidade; idempotência passa.
- **Pode ser mockado:** policies fixture e Firestore.
- **Equipe de seguros:** nenhuma; a chave de correspondência é o `concept_id`.

## Fase 10 — Avaliação, pontuação e decisão

- **Objetivo:** avaliar conceitos, pontuar e recomendar de forma condicionada sem ultrapassar evidências.
- **Dependências:** Fase 9, acesso ao Gemini e revisão de prompts.
- **Entregável:** avaliação com Gemini, `P-ASSESS-001`, `ScoringService`, perfis de risco, `P-EXECUTIVE-001`, `QualityGate`, `POST /queries` e falha parcial.
- **Definition of Done:** avaliações fora da escala são rejeitadas; fórmulas, pareceres e perfis passam na tabela de casos (incluindo total 207 e o exemplo 77,6 % × 79,4 %); resumo não cria números; “Consulte seu corretor de seguros.” aparece nas limitações.
- **Pode ser mockado:** Gemini na maioria dos testes; smoke test real controlado.
- **Equipe de seguros:** confirmar `profile_multiplier`, `close_score_threshold` e `min_completeness`.

## Fase 11 — Frontend

- **Objetivo:** entregar fluxo completo para usuário.
- **Dependências:** endpoints estáveis das Fases 5, 8–10.
- **Entregável:** upload, lista/status, detalhe de policy com evidências, consulta por conceito, seleção de duas, filtro por importância, seletor de perfil, tabela ponderada, scores, resumo executivo, alertas e erros.
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

## Fase 15 — Entregáveis do Projeto Final

- **Objetivo:** cumprir os requisitos de entrega do desafio.
- **Dependências:** Fase 14.
- **Entregável:** repositório GitHub público; README com descrição, instalação, execução, tecnologias, integrantes e licença MIT; ZIP do código; em `Projeto_Final_Artefatos/`: relatório técnico em PDF (arquitetura, tecnologias, agentes, fluxo, justificativas, limitações e evolução futura), `InsurMinds_Projeto_Final.pptx` e `InsurMinds_Projeto_Final.mp4` (até 5 minutos: problema, arquitetura, funcionamento e resultados), com fontes de documentos citadas.
- **Definition of Done:** checklist “entrega completa” do enunciado atendido até 06/10/2026, 23h59.
- **Pode ser mockado:** nada.
- **Equipe de seguros:** revisão final do relatório.

## Incrementos pós-MVP

Estados: `Documentado` (spec e ADR prontos), `Em andamento`, `Concluído`. Só marcar `Concluído` depois da validação do `qa`.

| ID | Incremento | Referências | Estado |
|---|---|---|---|
| I-01 | Suporte a DOCX: detecção por conteúdo, leitura local sem OCR, origem estável da evidência (bloco lógico), erros classificados, comparação PDF × DOCX | ADR-024; SPEC-001 a SPEC-004 | Implementado (backend: leitor, erros classificados, testes; frontend: rótulo "bloco" nas evidências; apólices de exemplo em PDF e DOCX em `Policy/`). Aguardando validação final do `qa`, incluindo a comparação PDF × DOCX ponta a ponta. Limitações conhecidas abaixo |
| I-02 | Remake visual e identidade de marca: fontes, cores, selos, navegação, envio com validação, processamento em 3 passos, slots A e B, resultado em ordem fixa | ADR-025; SPEC-007, SPEC-010, SPEC-019 | Implementado (fontes, cores, selos, menu, envio com validação por arquivo, 3 passos, tela de sucesso, slots A e B, resultado sem abas com "Ver cálculo" recolhido, "Tentar de novo"). Aguardando validação final do `qa`, incluindo a revisão de contraste |

Limitações conhecidas de I-01 (evolução futura): o leitor de DOCX não extrai a numeração automática de listas e cláusulas do Word (`numbering.xml`), notas de rodapé nem caixas de texto. Evidências que dependam desses elementos podem perder o número da cláusula ou o texto. Detalhes na SPEC-004.

Limitações conhecidas de I-02 (SPEC-010):

- O upload é recusado inteiro se um arquivo do lote for inválido. O frontend associa o erro ao arquivo pelo nome citado na mensagem.
- O backend não expõe o tipo de arquivo nas evidências. O frontend busca os dois `GET /policies/{id}` da comparação e usa a extensão `.docx` como fallback.
- As apólices de exemplo de `Policy/` são menores que apólices reais (cerca de 12 páginas). Servem para testar a comparação, não para medir desempenho em documentos longos.

Definição de pronto: critérios de aceite das specs citadas passam, incluindo uma comparação PDF × DOCX ponta a ponta e a revisão de contraste da nova paleta.

## Priorização de backlog futuro

1. fila durável/executor externo se o volume exigir;
2. autenticação e autorização;
3. revisão humana e correção assistida;
4. múltiplas apólices/documento e versionamento;
5. comparação de mais de duas apólices e edição de pesos pelo usuário com trilha de auditoria;
6. exportação e auditoria avançada;
7. circuit breaker, tracing distribuído e escala horizontal;
8. DOCX: extrair numeração automática de listas e cláusulas (`numbering.xml`), notas de rodapé e caixas de texto.
