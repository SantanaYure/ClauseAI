# ClauseAI

Plataforma inteligente para análise e comparação de apólices D&O, desenvolvida como Projeto Final do Instituto de Inteligência Artificial Aplicada (I2A2).

## Descrição do projeto

O ClauseAI recebe apólices D&O em PDF, imagem (JPG, PNG) ou DOCX, extrai o conteúdo por leitura nativa (PDF e DOCX) ou OCR com IA generativa (imagem e PDF digitalizado), normaliza cláusulas e coberturas contra um dicionário D&O, armazena as evidências de forma estruturada e compara duas apólices conceito a conceito. A comparação aceita PDF × PDF, DOCX × DOCX e PDF × DOCX. Ela aplica pesos técnicos, calcula Score de Aderência e Índice de Completude, avalia perfis de risco e apresenta um resumo executivo condicionado, sempre com o trecho literal, a cláusula e a página de origem. Quando a informação é ambígua, incompleta ou não comprovada, o sistema orienta: “Consulte seu corretor de seguros.”

As regras de negócio estão em [`docs/domain/DO_KNOWLEDGE_BASE.md`](docs/domain/DO_KNOWLEDGE_BASE.md) e a documentação técnica em [`docs/`](docs/README.md).

## Visão geral

O repositório contém um frontend React/TypeScript/SCSS e um backend Python/FastAPI organizados como monólito modular. O fluxo completo — envio, extração, organização, armazenamento, consulta, comparação e apresentação — está implementado; o que falta configurar são as credenciais em `backend/.env`.

## Stack

- Frontend: React, TypeScript, Vite e SCSS.
- Backend: Python, FastAPI e Uvicorn.
- Qualidade: Ruff, Ruff Formatter, mypy, pytest, ESLint, Prettier e Vitest.
- Integrações: Firebase Firestore (arquivos originais em pasta local ou, opcionalmente, no Firebase Storage), Gemini 3.5 Flash Lite (extração, OCR multimodal, avaliação por conceito e resumo).
- Automações: Python (`backend/scripts/`).

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
├── Projeto_Final_Artefatos/
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

Nunca use credenciais reais no repositório: o `.env` é ignorado pelo Git. Preencha `backend/.env` (chave do Gemini e credenciais do Firebase; veja a tabela em [`backend/README.md`](backend/README.md)) e, se necessário, `frontend/.env`. Sem as variáveis obrigatórias o backend não sobe e lista o que falta.

## Escopo atual

Implementado:

- **Frontend:** cinco telas navegáveis e mobile first (Início, Apólices, Comparar, Conceitos, Histórico), ligadas à API.
- **Backend:** upload de apólices com vários documentos, processamento assíncrono, extração com Gemini (texto nativo de PDF e DOCX ou OCR multimodal de imagem e PDF digitalizado), normalização pelo catálogo D&O, comparação com avaliação por conceito pelo Gemini, pontuação ponderada, perfis de risco, resumo executivo, checklist de qualidade e consulta por conceito.
- Persistência em Firestore e arquivos em pasta local (Firebase Storage opcional), logs estruturados com correlação e testes automatizados.

Não implementado: autenticação, fila durável e endpoints `/documents` isolados. A sequência está em [`docs/ROADMAP.md`](docs/ROADMAP.md).

## Integrantes

<!-- Preencher com nome e contato de cada integrante do grupo antes da entrega. -->

- A definir.

## Licença

Este projeto está licenciado sob a [licença MIT](LICENSE).
