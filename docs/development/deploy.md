# Deploy

O backend roda no Render e o frontend na Vercel. Ordem: publique o backend, depois o frontend apontando para ele, e por fim libere a URL do frontend no CORS do backend.

## 1. Backend no Render

A configuração está em [`render.yaml`](../../render.yaml) (Blueprint): serviço web `clauseai-api`, Python 3.12, raiz `backend/`, health check em `/health`. O Render só publica um commit da `main` depois que o CI dele passa.

1. No Render, **New > Blueprint** e selecione o repositório `SantanaYure/ClauseAI`.
2. Preencha as variáveis marcadas como secretas:
   - `GEMINI_API_KEY`: chave do Google AI Studio.
   - `CORS_ALLOWED_ORIGINS`: URL de produção da Vercel, sem barra final (ex.: `https://clauseai.vercel.app`). Se ainda não tiver essa URL, use `http://localhost:5173` e troque no passo 3.
3. Depois de criado o serviço, em **Environment > Secret Files**, adicione `clauseai-firebase.json` com o conteúdo do JSON da conta de serviço do Firebase. Ele fica em `/etc/secrets/clauseai-firebase.json`, caminho já apontado por `FIREBASE_CREDENTIALS_PATH`.
4. Confira `https://<serviço>.onrender.com/health` e a documentação em `/api/v1/docs`.

Se faltar alguma variável, o serviço não sobe e o log do Render informa quais.

## 2. Frontend na Vercel

O projeto `clauseai` já está vinculado em `frontend/.vercel/`. As variáveis `VITE_*` entram no build, então qualquer mudança nelas exige novo deploy.

1. Configure as variáveis de produção:
   - `VITE_API_BASE_URL`: URL do Render, sem barra final.
   - `VITE_MAX_UPLOAD_MB`: mesmo valor de `MAX_UPLOAD_MB` do backend (20).
2. Publique de dentro de `frontend/`:

   ```bash
   vercel --prod
   ```

   Se o projeto for conectado ao GitHub, defina **Root Directory = `frontend`** nas configurações.

## 3. CORS

Atualize `CORS_ALLOWED_ORIGINS` no Render com a URL de produção da Vercel. O Render reinicia o serviço sozinho. Deploys de preview da Vercel têm outras URLs e são bloqueados pelo CORS; para testá-los, adicione a URL separada por vírgula.

## Limitações do plano gratuito

- O serviço hiberna após 15 minutos sem requisições. A primeira requisição depois disso leva cerca de um minuto.
- O disco é efêmero. Os arquivos enviados (`STORAGE_BACKEND=local`) somem a cada deploy ou reinício. Os dados extraídos ficam no Firestore; só um documento ainda em processamento durante um reinício se perde.
- A fila de eventos roda em memória (ADR sobre worker em processo): tarefas em andamento se perdem em reinício. Por isso o serviço usa um único processo uvicorn.
