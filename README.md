# ClauseAI

Fundação do MVP acadêmico para análise e comparação inteligente de apólices D&O.

## Visão geral

O repositório contém um frontend React/TypeScript/SCSS e um backend Python/FastAPI organizados como monólito modular. Nesta etapa existe somente a base executável: health check, configuração, logging, tratamento de erros, contratos do Event Bus e testes. Upload, Firebase, IA, extração e comparação permanecem para etapas posteriores.

## Stack

- Frontend: React, TypeScript, Vite e SCSS.
- Backend: Python, FastAPI e Uvicorn.
- Qualidade: Ruff, Ruff Formatter, mypy, pytest, ESLint, Prettier e Vitest.
- Integrações futuras: Firebase/Firestore/Storage, Gemini e Groq.

## Requisitos

- Python 3.12 ou superior.
- Node.js 20.19 ou superior e npm.
- Git.

## Estrutura

```text
ClauseAI/
├── backend/
├── frontend/
├── docs/
├── .editorconfig
├── .gitignore
├── CONTRIBUTING.md
├── LICENSE
└── README.md
```

Veja [`docs/development/getting-started.md`](docs/development/getting-started.md) para o passo a passo local e [`docs/architecture/repository-structure.md`](docs/architecture/repository-structure.md) para as regras de dependência.

## Development Workflow

O fluxo adotado é:

```text
branch curta → commit Conventional Commits → push → Pull Request → CI → squash merge
```

Não desenvolva diretamente em `main`. Consulte [`docs/development/git-workflow.md`](docs/development/git-workflow.md) para convenções de branches, comandos reais do projeto, proteção da `main`, releases, secrets e troubleshooting operacional.

## Execução rápida

Backend:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
python -m uvicorn app.main:app --reload
```

Frontend, em outro terminal:

```powershell
cd frontend
npm install
Copy-Item .env.example .env
npm run dev
```

Abra `http://localhost:5173`. O frontend consulta `http://localhost:8000/health` por padrão.

## Comandos de qualidade

```powershell
# backend
cd backend
python -m pytest
python -m ruff check .
python -m ruff format --check .
python -m mypy app

# frontend
cd ..\frontend
npm run test:run
npm run lint
npm run format:check
npm run typecheck
npm run build
```

## Configuração

Nunca use credenciais reais no repositório. Consulte `backend/.env.example` e `frontend/.env.example`. Firebase e providers de IA aparecem apenas como placeholders nesta fase.

## Escopo atual

Implementado: bootstrap executável, `GET /health`, CORS configurável, correlação, erros padronizados, logging estruturado, `InMemoryEventBus`, configuração tipada e testes básicos.

Não implementado: upload, persistência real, extração, comparação, autenticação, filas externas e regras de seguros.
