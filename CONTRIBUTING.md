# Contribuindo

## Convenções

- Siga a arquitetura documentada em `docs/architecture/`.
- Mantenha dependências apontando de infraestrutura/apresentação para aplicação/domínio.
- Não adicione integração real de Firebase ou IA sem atualizar a spec e o ADR correspondente.
- Use nomes explícitos, funções pequenas e tipos completos.

## GitHub Flow e branches

Trabalhe sempre em uma branch curta criada a partir de `main` atualizada. Abra uma Pull Request para `main`, aguarde o CI e use Squash and Merge. Não desenvolva diretamente na `main`.

Use nomes curtos e descritivos:

- `feat/<descricao>`
- `fix/<descricao>`
- `chore/<descricao>`
- `docs/<descricao>`
- `refactor/<descricao>`
- `test/<descricao>`

## Commits

Use Conventional Commits, no imperativo e com escopo claro. Os tipos adotados são `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `ci` e `build`.

Exemplos:

```text
feat(bootstrap): add health endpoint
test(events): cover duplicate subscription
docs(repo): describe local setup
ci: add backend validation workflow
```

## Antes de abrir uma Pull Request

Backend:

```powershell
cd backend
python -m ruff check .
python -m ruff format --check .
python -m pytest
python -m mypy app
```

Frontend:

```powershell
cd frontend
npm run lint
npm run format:check
npm run typecheck
npm run test:run
npm run build
```

Atualize a documentação quando alterar contratos, decisões, workflows ou comandos de desenvolvimento. O checklist completo e os procedimentos operacionais estão em [`docs/development/git-workflow.md`](docs/development/git-workflow.md).
