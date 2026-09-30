# ClauseAI backend

API FastAPI do MVP: recebe apólices D&O em PDF, DOCX ou imagem (JPG, PNG), extrai evidências com o **Gemini 3.5 Flash Lite** (texto nativo de PDF e DOCX, lido em faixas de páginas, ou OCR multimodal para PDF escaneado e imagem), normaliza pelo catálogo D&O, avalia cada conceito também com o Gemini e calcula pontuação, perfis de risco, resumo executivo e checklist de qualidade de forma determinística. Regras de negócio: [`docs/domain/DO_KNOWLEDGE_BASE.md`](../docs/domain/DO_KNOWLEDGE_BASE.md). Contratos: [`docs/architecture/PERSISTENCE_AND_API.md`](../docs/architecture/PERSISTENCE_AND_API.md).

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
Copy-Item .env.example .env   # já existe um .env em branco; basta preenchê-lo
```

### Variáveis obrigatórias (`backend/.env`)

| Variável | Onde obter |
|---|---|
| `GEMINI_API_KEY` | Google AI Studio → API keys |
| `GEMINI_MODEL` | identificador exato do Gemini 3.5 Flash Lite na sua conta (padrão `gemini-3.5-flash-lite`) |
| `FIREBASE_CREDENTIALS_PATH` **ou** `FIREBASE_PROJECT_ID` + `FIREBASE_CLIENT_EMAIL` + `FIREBASE_PRIVATE_KEY` | Firebase Console → Configurações do projeto → Contas de serviço → Gerar nova chave privada |

Sem essas variáveis o servidor não sobe e informa exatamente o que falta.

- Os dados ficam no **Firestore**, que funciona no plano gratuito (Spark).
- Os arquivos originais (PDF, DOCX, imagem) ficam em `backend/.data/uploads` (`STORAGE_BACKEND=local`, padrão). Para usar o Firebase Storage, que exige o plano Blaze, defina `STORAGE_BACKEND=firebase` e `FIREBASE_STORAGE_BUCKET`.
- Para rodar sem Firebase (dados só em memória), use `PERSISTENCE_BACKEND=memory`; a chave do Gemini continua obrigatória, salvo no modo local abaixo.
- Toda rota em `/api/v1` exige `Authorization: Bearer <ID token do Firebase>` (conta anônima criada pelo navegador). `AUTH_BACKEND=firebase` é o padrão e usa as mesmas credenciais do Firebase.
- Cada apólice é apagada `RETENTION_HOURS` (padrão 24) horas após o envio. As cotas por navegador ficam em `MAX_ACTIVE_POLICIES_PER_OWNER`, `UPLOADS_PER_HOUR` e `COMPARISONS_PER_HOUR`.

### Rodar sem credenciais (modo local)

Para desenvolver ou testar a interface sem Gemini nem Firebase, use estas variáveis em `backend/.env`:

```
PERSISTENCE_BACKEND=memory
STORAGE_BACKEND=local
AI_PROVIDER=local
AUTH_BACKEND=fake
```

Com `AUTH_BACKEND=fake`, o token `Bearer dev-<uid>` identifica o navegador `<uid>` (ex.: `Authorization: Bearer dev-alice`). Recusado com `APP_ENV=production`.

Com `AI_PROVIDER=local`, extrator, avaliador e redator são determinísticos e não chamam modelo. O extrator só lê texto nativo (PDF com texto e DOCX) e cita a linha que contém uma variante do catálogo. PDF escaneado e imagem não geram ocorrências. Os resultados servem para testar o fluxo, não têm valor de negócio. O modo é recusado com `APP_ENV=production`. Os dados somem ao reiniciar o servidor.

Limites úteis (opcionais): `EXTRACTION_PAGES_PER_CALL` (páginas de texto nativo por chamada de extração, padrão 30), `AI_MAX_ATTEMPTS`, `AI_TIMEOUT_SECONDS` e `MAX_UPLOAD_MB`. Veja `.env.example`.

## Run

```powershell
python -m uvicorn app.main:app --reload
```

- Health check: `GET http://localhost:8000/health`
- Documentação interativa: `http://localhost:8000/api/v1/docs`

## Automação da base de conhecimento

O catálogo D&O (44 conceitos, 31 com peso, soma 207) é gerado a partir de `docs/domain/`:

```powershell
python scripts/build_knowledge_base.py --version 2026.09.1
```

Rode novamente sempre que a planilha em `docs/domain/sources/` ou o `DO_KNOWLEDGE_BASE.md` mudarem; o script falha se a soma dos pesos não for 207.

## Apólices de exemplo

`scripts/generate_sample_policies.py` gera as 5 apólices D&O fictícias de `Policy/` (PDF e DOCX, mesmo conteúdo, sem valor contratual). Precisa do extra opcional `samples` (reportlab):

```powershell
python -m pip install -e ".[dev,samples]"
python scripts/generate_sample_policies.py [--output-dir ..\Policy] [--only 03]
```

A geração é determinística. Os fatos de cada apólice estão em `scripts/sample_policies/catalog.py`. Detalhes e a matriz de diferenças em [`docs/development/getting-started.md`](../docs/development/getting-started.md).

## Quality

```powershell
python -m pytest
python -m ruff check .
python -m ruff format --check .
python -m mypy app
```

Os testes usam dublês dos provedores de IA e persistência em memória; não chamam o Gemini nem o Firebase.

## Architecture

| Camada | Conteúdo |
|---|---|
| `domain` | entidades, vocabulários, travas de regra de negócio (`guardrails`), consolidação por apólice e `scoring` determinístico |
| `application` | casos de uso de apólices, comparações e conceitos; comandos e erros públicos |
| `infrastructure` | cliente Gemini (extração, avaliação e conclusão), IA local determinística, prompts versionados, Firestore/Storage, memória, leitura de PDF e de DOCX, base de conhecimento e worker em fila |
| `presentation` | rotas `/api/v1`, DTOs e envelope de erro |

Fluxo: `POST /policies` grava os arquivos e responde `202`; o worker extrai cada documento, aplica as travas, consolida as ocorrências e define o status (`READY`, `ATTENTION` ou `FAILED`). `POST /comparisons` responde `202`; o worker compara fatos, pede ao Gemini a avaliação por conceito, calcula scores e perfis, gera o resumo e roda o checklist de qualidade. O composition root está em `app/main.py`; o app é criado no primeiro acesso a `app.main:app`, então importar o módulo não exige configuração.

## Formatos e erros

Aceitos: PDF, DOCX, JPG e PNG, detectados pelo conteúdo. Em DOCX, a "página" da evidência é um bloco lógico numerado a partir de 1 (quebra de página, quebra de seção ou 3.500 caracteres). Arquivos protegidos ou corrompidos respondem `422` (`DOCX_PROTECTED`, `DOCX_CORRUPTED`, `PDF_PROTECTED`, `PDF_CORRUPTED`); XLSX, PPTX e outros zips, `415`. Falhas da IA têm código próprio e `retryable`, e a comparação vira `PARTIAL` se a avaliação por conceito ou o resumo falhar. Documento `FAILED` expõe `failure`, `failure_code` e `failure_retryable` (falha inesperada grava `UNEXPECTED_ERROR`, retryable). Falha de storage no envio responde `503 STORAGE_UNAVAILABLE` (retryable), apaga os originais já gravados e não cria a apólice. Detalhes em `docs/specs/SDD_SPECIFICATIONS.md` (SPEC-001, SPEC-004 e SPEC-009).
