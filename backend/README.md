# ClauseAI backend

Backend FastAPI da fundação do MVP. A aplicação expõe apenas o health check nesta etapa; as camadas e contratos necessários para evolução foram preparados sem conectar Firebase ou providers de IA.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
```

## Run

```powershell
python -m uvicorn app.main:app --reload
```

Health check: `GET http://localhost:8000/health`.

## Quality

```powershell
python -m pytest
python -m ruff check .
python -m ruff format --check .
python -m mypy app
```

## Architecture

`domain` contém contratos independentes de framework; `application` conterá casos de uso; `infrastructure` implementará adapters; `presentation` contém o contrato HTTP; `shared` contém configuração, logs e exceções transversais. O composition root está em `app/main.py`.
