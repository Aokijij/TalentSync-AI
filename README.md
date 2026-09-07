# TalentSync AI

Plataforma de gestión y recomendación laboral que conecta perfiles profesionales con vacantes. Permite cargar una hoja de vida en PDF, revisar la información extraída, recibir recomendaciones y dar seguimiento a procesos de selección.

## Funcionalidades

- **Candidatos:** registro, perfil profesional, carga de CV, búsqueda de vacantes, recomendaciones, postulaciones y notificaciones.
- **Empresas:** perfil de organización, publicación de vacantes, búsqueda de talento, comparación de candidatos y seguimiento por etapas configurables.
- **Administración:** métricas, análisis de actividad y gestión de usuarios, empresas y vacantes.
- **Interfaz:** navegación según el rol, filtros por ubicación y sector, indicadores de compatibilidad y temas claro y oscuro.

## Tecnologías y arquitectura

| Área | Tecnologías |
| --- | --- |
| Frontend | React 19, Vite 6, React Router, Tailwind CSS, Axios y React Hook Form |
| API | Python, FastAPI y Pydantic |
| Persistencia | SQLAlchemy, Alembic y PostgreSQL; SQLite para desarrollo aislado y pruebas |
| Autenticación | JWT y contraseñas protegidas con bcrypt |
| Procesamiento de CV | Docling, EasyOCR y pypdf |
| Matching | scikit-learn, HashingVectorizer y similitud coseno |

El backend sigue una arquitectura por capas. El dominio define las reglas y los contratos; la aplicación coordina los casos de uso; la infraestructura implementa persistencia, seguridad y NLP; la API valida las solicitudes y proporciona las dependencias. En React se separan las pantallas, los componentes, los proveedores de contexto y los hooks.

```text
backend/
  app/
    api/                 Rutas HTTP, esquemas y dependencias
    application/         Casos de uso y puertos de servicios
    domain/              Entidades, contratos y reglas de matching
    infrastructure/      Base de datos, repositorios, seguridad y NLP
    core/                Configuración y limitación de solicitudes
    main.py              Arranque de FastAPI
  alembic/               Migraciones de base de datos
  scripts/               Herramientas de administración
  tests/                 Pruebas de API, dominio e infraestructura
frontend/
  src/
    api/                 Cliente HTTP
    components/          Controles y gráficos
    constants/           Sectores y ubicaciones
    contexts/            Autenticación y tema
    hooks/               Lógica reutilizable
    layouts/             Estructura de navegación
    pages/               Pantallas por rol
    routes/              Rutas y protección de acceso
    styles/              Estilos globales
  tests/                 Pruebas de selección de recomendaciones
scripts/                 Arranque local desde PowerShell
```

## Requisitos

- Python 3.12 o 3.13.
- Node.js 22 y npm.
- PostgreSQL instalado localmente o accesible desde un servidor.
- Git para clonar el repositorio.

La aplicación se ejecuta directamente con Python y Node.js; el repositorio no requiere contenedores.

El directorio local `docs/` contiene material de entregas y apoyo del proyecto, pero está excluido por `.gitignore` y no se publicará en el repositorio. También quedan fuera los archivos `.env`, las bases de datos locales, los CV cargados, los entornos virtuales y las compilaciones.

## Instalación local

Los siguientes comandos usan PowerShell y parten de una copia nueva del repositorio. Si ya tienes archivos `.env`, conserva sus valores en lugar de sobrescribirlos.

### 1. Preparar PostgreSQL

Conéctate como administrador mediante `psql` y crea un usuario y una base de datos para la aplicación:

```sql
CREATE ROLE talentsync LOGIN;
\password talentsync
CREATE DATABASE talentsync OWNER talentsync;
```

`\password` solicita la contraseña de forma interactiva. Guarda esos datos para configurar `DATABASE_URL`.

### 2. Instalar y configurar el backend

Desde la raíz del proyecto:

```powershell
cd backend
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Si utilizas Python 3.12, cambia `py -3.13` por `py -3.12`. En otros sistemas puedes crear el entorno con `python3 -m venv .venv` y utilizar `.venv/bin/python`.

Edita `backend/.env`:

- Sustituye `CHANGE_ME` en `DATABASE_URL` por la contraseña del usuario PostgreSQL. Los caracteres reservados de una contraseña deben codificarse para su uso en una URL.
- Completa `SECRET_KEY` con un valor aleatorio de al menos 32 caracteres. Puedes generar uno con:

```powershell
.\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(48))"
```

Para una instalación ligera, puedes instalar `requirements-lite.txt` en lugar de `requirements.txt` y configurar `CV_PARSER=pypdf`. Esta variante extrae la capa de texto del PDF y no realiza OCR.

### 3. Crear las tablas e iniciar la API

Desde `backend/`, con la base de datos disponible y el archivo `.env` configurado:

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Las migraciones crean el esquema. Las cuentas y las vacantes se crean al utilizar la aplicación.

- Estado del servicio: [http://localhost:8000/health](http://localhost:8000/health).
- Documentación interactiva de la API: [http://localhost:8000/docs](http://localhost:8000/docs).
- Contrato OpenAPI: [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json).

Para desarrollo aislado sin un servidor PostgreSQL, configura `DATABASE_URL=sqlite:///./talentsync.db` antes de ejecutar las migraciones sobre una base nueva. Los comandos del backend son los mismos.

### 4. Instalar e iniciar el frontend

Abre otra terminal en la raíz del proyecto:

```powershell
cd frontend
npm ci
Copy-Item .env.example .env
npm run dev
```

Abre [http://localhost:5173](http://localhost:5173). `frontend/.env` debe apuntar a la API mediante `VITE_API_URL=http://localhost:8000/api/v1`.

Después de la instalación inicial, puedes usar `scripts/dev-backend.ps1` y `scripts/dev-frontend.ps1`, cada uno en una terminal. El backend usa el puerto 8000 por defecto; para cambiarlo, ejecuta `./scripts/dev-backend.ps1 -Port 8007` y actualiza `VITE_API_URL` con el mismo puerto.

## Configuración

Las plantillas `.env.example` se incluyen en el repositorio. Los archivos `.env`, las bases de datos locales y los CV quedan excluidos del control de versiones.

| Variable | Uso |
| --- | --- |
| `APP_NAME` | Nombre mostrado por la API |
| `ENVIRONMENT` | `development` durante el desarrollo local; controla también la validación de hosts |
| `DATABASE_URL` | Conexión PostgreSQL o SQLite |
| `SECRET_KEY` | Clave de firma de los tokens JWT; obligatoria, mínimo 32 caracteres |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Vigencia del token, 120 minutos por defecto |
| `UPLOAD_DIR` | Directorio donde se guardan los CV, relativo a `backend/` al iniciar desde esa carpeta |
| `CORS_ORIGINS` | Lista JSON con los orígenes del frontend permitidos |
| `CV_PARSER` | `docling`, `auto` o `pypdf` |
| `CV_OCR_ENABLED` | Activa OCR en el procesamiento con Docling |
| `CV_OCR_FORCE_FULL_PAGE` | Fuerza OCR de página completa |
| `CV_DOCLING_TIMEOUT_SECONDS` | Tiempo límite configurado para Docling, 120 segundos por defecto |
| `CV_DOCLING_MIN_TEXT_CHARS` | Umbral mínimo de texto usado por el modo `auto`, 200 por defecto |
| `VITE_API_URL` | URL base del backend en el frontend, incluido `/api/v1` |

Reinicia el proceso correspondiente después de modificar su `.env`. Las variables `VITE_*` se incorporan al frontend y son visibles en el navegador; utiliza allí únicamente configuración pública.

## Cuentas y flujo de uso

Los candidatos y las empresas crean su cuenta desde **Crear cuenta**. El registro de una empresa requiere su nombre y NIT. El registro público no permite crear administradores.

Para crear una cuenta administradora, ejecuta desde `backend/`, después de aplicar las migraciones:

```powershell
.\.venv\Scripts\python.exe -m scripts.create_admin --name "Tu nombre" --email "tu-correo@tu-dominio.com"
```

La herramienta solicita y confirma la contraseña sin mostrarla en pantalla. Crea una cuenta nueva con la contraseña almacenada como hash bcrypt; rechaza correos existentes para evitar sobrescribir cuentas o cambiar sus permisos.

El flujo principal es:

1. La empresa completa su perfil y publica una vacante con requisitos, sector y etapas de selección.
2. El candidato completa su perfil y carga un CV en PDF de hasta 5 MB.
3. La aplicación extrae texto y datos profesionales; el candidato puede revisar y editar su perfil.
4. El motor compara perfiles y vacantes y presenta compatibilidad, habilidades coincidentes y brechas.
5. El candidato se postula y la empresa gestiona el proceso; los cambios generan notificaciones dentro de la aplicación.

## Extracción de CV y matching

Docling reconstruye la estructura del documento y utiliza EasyOCR cuando corresponde. `pypdf` proporciona una ruta alternativa de extracción. El modo `auto` recurre a Docling cuando la capa de texto parece insuficiente; el modo `docling` intenta usarlo siempre.

La primera ejecución puede descargar modelos y tardar más. Forzar OCR de página completa aumenta el trabajo de procesamiento. Los resultados dependen de la calidad del PDF; los datos del perfil siguen siendo editables.

La normalización y las heurísticas extraen habilidades, experiencia, formación, ubicación y otros campos. `HashingVectorizer` genera vectores de 384 dimensiones y el matching combina:

```text
compatibilidad = 0.60 × cobertura de habilidades + 0.40 × similitud textual
```

Los resultados incluyen motivos, categorías y filtros de relevancia. Las reglas se encuentran en `backend/app/domain/services/matching.py`; la persistencia y el ordenamiento se coordinan en `backend/app/application/use_cases/matching.py`.

## API

Las rutas funcionales comienzan con `/api/v1`. Las operaciones protegidas reciben el token mediante `Authorization: Bearer <token>`.

| Grupo | Responsabilidad |
| --- | --- |
| `/auth` | Registro, inicio de sesión e identidad actual |
| `/profiles` | Perfil profesional, CV y acceso autorizado a candidatos |
| `/companies` | Información y gestión de empresas |
| `/jobs` | Búsqueda, publicación y actualización de vacantes |
| `/applications` | Postulaciones, etapas, notas y entrevistas |
| `/recommendations` | Recomendaciones de vacantes y ranking de candidatos |
| `/notifications` | Notificaciones y estado de lectura |
| `/admin` | Métricas y gestión administrativa |

Los parámetros, esquemas y permisos se pueden consultar en la documentación interactiva de la API.

## Pruebas y compilación

Desde `backend/`:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider
```

Las pruebas de integración usan SQLite en memoria y las de migraciones utilizan archivos temporales. La generación de SQL PostgreSQL se comprueba sin conectarse a un servidor. Estas pruebas no sustituyen la verificación de un despliegue PostgreSQL ni una ejecución completa del OCR.

Desde `frontend/`:

```powershell
npm run lint
npm test
npm run build
```

La compilación produce `frontend/dist`. `npm run preview` permite revisarla localmente. Para publicar la aplicación se necesita un servicio que ejecute la API y un alojamiento para los archivos estáticos con redirección de rutas hacia `index.html`. Al preparar producción, configura HTTPS, CORS, almacenamiento persistente de CV y los hosts permitidos en `backend/app/main.py` según tu dominio.

## Antes de producción

El repositorio contiene el código funcional y las migraciones, pero todavía requiere una infraestructura de despliegue. Antes de exponerlo públicamente debes:

- desplegar la API y el frontend en servicios con HTTPS;
- usar PostgreSQL administrado y definir un proceso de copias de seguridad y restauración;
- mover los CV a almacenamiento persistente y privado, con una política de retención;
- configurar dominios, CORS, hosts permitidos y secretos fuera del repositorio;
- añadir correo transaccional si se necesitan avisos fuera de la aplicación;
- incorporar monitorización, registros centralizados, límites de tamaño y revisión de dependencias.

No se incluyen cuentas precargadas, vacantes de ejemplo ni datos de prueba. Crea los usuarios desde la interfaz y la cuenta administradora mediante `scripts/create_admin.py`.

## Problemas frecuentes

- **La API rechaza `SECRET_KEY`:** completa la variable con una clave de al menos 32 caracteres.
- **No hay conexión con PostgreSQL:** revisa que el servicio esté iniciado, la base exista y la URL contenga las credenciales correctas.
- **Faltan tablas:** ejecuta las migraciones desde `backend/` sobre la base configurada para esa instalación.
- **El frontend no conecta con la API:** comprueba el puerto, `VITE_API_URL` y `CORS_ORIGINS`; reinicia Vite después de modificar su configuración.
- **El CV no produce texto:** comprueba que tenga texto seleccionable o utiliza la instalación completa con OCR.
- **No aparecen recomendaciones:** completa el perfil, añade habilidades y verifica que existan vacantes activas compatibles.
