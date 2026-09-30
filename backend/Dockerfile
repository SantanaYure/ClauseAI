# ClauseAI API: imagem para serviço de processo contínuo (Render, Railway, Cloud Run).
# Um único worker: a fila de eventos (QueuedEventBus) vive em memória no processo.
# Segredos entram somente por variáveis de ambiente do provedor, nunca na imagem.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    APP_ENV=production \
    PORT=8000

WORKDIR /srv/clauseai

COPY pyproject.toml README.md ./
COPY app ./app
RUN pip install . \
    && useradd --create-home --uid 10001 clauseai \
    && mkdir -p .data/uploads \
    && chown -R clauseai:clauseai /srv/clauseai

USER clauseai

EXPOSE 8000

CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1 --proxy-headers --forwarded-allow-ips='*'"]
