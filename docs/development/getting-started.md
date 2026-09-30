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

Variáveis opcionais do frontend (`frontend/.env`):

| Variável | Padrão | Uso |
|---|---|---|
| `VITE_API_BASE_URL` | `http://localhost:8000` | Endereço do backend |
| `VITE_UPLOAD_TIMEOUT_MS` | `300000` (5 min) | Tempo máximo do envio de arquivos |
| `VITE_MAX_UPLOAD_MB` | `20` | Tamanho máximo por arquivo na validação local. Mantenha igual a `MAX_UPLOAD_MB` do backend |

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

O sistema aceita PDF, JPG, PNG e DOCX. Para testar, use as apólices de exemplo de `Policy/` (PDF e DOCX, veja abaixo) ou envie seus próprios arquivos pela tela Apólices. DOCX é lido localmente, sem OCR, e a origem da evidência é um "bloco" numerado, não uma página. Arquivos protegidos ou corrompidos são recusados no envio. Detalhes na SPEC-001 e na SPEC-004.

## Apólices de exemplo

A pasta `Policy/` tem 5 apólices D&O **fictícias**, cada uma em PDF e em DOCX com o mesmo conteúdo. Empresas, seguradoras, números de apólice, processos SUSEP e pessoas são inventados e **não têm valor contratual**. Servem para testar o envio e a comparação. São menores que apólices reais (cerca de 12 páginas cada), então não medem desempenho em documentos longos. A capa e a nota final avisam que são fictícias.

Cada apólice tem um perfil e diferenças de propósito, para a comparação ter o que mostrar:

| Arquivo | Perfil | Diferenças principais |
|---|---|---|
| `01_Aurelius_DO_Energia_Capital_Aberto` | Energia, companhia aberta. LMG R$ 50 mi | Retroatividade ilimitada. Prazo complementar de 36 meses e suplementar de 72. Território mundial. Poluição: exclui só limpeza. Cobertura C contratada. Trabalhista contratada. Reputação R$ 1 mi. Regulatório R$ 2 mi. Limite adicional da Cobertura A de R$ 10 mi |
| `02_Boreal_DO_Industria_Capital_Fechado` | Indústria, capital fechado. LMI R$ 20 mi | Retroatividade datada (01/03/2021). Complementar de 12 meses, sem suplementar. Território só Brasil. Poluição: exclusão absoluta. Cobertura C excluída. Trabalhista só defesa (R$ 1 mi). Sem reputação e sem regulatório. Sem limite adicional da Cobertura A |
| `03_Cerrado_DO_Agronegocio` | Agronegócio, capital fechado. LMG R$ 30 mi | Retroatividade de 24 meses. Complementar de 12 meses, mediante prêmio. Suplementar de 36. Território Brasil e Paraguai. Poluição: cobre ambiental, exceto limpeza. Cobertura C não contratada. Trabalhista R$ 5 mi. Reputação R$ 500 mil. Regulatório R$ 1 mi. Sem limite adicional da Cobertura A |
| `04_Delfos_DO_Tecnologia` | SaaS com investidores e filiais nos EUA. LMG R$ 40 mi | Retroatividade datada (15/08/2022). Complementar de apenas 3 meses. Suplementar de 60, a 200% do prêmio. Cauda/run-off de 72 meses em mudança de controle, com prêmio adicional. Território mundial com sublimite EUA e Canadá (R$ 10 mi). Poluição padrão. Cobertura C contratada. Trabalhista R$ 5 mi. Reputação R$ 1 mi. Regulatório R$ 2 mi. Sem limite adicional da Cobertura A |
| `05_Fenix_Austral_DO_Financeiro` | Instituição financeira, companhia aberta. LMG R$ 100 mi | Retroatividade ilimitada. Complementar de 60 meses e suplementar de 120. Cauda/run-off de 84 meses, sem prêmio adicional. Território mundial. Poluição: exceção só para a Cobertura A (Side A). Cobertura C contratada (R$ 50 mi). Trabalhista excluída. Reputação R$ 1,5 mi. Regulatório R$ 15 mi. Limite adicional da Cobertura A de R$ 25 mi |

Os valores vêm de `backend/scripts/sample_policies/catalog.py`, que é a fonte de verdade dos fatos de cada apólice.

### Gerar de novo

A geração é reprodutível: o mesmo catálogo produz sempre o mesmo conteúdo. Precisa do extra opcional `samples` (reportlab), a partir de `backend/`:

```powershell
python -m pip install -e ".[dev,samples]"
python scripts/generate_sample_policies.py
```

Opções:

- `--output-dir CAMINHO` grava em outra pasta (padrão: `Policy/` na raiz).
- `--only 03` gera só a apólice cujo arquivo começa com o prefixo informado.

Para mudar uma apólice, edite `catalog.py` e gere de novo. Os textos das cláusulas ficam em `texts.py` e `builder.py`.

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
