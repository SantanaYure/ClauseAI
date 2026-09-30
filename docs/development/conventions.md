# Convenções de desenvolvimento

## Equipe de subagentes e fluxo de trabalho

O fluxo de trabalho é orientado por duas fontes na raiz do repositório:

- [`CLAUDE.md`](../../CLAUDE.md): regras da sessão, tabela da equipe, fluxo e critérios de conclusão.
- [`.claude/agents/`](../../.claude/agents/): um arquivo por subagente, com função e limites.

Toda melhoria do sistema passa pela equipe. O fluxo é:

```text
ux-ui-norman decide → interface-designer e frontend-specialist implementam → backend-specialist entrega a API → software-engineer-docs documenta → qa valida → devops publica (só quando pedido)
```

Regras:

- A documentação em `docs/` é a fonte de verdade (SDD). Decisão nova vira spec, ADR ou roadmap junto da implementação.
- Cada agente mexe só na sua área. Documentação não altera código, e código não altera documentação por conta própria.
- O que depender do código final fica marcado como pendente de confirmação até o especialista confirmar.
- Se a sessão for interrompida, retome a tarefa com os mesmos agentes.
- Commit, PR e deploy só a pedido, pelo `devops`.

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
- Grid com filho de largura intrínseca (`select`, tabela, código) usa `minmax(0, 1fr)` nas colunas e `min-width: 0` no filho. `1fr` sozinho equivale a `minmax(auto, 1fr)` e deixa o conteúdo estourar a coluna. Exemplo: `.slots` usa `repeat(2, minmax(0, 1fr))` a partir de 640px, e o `select` do slot ocupa 100% e corta texto longo.

## Eventos

Eventos possuem `event_id`, `event_type`, `occurred_at`, `correlation_id`, `payload` e `version`. Handlers futuros devem ser pequenos, observáveis e idempotentes.

## Testes

Teste comportamento público e contratos. Não adicione testes de regras D&O, IA ou Firebase até essas etapas serem implementadas e especificadas.

## Commits e revisão

Use Conventional Commits de forma simples (`feat`, `fix`, `test`, `docs`, `chore`). Antes do merge, execute os comandos de qualidade do `CONTRIBUTING.md`.
