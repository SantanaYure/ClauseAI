# Convenções de desenvolvimento

## Dependências

O domínio não importa FastAPI, Firebase, Gemini, bibliotecas de UI ou detalhes de banco. Adapters externos pertencem à infraestrutura. A apresentação traduz HTTP; a aplicação orquestra casos de uso; o domínio mantém contratos independentes.

## Python

- 4 espaços; linha de até 100 caracteres.
- Tipagem explícita e `mypy` em `app`.
- `ruff check` e `ruff format` são a fonte de lint/format.
- Exceções devem ser classificadas; não retornar stack trace ao cliente.
- Timestamps e IDs devem ser injetáveis quando fizerem parte de regra/teste.

## TypeScript

- `strict` habilitado.
- Componentes não fazem `fetch` diretamente.
- Integrações HTTP ficam em `src/services/api`.
- Configuração vem de `import.meta.env` através de `src/config`.
- Estilos globais ficam em `src/styles`; componentes devem evitar CSS inline sem necessidade.

## Eventos

Eventos possuem `event_id`, `event_type`, `occurred_at`, `correlation_id`, `payload` e `version`. Handlers futuros devem ser pequenos, observáveis e idempotentes.

## Testes

Teste comportamento público e contratos. Não adicione testes de regras D&O, IA ou Firebase até essas etapas serem implementadas e especificadas.

## Commits e revisão

Use Conventional Commits de forma simples (`feat`, `fix`, `test`, `docs`, `chore`). Antes do merge, execute os comandos de qualidade do `CONTRIBUTING.md`.
