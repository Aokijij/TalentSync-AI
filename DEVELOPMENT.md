# Desarrollo local por bloques

Rama: `codex/desarrollo-funcionalidades-local`. Sin despliegues ni push.

## Arranque aislado

Desde la raíz, con Python disponible (o `backend/.venv/Scripts/python.exe`):

```powershell
backend/.venv/Scripts/python.exe scripts/local.py setup
backend/.venv/Scripts/python.exe scripts/local.py seed
backend/.venv/Scripts/python.exe scripts/local.py accounts
backend/.venv/Scripts/python.exe scripts/local.py backend
```

En otra terminal, desde `frontend/`:

```powershell
$env:VITE_API_URL='/api/v1'
npm run dev -- --host 127.0.0.1
```

Abre http://127.0.0.1:5173. Vite reenvía `/api` al backend local en 8000.
Los archivos `.env` existentes no se modifican. La base, archivos y credenciales
ficticias se guardan en `.local/` (excluido de Git). La semilla es idempotente y
rechaza cualquier base distinta de la SQLite aislada. Azure y sincronizaciones
externas permanecen desactivados, incluso si existen variables heredadas.

## Versionamiento

Cada bloque se confirma después de sus pruebas y revisión del diff. Las migraciones
son aditivas y se comprueba generación SQL de PostgreSQL además de SQLite.
Las integraciones sin credenciales deben mostrarse como no configuradas; no se
simulan accesos sociales, certificados, probabilidades o llamadas externas.

## Bloques y alcance

| Bloque | Alcance | Estado |
| --- | --- | --- |
| 1 | Entorno aislado, semilla ficticia e historial de eventos | Completado: 71 pruebas backend, 20 frontend, lint y build |
| 2 | Correo local, recuperación, verificación, sesiones, MFA y privacidad | Implementado y probado; SSO externo pendiente del bloque 9 |
| 3 | Verificación empresarial, equipos y permisos | Implementado: revisión manual local, borradores, invitaciones y permisos en API |
| 4 | Requisitos, evidencias, preferencias y matching avanzado | Base explicable implementada; embeddings neuronales y modelos de comportamiento en bloque 9 |
| 5 | Historial de etapas, plazos, avisos y feedback | Pendiente |
| 6 | Brechas, recursos, planes, evaluaciones, pasaporte y portafolio | Pendiente |
| 7 | Selección ciega, calidad de vacantes y contratación por potencial | Pendiente |
| 8 | Reputación, incidencias, auditoría y tendencias | Pendiente |
| 9 | Entrevistas, colaboración e integraciones avanzadas | Pendiente |

## Comprobaciones

```powershell
backend/.venv/Scripts/python.exe scripts/local.py test
# Desde frontend/: npm test; npm run lint; npm run build
```

El flujo de eventos acepta únicamente metadatos escalares permitidos. No contiene
contraseñas, tokens, CV completos ni respuestas privadas de entrevistas. Cada evento
se guarda en la misma transacción de la operación que describe.

## Bloque 2: acceso local

El lanzador aislado activa sesiones opacas revocables mediante cookie HttpOnly,
CSRF por sesión y cookies sin `Secure` exclusivamente en desarrollo HTTP local.
Producción siempre fuerza `Secure`. El modo JWT anterior permanece disponible
por defecto para compatibilidad, pero está desactivado en el entorno aislado.
Empresas y administradores deben configurar TOTP antes de operar. El secreto se
cifra en reposo; los códigos de recuperación se guardan como hashes y son de un
solo uso. La recuperación de contraseña conserva MFA y revoca las sesiones.

La bandeja `/desarrollo/correos` solo funciona con la opción local activada,
SQLite y acceso de loopback. Contiene enlaces temporales sensibles de prueba;
no es un servicio de correo ni debe exponerse a redes externas.

Los botones sociales aparecen desactivados: todavía no hay adaptadores OAuth.
Su implementación y vinculación segura corresponden al bloque 9; añadir
credenciales por sí solo no los habilita en este punto.

Validación del bloque: 77 pruebas backend en conjunto; 11 pruebas de seguridad,
arquitectura y migración repetidas tras endurecer el consumo de códigos MFA;
lint y build frontend. Se comprobó en navegador el login del candidato,
persistencia al navegar y pantalla de seguridad. La semilla utiliza direcciones
ficticias bajo el dominio reservado example.com.

## Bloque 3: organizaciones

`/empresa/equipo` reúne verificación, invitaciones de tres días y asignaciones.
`/admin/verificaciones` permite aprobar, pedir información, rechazar o suspender
con un motivo. Las nuevas empresas locales requieren correo confirmado y revisión
manual antes de publicar o consultar talento. Suspender pausa sus vacantes activas.
Las empresas anteriores conservan su acceso para una migración gradual.

Cada cuenta empresarial pertenece a una organización en esta versión. El propietario
gestiona la identidad y el equipo; el reclutador gestiona selección; el entrevistador
solo consulta las vacantes asignadas con alias de candidatos. Cambiar permisos revoca
las sesiones anteriores. Los borradores solo son visibles a la empresa y al admin.
Las invitaciones están ligadas al correo, almacenadas como hash y se consumen una vez.
La revisión local no consulta registros oficiales ni equivale a una verificación legal.

## Bloque 4: compatibilidad explicable

`/compatibilidad` permite al candidato comparar requisitos ponderados (esenciales
y deseables), preferencias imprescindibles y evidencias de portafolio. La empresa
edita allí los requisitos. Las bases relacionadas del grafo se muestran separadas:
Java no acredita Spring Boot y Spring Boot no acredita microservicios.
Los enlaces aportados son declaraciones; no se descargan ni se verifican solos.

Cada recomendación conserva versión del algoritmo, huella de sus entradas,
contribuciones al resultado y brechas. El caché detecta cambios del candidato y de
la vacante. La interfaz usa los pesos del servidor, incluidos idiomas y formación.
El porcentaje es un índice de afinidad; las preferencias se comparan aparte para
no alterar el mérito técnico. El componente textual actual usa HashingVectorizer
local y se identifica como lexical-hashing-v1. No se presenta como un modelo
neuronal ni una probabilidad de éxito. El procesamiento de CV existente se conserva.
Validación acumulada: 81 pruebas backend; lint y build frontend aprobados.
