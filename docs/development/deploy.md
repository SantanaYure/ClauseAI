# Deploy

O backend roda no Render (`https://clauseai-k1zq.onrender.com`) e o frontend na Vercel (`https://clauseai-phi.vercel.app`). Os dois usam o projeto Firebase `claude-ai-a36cf`, o mesmo do ambiente local. O isolamento entre visitantes vem da identidade anônima por navegador (ADR-027), não de projetos separados.

**Ordem.** Prepare o Firebase (seção 1). Depois publique backend e frontend juntos: o backend novo recusa chamadas sem token (`401`), então o frontend antigo para de funcionar assim que o backend sobe. Por fim, rode a limpeza dos dados legados (seção 5).

## 1. Firebase (uma vez)

1. **Ativar o login anônimo.** Console do Firebase > Authentication > Sign-in method > Anonymous > Ativar.
2. **Domínio autorizado.** Authentication > Configurações > Domínios autorizados: `clauseai-phi.vercel.app` (já cadastrado). Sem ele, o login anônimo falha em produção.
3. **Configuração web.** Em Configurações do projeto > Seus apps, use (ou crie) o app web e copie `apiKey`, `authDomain`, `projectId` e `appId`. Eles viram as variáveis `VITE_FIREBASE_*` (seção 3).
4. **Restringir a API key web.** Google Cloud Console > APIs e serviços > Credenciais > chave do navegador > Restrições de aplicativo: Referenciadores HTTP. Libere `https://clauseai-phi.vercel.app/*` e `http://localhost:5173/*`. A chave web é pública por natureza; a restrição impede uso em outros sites.
5. **Índices compostos.** Estão em `firestore.indexes.json`, na raiz: `policies` e `comparisons` com (`owner_id` ASC, `created_at` DESC). `fieldOverrides` fica vazio (`[]`): o TTL do Firestore não está ativo (veja abaixo). Publique da raiz, com a CLI do Firebase logada numa conta com permissão no projeto:

   ```bash
   firebase deploy --only firestore:indexes --project claude-ai-a36cf
   ```

   O comando lê o `firebase.json` da raiz. A conta de serviço do backend não tem permissão para criar índices; não use ela aqui. Sem os índices, as listas respondem erro.

   **TTL do Firestore desativado.** O TTL nativo exige faturamento (plano Blaze), e o projeto está sem faturamento. A retenção de 24 h depende só do `RetentionSweeper` do backend e do keepalive (seção Limitações). Itens expirados nunca aparecem, pois toda leitura os filtra (ADR-028). Ativar Blaze e TTL é melhoria opcional (ROADMAP).
6. **Regras.** `firestore.rules` (deny-all) está versionado e é o que já está publicado. Só o backend, com a conta de serviço, acessa o Firestore.

## 2. Backend no Render

A configuração está em [`render.yaml`](../../render.yaml) (Blueprint): serviço web `clauseai-api`, Python 3.12, raiz `backend/`, health check em `/health`. O Render só publica um commit da `main` depois que o CI dele passa.

1. No Render, **New > Blueprint** e selecione o repositório `SantanaYure/ClauseAI`.
2. Preencha as variáveis marcadas como secretas:
   - `GEMINI_API_KEY`: chave do Google AI Studio.
   - `CORS_ALLOWED_ORIGINS`: `https://clauseai-phi.vercel.app` (sem barra final).
3. Confira as variáveis de autenticação, retenção e cotas. Os valores abaixo são os padrões; só defina se quiser mudar:

   | Variável | Padrão | Observação |
   |---|---|---|
   | `AUTH_BACKEND` | `firebase` | `fake` é recusado com `APP_ENV=production` |
   | `AUTH_CLOCK_SKEW_SECONDS` | `10` | Tolerância de relógio do token (0 a 60) |
   | `RETENTION_HOURS` | `24` | Prazo de cada apólice |
   | `RETENTION_SWEEP_MINUTES` | `15` | Intervalo da varredura |
   | `MAX_ACTIVE_POLICIES_PER_OWNER` | `20` | Cota por navegador |
   | `UPLOADS_PER_HOUR` | `10` | Cota por navegador |
   | `COMPARISONS_PER_HOUR` | `20` | Cota por navegador |
4. Em **Environment > Secret Files**, adicione `clauseai-firebase.json` com o JSON da conta de serviço do Firebase. Ele fica em `/etc/secrets/clauseai-firebase.json`, caminho já apontado por `FIREBASE_CREDENTIALS_PATH`. A mesma conta verifica os tokens.
5. Confira `https://<serviço>.onrender.com/health`. Em produção, `/api/v1/docs` fica desligado.

Se faltar alguma variável, o serviço não sobe e o log do Render informa quais.

## 3. Frontend na Vercel

O projeto `clauseai` já está vinculado em `frontend/.vercel/`. As variáveis `VITE_*` entram no build, então qualquer mudança nelas exige novo deploy.

1. Configure as variáveis de produção:

   | Variável | Valor |
   |---|---|
   | `VITE_API_BASE_URL` | `https://clauseai-k1zq.onrender.com` |
   | `VITE_MAX_UPLOAD_MB` | mesmo valor de `MAX_UPLOAD_MB` do backend (20) |
   | `VITE_FIREBASE_API_KEY` | `apiKey` do app web |
   | `VITE_FIREBASE_AUTH_DOMAIN` | `authDomain` (ex.: `claude-ai-a36cf.firebaseapp.com`) |
   | `VITE_FIREBASE_PROJECT_ID` | `claude-ai-a36cf` |
   | `VITE_FIREBASE_APP_ID` | `appId` do app web |

2. `frontend/vercel.json` define a CSP e os headers de segurança. `VITE_AUTH_MODE` não é definida em produção; o modo `dev` só vale em `npm run dev`. O `connect-src` libera a API (`https://clauseai-k1zq.onrender.com`), `identitytoolkit.googleapis.com` e `securetoken.googleapis.com`; o `frame-src` libera `https://claude-ai-a36cf.firebaseapp.com`. Se a URL da API mudar, atualize o `connect-src`.
3. Publique de dentro de `frontend/`:

   ```bash
   vercel --prod
   ```

   Se o projeto for conectado ao GitHub, defina **Root Directory = `frontend`** nas configurações.

## 4. CORS

`CORS_ALLOWED_ORIGINS` no Render deve conter `https://clauseai-phi.vercel.app`. Ao mudar, o Render reinicia o serviço sozinho. Deploys de preview da Vercel têm outras URLs e são bloqueados pelo CORS; para testá-los, adicione a URL separada por vírgula (e libere o referrer na API key, seção 1).

## 5. Limpeza dos dados legados

Apólices, comparações e arquivos gravados antes do isolamento não têm `owner_id`. Ninguém os vê, mas eles precisam ser apagados. A partir de `backend/`, com as credenciais do Firebase configuradas:

```powershell
python scripts/purge_legacy.py          # dry-run: só lista o que seria apagado
python scripts/purge_legacy.py --apply  # apaga
```

Rode o dry-run primeiro e confira a lista.

## Verificação depois do deploy

- Abrir o site em dois navegadores: um não vê as apólices do outro.
- Chamada à API sem token responde `401 AUTH_REQUIRED`.
- Em GitHub > Actions, o workflow `retention-keepalive` está ativo e a última execução passou.
- Card da apólice mostra "Expira em X horas".
- "Apagar todos os meus dados", em Privacidade e dados (link no rodapé), esvazia a lista.

## Limitações do plano gratuito

- O serviço hiberna após 15 minutos sem requisições. A primeira requisição depois disso leva cerca de um minuto. O `RetentionSweeper` também para e roda de novo no startup. Para isso, o workflow `.github/workflows/retention-keepalive.yml` chama `GET /health` de hora em hora e acorda o serviço. Pior caso: um dado expirado fica guardado cerca de 1 hora após o vencimento, sem aparecer em nenhuma leitura. O GitHub desativa workflows agendados após 60 dias sem atividade no repositório; se isso ocorrer, reative em Actions.
- O disco é efêmero. Os arquivos enviados (`STORAGE_BACKEND=local`) somem a cada deploy ou reinício. Os dados extraídos ficam no Firestore; só um documento ainda em processamento durante um reinício se perde.
- A fila de eventos e as cotas por dono rodam em memória (ADR-021 e ADR-027): tarefas em andamento se perdem em reinício, e as cotas zeram. Por isso o serviço usa um único processo uvicorn.
