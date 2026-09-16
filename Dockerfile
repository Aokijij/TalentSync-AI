FROM node:22-alpine AS frontend-build

WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
ARG VITE_API_URL=/api/v1
ENV VITE_API_URL=${VITE_API_URL}
RUN npm run build

FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    STATIC_DIR=/app/static

WORKDIR /app
COPY backend/requirements-lite.txt ./requirements.txt
RUN python -m pip install --no-cache-dir -r requirements.txt \
    && useradd --create-home --uid 10001 talentsync

COPY backend/ ./
COPY --from=frontend-build /frontend/dist ./static

RUN chown -R talentsync:talentsync /app
USER talentsync

EXPOSE 8000
CMD ["sh", "-c", "python -m alembic upgrade head && exec python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
