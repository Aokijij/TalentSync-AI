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
| 3 | Verificación empresarial, equipos y permisos | Pendiente |
| 4 | Requisitos, evidencias, preferencias y matching avanzado | Pendiente |
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
