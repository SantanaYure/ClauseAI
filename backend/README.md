# ClauseAI backend

API FastAPI do MVP: recebe apólices D&O em PDF ou imagem, extrai evidências com o **Gemini 3.5 Flash Lite** (leitura nativa de PDF ou OCR multimodal), normaliza pelo catálogo D&O, avalia cada conceito também com o Gemini e calcula pontuação, perfis de risco, resumo executivo e checklist de qualidade de forma determinística. Regras de negócio: [`docs/domain/DO_KNOWLEDGE_BASE.md`](../docs/domain/DO_KNOWLEDGE_BASE.md). Contratos: [`docs/architecture/PERSISTENCE_AND_API.md`](../docs/architecture/PERSISTENCE_AND_API.md).

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
- Os PDFs e imagens originais ficam em `backend/.data/uploads` (`STORAGE_BACKEND=local`, padrão). Para usar o Firebase Storage, que exige o plano Blaze, defina `STORAGE_BACKEND=firebase` e `FIREBASE_STORAGE_BUCKET`.
- Para rodar sem Firebase (dados só em memória), use `PERSISTENCE_BACKEND=memory`; as chaves de IA continuam obrigatórias.

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
| `infrastructure` | cliente Gemini (extração, avaliação e conclusão), prompts versionados, Firestore/Storage, memória, leitura de PDF, base de conhecimento e worker em fila |
| `presentation` | rotas `/api/v1`, DTOs e envelope de erro |

Fluxo: `POST /policies` grava os arquivos e responde `202`; o worker extrai cada documento, aplica as travas, consolida as ocorrências e define o status (`READY`, `ATTENTION` ou `FAILED`). `POST /comparisons` responde `202`; o worker compara fatos, pede ao Gemini a avaliação por conceito, calcula scores e perfis, gera o resumo e roda o checklist de qualidade. O composition root está em `app/main.py`.
