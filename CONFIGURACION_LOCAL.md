# Configuración y revisión de TalentSync

Guía del 13 de octubre de 2026. Se utiliza el entorno aislado `.local/`, SQLite y los servidores de tu computador. No requiere publicar la aplicación, comprar un dominio ni crear recursos de Azure.

## 1. Abrir el proyecto

Abre PowerShell en la carpeta del proyecto:

```powershell
cd "C:\Users\USUARIO\OneDrive\Escritorio\TalentSync AI"
```

Las dependencias ya están instaladas en esta máquina. Si preparas otro equipo, instala Python compatible con los requisitos del proyecto y Node.js, crea `backend/.venv`, instala `backend/requirements-lite.txt` y `backend/requirements-dev.txt`, y ejecuta `npm ci` dentro de `frontend`. Los pesos locales del motor se preparan con `scripts/local.py model-prepare`; ese paso requiere descargar el modelo. En esta máquina los pesos ya existen.

## 2. Preparar y comprobar la base local

```powershell
backend/.venv/Scripts/python.exe scripts/local.py setup
backend/.venv/Scripts/python.exe scripts/local.py doctor
```

`setup` aplica las migraciones existentes. Esta entrega conserva las fechas y preferencias en campos JSON existentes: no sustituye cuentas ni necesita una migración nueva. `doctor` comprueba archivos, base y servidores; los servidores pueden aparecer como aviso si todavía no los abriste.

No cambies DATABASE_URL al PostgreSQL de otro entorno. Los comandos locales no leen `backend/.env`; usan `.local/backend.env` y `.local/talentsync.sqlite3`.

## 3. Iniciar los dos servidores

En una primera terminal, desde la raíz:

```powershell
backend/.venv/Scripts/python.exe scripts/local.py backend
```

En otra terminal:

```powershell
cd "C:\Users\USUARIO\OneDrive\Escritorio\TalentSync AI\frontend"
node node_modules/vite/bin/vite.js --host 127.0.0.1 --port 5173 --strictPort
```

Abre [TalentSync local](http://127.0.0.1:5173). Conserva ambas terminales abiertas. Si un puerto está ocupado, reutiliza el servidor del proyecto o detenlo con Ctrl+C en su terminal antes de iniciarlo otra vez. No cierres procesos desconocidos.

## 4. Entrar con las cuentas de revisión

Las cuentas ficticias y sus contraseñas se guardan en `.local/escenarios/accounts.json`. Usa el portal correspondiente a candidato, empresa o administrador. Ese archivo es privado y no se incorpora a Git.

Si estás preparando una base local nueva, puedes crear los escenarios con:

```powershell
backend/.venv/Scripts/python.exe scripts/local.py seed-scenarios
```

La base actual ya contiene esos escenarios; no necesitas volver a generarlos para revisar esta entrega. El correo permanece en la bandeja local y la pausa local de la verificación en dos pasos se conserva.

## 5. Configurar el perfil del candidato

1. En **Mi perfil**, pulsa Editar.
2. Confirma tu ciudad y departamento.
3. En **Preferencias laborales → Ciudad y movilidad**, indica si aceptas trasladarte y si puedes viajar. Son decisiones diferentes.
4. Añade otras ciudades donde puedes asistir habitualmente, separadas por comas. Esto no representa una preferencia de viajes ocasionales.
5. Solo marca un trabajo como actual. Al seleccionar otro, revisa y completa la finalización del anterior. En cada experiencia, abre el calendario, escribe el año y elige un mes de la cuadrícula para inicio y finalización, o marca **Trabajo actualmente aquí**. Guarda el perfil.

En Formación académica, marca **Estudio actualmente aquí** para una carrera en curso. Se mostrará **En curso** en el perfil y la hoja de vida, y no se tomará como un nivel académico terminado.

Las fechas antiguas que solo tienen año siguen disponibles: no se inventaron meses. Las fechas futuras o invertidas se rechazan. Un final vacío no cuenta como empleo actual. Los meses de cargos simultáneos no se suman dos veces al calcular la experiencia total.

## 6. Revisar las vacantes y su calidad

1. En Empresa → **Calidad de ofertas**, elige una vacante.
2. Completa salario fijo o rango, contrato, días y horario, modalidad y ciudad/territorio.
3. Describe responsabilidades y al menos un resultado con su evaluación y plazo.
4. Indica nivel, años mínimos —pueden ser cero— y evidencia aceptada. Distingue habilidades esenciales, deseables y aprendibles.
5. En Idiomas, pulsa Añadir idioma, selecciona su nombre y nivel mínimo. Elimina filas que no vayas a completar.
6. Completa entrevistas, duración total y plazo de respuesta por avance.
7. Revisa las indicaciones. Pulsar una mejora abre el paso correspondiente y lleva al campo cuando está disponible.
8. Guarda como borrador o publica cuando la revisión y la verificación de empresa lo permitan.

La puntuación se recalcula con el borrador actual. Si una revisión falla, no se presenta la puntuación anterior como vigente. El horario debe explicar días y horas o turnos; texto de relleno no basta. La revisión sigue siendo orientativa, basada en reglas; no verifica contratos ni condiciones reales.

En **Mis vacantes**, Ver candidatos y Editar son las acciones principales. Debajo aparecen Revisar calidad, Pausar/Activar/Reabrir y Eliminar, sin desplegar un menú. En Postulaciones, guarda los movimientos pendientes antes de finalizar el proceso.

La puntuación muestra cuatro niveles: **A · Excelente (90–100)**, **B · Buena (75–89)**, **C · Por mejorar (50–74)** y **D · Inicial (0–49)**. Abre **¿Qué significa cada nivel?** junto a la puntuación para consultar la explicación. El nivel describe la claridad e información registrada; los requisitos obligatorios para publicar se revisan por separado.

En **Mejora la redacción de tu oferta**, pulsa Preparar mejoras. Revisa las pestañas Responsabilidades y Requisitos, consulta qué cambió y edita la propuesta. **Aplicar este texto** modifica el borrador; **Restaurar texto anterior** revierte esa aplicación. Guarda únicamente después de revisar. El asistente local conserva el contexto, organiza los datos y retira frases genéricas independientes; no inventa funciones, condiciones ni cifras. Si detecta información contradictoria, pide confirmarla.

## 7. Buscar talento y revisar procesos

1. En **Buscar talento**, selecciona la vacante y el grupo: personas para invitar o quienes ya se postularon.
2. Busca por nombre, profesión o habilidad y ajusta el porcentaje mínimo. Usa Anterior/Siguiente: se muestran nueve candidatos por página, en tres columnas cuando hay espacio.
3. Revisa **Ubicación y movilidad**. Para presencial/híbrido, se compara la ciudad y el departamento cuando están disponibles; también se consideran las ciudades de asistencia declaradas.
4. Un traslado aceptado se señala como pendiente de acordar. Poder viajar no se considera aceptación de asistencia diaria. Si faltan datos, se pide confirmar disponibilidad.
5. Cuando hay otra ciudad y el candidato rechaza tanto viajes como traslado, el índice mostrado a la empresa recibe un ajuste relativo de −20%, explicado junto al índice profesional, y se bloquea la invitación. Es una regla local de disponibilidad, no una probabilidad de contratación. Las preferencias no modifican el índice profesional del candidato.
6. En **Organización y equipo → Procesos asignados**, filtra por vacante, etapa o candidato. La lista muestra ocho procesos por página; Abrir proceso conserva el acceso a entrevista y evaluación interna según el rol.

El propietario y el reclutador pueden abrir **Asignar entrevistas**, elegir un entrevistador activo y seleccionar sus vacantes. Guardar reemplaza las asignaciones de ese entrevistador; desmarcar una vacante retira el acceso. Esta acción no cambia roles ni permite invitar o retirar integrantes. Cuando la empresa ya está verificada, Verificada pasa al último apartado y la pantalla abre Equipo o Procesos.

## 8. Administración y catálogo educativo

En **Salud del ecosistema** hay dos apartados: Comportamiento de empresas y Bandeja de incidencias. El mapa de habilidades y la auditoría están desplegables dentro del primero; las incidencias se atienden en su propia bandeja.

En **Catálogo educativo**:

1. Biblioteca muestra una tabla administrativa con recursos publicados, sin publicar y base de plataforma. Permite buscar por título/habilidad, filtrar por proveedor, editar y abrir la fuente oficial.
2. Fuentes y conectores organiza cada proveedor en su propio apartado: Selección editorial, SENA, Sapiencia, YouTube y Microsoft. Muestra un conector a la vez y los pasos para activarlo.
3. Biblioteca oficial contiene la selección editorial de 65 recursos. SENA y Sapiencia consultan fuentes públicas; YouTube y Microsoft requieren su configuración externa.
4. Importa primero como borrador, comprueba contenido, habilidades, acceso y certificado, y publica la selección revisada.

Para cargar la selección editorial y actualizar las fuentes públicas en la base local:

```powershell
backend/.venv/Scripts/python.exe scripts/local.py seed-education
backend/.venv/Scripts/python.exe scripts/local.py sync-education
```

La carga conserva ediciones y planes existentes. La consulta al SENA y Sapiencia requiere Internet. Una inscripción anunciada no garantiza cupo.

## 9. Integraciones sin clave: SENA, Sapiencia, GitHub y Codewars

Edita únicamente `.local/backend.env`, conservando sus demás valores:

```dotenv
PUBLIC_LEARNING_REFRESH_ENABLED=true
GITHUB_PROJECT_ANALYSIS_ENABLED=true
CODEWARS_ENABLED=true
```

Reinicia el backend. El refresco de SENA/Sapiencia revisa fichas ya guardadas mientras el servidor está abierto; no publica cursos automáticamente. Desde el catálogo administrativo puedes buscar e incorporar otros programas del SENA.

GitHub y Codewars se consultan desde **Mi perfil → Evidencias → Otras fuentes de evidencia** o el apartado de programación, según el perfil. Son opcionales. Solo consultan información pública y no verifican por sí mismos la autoría ni el dominio de una habilidad.

La guía detallada para comenzar las dos integraciones está en [ACTIVAR_YOUTUBE_MICROSOFT.md](ACTIVAR_YOUTUBE_MICROSOFT.md).

## 10. YouTube: preparado, desactivado por ahora

Cuando decidas activarlo:

1. Crea o elige tu proyecto de Google Cloud.
2. Habilita **YouTube Data API v3**.
3. Crea una clave y restríngela a esa API. No la copies al chat ni al frontend.
4. Configura en `.local/backend.env`:

```dotenv
YOUTUBE_LEARNING_ENABLED=true
YOUTUBE_API_KEY=tu_clave_privada
YOUTUBE_LEARNING_DAILY_REQUESTS=100
```

5. Reinicia el backend y recarga Administración → Catálogo educativo → Fuentes y conectores → YouTube.
6. Consulta una lista pública. Revisa la muestra de vídeos y redacta una ficha propia antes de incorporarla.

El límite local es por proceso y día UTC; consulta también la cuota real del proyecto de Google. No se descargan vídeos, no hay búsqueda masiva y no se atribuye una certificación a una lista. Por tu elección actual, el conector permanece desactivado hasta disponer del proyecto y la clave.

## 11. Microsoft Learn: acceso autorizado pendiente

1. Registra una aplicación en Microsoft Entra y verifica que tiene acceso autorizado a Learn Platform API.
2. Obtén el tenant, el identificador de aplicación y un secreto vigente.
3. Configura privadamente:

```dotenv
LEARN_ENABLED=true
LEARN_TENANT_ID=uuid_del_directorio
LEARN_CLIENT_ID=uuid_de_la_aplicacion
LEARN_CLIENT_SECRET=secreto_privado
```

4. Reinicia el backend. En Fuentes y conectores → Microsoft Learn, consulta módulos o rutas e importa una selección.
5. Revisa el mapeo de habilidades antes de publicar. Completar un plan local no verifica credenciales de Microsoft.

Este paso depende del acceso que Microsoft conceda a la aplicación. No crea ni requiere desplegar TalentSync en Azure. Conserva LEARN_ENABLED=false si no dispones de esa configuración.

## 12. Correo y acceso social opcionales

**Correo:** `scripts/local.py` mantiene el buzón local y fuerza apagados Resend y SMTP. Cambiar RESEND_ENABLED en el archivo no convierte las cuentas ficticias en destinatarios reales. Puedes ver el diseño sin enviar correos:

```powershell
backend/.venv/Scripts/python.exe scripts/resend_test.py --preview
```

La prueba aislada de Resend usa `.local/resend.env`, `onboarding@resend.dev` y un único destinatario autorizado. El script impide repetir un envío ya aceptado. No borres su registro para reenviar accidentalmente. No necesitas dominio para continuar revisando localmente; el envío general con dominio propio es una etapa distinta.

**Acceso social:** si quieres Google o GitHub, registra una aplicación OAuth en el proveedor y usa sus variables OAUTH_GOOGLE_CLIENT_ID/OAUTH_GOOGLE_CLIENT_SECRET u OAUTH_GITHUB_CLIENT_ID/OAUTH_GITHUB_CLIENT_SECRET en el archivo privado. Registra exactamente estos retornos para el origen local actual:

```text
http://127.0.0.1:5173/api/v1/auth/social/google/callback
http://127.0.0.1:5173/api/v1/auth/social/github/callback
```

Reinicia el backend. No es necesario activar acceso social para revisar las cuentas locales existentes.

## 13. Comprobar la instalación

```powershell
backend/.venv/Scripts/python.exe scripts/local.py doctor
backend/.venv/Scripts/python.exe scripts/local.py verify
```

Los informes agregados están en `.local/verification/`. La verificación usa bases temporales y no envía correos ni despliega la aplicación. Conserva los archivos privados de configuración fuera de Git.

## Revisión del diseño y acceso

En **Mi desarrollo**, el área de aprendizaje se elige con tarjetas e iconos; puedes cambiar entre tu perfil y otras áreas. En **Seguridad de cuenta**, usa la navegación lateral para Correo y acceso, Verificación en dos pasos y Dispositivos; el candidato también tiene Privacidad. Los dispositivos se organizan en sesiones activas/cerradas y páginas de seis. La verificación en dos pasos continúa pausada durante la revisión local.

Después de actualizar, recarga la página con Ctrl+F5 para cargar los estilos actuales.
