# A4/A5 — Persistência e API REST

## 1. Firestore

O Firestore armazena metadados e estruturas consultáveis. O original (PDF, imagem ou DOCX) fica no armazenamento de arquivos (ver ADR-022). O resultado bruto da IA é separado do modelo estruturado para auditoria e para evitar que uma resposta não validada seja usada na UI.

### Implementação atual (MVP)

O backend grava hoje um modelo mais enxuto, com o mesmo conteúdo:

```text
policies/{policy_id}                                  # apólice + documentos (metadados, status, falha)
policies/{policy_id}/concept_occurrences/{concept_id} # ocorrências consolidadas com evidências literais
comparisons/{comparison_id}                           # itens, avaliações, scores, perfis, resumo e Quality Gate
```

Os originais ficam em `policies/{policy_id}/{document_id}.{pdf|png|jpg|docx}`, sem URL pública: por padrão numa pasta local do backend (`STORAGE_BACKEND=local`, `backend/.data/uploads`) e, opcionalmente, no Firebase Storage (`STORAGE_BACKEND=firebase`, plano Blaze) — ver ADR-022. A base de conhecimento é um arquivo JSON versionado no código (`backend/app/infrastructure/knowledge_base/knowledge_base.json`), gerado pelo script Python `backend/scripts/build_knowledge_base.py` a partir de `docs/domain/`. As coleções abaixo continuam como alvo de evolução (histórico de jobs, resultado bruto da IA e `processed_events`).

### Coleções (modelo de referência)

```text
documents/{document_id}
documents/{document_id}/processing_jobs/{processing_id}
documents/{document_id}/extraction_results/{extraction_result_id}
documents/{document_id}/evidences/{evidence_id}
policies/{policy_id}
policies/{policy_id}/concept_occurrences/{occurrence_id}
knowledge_base/{version}/concepts/{concept_id}
knowledge_base/{version}/profiles/{profile_id}
comparisons/{comparison_id}
comparisons/{comparison_id}/items/{item_id}
comparisons/{comparison_id}/assessments/{policy_id}_{concept_id}
comparisons/{comparison_id}/scores/{policy_id}_{profile}
processed_events/{event_id}
```

As entidades mínimas do documento 3 (prompt 5) mapeiam assim: **Documento** → `documents`; **Evidência** → `evidences`; **Conceito** → `knowledge_base/.../concepts`; **Resultado por apólice** → `assessments`; **Comparação** → `items`; **Decisão** → `scores` e `executive_summary` em `comparisons`.

### `knowledge_base`

Carregada a partir de [`domain/DO_KNOWLEDGE_BASE.md`](../domain/DO_KNOWLEDGE_BASE.md) e dos arquivos em `domain/sources/` por um comando de seed versionado. Cada versão é imutável; uma comparação grava a `knowledge_base_version` usada. Conceito:

```json
{
  "concept_id": "DO-036",
  "domain": "Limites",
  "base_concept": "LMG – Limite Máximo de Garantia",
  "variants": ["LMG", "limite máximo de garantia"],
  "importance": "CRITICAL",
  "technical_weight": "10",
  "weight_justification": "Capacidade financeira máxima da apólice.",
  "evaluation_criterion": "valor, moeda, agregado/por evento, sublimites, erosão, franquia",
  "related_concepts": [],
  "active": true,
  "pending_business_validation": ["variants"]
}
```

### `evidences`

`evidence_id`, `document_id`, `page`, `clause_ref`, `literal_text`, `content_kind`, `extraction_method`, `confidence`, `low_confidence`, `version`. Registros não são sobrescritos; correções criam nova versão.

**Origem em DOCX.** DOCX não tem páginas fixas. O backend divide o texto em blocos lógicos numerados a partir de 1, e o número do bloco vai em `page`. Um bloco novo começa em quebra de página explícita, quebra de seção que inicia página ou a cada 3.500 caracteres, sempre entre parágrafos. A numeração é determinística: o mesmo arquivo gera sempre os mesmos blocos. `extraction_method` é `NATIVE`. Não existe `section_ref` no modelo de evidência atual. A interface mostra "bloco" para DOCX (SPEC-004).

### `documents/{document_id}`

```json
{
  "document_id": "doc_01",
  "original_filename": "apolice.pdf",
  "content_type": "application/pdf",
  "file_kind": "SEARCHABLE_PDF",
  "document_type": "POLICY",
  "insurer": "Não identificado",
  "version": null,
  "ocr_required": false,
  "extraction_quality": "HIGH",
  "size_bytes": 345678,
  "checksum_sha256": "...",
  "storage_key": "documents/doc_01/original.pdf",
  "status": "EXTRACTING",
  "uploaded_at": "2026-09-20T12:00:00Z",
  "page_count": 18,
  "correlation_id": "cor_01",
  "failure": null,
  "schema_version": 1
}
```

`file_kind` aceita `SEARCHABLE_PDF`, `SCANNED_PDF`, `IMAGE` e `DOCX`. Em DOCX, `ocr_required` é sempre `false` e `page_count` é o total de blocos lógicos (não há páginas fixas).

### `processing_jobs`

Guarda `processing_id`, `entity_type`, `entity_id`, `status`, `attempt`, `max_attempts`, timestamps, último evento e erro sanitizado. O documento pai é a fonte rápida para status público; o subdocumento é o histórico operacional.

### `extraction_results`

Guarda `raw_response` apenas com política de acesso restrita, `parsed_payload`, `validation_errors`, `model`, `provider`, `prompt_version`, tokens, latência e custo estimado. Se a retenção do texto bruto for proibida, persistir hash e payload sanitizado, mantendo as evidências extraídas.

### `policies/{policy_id}`

```json
{
  "policy_id": "pol_01",
  "document_id": "doc_01",
  "schema_version": 1,
  "status": "STORED",
  "insurer": {"value": "Exemplo", "source_text": "...", "page": 1, "confidence": 0.96},
  "insured": {"value": null, "missing_reason": "NOT_FOUND"},
  "validity": {"start": "2026-01-01", "end": "2026-12-31"},
  "limits": [],
  "deductibles": [],
  "coverages": [],
  "exclusions": [],
  "clauses": [],
  "source_extraction_id": "ext_01",
  "created_at": "2026-09-20T12:03:00Z",
  "updated_at": "2026-09-20T12:03:00Z"
}
```

### `comparisons/{comparison_id}`

Contém os dois IDs, `selected_profile`, `knowledge_base_version`, status, `deterministic_result`, `executive_summary`, `quality_gate`, modelos/prompts usados, timestamps, correlação e falha. Itens, avaliações e scores ficam em subcoleções para leitura paginada; no MVP, também é aceitável um array limitado se o tamanho máximo for validado. Pesos ajustados por perfil ficam em `scores`, junto do motivo do ajuste, sem alterar `knowledge_base`.

### `processed_events`

Chave por `event_id`, com `handler_name`, `processed_at`, `entity_id` e resultado. Usada para deduplicação atômica. O handler deve verificar/gravar esse marcador de forma segura; a operação de negócio e o marcador devem ser transacionais quando possível.

## 2. Índices e consultas

- `documents`: `status` + `uploaded_at desc`.
- `policies`: `status` + `updated_at desc`; `insurer` + `updated_at desc`.
- `concept_occurrences` (collection group): `concept_id` + `contract_status`.
- `comparisons`: `created_at desc` e, futuramente, `policy_a_id`/`policy_b_id`.
- Não indexar texto integral de cláusulas no MVP.

Limitar listas, tamanho de payload e paginação. O cliente não deve buscar todos os documentos sem cursor.

## 3. API REST

Base path: `/api/v1`. Todos os endpoints aceitam e respondem JSON, exceto o upload multipart. Respostas de criação assíncrona usam `202 Accepted`. Documentação interativa em `/api/v1/docs`.

Implementados: `POST/GET /policies`, `GET/DELETE /policies/{id}`, `POST/GET /comparisons`, `GET /comparisons/{id}`, `GET /concepts`, `GET /concepts/{id}`, `GET /concepts/{id}/occurrences` e `POST /queries`. Os endpoints `/documents` abaixo continuam planejados: no MVP, os documentos são enviados e consultados pela apólice.

### POST `/policies`

**Objetivo:** criar uma apólice com todos os seus documentos de uma vez (tela “Adicionar apólice”).

**Request:** `multipart/form-data` com `insurer?`, `name?` e um ou mais campos `files[]`, cada um acompanhado de `document_types[]` (`POLICY`, `SPECIFICATION`, `GENERAL_CONDITIONS`, `ENDORSEMENT`…). Cada arquivo (PDF, JPG, PNG ou DOCX) passa pelas mesmas validações de `POST /documents` e gera um `Document` ligado à apólice.

**Response `202`:** `policy_id`, `status: PROCESSING`, `document_ids[]`, `correlation_id`.

**Erros:** os de `POST /documents`, mais `422 INVALID_DOCUMENT_TYPE`. O envio é tudo ou nada: um arquivo inválido recusa o lote inteiro e a mensagem cita o nome do arquivo. Qualquer falha de storage responde `503 STORAGE_UNAVAILABLE` (`details.retryable = true`), apaga os originais já gravados e não cria a apólice.

### POST `/documents`

**Objetivo:** receber PDF, imagem (JPG, PNG) ou DOCX, validar o tipo pelo conteúdo, o tamanho e a integridade, salvar o original e iniciar processamento. Com `policy_id`, acrescenta o documento (por exemplo, um endosso) a uma apólice existente.

**Request:** `multipart/form-data`, campo `file`; opcional `policy_id`, `document_type` e `metadata` JSON limitado.

**Response `202`:**

```json
{
  "document_id": "doc_01",
  "status": "UPLOADED",
  "correlation_id": "cor_01",
  "status_url": "/api/v1/documents/doc_01/status"
}
```

**Erros:** `400 INVALID_FILE`, `413 FILE_TOO_LARGE`, `415 UNSUPPORTED_MEDIA_TYPE`, `422` (`DOCX_PROTECTED`, `DOCX_CORRUPTED`, `PDF_PROTECTED`, `PDF_CORRUPTED`, `INVALID_METADATA`), `503 STORAGE_UNAVAILABLE`.

**Formatos e detalhe do erro.** Aceitos: `application/pdf`, `image/jpeg`, `image/png` e `application/vnd.openxmlformats-officedocument.wordprocessingml.document` (DOCX). O tipo vem do conteúdo: DOCX é um zip com `[Content_Types].xml` e `word/document.xml`. A mensagem vem em português:

| Situação | HTTP e código | `message` |
|---|---|---|
| DOCX protegido por senha ou `.doc` legado | `422 DOCX_PROTECTED` | "O arquivo {nome} está protegido por senha ou está em formato antigo (.doc). Remova a proteção e envie novamente como .docx." |
| DOCX corrompido | `422 DOCX_CORRUPTED` | "O arquivo {nome} está corrompido e não pôde ser aberto. Gere o DOCX novamente." |
| PDF protegido por senha | `422 PDF_PROTECTED` | "O arquivo {nome} está protegido por senha. Remova a proteção e envie novamente." |
| PDF corrompido | `422 PDF_CORRUPTED` | "O arquivo {nome} está corrompido e não pôde ser aberto. Gere o PDF novamente." |
| Zip acima de 20 × `MAX_UPLOAD_MB` descompactado | `413 FILE_TOO_LARGE` | "O conteúdo do arquivo {nome} excede o limite permitido." |
| XLSX, PPTX, `.docm`, `.dotx`, outros zips e arquivo renomeado | `415 UNSUPPORTED_MEDIA_TYPE` | "Formato não aceito: {nome}. Use PDF, DOCX, JPG ou PNG." |

As regras de decisão entre "protegido", "corrompido" e "não suportado" estão na SPEC-001.

**Erros do processamento (assíncrono).** Não mudam o `202` do upload. Documento com falha fica `FAILED`. Os documentos da apólice (`GET /policies/{id}`) trazem `failure` (mensagem), `failure_code` (código do erro do worker, ou `UNEXPECTED_ERROR` para falha inesperada) e `failure_retryable` (`true` em `UNEXPECTED_ERROR` e nos códigos de IA retryable). Os dois campos novos são aditivos: `null` e `false` quando não há falha. Códigos: `DOCX_WITHOUT_TEXT` (422, "O arquivo {nome} não contém texto legível."), os de arquivo acima e os da IA: `AI_AUTH_FAILED` (503), `AI_MODEL_NOT_FOUND` (503), `AI_BAD_REQUEST` (502), `AI_OUTPUT_TRUNCATED` (422), `MODEL_UNAVAILABLE` (503), `MODEL_RATE_LIMITED` (503) e `INVALID_MODEL_OUTPUT` (503). Todos os de IA levam `details.retryable` no envelope de erro: `true` para `MODEL_UNAVAILABLE`, `MODEL_RATE_LIMITED` e `INVALID_MODEL_OUTPUT`; `false` para os demais. Mensagens completas na SPEC-004.

### GET `/documents`

**Objetivo:** listar documentos com paginação.

**Query:** `status?`, `limit` (1–100, default 20), `cursor?`.

**Response `200`:**

```json
{"items":[{"document_id":"doc_01","original_filename":"apolice.pdf","status":"COMPLETED","uploaded_at":"2026-09-20T12:00:00Z"}],"next_cursor":null}
```

### GET `/documents/{document_id}`

**Objetivo:** consultar metadados e links/IDs relacionados; não retorna o binário por padrão.

**Responses:** `200`; `404 DOCUMENT_NOT_FOUND`.

### GET `/documents/{document_id}/status`

**Objetivo:** consultar estado resumido do processamento.

```json
{
  "document_id": "doc_01",
  "status": "EXTRACTING",
  "processing_id": "prc_01",
  "attempt": 1,
  "updated_at": "2026-09-20T12:01:00Z",
  "failure": null,
  "correlation_id": "cor_01"
}
```

Estados públicos: `UPLOADED`, `PROCESSING`, `EXTRACTING`, `VALIDATING`, `COMPLETED`, `FAILED`.

### GET `/policies`

**Objetivo:** listar apólices armazenadas e aptas para comparação.

**Query:** `status?`, `document_id?`, `limit`, `cursor`.

**Response `200`:** item resumido com `policy_id`, `document_id`, seguradora se disponível, vigência se disponível e `status`.

### DELETE `/policies/{policy_id}`

**Objetivo:** excluir a apólice, as ocorrências e evidências (inclusive a subcoleção `concept_occurrences`) e os arquivos originais no armazenamento.

**Responses:** `204` sem corpo; `404 POLICY_NOT_FOUND`; `409 POLICY_PROCESSING` enquanto a apólice estiver em processamento. As comparações concluídas não são alteradas.

### GET `/policies/{policy_id}`

**Objetivo:** obter estrutura completa, evidências e campos ausentes/ambíguos.

**Responses:** `200`; `404 POLICY_NOT_FOUND`; `409 POLICY_NOT_READY`.

### POST `/comparisons`

**Objetivo:** criar comparação assíncrona de exatamente duas apólices.

**Request:**

```json
{"policy_a_id":"pol_01","policy_b_id":"pol_02","selected_profile":"FINANCIAL"}
```

`selected_profile` é opcional; todos os perfis são calculados e o selecionado é destacado.

**Response `202`:**

```json
{"comparison_id":"cmp_01","status":"REQUESTED","correlation_id":"cor_02"}
```

**Erros:** `400 SAME_POLICY`, `404 POLICY_NOT_FOUND`, `409 POLICY_NOT_READY`, `422 INVALID_POLICY_COUNT`, `503 EVENT_BUS_UNAVAILABLE`.

### GET `/comparisons`

**Objetivo:** listar comparações para a tela Histórico.

**Query:** `status?`, `decision_mode?`, `limit`, `cursor`.

**Response `200`:** itens com `comparison_id`, `created_at`, `status`, `policies` (A/B com seguradora), `adherence_a`, `adherence_b`, `decision_mode` e, quando `FAILED`, `failure_reason` (mensagem), `failure_code` e `failure_retryable` (campos aditivos; `null` e `false` nas demais).

### GET `/comparisons/{comparison_id}`

**Objetivo:** consultar status e resultado parcial/final.

**Query:** `profile?` (`BASE`, `FINANCIAL`, `INTERNATIONAL`, `REGULATORY`, `TAIL`, `LABOR_REPUTATIONAL`), `importance?`.

**Response `200`:**

```json
{
  "comparison_id":"cmp_01",
  "status":"COMPLETED",
  "knowledge_base_version":"2026.09.1",
  "policies":{"a":"pol_01","b":"pol_02"},
  "items":[{
    "concept_id":"DO-002","base_concept":"Garantia A","importance":"CRITICAL","weight":"10",
    "a":{"term":"...","evidence_ids":["ev_1"],"contract_status":"CONTRACTED","base_result":"1.00","adjustment_factor":"1.00","weighted_points":"10.00"},
    "b":{"term":"...","evidence_ids":["ev_9"],"contract_status":"NOT_PROVEN","base_result":"0.25","adjustment_factor":"0.50","weighted_points":"1.25","justification":"..."},
    "main_difference":"...","verdict":"INCONCLUSIVE","confidence":"MEDIUM",
    "user_guidance":"Consulte seu corretor de seguros."
  }],
  "scores":[{"policy":"a","profile":"BASE","raw_score":"...","max_possible":"207","adherence_score":"0.776","documentary_score":"...","completeness_index":"..."}],
  "executive_summary":{"decision_mode":"CONDITIONED","conclusion":"...","broker_guidance":"Consulte seu corretor de seguros."},
  "quality_gate":{"passed":false,"checks":[]},
  "correlation_id":"cor_02"
}
```

Estados: `REQUESTED`, `DETERMINISTIC_COMPLETED`, `ASSESSING`, `SCORED`, `SUMMARIZING`, `COMPLETED`, `PARTIAL`, `FAILED`. `PARTIAL` ocorre quando a avaliação por conceito ou a redação do resumo falha (SPEC-009). Na avaliação, os conceitos que dependiam da IA ficam com 0 ponto, confiança baixa e evidência insuficiente. A falha fica em `failure` com `code`, `message` e `retryable`; a API expõe `failure_reason` (mensagem), `failure_code` e `failure_retryable` na listagem de comparações. Números trafegam como números JSON; o cálculo interno usa `Decimal` e arredonda só na saída.

### GET `/concepts`

**Objetivo:** listar o catálogo vigente com importância, peso, justificativa e critério. **Query:** `importance?`, `domain?`, `active?`.

### GET `/concepts/{concept_id}/occurrences`

**Objetivo:** listar ocorrências do conceito nas apólices, com termo, trecho literal, documento, cláusula, página e status. **Query:** `policy_id?`, `insurer?`, `contract_status?`, `limit`, `cursor`.

### GET `/search`

**Objetivo:** consulta estruturada por variante, cobertura, seguradora, número da apólice, documento, cláusula, página, importância, peso e status. Resolve variantes para `concept_id`.

### POST `/queries`

**Objetivo:** pergunta em linguagem natural respondida só com evidências armazenadas (`P-QUERY-001`). **Response:** resposta objetiva, conceito, termo, trecho, fonte, interpretação, status, peso, impacto e orientação.

## 4. Envelope de erro

```json
{
  "error": {
    "code": "EXTRACTION_TIMEOUT",
    "message": "Não foi possível concluir o processamento.",
    "correlation_id": "cor_01",
    "details": {"retryable": true}
  }
}
```

Mensagens públicas não devem expor prompt, credencial, stack trace, resposta integral de provider ou path interno.

## 5. HTTP e concorrência

- `202` para upload/comparação aceitos para processamento.
- `200` para consultas.
- `400/415/422` para entrada inválida.
- `404` para entidade inexistente.
- `409` para estado incompatível.
- `413` para arquivo grande.
- `429` se houver limitação do provider/API.
- `500` apenas para erro inesperado, com log correlacionado.

O endpoint de upload não espera IA. Requisições repetidas com uma chave de idempotência futura devem retornar o mesmo recurso; no MVP, `checksum_sha256` pode ser usado apenas para detectar duplicata, sem rejeitar automaticamente até validação de produto.
