# Git workflow e operação de desenvolvimento

Este guia descreve o fluxo recomendado para o ClauseAI usando GitHub Flow, Pull Requests, CI obrigatório e Conventional Commits. Ele foi escrito para um único desenvolvedor, mas mantém rastreabilidade para uma equipe futura.

## 1. Princípios

- `main` representa sempre uma versão estável.
- Não desenvolver diretamente em `main`.
- Uma tarefa pequena por branch e Pull Request.
- CI deve estar verde antes do merge.
- Preferir commits pequenos e mensagens claras.
- Não versionar credenciais, `.env`, artefatos de build ou caches.
- Nenhum comando deste guia autoriza alterar regras de negócio sem atualizar a spec/ADR correspondente.

## 2. GitHub Flow

```text
main
  ↓
criar branch curta
  ↓
desenvolver e testar
  ↓
commit Conventional Commits
  ↓
push
  ↓
Pull Request
  ↓
CI + revisão
  ↓
Squash and Merge
  ↓
atualizar main e remover branch
```

### Prefixos de branch

| Prefixo | Usar para | Exemplo |
|---|---|---|
| `feat/` | funcionalidade nova | `feat/document-upload` |
| `fix/` | correção de defeito | `fix/health-endpoint` |
| `docs/` | documentação | `docs/api-spec` |
| `refactor/` | alteração estrutural sem mudar comportamento pretendido | `refactor/ai-orchestrator` |
| `test/` | testes ou fixtures | `test/document-service` |
| `chore/` | manutenção, tooling ou dependências | `chore/update-dependencies` |

Nomes devem ser curtos, minúsculos e separados por hífen. A branch deve representar uma tarefa que possa ser revisada como uma unidade.

## 3. Configuração inicial

Clone o repositório fornecido pelo GitHub:

```bash
git clone <repository>
cd <repository>
```

`git clone` baixa o repositório e configura `origin`; `cd` entra na pasta do projeto. Substitua `<repository>` pela URL real, sem registrar essa URL como segredo.

Configure a identidade dos commits:

```bash
git config user.name "Seu Nome"
git config user.email "seu@email.com"
```

Esses valores ficam na configuração local do Git e aparecem no histórico. Use o e-mail associado à sua conta GitHub quando desejar atribuição automática.

Confira os remotes:

```bash
git remote -v
```

Resultado esperado: `origin` apontando para o repositório correto. Não invente ou substitua o remote sem confirmar a URL com o responsável pelo projeto.

## 4. Atualizar `main`

Antes de começar uma tarefa:

```bash
git switch main
git pull origin main
```

`git switch main` seleciona a branch estável. `git pull origin main` busca e integra o estado publicado. Isso reduz a chance de iniciar uma tarefa sobre uma base antiga.

Se houver alterações locais, pare e revise `git status` antes de fazer pull. Não use `reset --hard` para “resolver” o estado sem confirmar que as alterações podem ser descartadas.

## 5. Criar uma nova funcionalidade

```bash
git switch main
git pull origin main
git switch -c feat/document-upload
```

`git switch -c` cria e seleciona uma branch local a partir da `main` atualizada. Para correção, documentação, refatoração, testes ou manutenção, troque `feat/` pelo prefixo adequado.

## 6. Verificar estado

```bash
git status
git branch
git log --oneline --decorate --graph
```

- `git status`: mostra branch atual, arquivos modificados, staged e não rastreados.
- `git branch`: lista branches locais e destaca a ativa.
- `git log --oneline --decorate --graph`: mostra o histórico compacto e a topologia.

Resultado esperado antes de um commit: alterações conhecidas, branch correta e nenhum arquivo sensível listado.

## 7. Preparar um commit

Revise primeiro:

```bash
git diff
```

`git diff` mostra alterações ainda não staged. Depois adicione somente o que pertence à tarefa:

```bash
git add <arquivo>
```

Adicionar arquivos específicos é preferível quando a pasta contém alterações de tarefas diferentes. `git add .` adiciona todas as alterações sob a pasta atual e só deve ser usado depois de revisar o estado:

```bash
git add .
```

Após o stage, revise novamente:

```bash
git diff --cached
```

Nunca faça commit de `.env`, credenciais Firebase, chaves de API, `node_modules`, `.venv`, `dist`, `build`, coverage ou caches.

## 8. Conventional Commits

Tipos adotados:

```text
feat:       nova funcionalidade
fix:        correção de defeito
docs:       documentação
refactor:   refatoração sem mudança intencional de comportamento
test:       testes
chore:      manutenção
ci:         GitHub Actions ou automação de CI
build:      build, empacotamento ou dependências de build
```

Formato recomendado:

```text
<tipo>(<escopo opcional>): <descrição curta no imperativo>
```

Exemplos:

```bash
git commit -m "feat: add document upload endpoint"
git commit -m "fix: handle invalid document format"
git commit -m "docs: add architecture overview"
git commit -m "refactor: isolate event bus interface"
git commit -m "test: add health endpoint tests"
git commit -m "ci: add backend validation workflow"
```

Um commit deve ser compreensível e reversível quando possível. Não misture refatoração ampla com mudança funcional sem necessidade.

## 9. Push

No primeiro push da branch:

```bash
git push -u origin feat/document-upload
```

`-u` configura o upstream; depois disso, a branch pode ser enviada com:

```bash
git push
```

Resultado esperado: branch disponível no GitHub e pronta para abrir uma PR. Se o push for rejeitado, atualize a branch com cuidado em vez de usar force push por padrão.

## 10. Pull Request

No GitHub:

1. Abra uma PR da branch de tarefa para `main`.
2. Preencha `.github/PULL_REQUEST_TEMPLATE.md`.
3. Relacione a SPEC/ADR ou indique que a alteração é infraestrutura.
4. Informe comandos e resultados dos testes.
5. Aguarde os checks `Backend CI` e `Frontend CI` quando os respectivos paths tiverem mudado.
6. Faça a revisão e responda aos comentários.
7. Use **Squash and merge** quando aprovado.

Opcionalmente, com GitHub CLI autenticado:

```bash
gh pr create
```

`gh pr create` abre a PR interativamente; não é requisito do projeto nem substitui a revisão no GitHub.

## 11. Atualizar branch com `main`

### Rebase — abordagem preferida para branch pessoal

```bash
git switch main
git pull origin main
git switch feat/document-upload
git rebase main
```

O rebase reaplica os commits da branch sobre a `main` atual e mantém histórico linear. Ele reescreve os hashes dos commits da branch; não faça rebase de uma branch compartilhada sem alinhar com quem a utiliza.

Se houver conflito:

```bash
git status
git add <arquivo-corrigido>
git rebase --continue
```

Depois de um rebase, o push pode precisar de:

```bash
git push --force-with-lease
```

Cancelar o rebase:

```bash
git rebase --abort
```

### Merge — alternativa para branch compartilhada

```bash
git switch feat/document-upload
git fetch origin
git merge origin/main
```

O merge preserva a topologia e cria um commit de merge quando necessário. Escolha uma abordagem para a branch; não alterne entre merge e rebase sem motivo.

## 12. Corrigir o último commit antes do push

```bash
git add <arquivo>
git commit --amend
```

`--amend` substitui o último commit e permite corrigir mensagem ou conteúdo. Use somente antes de compartilhar a branch ou quando todos os consumidores souberem que o histórico foi reescrito.

## 13. Desfazer alterações locais

Arquivo modificado e não staged:

```bash
git restore <arquivo>
```

Isso descarta as alterações não staged daquele arquivo. Staged:

```bash
git restore --staged <arquivo>
```

Isso remove o arquivo do stage, mas preserva a alteração no working tree. Revise `git diff` e `git diff --cached` antes de qualquer restore; dados descartados podem não ser recuperáveis.

## 14. Stash

```bash
git stash
git stash list
git stash pop
```

`git stash` guarda temporariamente alterações locais; `git stash list` mostra os stashes; `git stash pop` reaplica o mais recente e o remove da lista se aplicado com sucesso.

Exemplo: use stash para trocar de branch com trabalho incompleto quando a alteração não está pronta para commit. Revise conflitos após `pop`.

## 15. Remover branch concluída

Depois que a PR foi mergeada:

```bash
git branch -d feat/document-upload
git push origin --delete feat/document-upload
```

O primeiro comando remove a branch local mesclada; o segundo remove a branch remota. Confirme que a PR correta foi mergeada antes de apagar qualquer branch.

## 16. Hotfix

Mesmo um hotfix segue PR e CI:

```bash
git switch main
git pull origin main
git switch -c fix/critical-processing-error
```

Corrija, teste, faça commit, push e PR. Não faça alteração direta em `main` mesmo sob pressão.

## 17. Documentação e refatoração

Documentação:

```bash
git switch main
git pull origin main
git switch -c docs/update-architecture
git add .
git commit -m "docs: update architecture guide"
git push -u origin docs/update-architecture
```

Refatoração:

```bash
git switch main
git pull origin main
git switch -c refactor/document-service
git add .
git commit -m "refactor: isolate document service"
git push -u origin refactor/document-service
```

Refatorações devem preservar o comportamento, salvo se a PR explicar claramente a mudança.

## 18. Tags e releases

O projeto usa Semantic Versioning: `MAJOR.MINOR.PATCH`.

- **PATCH:** correção compatível, por exemplo `v0.1.1`.
- **MINOR:** funcionalidade compatível, por exemplo `v0.2.0`.
- **MAJOR:** mudança incompatível, por exemplo `v1.0.0`.

Durante a fundação/MVP, versões `v0.1.0`, `v0.2.0` e `v0.3.0` representam marcos. A primeira versão considerada MVP pode ser `v1.0.0`.

Após o merge de uma versão estável:

```bash
git switch main
git pull origin main
git tag -a v0.1.0 -m "Repository foundation"
git push origin v0.1.0
```

`git tag -a` cria uma tag anotada; `git push origin v0.1.0` envia somente essa tag. No GitHub, abra **Releases → Draft a new release**, selecione a tag, escreva notas curtas e publique. Não automatizar releases complexos nesta etapa.

Ver tags:

```bash
git tag
git show v0.1.0
```

## 19. Sincronizar branches remotas

```bash
git fetch --prune
```

`git fetch` atualiza referências remotas sem alterar seu working tree; `--prune` remove referências locais de branches remotas que já não existem no servidor. Ele não apaga seus arquivos locais nem branches locais.

## 20. Comandos perigosos

Use com cuidado e somente depois de confirmar o alvo e preservar o que importa:

```bash
git reset --hard
git push --force
git clean -fd
```

- `git reset --hard` descarta alterações locais e pode mover a branch.
- `git push --force` sobrescreve histórico remoto e pode apagar commits de outras pessoas.
- `git clean -fd` remove arquivos/diretórios não rastreados; não há garantia de recuperação.

Eles não fazem parte do fluxo comum. Após um rebase em branch pessoal, prefira:

```bash
git push --force-with-lease
```

`--force-with-lease` só força se a referência remota ainda estiver no estado esperado localmente, reduzindo o risco de sobrescrever trabalho novo de outra pessoa.

## 21. Comandos de desenvolvimento

Execute a partir da pasta indicada. Estes comandos refletem os scripts e configurações atualmente versionados.

### Backend

Instalar dependências de desenvolvimento:

```powershell
cd backend
python -m pip install -e ".[dev]"
```

Resultado esperado: pacote local e extras de desenvolvimento instalados. Use `.venv` ativado para isolar o ambiente.

Iniciar FastAPI:

```powershell
python -m uvicorn app.main:app --reload
```

Resultado esperado: API em `http://localhost:8000`; health em `/health`. `--reload` é para desenvolvimento local, não deploy.

Lint:

```powershell
python -m ruff check .
```

Format check:

```powershell
python -m ruff format --check .
```

Para formatar arquivos localmente:

```powershell
python -m ruff format .
```

Testes:

```powershell
python -m pytest
```

Type check:

```powershell
python -m mypy app
```

### Frontend

Instalação reproduzível de CI:

```powershell
cd frontend
npm ci
```

Para a primeira instalação local sem lock existente, use `npm install`; neste repositório o `package-lock.json` existe, portanto `npm ci` é preferível para reproduzir versões.

Desenvolvimento:

```powershell
npm run dev
```

Testes em modo watch:

```powershell
npm run test
```

Testes únicos, usados no CI:

```powershell
npm run test:run
```

Lint:

```powershell
npm run lint
```

Format check:

```powershell
npm run format:check
```

Formatar:

```powershell
npm run format
```

TypeScript check:

```powershell
npm run typecheck
```

Build de produção local:

```powershell
npm run build
```

O build valida TypeScript e gera `frontend/dist/`, que é ignorado pelo Git e não representa deploy nesta etapa.

## 22. Fluxos prontos para copiar

### Nova feature

```bash
git switch main
git pull origin main
git switch -c feat/nome-da-feature

# desenvolver e testar
git status
git diff
git add .
git commit -m "feat: descrição"
git push -u origin feat/nome-da-feature

# abrir PR no GitHub ou, opcionalmente:
gh pr create
```

### Correção

```bash
git switch main
git pull origin main
git switch -c fix/nome-do-problema

# corrigir e testar
git add .
git commit -m "fix: descrição"
git push -u origin fix/nome-do-problema
```

### Documentação

```bash
git switch main
git pull origin main
git switch -c docs/nome
git add .
git commit -m "docs: descrição"
git push -u origin docs/nome
```

## 23. Checklist antes do push

- [ ] `git status` revisado.
- [ ] `git diff`/`git diff --cached` revisados.
- [ ] nenhum `.env` incluído.
- [ ] nenhuma credencial incluída.
- [ ] testes locais passando.
- [ ] lint passando.
- [ ] formatter passando.
- [ ] documentação atualizada quando necessário.
- [ ] commit segue Conventional Commits.

## 24. Checklist antes do merge

- [ ] Backend CI verde quando aplicável.
- [ ] Frontend CI verde quando aplicável.
- [ ] build verde.
- [ ] critérios da spec atendidos.
- [ ] documentação atualizada.
- [ ] nenhuma secret exposta.
- [ ] PR descreve claramente a alteração.
- [ ] merge escolhido é **Squash and merge**.

## 25. Proteção da branch `main`

No GitHub, vá a **Settings → Branches → Add branch ruleset** ou à área de proteção de branches e configure para `main`:

- exigir Pull Request antes do merge;
- exigir os status checks `Backend CI` e `Frontend CI` quando aplicáveis;
- exigir branch atualizada antes do merge se o volume de contribuições justificar;
- bloquear force pushes;
- bloquear exclusão da `main`;
- permitir **Squash and merge**;
- não exigir múltiplos reviewers enquanto houver apenas um desenvolvedor.

Se o path filtering fizer um status check não aparecer em PRs que não alteram aquele componente, mantenha como obrigatórios apenas os checks compatíveis com a política do repositório. Quando a equipe crescer, adicione pelo menos um reviewer obrigatório, CODEOWNERS e aprovação independente para áreas críticas.

## 26. Estratégia de merge

Preferir **Squash and merge**: a `main` recebe um commit representando a PR, mantendo histórico limpo mesmo quando a branch teve commits intermediários.

**Rebase and merge** pode ser usado quando os commits da branch já são pequenos, coerentes e devem ser preservados individualmente. Evitar merge commits comuns sem necessidade, pois eles adicionam ruído ao histórico de uma equipe pequena.

## 27. Secrets e configuração do GitHub

Secrets futuros possíveis:

```text
FIREBASE_PROJECT_ID
FIREBASE_CLIENT_EMAIL
FIREBASE_PRIVATE_KEY
FIREBASE_STORAGE_BUCKET
GEMINI_API_KEY
GROQ_API_KEY
```

No GitHub, configure em **Settings → Secrets and variables → Actions → New repository secret**. Nesta etapa os workflows não precisam desses secrets porque não executam Firebase ou IA.

Nunca:

- inserir secrets em YAML;
- imprimir secrets nos logs;
- versionar `.env`;
- colar chaves em issues, PRs ou artefatos;
- usar secrets como workaround para uma dependência que não é necessária ao CI.

## 28. Dependabot

O arquivo `.github/dependabot.yml` monitora semanalmente:

- npm em `/frontend`;
- pip em `/backend`;
- GitHub Actions na raiz.

O limite de cinco PRs abertas por ecossistema reduz ruído. Cada atualização deve passar pelo CI; upgrades grandes devem ser revisados separadamente, com atenção a breaking changes.

## 29. Workflows de CI

- `.github/workflows/backend-ci.yml`: roda em PRs para `main` e pushes para `main` quando backend/configuração compartilhada relevante muda. Executa instalação, Ruff, formatter, mypy e pytest.
- `.github/workflows/frontend-ci.yml`: roda nos mesmos eventos quando frontend/configuração compartilhada relevante muda. Executa `npm ci`, lint, formatter, typecheck, testes e build.

O path filtering evita trabalho desnecessário. Alterações no próprio workflow também acionam o workflow correspondente para validar sua configuração.

## 30. Remote e configuração manual pendente

O repositório local pode ser inicializado sem remote. Antes do primeiro push, o responsável deve criar/selecionar o repositório GitHub e configurar:

```bash
git remote add origin <repository>
git push -u origin main
```

Depois, habilite as regras de proteção, os status checks e as permissões de Actions conforme as seções acima. A URL real do remote não é inferida nem registrada nesta documentação.
