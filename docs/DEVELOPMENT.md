# Desarrollo y comprobaciones

Referencia técnica para mantener TalentSync AI. La presentación del producto está en el [README](../README.md).

## Entorno

Python 3.12 o 3.13, Node.js 22 y npm. PostgreSQL para persistencia compartida; SQLite para pruebas aisladas. Los comandos siguientes parten de la raíz en PowerShell.

```powershell
py -3.13 -m venv backend/.venv
backend/.venv/Scripts/python.exe -m pip install -r backend/requirements-dev.txt
Copy-Item backend/.env.example backend/.env
Set-Location frontend
npm ci
Copy-Item .env.example .env
```

Conservar los valores existentes si los archivos de entorno ya están creados. En `backend/.env`, configurar `SECRET_KEY` con al menos 32 caracteres aleatorios, `DATABASE_URL`, los orígenes de CORS y el procesamiento de CV. `frontend/.env` usa `VITE_API_URL`; los valores `VITE_*` son públicos.

## Ejecutar

Desde `backend/`:

```powershell
.venv/Scripts/python.exe -m alembic upgrade head
.venv/Scripts/python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Desde `frontend/`:

```powershell
npm run dev
```

Interfaz: `http://localhost:5173`. Contrato de la API: `http://127.0.0.1:8000/docs`.

Los lanzadores `scripts/dev-backend.ps1` y `scripts/dev-frontend.ps1` ofrecen el mismo punto de entrada. Para preparar un entorno aislado en `.local/`, consultar `python scripts/local.py --help`.

## Pruebas y compilación

Desde `backend/`:

```powershell
.venv/Scripts/python.exe -m pytest tests -q
.venv/Scripts/python.exe -m ruff check app scripts tests
```

Desde `frontend/`:

```powershell
npm run lint
npm test
npm run build
npm run build:public
npm run quality:ui
npm run quality:visual
```

Las pruebas de navegador necesitan Chromium de Playwright: `npx playwright install chromium`. La regresión visual usa referencias de Windows y se ejecuta en ese sistema. Más detalles en [quality/README](../frontend/quality/README.md).

GitHub Actions ejecuta las comprobaciones de frontend, backend, interfaz, regresión visual y construcción de contenedor. Los flujos de CI validan cambios; el despliegue utiliza herramientas independientes.

## Dependencias opcionales

| Archivo del backend | Uso |
| --- | --- |
| `requirements-lite.txt` | API, lectura PDF nativa y exportación. |
| `requirements-dev.txt` | Runtime ligero y herramientas de pruebas y lint. |
| `requirements.txt` | Entrada compatible para instalar el runtime ligero. |
| `requirements-ocr.txt` | Docling/OCR en un entorno separado. |
| `requirements-cv-local.txt` | Extracción opcional de entidades con modelos locales. |
| `requirements-model-local.txt` | Comparación semántica opcional con sentence-transformers. |
| `requirements-model-local-lock.txt` | Dependencias fijadas del entorno local de comparación. |

Los entornos de OCR, extracción de entidades y comparación tienen dependencias diferentes. Mantenerlos separados. `CV_DOCLING_PYTHON` y `CV_ENTITY_PYTHON` apuntan a sus ejecutables; `MATCH_MODEL_PATH` apunta a un modelo local preparado. Los modelos no se descargan automáticamente al iniciar la API. Las herramientas `backend/scripts/local_model.py` y `backend/scripts/cv_model.py` muestran sus opciones con `--help`.

## Datos, migraciones y cuentas

- Conservar todas las migraciones versionadas: una instalación existente necesita su historial completo.
- Las cuentas públicas pertenecen a candidatos o empresas. El administrador se crea desde `backend/` con `.venv/Scripts/python.exe -m scripts.create_admin --name "Nombre" --email "correo@dominio.com"`; el programa solicita la contraseña.
- Los scripts de semillas generan datos ficticios para revisión. No ejecutarlos sobre una base productiva.
- Las pruebas usan archivos temporales y sus propios datos; el ejemplo de evaluación vive en `backend/tests/fixtures/`.
- Bases locales, archivos subidos, credenciales, modelos e informes de pruebas permanecen fuera de Git.

## Operación

### Redacción opcional con Groq

`CAREER_WRITER_PROVIDER=groq` habilita borradores de experiencias y resúmenes usando `openai/gpt-oss-20b`. Requiere `GROQ_API_KEY` solo en el backend, una cuenta gratuita y **Inference APIs ZDR** activado en la organización de Groq. Después de comprobar esos ajustes, establecer `GROQ_FREE_PLAN_CONFIRMED=true` y `GROQ_ZERO_DATA_RETENTION_CONFIRMED=true`. Estas confirmaciones son operativas; la API de generación no verifica el plan de facturación. No activar una suscripción de pago para esta función.

Aplicar `alembic upgrade head` antes de habilitarla. La tabla `ai_writer_usage` reserva solicitudes y tokens de forma compartida entre procesos, antes de cada llamada. Los valores de `.env.example` limitan el conjunto de candidatos a 500 solicitudes y 180.000 tokens diarios, 20 solicitudes y 7.500 tokens por minuto, y 20 solicitudes por candidato al día. El cómputo diario cambia a medianoche UTC. Las cuotas de Groq pueden variar y otros usos de la misma organización también consumen su saldo; consultar [sus límites vigentes](https://console.groq.com/docs/rate-limits). No hay reintentos automáticos, cambio automático de proveedor ni ampliación del plan.

Cada envío exige autorización del candidato. Se seleccionan las funciones necesarias, se ocultan contactos y nombres conocidos, y se valida cada responsabilidad al recibir la respuesta. Esta minimización no garantiza anonimato: el candidato debe revisar el texto antes de compartirlo. El resultado requiere revisión y aplicación explícita. No se envía el PDF completo ni se utiliza Groq para extraer CV. Los fallos conservan el texto original. La comprobación periódica consulta `/models`, sin enviar perfiles ni generar textos. Revisar [el tratamiento de datos de Groq](https://console.groq.com/docs/your-data) si cambia la configuración de la organización.

`CAREER_WRITER_PROVIDER=local` conserva el adaptador GGUF existente; sin modelo local, el resumen estructurado sigue disponible. `disabled` desactiva la inferencia. Ninguno de estos modos contacta con Groq.

Las referencias vigentes de despliegue e integraciones están en `infra/production/`. Consultar [AWS](../infra/production/AWS.md), [archivos privados R2](../infra/production/R2.md), [correo](../infra/production/MAIL.md) y [publicación web](../infra/production/PUBLIC_SITE.md). El `Dockerfile` y las plantillas de infraestructura siguen siendo parte del proyecto.
