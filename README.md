<p align="center">
  <img src="frontend/public/brand/talentsync-mark.png" alt="Logo de TalentSync AI" width="112" />
</p>

# TalentSync AI

TalentSync AI es una plataforma de selección laboral para candidatos, empresas y administradores. Centraliza la hoja de vida, las vacantes, las postulaciones y el seguimiento de cada proceso. También calcula una compatibilidad explicable entre el perfil y la vacante para ayudar a ordenar oportunidades y candidatos; el resultado sirve como apoyo y no reemplaza la evaluación de la empresa.

## Aplicación publicada

- Frontend: [https://talentsync-ai.pages.dev](https://talentsync-ai.pages.dev)
- Estado de la API: [https://talentsync-3c02d6e1.yellowwater-01e17d41.eastus2.azurecontainerapps.io/health](https://talentsync-3c02d6e1.yellowwater-01e17d41.eastus2.azurecontainerapps.io/health)

El frontend se publica en Cloudflare Pages. La API, PostgreSQL y el almacenamiento privado de archivos se ejecutan en Azure.

## Qué puede hacer cada rol

### Candidato

- Completar su perfil profesional y registrar idiomas con nivel.
- Cargar una hoja de vida en PDF y corregir la información extraída.
- Elegir estilo, fotografía y paleta de colores para la vista previa del CV.
- Explorar vacantes con filtros progresivos por ubicación, modalidad, contrato, sector, rango salarial y fecha de publicación.
- Consultar cuánto tiempo lleva publicada cada oportunidad y recibir recomendaciones ordenadas por compatibilidad.
- Definir el porcentaje mínimo para sus recomendaciones y avisos.
- Responder las preguntas de preselección que una empresa haya configurado antes de postularse.
- Consultar postulaciones, empresas seguidas y notificaciones organizadas por categoría.
- Exportar la hoja de vida con el nombre `Nombre - HV - TalentSync.pdf`.

### Empresa

- Crear un perfil público con logo, portada, propósito, cultura y beneficios.
- Publicar vacantes con modalidad, contrato, ubicación, habilidades, idiomas y preguntas opcionales de preselección. Las opciones se valoran individualmente y las respuestas abiertas se revisan de forma manual.
- Buscar talento por vacante, nombre, profesión o habilidad; la lista de perfiles para invitar muestra compatibilidades desde 80%.
- Revisar candidatos en una tabla paginada y comparar únicamente los cinco perfiles y habilidades más relevantes.
- Invitar candidatos compatibles y revisar tanto el porcentaje base como el ajuste privado de preselección.
- Preparar cambios de etapa y confirmarlos antes de enviar notificaciones.
- Marcar una vacante como cubierta cuando el cupo esté completo.
- Reabrir una vacante con el mismo proceso o crear uno nuevo sin perder el historial.

### Administración

- Acceder desde una dirección independiente.
- Consultar métricas de la plataforma.
- Gestionar usuarios, empresas y vacantes según los permisos del rol.
- Importar catálogos autorizados de vacantes desde CSV o Excel. La plataforma conserva la fuente y el enlace original, actualiza ofertas repetidas mediante su ID externo y oculta automáticamente las que hayan vencido.

### Catálogos externos de vacantes

La consola administrativa incluye una plantilla descargable para cargar hasta 2.000 ofertas por archivo. Cada fila debe identificar la fuente, un ID externo estable, la empresa, el cargo, la descripción, los requisitos, el sector y el enlace de la publicación original. También admite salario, ubicación, modalidad, contrato, habilidades, beneficios, idiomas y fechas de publicación y vencimiento.

Las habilidades y los beneficios se separan con `|`; los idiomas se escriben como `idioma:nivel`, por ejemplo `inglés:B2|español:NATIVE`. Las ofertas importadas aparecen señaladas como externas y el candidato continúa la postulación en el sitio de origen. Solo deben cargarse fuentes que permitan reutilizar y mostrar sus publicaciones; este mecanismo no autoriza copiar datos de terceros sin permiso.

#### Sincronización con Jooble Colombia

La sección **Administración → Vacantes** también puede consultar la API regional de Jooble. El administrador elige los perfiles, la ubicación y entre una y cinco páginas; TalentSync conserva la atribución, el enlace original y el ID de Jooble para actualizar cada oferta sin duplicarla. Las ofertas dejan de mostrarse después de 30 días si no se sincronizan nuevamente.

Jooble entrega mediante su API un **resumen** de cada anuncio, no su descripción completa. TalentSync identifica habilidades explícitas y equivalencias profesionales a partir del cargo y de ese resumen, marca la compatibilidad como estimada y conserva el enlace original para confirmar funciones y requisitos. Cuando Jooble informa un rango salarial, TalentSync usa el límite inferior para no mostrar una promesa superior a la publicada. Consulta la [documentación oficial de la API de Jooble](https://help.jooble.org/en/support/solutions/articles/60001448238).

Solicita la clave en [Jooble Colombia](https://co.jooble.org/api/about) y guárdala exclusivamente en el backend:

```dotenv
JOOBLE_API_KEY=clave_regional_de_colombia
JOOBLE_API_BASE_URL=https://co.jooble.org/api
JOOBLE_TIMEOUT_SECONDS=20
```

La clave no utiliza el prefijo `VITE_` y nunca debe guardarse en Git. Cada página consultada consume una solicitud de la cuota asignada por Jooble, por eso la sincronización se ejecuta de forma manual desde la consola administrativa.

## Cómo funciona la compatibilidad

El backend usa la misma función para la vista del candidato y para el ranking de la empresa. Así evita que un mismo perfil muestre porcentajes distintos para la misma vacante.

Sin requisitos de idioma:

```text
compatibilidad = 60% habilidades requeridas + 40% contexto profesional
```

Cuando la vacante exige idiomas:

```text
compatibilidad = 60% habilidades + 30% contexto profesional + 10% nivel de idioma
```

El contexto profesional combina similitud de texto con profesión, cargos, responsabilidades y formación. Los niveles de idioma se comparan de forma ordinal desde A1 hasta C2 y nativo. El porcentaje es orientativo: depende de la información registrada y no certifica competencias.

Las preguntas de preselección no alteran el porcentaje público que ve el candidato. Las preguntas con opciones pueden aportar o restar puntos según la valoración configurada para cada respuesta; el ajuste privado se limita a 20 puntos y solo puede consultarlo la empresa. Las respuestas abiertas no se califican automáticamente porque requieren la revisión del equipo de selección.

## Arquitectura

| Capa | Tecnologías y responsabilidad |
| --- | --- |
| Frontend | React 19, React Router, Vite 6, Tailwind CSS, Axios y React Hook Form |
| API | FastAPI, Pydantic y Uvicorn |
| Dominio | Reglas de matching, habilidades, estados y contratos |
| Aplicación | Casos de uso para autenticación, perfiles, vacantes, postulaciones y recomendaciones |
| Persistencia | SQLAlchemy, Alembic y PostgreSQL; SQLite para pruebas aisladas |
| Seguridad | JWT, bcrypt, autorización por rol y limitación de solicitudes |
| Procesamiento de CV | pypdf en la imagen ligera; Docling y EasyOCR en la instalación completa |
| Producción | Cloudflare Pages, Azure Container Apps, PostgreSQL Flexible Server y Blob Storage |

El backend mantiene separadas las reglas de negocio, los casos de uso, la infraestructura y las rutas HTTP. El frontend divide pantallas, componentes, contextos, hooks y acceso a la API. Esta separación permite probar las reglas sin depender de la interfaz.

```text
backend/
  app/
    domain/              Entidades, contratos y reglas de matching
    application/         Casos de uso y puertos de servicios
    infrastructure/      Base de datos, repositorios, seguridad y NLP
    api/                  Rutas, esquemas y dependencias HTTP
    core/                 Configuración y limitación de solicitudes
  alembic/               Migraciones versionadas
  scripts/               Herramientas de administración
  tests/                 Pruebas de dominio, infraestructura y API

frontend/
  public/brand/          Logo y recursos de identidad
  src/
    api/                 Cliente Axios y tratamiento de errores
    components/          Controles reutilizables
    constants/           Idiomas, sectores, ciudades y paletas
    contexts/            Autenticación y tema
    hooks/               Lógica reutilizable
    layouts/             Navegación por rol
    pages/               Pantallas de candidato, empresa y administración
    routes/              Rutas y protección de acceso
    styles/              Estilos globales
  tests/                 Pruebas de utilidades de interfaz

scripts/                 Desarrollo y despliegue desde PowerShell
```

## Requisitos para desarrollo

- Python 3.12 o 3.13.
- Node.js 22 y npm.
- Git.
- PostgreSQL para un entorno persistente. SQLite también sirve para una prueba local aislada.

Docker se usa para construir la imagen de producción; no es necesario para ejecutar el proyecto localmente.

## Instalación local

Los comandos siguientes usan PowerShell y parten de una copia nueva. Si ya existen archivos `.env`, conserva sus valores.

### 1. Clonar el repositorio

```powershell
git clone https://github.com/Aokijij/TalentSync-AI.git
cd TalentSync-AI
```

### 2. Preparar el backend

```powershell
cd backend
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lite.txt
Copy-Item .env.example .env
```

La instalación ligera utiliza `pypdf` y funciona con PDF que contienen texto seleccionable. Para habilitar Docling y OCR, instala `requirements.txt` y revisa las variables `CV_*`.

Para una prueba rápida con SQLite, edita `backend/.env`:

```dotenv
ENVIRONMENT=development
DATABASE_URL=sqlite:///./talentsync.db
SECRET_KEY=PEGA_AQUI_UNA_CLAVE_ALEATORIA_DE_AL_MENOS_32_CARACTERES
CV_PARSER=pypdf
CV_OCR_ENABLED=false
CORS_ORIGINS=["http://localhost:5173","http://127.0.0.1:5173"]
```

Genera `SECRET_KEY` localmente:

```powershell
.\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(48))"
```

Aplica las migraciones e inicia la API:

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Comprueba estos puntos:

- [http://localhost:8000/health](http://localhost:8000/health)
- [http://localhost:8000/docs](http://localhost:8000/docs)
- [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

### 3. Preparar el frontend

Abre otra terminal en la raíz del repositorio:

```powershell
cd frontend
npm ci
Copy-Item .env.example .env
npm run dev
```

`frontend/.env` debe contener:

```dotenv
VITE_API_URL=http://127.0.0.1:8000/api/v1
```

Abre [http://localhost:5173](http://localhost:5173). Después de la instalación inicial también puedes iniciar cada parte con `scripts/dev-backend.ps1` y `scripts/dev-frontend.ps1`.

### 4. Usar PostgreSQL en local

Crea un usuario y una base con un administrador de PostgreSQL:

```sql
CREATE ROLE talentsync LOGIN;
\password talentsync
CREATE DATABASE talentsync OWNER talentsync;
```

Luego configura `DATABASE_URL` con el formato `postgresql+psycopg://usuario:contraseña@servidor:5432/base`. Codifica los caracteres reservados de la contraseña para que formen una URL válida y vuelve a ejecutar las migraciones.

## Variables de entorno principales

### Backend

| Variable | Uso |
| --- | --- |
| `ENVIRONMENT` | Entorno de ejecución y validaciones asociadas |
| `DATABASE_URL` | Conexión PostgreSQL o SQLite |
| `SECRET_KEY` | Firma de JWT; es obligatoria y debe tener al menos 32 caracteres |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Vigencia de la sesión |
| `UPLOAD_DIR` | Almacenamiento local de archivos durante desarrollo |
| `AZURE_STORAGE_ACCOUNT_URL` | Cuenta de Blob Storage usada en producción |
| `AZURE_STORAGE_CONTAINER` | Contenedor privado para CV e imágenes |
| `ALLOWED_HOSTS` | Hosts HTTP aceptados por la API |
| `CORS_ORIGINS` | Orígenes exactos que pueden llamar a la API desde el navegador |
| `CV_PARSER` | `pypdf`, `docling` o `auto` |
| `CV_OCR_ENABLED` | Activa OCR cuando el procesador lo admite |

### Frontend

| Variable | Uso |
| --- | --- |
| `VITE_API_URL` | URL base de la API, incluido `/api/v1` |

Las variables `VITE_*` quedan incluidas en los archivos enviados al navegador. No guardes secretos en ellas ni agregues archivos `.env` al repositorio.

## Flujo de uso

1. La empresa completa su perfil, publica una vacante y, si lo necesita, añade preguntas de preselección.
2. El candidato completa su perfil, registra idiomas y carga su CV.
3. El backend extrae la información disponible y calcula la compatibilidad.
4. El candidato revisa recomendaciones, responde las preguntas requeridas y decide a cuáles postularse.
5. La empresa compara perfiles, respuestas y compatibilidad ajustada, invita talento y prepara movimientos en el tablero.
6. El botón **Guardar cambios y notificar** confirma los movimientos pendientes.
7. Contratar a una persona no rechaza a las demás ni cubre la vacante automáticamente.
8. La empresa marca la vacante como cubierta cuando completa el cupo.
9. Si necesita reabrirla, puede continuar con el historial existente o crear otro proceso.

## Cuenta administradora

El registro público solo crea candidatos y empresas. Para crear un administrador, ejecuta desde `backend/`:

```powershell
.\.venv\Scripts\python.exe -m scripts.create_admin --name "Tu nombre" --email "tu-correo@tu-dominio.com"
```

El comando solicita la contraseña sin mostrarla. El acceso administrativo se abre en `/acceso-administracion`; las cuentas de candidato y empresa no pueden ingresar allí.

## Pruebas y compilación

Backend:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider
```

Frontend:

```powershell
cd frontend
npm test
npm run lint
npm run build
```

Las pruebas de integración usan SQLite aislado. La generación de SQL de PostgreSQL se valida sin conectarse a producción. El repositorio aún no incluye una suite de navegador con Cypress o Playwright ni una campaña documentada de carga.

El workflow `.github/workflows/ci.yml` ejecuta pruebas, lint, auditorías, migraciones y una construcción Docker. CI valida el commit, pero no despliega automáticamente.

## API

Todas las rutas funcionales comienzan en `/api/v1`. Las operaciones protegidas reciben `Authorization: Bearer <token>`.

| Grupo | Responsabilidad |
| --- | --- |
| `/auth` | Registro, inicio de sesión e identidad actual |
| `/profiles` | Perfil, CV, idiomas y acceso autorizado a candidatos |
| `/companies` | Perfil público y gestión de empresas |
| `/jobs` | Métricas públicas, búsqueda avanzada, preguntas, publicación, cierre y reapertura de vacantes |
| `/applications` | Postulaciones, respuestas de preselección, etapas, notas e entrevistas |
| `/recommendations` | Vacantes sugeridas y ranking de candidatos |
| `/notifications` | Avisos por categoría, paginación, estado de lectura y eliminación |
| `/admin` | Métricas, gestión administrativa e importación CSV/XLSX de catálogos autorizados |

Consulta `/docs` para ver parámetros, esquemas y respuestas del contrato vigente.

## Actualización de producción

La publicación tiene dos pasos separados: Azure para la API y Cloudflare Pages para el frontend. Antes de actualizar, ejecuta pruebas, revisa el diff, confirma un respaldo recuperable y crea el commit que identificará la imagen.

Desde PowerShell 7, en la raíz del repositorio:

```powershell
./scripts/update-production.ps1 -WhatIf
./scripts/update-production.ps1 -BackupVerified -FrontendOrigin https://talentsync-ai.pages.dev
./scripts/deploy-cloudflare.ps1
```

`-WhatIf` muestra el destino y la operación prevista. La actualización real exige un árbol Git limpio, conserva los secretos y comprueba que la nueva revisión responda `/health`. El script de Cloudflare compila con la URL HTTPS de la API y publica únicamente `frontend/dist`.

No ejecutes semillas, `alembic downgrade` ni reinicios de base de datos en producción. Si una revisión falla, comprueba primero que la imagen anterior sea compatible con el esquema actual. Las fotos, logos, portadas y CV deben permanecer en Blob Storage antes de retirar una revisión.

## Seguridad y datos

- JWT identifica al usuario y su rol; el backend vuelve a verificar permisos y propiedad de cada recurso.
- Las contraseñas se almacenan como hash bcrypt.
- CV e imágenes se guardan en almacenamiento privado en producción.
- `SECRET_KEY`, credenciales, tokens y archivos `.env` deben permanecer fuera de Git.
- El matching y los niveles de idioma son orientativos y no deben usarse como única decisión de contratación.
- El procesamiento de CV depende de la calidad del archivo; la imagen ligera no aplica OCR a documentos escaneados.

## Problemas frecuentes

- **La API rechaza `SECRET_KEY`:** usa una clave aleatoria de al menos 32 caracteres.
- **No hay conexión con PostgreSQL:** revisa el servicio, la base, las credenciales y la codificación de la URL.
- **Faltan tablas:** ejecuta `alembic upgrade head` con la misma `DATABASE_URL` que usa la API.
- **El frontend no conecta:** comprueba `VITE_API_URL`, `CORS_ORIGINS` y el puerto; reinicia Vite después de cambiar `.env`.
- **El CV no produce texto:** usa un PDF con texto seleccionable o instala la variante con Docling y OCR.
- **No aparecen recomendaciones:** completa profesión, experiencia, habilidades e idiomas y verifica que existan vacantes activas.
- **Git busca `credential-manager`:** configura el helper instalado, por ejemplo `git config --global credential.helper manager-core`.
