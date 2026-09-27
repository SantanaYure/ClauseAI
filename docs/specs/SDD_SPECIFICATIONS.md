# C — SDD Specifications

## Como implementar

Cada spec segue `SPEC → critérios de aceite → contrato → testes → implementação futura`. Uma implementação só está pronta quando os critérios de aceite passam e a documentação de contrato permanece consistente. `PENDING_BUSINESS_VALIDATION` é uma saída válida e rastreável, nunca uma lacuna a ser preenchida por suposição.

Regras de domínio (conceitos, pesos, escalas, pareceres, perfis, cores e frase “Consulte seu corretor de seguros.”) vêm de [`domain/DO_KNOWLEDGE_BASE.md`](../domain/DO_KNOWLEDGE_BASE.md). As specs SPEC-015 a SPEC-019 cobrem normalização, pontuação, decisão, consulta por conceito e controle de qualidade.

| Etapa do desafio | Specs |
|---|---|
| 1. Recebimento | SPEC-001, SPEC-002 |
| 2. Extração | SPEC-003, SPEC-004 |
| 3. Organização | SPEC-015 |
| 4. Armazenamento | SPEC-005 |
| 5. Consulta | SPEC-006, SPEC-018 |
| 6. Comparação | SPEC-007, SPEC-008, SPEC-009, SPEC-016, SPEC-017 |
| 7. Apresentação | SPEC-010, SPEC-019 |

## Contratos transversais

- IDs e timestamps são gerados/injetados, UTC e estáveis durante uma operação.
- Todo command mutável recebe `correlation_id`; toda resposta de erro o devolve.
- Todo event tem `event_id`, `event_type`, `event_version`, `occurred_at`, `correlation_id`, `entity_id` e `payload`.
- Operações demoradas retornam `202` e status consultável.
- Handlers verificam `processed_events`/chave de processamento antes de efeitos não idempotentes.
- Falhas têm `code`, `retryable`, `attempt` e mensagem sanitizada.

---

## SPEC-001 — Upload de documento

### Objetivo e contexto

Receber um PDF ou imagem e criar um `Document` em estado `UPLOADED` sem esperar extração. A classificação do documento (tipo, seguradora, vigência, versão, necessidade de OCR) ocorre no início do processamento com `P-INTAKE-001`.

### Comportamento, entradas e saídas

- Entrada: multipart `file`, MIME detectável, tamanho dentro do limite configurado e metadados opcionais.
- Saída: `document_id`, `status`, `correlation_id`, `status_url`, HTTP `202`.
- Publica `DocumentUploaded` somente após persistir original e metadados.

### Dependências

`BlobStorage`, `DocumentRepository`, `EventBus`, `Clock`, `IdGenerator` e configuração de limites.

### Regras e erros

Aceitar somente `application/pdf` e imagens explicitamente configuradas; validar MIME por conteúdo quando possível; rejeitar vazio, excesso de tamanho e metadata inválida. Erros: `INVALID_FILE`, `UNSUPPORTED_MEDIA_TYPE`, `FILE_TOO_LARGE`, `STORAGE_UNAVAILABLE`.

### Critérios de aceite

- Arquivo válido cria exatamente um documento e um objeto no Storage.
- Resposta ocorre antes de chamadas de IA.
- Falha no Storage não cria documento “processável”.
- Evento contém envelope completo e correlação.
- Requisição repetida não duplica quando a mesma chave de idempotência for fornecida.

### Fora de escopo

Antivírus avançado, autenticação e parecer jurídico.

### Questões abertas

Tamanho máximo, formatos de imagem e política de retenção: `PENDING_BUSINESS_VALIDATION`/configuração operacional.

### Testes futuros

Unitários de validação; contrato multipart; integração com Storage fake; teste de publicação pós-persistência; teste de idempotência.

## SPEC-002 — Armazenamento

### Objetivo e contexto

Persistir original no Firebase Storage e metadados no Firestore com chave estável.

### Comportamento, entradas e saídas

Entrada: stream, metadados e ID. Saída: `StorageObject` (`storage_key`, tamanho, checksum, content_type) e `Document` persistido.

### Dependências

Portas `BlobStorage`/`DocumentRepository`, adapters Firebase e transação/compensação.

### Regras e erros

Calcular checksum; não expor URL pública por padrão; atualizar status de modo monotônico; sanitizar filename. Erros: `STORAGE_UNAVAILABLE`, `METADATA_WRITE_FAILED`, `CHECKSUM_FAILED`.

### Critérios de aceite

- Original e metadados podem ser recuperados pelo ID.
- `storage_key` não depende de nome fornecido pelo usuário.
- Falha após upload é registrada e recuperável.
- Nenhum segredo aparece em metadados ou logs.

### Fora de escopo

Versionamento de arquivos pelo usuário e edição do original.

### Questões abertas

Retenção, criptografia adicional e limite de páginas: `PENDING_BUSINESS_VALIDATION`.

### Testes futuros

Contrato do adapter; checksum; falhas parciais; regra de acesso; nomes maliciosos.

## SPEC-003 — Processamento

### Objetivo e contexto

Consumir `DocumentUploaded`, controlar o ciclo de processamento e publicar etapas.

### Comportamento, entradas e saídas

Entrada: evento e documento armazenado. Saída: `DocumentProcessingStarted`, `ExtractionRequested` ou `ProcessingFailed`.

### Dependências

`DocumentRepository`, `ProcessingJobRepository`/subcoleção, `EventBus`, `DocumentValidator`.

### Regras e erros

Transições válidas: `UPLOADED → PROCESSING → EXTRACTING → VALIDATING → COMPLETED/FAILED`; reexecução de evento já processado é no-op ou retorna estado atual. `max_attempts` finito.

### Critérios de aceite

- Cada transição gera log e timestamp.
- Documento inexistente gera falha clara, não exceção silenciosa.
- Retry não cria jobs paralelos para o mesmo `processing_id`.
- Estado final é consultável por endpoint de status.

### Fora de escopo

Orquestração distribuída e fila durável.

### Questões abertas

Política de retry por classe de erro: valores operacionais a calibrar.

### Testes futuros

Máquina de estados; duplicação de evento; crash simulado; limites de retry.

## SPEC-004 — Extração estruturada

### Objetivo e contexto

Extrair evidências de PDF ou imagem por leitura nativa e, quando necessário, OCR multimodal com Gemini, por meio do `AIOrchestrator` (documento 3, prompts 2 e 3).

### Comportamento, entradas e saídas

Entrada: `document_id`, bytes/contexto, schema e `prompt_version`. Saída: `ExtractionResult` validado ou falha.

### Dependências

`BlobStorage`, `AIOrchestrator`, schema v1, `ExtractionResultRepository`, observabilidade.

### Regras e erros

Não inventar; preservar ausência, ambiguidade, conflitos, tabelas, numeração de cláusulas, valores, datas, limites, exclusões e condições precedentes. Usar leitura nativa quando houver camada de texto e OCR multimodal para PDF digitalizado ou imagem. OCR ilegível ou inconsistente gera evidência de baixa confiança, nunca texto completado. Resposta inválida não vira apólice. Timeout/429/5xx têm retry limitado. Erros: `INVALID_MODEL_OUTPUT`, `EXTRACTION_TIMEOUT`, `MODEL_UNAVAILABLE`, `SCHEMA_VALIDATION_FAILED`, `LOW_OCR_CONFIDENCE` (aviso, não falha).

### Critérios de aceite

- Modelo é chamado apenas pela orquestração.
- Resultado registra modelo, prompt, tokens, latência e tentativa.
- Cada campo preenchido tem evidência (página, seção/cláusula quando houver, método e confiança) ou é rejeitado.
- PDF pesquisável, PDF digitalizado e imagem são processados; todas as páginas são contabilizadas.
- Evidência de baixa confiança aparece com `BROKER_GUIDANCE`.
- Injection no PDF não altera instruções do sistema.
- Ao exceder retries, status é `FAILED` com `retryable` correto.

### Fora de escopo

Vínculo a conceitos (SPEC-015), pontuação (SPEC-016) e aconselhamento jurídico.

### Questões abertas

Limite de páginas/tokens e política de retenção do raw response.

### Testes futuros

Mocks, golden datasets, respostas truncadas, conflitos, documentos extensos e injection.

## SPEC-005 — Persistência da apólice

### Objetivo e contexto

Transformar `ExtractionResult` validado em `Policy` idempotente.

### Comportamento, entradas e saídas

Entrada: resultado validado e `document_id`. Saída: `PolicyStructured` e `PolicyStored`.

### Dependências

`PolicyRepository`, value objects, `processed_events`, schema v1.

### Regras e erros

Upsert por `document_id`/`processing_id`; não duplicar em `ExtractionCompleted` repetido; manter origem e versão; não persistir JSON inválido como policy válida; não sobrescrever evidências originais — correção, nova versão ou novo documento geram novo registro com histórico (documento 3, prompt 5).

### Critérios de aceite

- Um resultado validado produz uma policy identificável.
- Reprocessamento atualiza/reconhece a mesma versão sem duplicar.
- Campos ausentes permanecem ausentes.
- Falha de persistência deixa job recuperável e não publica `PolicyStored`.

### Fora de escopo

Revisão manual, edição colaborativa e histórico completo de versões.

### Questões abertas

Política para múltiplas apólices no mesmo documento: `PENDING_BUSINESS_VALIDATION`.

### Testes futuros

Upsert, concorrência, schema incompatível, consistência de evidências.

## SPEC-006 — Consulta da apólice

### Objetivo e contexto

Permitir leitura de apólices prontas e suas evidências.

### Comportamento, entradas e saídas

`GET /policies` lista resumidos; `GET /policies/{id}` retorna estrutura completa, status e ambiguidades.

### Dependências

`PolicyRepository`, DTOs de leitura, paginação.

### Regras e erros

Não retornar policy em estado não pronto como se fosse final; usar `409 POLICY_NOT_READY`; respeitar limites de página e tamanho.

### Critérios de aceite

- Policy existente retorna dados e origem.
- ID inexistente retorna `404` com envelope padrão.
- Lista pagina sem carregar todos os registros.
- DTO não expõe raw response nem segredo.

### Fora de escopo

Busca full-text e edição.

### Questões abertas

Nenhuma; consulta por conceito, variante e peso está em SPEC-018.

### Testes futuros

Contrato de response, paginação, status e controle de exposição.

## SPEC-007 — Seleção de apólices

### Objetivo e contexto

Permitir selecionar exatamente duas policies válidas para comparação na UI/API.

### Comportamento, entradas e saídas

Entrada: dois IDs. Saída: `ComparePoliciesCommand`/`202` quando aceitos.

### Dependências

`PolicyRepository`, componente de seleção React e `ComparisonRepository`.

### Regras e erros

IDs distintos, existentes e `STORED`; a ordem A/B deve ser preservada, mas não implica preferência. Erros `INVALID_POLICY_COUNT`, `SAME_POLICY`, `POLICY_NOT_READY`.

### Critérios de aceite

- UI impede terceira seleção ou deixa claro que substitui uma anterior.
- API rejeita zero, uma ou mais de duas policies.
- Policy falha não inicia comparação.
- A e B permanecem identificáveis no resultado.

### Fora de escopo

Comparação em lote de mais de duas apólices (evolução prevista pelo prompt mestre).

### Questões abertas

Permitir comparar versões da mesma apólice: `PENDING_BUSINESS_VALIDATION`.

### Testes futuros

Validação de cardinalidade, estados e contrato da seleção.

## SPEC-008 — Comparação determinística

### Objetivo e contexto

Gerar diferenças factuais reproduzíveis antes da avaliação por IA.

### Comportamento, entradas e saídas

Entrada: duas policies. Saída: `Comparison` com `ComparisonItem[]` em ordem estável.

### Dependências

`ComparisonService`, normalizadores e `ComparisonRepository`.

### Regras e erros

Comparar presença, valor, data e listas por `concept_id`; declarar incompatibilidade de moeda/base (agregado × por evento, erosão, sublimite); nunca inferir equivalência jurídica. Índice de capacidade financeira do LMG só é calculado quando os limites forem comparáveis.

### Critérios de aceite

- Mesmo input produz o mesmo resultado e ordem.
- Ausência de um lado vira `ONLY_LEFT/ONLY_RIGHT`.
- Campos incomparáveis viram `NOT_COMPARABLE` ou `UNKNOWN`.
- Evidências acompanham os dois lados.
- Reexecução é idempotente.

### Fora de escopo

Conversão cambial. Pontuação e pesos ficam em SPEC-016.

### Questões abertas

Nenhuma para correspondência: a chave é o `concept_id` do catálogo. Itens sem conceito ficam `UNKNOWN`.

### Testes futuros

Tabela de casos, datas, dinheiro, listas, nulos, ordem e concorrência.

## SPEC-009 — Avaliação por conceito com IA

### Objetivo e contexto

Avaliar cada conceito ativo nas duas apólices com os mesmos critérios, atribuindo Resultado-base e Fator de Ajuste sem alterar fatos (documento 3, prompts 7, 9 e 10).

### Comportamento, entradas e saídas

Entrada: resultado determinístico, ocorrências, evidências selecionadas e critério de cada conceito. Saída: `ConceptAssessment[]` por apólice e diferença principal por conceito.

### Dependências

`AIOrchestrator`, Groq provider, prompt `P-ASSESS-001`, catálogo, `ComparisonRepository`.

### Regras e erros

Usar apenas contexto fornecido; valores só das escalas fechadas; justificativa para valor ≠ 1,00; sem dupla redução pelo mesmo motivo; exclusão expressa zera o conceito; contratação só com documento contratual aplicável; citar `evidence_id`. Erros têm retry limitado.

### Critérios de aceite

- IA não cria item factual fora da comparação nem calcula pontos.
- Resultado com valor fora da escala ou sem justificativa é rejeitado.
- Modelo/prompt/latência são registrados.
- Conceito sem evidência suficiente fica `sufficient_evidence=false` e recebe `BROKER_GUIDANCE`.
- Falha de avaliação preserva resultado determinístico e status `PARTIAL` explícito.

### Fora de escopo

Parecer jurídico.

### Questões abertas

Tom editorial final das justificativas.

### Testes futuros

Mock de provider, injection, hallucination fixtures, timeout e validação de schema.

## SPEC-010 — Exibição do resultado

### Objetivo e contexto

Apresentar comparação compreensível, rastreável e auditável (documento 3, prompts 14 e 15; base de conhecimento, seção 8).

### Comportamento, entradas e saídas

Entrada: response de comparison. UI exibe documentos processados, qualidade da extração, seletor de Apólice 01/02, filtro por nível de importância, seletor de perfil de risco, tabela com uma linha por conceito (colunas do prompt 15, incluindo peso, Resultado-base, Fator de Ajuste, pontos e parecer), Score de Aderência, Índice de Completude, indicador comparativo, resumo executivo, evidência literal com fonte/cláusula/página e alertas.

### Dependências

React, TypeScript, SCSS, API client e contratos de response.

### Regras e erros

Não esconder `UNKNOWN`, `NOT_COMPARABLE`, `INCONCLUSIVE` ou `PENDING_BUSINESS_VALIDATION`; separar visualmente evidência, avaliação, pontuação e recomendação; usar as cores da base de conhecimento sempre acompanhadas de rótulo; não usar verde para mera menção em Condições Gerais; percentuais com uma casa decimal; exibir “Consulte seu corretor de seguros.” onde houver limitação; polling para em estados finais.

### Critérios de aceite

- Usuário sabe qual policy é A/B.
- Itens têm conceito, peso, valores, pontos, parecer e evidência quando disponível.
- Filtro por importância e troca de perfil não alteram os pesos-base exibidos.
- Recomendação `CONDITIONED` é visualmente distinta de `TECHNICAL`.
- Loading/erro/resultado parcial são estados explícitos.
- Layout é utilizável em viewport definido pelo MVP e tem acessibilidade básica.

### Fora de escopo

Exportação PDF, dashboard analítico e edição de dados/pesos pelo usuário.

### Questões abertas

Design visual, paginação da tabela e idioma final.

### Testes futuros

Componentes, contrato com fixtures, acessibilidade e estados de erro.

## SPEC-011 — Tratamento de falhas

### Objetivo e contexto

Uniformizar falhas técnicas, de domínio e de providers sem perder contexto.

### Comportamento, entradas e saídas

Entrada: exceção/erro classificado. Saída: estado, log estruturado, retry quando permitido e erro público sanitizado.

### Dependências

Error catalog, `ProcessingJob`, logger, `Clock`, Event Bus.

### Regras e erros

Classificar `validation`, `not_found`, `conflict`, `transient_external`, `permanent_external`, `unexpected`; nunca retry infinito; preservar determinístico se avaliação ou resumo falharem.

### Critérios de aceite

- Cada falha tem código estável e correlação.
- Retry só ocorre em erros retryable e respeita `max_attempts`.
- Stack trace fica apenas em log protegido.
- UI mostra ação possível sem detalhes sensíveis.

### Fora de escopo

Circuit breaker; fica como evolução.

### Questões abertas

SLAs e limites exatos de timeout.

### Testes futuros

Matriz erro/retry, falha parcial, crash/restart e redaction.

## SPEC-012 — Observabilidade

### Objetivo e contexto

Permitir rastrear uma operação ponta a ponta.

### Comportamento, entradas e saídas

Toda operação gera logs estruturados com `event_id`, `correlation_id`, IDs de entidade, duração, status, modelo/prompt quando IA, tokens, latência, retry e custo estimado.

### Dependências

Logger, métricas, `Clock`, contexto de correlação.

### Regras e erros

JSON estruturado; sem credenciais, documento integral ou prompt confidencial em logs comuns; correlation deve atravessar eventos e handlers.

### Critérios de aceite

- É possível seguir upload → policy → comparison por correlação.
- Duração e status existem em operações externas.
- Falhas incluem código e tentativa.
- Teste confirma redaction de segredos.

### Fora de escopo

Tracing distribuído e plataforma comercial de observabilidade.

### Questões abertas

Formato final de métricas e retenção de logs.

### Testes futuros

Context propagation, redaction, campos obrigatórios e métricas de latência.

## SPEC-013 — Event Bus

### Objetivo e contexto

Desacoplar etapas demoradas dentro do monólito sem introduzir broker externo.

### Comportamento, entradas e saídas

`publish(event)` entrega a handlers inscritos; `subscribe(type, handler)` registra consumidores; erros são capturados e enviados ao fluxo de falha.

### Dependências

`Event`, registry, logger e lifecycle do worker.

### Regras e erros

Envelope versionado, ordem por entidade quando possível, sem assumir durabilidade; handler não deve bloquear request HTTP.

### Critérios de aceite

- Event Bus permite fake síncrono em testes.
- Publicação não expõe exceção interna ao endpoint após aceite.
- Duplicatas são toleradas pelos handlers.
- Falha de handler é observável e não interrompe todos os consumidores.

### Fora de escopo

Kafka, RabbitMQ, garantia exactly-once e replay completo.

### Questões abertas

Estratégia de reprocessamento após restart.

### Testes futuros

Subscribe/publish, isolamento de handlers, ordem, exceção e shutdown.

## SPEC-014 — Processamento assíncrono

### Objetivo e contexto

Executar PDF, IA e comparação fora do ciclo HTTP.

### Comportamento, entradas e saídas

Upload/comparison persistem comando e retornam `202`; worker processa eventos; endpoints de status/resultados refletem progresso.

### Dependências

Event Bus, worker, repositories, lifecycle FastAPI e `ProcessingJob`.

### Regras e erros

Worker inicia/paralisa de modo previsível; não perder estado persistido; estados públicos monotônicos; polling do frontend com intervalo limitado.

### Critérios de aceite

- Upload não aguarda provider.
- Status evolui e termina em `COMPLETED`/`FAILED`.
- Reinício não duplica policy/comparison.
- Falha de IA permite consultar erro e, se aplicável, repetir.
- Comparação determinística pode ser consultada antes da avaliação e da pontuação terminarem.

### Fora de escopo

Escala horizontal e fila durável.

### Questões abertas

Executar worker no mesmo processo ou comando separado no ambiente final; ambos devem respeitar as mesmas portas.

### Testes futuros

Teste end-to-end com fake providers, restart, concorrência e polling.

## SPEC-015 — Normalização por catálogo D&O

### Objetivo e contexto

Relacionar cada evidência aos conceitos do catálogo DO-001 a DO-044 (documento 3, prompt 4; dicionário D&O).

### Comportamento, entradas e saídas

Entrada: evidências validadas de uma apólice e catálogo na `knowledge_base_version` vigente. Saída: `ConceptOccurrence[]` e evento `EvidenceNormalized`.

### Dependências

`AIOrchestrator` (`P-NORMALIZE-001`), `ConceptCatalog`, `PolicyRepository`.

### Regras e erros

Classificar tipo de ocorrência, relação terminológica, status documental e contratação; não unir conceitos distintos; correspondência temática não é equivalência; menção em Condições Gerais é no máximo `NOT_PROVEN`; ocorrência ambígua guarda hipóteses e recebe `BROKER_GUIDANCE`. `concept_id` inexistente é rejeitado.

### Critérios de aceite

- Toda ocorrência referencia evidência existente e conceito existente.
- Os 31 conceitos ponderados são pesquisados em toda apólice; os não encontrados ficam `NOT_FOUND`.
- A mesma evidência pode sustentar mais de um conceito apenas como hipóteses explícitas.
- Versão do catálogo é registrada.

### Fora de escopo

Edição do catálogo pela UI.

### Questões abertas

Variantes de DO-036 a DO-044: `PENDING_BUSINESS_VALIDATION`.

### Testes futuros

Variantes AKAD/KOVR do dicionário como fixtures, termos ambíguos, conceitos relacionados e Condições Gerais isoladas.

## SPEC-016 — Pontuação ponderada

### Objetivo e contexto

Calcular pontos, scores, completude e pareceres de forma determinística (documento 2; documento 3, prompts 8, 9 e 11).

### Comportamento, entradas e saídas

Entrada: `ConceptAssessment[]` validados e pesos do catálogo. Saída: `ScoreSummary` por apólice (perfil `BASE`), `verdict` por item e evento `ScoringCompleted`.

### Dependências

`ScoringService` do domínio, `ConceptCatalog`, `ComparisonRepository`.

### Regras e erros

Aplicar as fórmulas da seção 6.4 da base de conhecimento com `Decimal`; somente conceitos ativos entram no máximo possível; conceitos relacionados não somam peso duas vezes; parecer pela tabela da seção 4.6 (limiar 0,10); ausência de evidência não vira vantagem; percentuais com uma casa decimal na apresentação.

### Critérios de aceite

- Com todos os conceitos ativos, `max_possible = 207`.
- Mesma entrada produz os mesmos números e pareceres.
- Exclusão expressa resulta em 0 pontos para o conceito.
- Score Documental e Índice de Completude são calculados sempre.
- Indicadores adicionais (contagens, peso inconclusivo, críticas sem confirmação, cinco conceitos de maior impacto) estão presentes.

### Fora de escopo

Pesos editáveis pelo usuário final.

### Questões abertas

Pesos dos conceitos hoje sem peso.

### Testes futuros

Tabela de casos por escala, arredondamento, relacionados, ambos excluídos, evidência não comparável e fixture do exemplo 77,6 % × 79,4 %.

## SPEC-017 — Decisão por perfil de risco e resumo executivo

### Objetivo e contexto

Produzir a decisão em três níveis — técnico geral, por perfil e condicionado — sem substituir a análise documental (documento 2, seção 8; documento 3, prompts 12 e 13).

### Comportamento, entradas e saídas

Entrada: `ScoreSummary` base, perfil selecionado opcional e avaliações. Saída: `ScoreSummary` por perfil com pesos ajustados e `ExecutiveSummary` (`P-EXECUTIVE-001`).

### Dependências

`ScoringService`, `AIOrchestrator`, parâmetros `profile_multiplier`, `close_score_threshold` e `min_completeness`.

### Regras e erros

Calcular todos os perfis; preservar pesos-base e registrar motivo dos pesos ajustados; `decision_mode = CONDITIONED` quando a diferença de score for menor que o limiar, a completude for baixa ou um conceito crítico inconclusivo decidir o resultado; explicar divergência entre score e leitura qualitativa; terminar com `BROKER_GUIDANCE` se houver informação incompleta. A IA não altera números.

### Critérios de aceite

- Cada perfil mostra vencedora no perfil, score ajustado, conceitos decisivos, limitações, sensibilidade e orientação.
- Resumo contém todos os itens da seção 7.2 da base de conhecimento.
- Resumo que cite número diferente do calculado é rejeitado.

### Fora de escopo

Recomendação de compra incondicional.

### Questões abertas

Valores definitivos de `profile_multiplier`, `close_score_threshold` e `min_completeness`: `PENDING_BUSINESS_VALIDATION`.

### Testes futuros

Sensibilidade por perfil, empate técnico, completude baixa, crítico inconclusivo e divergência score × qualitativo.

## SPEC-018 — Consulta por conceito

### Objetivo e contexto

Permitir consultas por conceito-base, variante, cobertura, seguradora, número da apólice, documento, cláusula, página, nível de importância, peso, status e diferença entre apólices (documento 3, prompt 6).

### Comportamento, entradas e saídas

Filtros estruturados em `GET /concepts/{concept_id}/occurrences` e `GET /search`; pergunta em linguagem natural opcional em `POST /queries`, respondida por `P-QUERY-001` sobre registros já recuperados.

### Dependências

`ConceptCatalog`, repositories, `AIOrchestrator`.

### Regras e erros

Responder só com evidências armazenadas; cada resposta traz conceito, termo, trecho literal, documento/cláusula/página, interpretação, status, peso, impacto e orientação; se a base não bastar, dizer o limite e aplicar `BROKER_GUIDANCE`.

### Critérios de aceite

- Busca por variante encontra o conceito-base correspondente.
- Resposta sem evidência não é exibida como fato.
- Paginação e limites respeitados.

### Fora de escopo

Busca full-text em todo o texto bruto.

### Questões abertas

Nenhuma.

### Testes futuros

Variantes, filtros combinados, consulta sem resultado e injection na pergunta.

## SPEC-019 — Controle de qualidade

### Objetivo e contexto

Auditar o processamento antes de apresentar o resultado (documento 3, prompt 16).

### Comportamento, entradas e saídas

Entrada: comparação pontuada. Saída: `quality_gate` com cada verificação, resultado e limitação; comparação vai para `COMPLETED` ou `PARTIAL`.

### Dependências

Repositories, `ScoringService`.

### Regras e erros

Verificar: arquivos lidos, OCR e confiança, páginas processadas, classificação de documentos, página e cláusula nas evidências, todos os conceitos ponderados pesquisados, mesmos critérios nas duas apólices, contratação separada de presença, ausência separada de exclusão, pesos preservados, cálculos corretos, limites e prazos em bases equivalentes, completude calculada, críticos inconclusivos destacados, recomendação compatível com evidências e orientação ao usuário. Verificação negativa gera correção ou limitação explícita com `BROKER_GUIDANCE`.

### Critérios de aceite

- Resultado nunca é exibido como completo com verificação negativa oculta.
- O checklist aparece na API e pode ser mostrado na UI.

### Fora de escopo

Revisão humana dentro do sistema.

### Questões abertas

Nenhuma.

### Testes futuros

Um caso por verificação negativa.
