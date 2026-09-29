# Getting started

## Pré-requisitos

- Python 3.12+.
- Node.js 20.19+ e npm.
- PowerShell ou terminal equivalente.

## Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
python -m uvicorn app.main:app --reload
```

Verifique `http://localhost:8000/health`. A resposta esperada é:

```json
{"status":"ok"}
```

## Frontend

Em outro terminal:

```powershell
cd frontend
npm install
Copy-Item .env.example .env
npm run dev
```

Abra `http://localhost:5173`. A tela fará uma chamada para `VITE_API_BASE_URL/health` e mostrará `Online` ou `Offline`.

## Verificação local

```powershell
cd backend
python -m pytest
python -m ruff check .
python -m ruff format --check .
python -m mypy app

cd ..\frontend
npm run test:run
npm run lint
npm run format:check
npm run typecheck
npm run build
```

## Formatos de documento

O sistema aceita PDF, JPG, PNG e DOCX. Para testar, use os exemplos de `Policy/` (PDF) ou envie um DOCX pela tela Apólices. DOCX é lido localmente, sem OCR, e a origem da evidência é um "bloco" numerado, não uma página. Arquivos protegidos ou corrompidos são recusados no envio. Detalhes na SPEC-001 e na SPEC-004.

## Rodar tudo localmente, sem credenciais

Sem chave do Gemini e sem Firebase, edite `backend/.env` (copiado de `.env.example`) com:

```
PERSISTENCE_BACKEND=memory
STORAGE_BACKEND=local
AI_PROVIDER=local
```

Depois suba o backend e o frontend como acima. A IA local é determinística: só lê texto nativo (PDF com texto e DOCX) e cita trechos que contêm termos do catálogo. PDF escaneado e imagem não geram ocorrências. Os dados ficam em memória e somem ao reiniciar. O modo é recusado com `APP_ENV=production`. Detalhes no [`backend/README.md`](../../backend/README.md) e no ADR-026.

## Como a equipe trabalha

O fluxo com subagentes está em [`conventions.md`](conventions.md#equipe-de-subagentes-e-fluxo-de-trabalho).

## Ambiente

Copie os dois `.env.example` para `.env` apenas localmente. Para usar o Gemini e o Firebase de verdade, preencha as variáveis descritas no [`backend/README.md`](../../backend/README.md). O backend não sobe se faltar alguma delas, e informa quais.
