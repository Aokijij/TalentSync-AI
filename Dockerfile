FROM node:22-alpine AS frontend-build

WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
# Shared public document versions are also imported by the registration UI.
COPY backend/legal_documents/ /backend/legal_documents/
ARG VITE_API_URL=/api/v1
ENV VITE_API_URL=${VITE_API_URL}
ARG VITE_LEGAL_NAME
ARG VITE_LEGAL_EMAIL
ARG VITE_LEGAL_CITY
ARG VITE_LEGAL_COUNTRY
ARG VITE_LEGAL_ADDRESS
ARG VITE_LEGAL_PHONE
ARG VITE_LEGAL_EFFECTIVE_DATE
ENV VITE_LEGAL_NAME=${VITE_LEGAL_NAME} \
    VITE_LEGAL_EMAIL=${VITE_LEGAL_EMAIL} \
    VITE_LEGAL_CITY=${VITE_LEGAL_CITY} \
    VITE_LEGAL_COUNTRY=${VITE_LEGAL_COUNTRY} \
    VITE_LEGAL_ADDRESS=${VITE_LEGAL_ADDRESS} \
    VITE_LEGAL_PHONE=${VITE_LEGAL_PHONE} \
    VITE_LEGAL_EFFECTIVE_DATE=${VITE_LEGAL_EFFECTIVE_DATE}
RUN node -e 'for (const field of ["NAME","EMAIL","CITY","COUNTRY","ADDRESS","PHONE","EFFECTIVE_DATE"]) { if (!process.env["VITE_LEGAL_"+field]?.trim()) throw new Error("Missing public legal contact: "+field); }'
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
CMD ["sh", "-c", "python -m alembic upgrade head && exec python -m uvicorn app.main:app --no-access-log --host 0.0.0.0 --port ${PORT:-8000}"]
