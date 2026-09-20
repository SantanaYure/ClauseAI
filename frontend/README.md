# ClauseAI frontend

Frontend React/TypeScript/SCSS da fundação do MVP. A tela inicial consulta `GET /health` por meio do `ApiClient` e exibe se o backend está online. Não há upload nem telas de domínio nesta etapa.

## Setup

```powershell
npm install
Copy-Item .env.example .env
```

## Run

```powershell
npm run dev
```

## Quality

```powershell
npm run test:run
npm run lint
npm run format:check
npm run typecheck
npm run build
```

`VITE_API_BASE_URL` aponta para o backend e pode ser alterada sem mudar os componentes.
