# ClauseAI frontend

Frontend React/TypeScript/SCSS do MVP, mobile first. As cinco telas do menu (Início, Apólices, Comparar, Conceitos e Histórico) são navegáveis e seguem [`docs/specs/SDD_SPECIFICATIONS.md`](../docs/specs/SDD_SPECIFICATIONS.md) (SPEC-010) e a [base de conhecimento D&O](../docs/domain/DO_KNOWLEDGE_BASE.md).

As telas não têm dados embutidos: tudo vem da API REST em `VITE_API_BASE_URL` + `/api/v1` (contratos em [`docs/architecture/PERSISTENCE_AND_API.md`](../docs/architecture/PERSISTENCE_AND_API.md)), acessada só por `src/services/api/clause-api.ts`. Sem o backend em execução, as telas mostram estados vazios ou de erro com a opção “Tentar novamente”. Processamento de apólices e comparações em andamento são acompanhados por consulta periódica até um estado final.

## Setup

```powershell
npm install
Copy-Item .env.example .env
```

## Run

```powershell
npm run dev
```

Rotas: `#/`, `#/apolices`, `#/apolices/nova`, `#/apolices/{id}`, `#/comparar`, `#/comparar/{id}`, `#/conceitos`, `#/conceitos/{id}`, `#/historico`.

## Quality

```powershell
npm run test:run
npm run lint
npm run format:check
npm run typecheck
npm run build
```

## Variáveis de ambiente

| Variável | Padrão | Uso |
|---|---|---|
| `VITE_API_BASE_URL` | `http://localhost:8000` | Backend. Pode mudar sem alterar os componentes |
| `VITE_UPLOAD_TIMEOUT_MS` | `300000` (5 min) | Tempo máximo do envio de arquivos |
| `VITE_MAX_UPLOAD_MB` | `20` | Tamanho máximo por arquivo na validação local. Deve espelhar `MAX_UPLOAD_MB` do backend |

Regras de envio, processamento, escolha das apólices e resultado: SPEC-010.
