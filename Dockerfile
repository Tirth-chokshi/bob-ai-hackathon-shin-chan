FROM node:24-slim AS frontend

WORKDIR /frontend
COPY src/web/package.json src/web/package-lock.json ./
RUN npm ci
COPY src/web/ ./
RUN npm run build

FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_HOST=0.0.0.0 \
    PYTHONPATH=/app/src

WORKDIR /app
COPY src/requirements.txt ./src/requirements.txt
RUN python -m pip install --no-cache-dir -r src/requirements.txt
COPY src/ ./src/
COPY .bob/rules-osint-analyst/ ./.bob/rules-osint-analyst/
COPY --from=frontend /frontend/dist ./src/web/dist

RUN mkdir -p /app/data && chown -R 10001:10001 /app
USER 10001:10001

CMD ["python", "src/main.py"]