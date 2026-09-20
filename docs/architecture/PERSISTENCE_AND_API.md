# A4/A5 — Persistência e API REST

## 1. Firestore

O Firestore armazena metadados e estruturas consultáveis. O PDF/imagem original fica no Firebase Storage. O resultado bruto da IA é separado do modelo estruturado para auditoria e para evitar que uma resposta não validada seja usada na UI.

### Coleções

```text
documents/{document_id}
documents/{document_id}/processing_jobs/{processing_id}
documents/{document_id}/extraction_results/{extraction_result_id}
policies/{policy_id}
comparisons/{comparison_id}
comparisons/{comparison_id}/items/{item_id}
processed_events/{event_id}
```

### `documents/{document_id}`

```json
{
  "document_id": "doc_01",
  "original_filename": "apolice.pdf",
  "content_type": "application/pdf",
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

Contém os dois IDs, status, `deterministic_result`, `semantic_result`, modelo/prompt semântico, timestamps, correlação e falha. Itens podem ser subcoleção para leitura paginada; no MVP, também é aceitável um array limitado se o tamanho máximo for validado.

### `processed_events`

Chave por `event_id`, com `handler_name`, `processed_at`, `entity_id` e resultado. Usada para deduplicação atômica. O handler deve verificar/gravar esse marcador de forma segura; a operação de negócio e o marcador devem ser transacionais quando possível.

## 2. Índices e consultas

- `documents`: `status` + `uploaded_at desc`.
- `policies`: `status` + `updated_at desc`; filtro por `insurer` somente se necessário.
- `comparisons`: `created_at desc` e, futuramente, `policy_a_id`/`policy_b_id`.
- Não indexar texto integral de cláusulas no MVP.

Limitar listas, tamanho de payload e paginação. O cliente não deve buscar todos os documentos sem cursor.

## 3. API REST

Base path recomendado: `/api/v1`. Todos os endpoints aceitam/responderão JSON, exceto upload multipart. Respostas de criação assíncrona usam `202 Accepted`.

### POST `/documents`

**Objetivo:** receber PDF/imagem, validar extensão/MIME/tamanho, salvar o original e iniciar processamento.

**Request:** `multipart/form-data`, campo `file`; opcional `metadata` JSON limitado.

**Response `202`:**

```json
{
  "document_id": "doc_01",
  "status": "UPLOADED",
  "correlation_id": "cor_01",
  "status_url": "/api/v1/documents/doc_01/status"
}
```

**Erros:** `400 INVALID_FILE`, `413 FILE_TOO_LARGE`, `415 UNSUPPORTED_MEDIA_TYPE`, `422 INVALID_METADATA`, `503 STORAGE_UNAVAILABLE`.

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

### GET `/policies/{policy_id}`

**Objetivo:** obter estrutura completa, evidências e campos ausentes/ambíguos.

**Responses:** `200`; `404 POLICY_NOT_FOUND`; `409 POLICY_NOT_READY`.

### POST `/comparisons`

**Objetivo:** criar comparação assíncrona de exatamente duas apólices.

**Request:**

```json
{"policy_a_id":"pol_01","policy_b_id":"pol_02"}
```

**Response `202`:**

```json
{"comparison_id":"cmp_01","status":"REQUESTED","correlation_id":"cor_02"}
```

**Erros:** `400 SAME_POLICY`, `404 POLICY_NOT_FOUND`, `409 POLICY_NOT_READY`, `422 INVALID_POLICY_COUNT`, `503 EVENT_BUS_UNAVAILABLE`.

### GET `/comparisons/{comparison_id}`

**Objetivo:** consultar status e resultado parcial/final.

**Response `200`:**

```json
{
  "comparison_id":"cmp_01",
  "status":"COMPLETED",
  "policies":{"a":"pol_01","b":"pol_02"},
  "deterministic":{"items":[]},
  "semantic":{"summary":"...","observations":[],"disclaimer":"Não é aconselhamento jurídico."},
  "correlation_id":"cor_02"
}
```

Estados: `REQUESTED`, `DETERMINISTIC_COMPLETED`, `SEMANTIC_PROCESSING`, `COMPLETED`, `FAILED`.

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
