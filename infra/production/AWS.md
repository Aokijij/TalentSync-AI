# AWS: despliegue de TalentSync durante un mes

Desplegado el 27 de octubre de 2026 (hora de Colombia). Sitio: **https://talentsync-ai.pages.dev**. API del mismo origen: `/api/v1`; disponibilidad: `/health/ready`.

## Estado comprobado

- Cuenta AWS en Free Plan activo, con 100 USD verificados antes de crear recursos. No se actualizó a pago ni se crearon claves AWS permanentes.
- Una instancia `m7i-flex.large`, Ohio (`us-east-2`): 2 vCPU, 8 GiB, Ubuntu 24.04 x86 y volumen gp3 cifrado de 40 GiB. Inventario e identificadores privados en `.local/aws-provisioning.json`.
- Servicio systemd con reinicio ante fallos; Nginx y HTTPS válido. El puerto 8000 solo escucha en loopback; SSH se limita a la IP de administración. El origen exige una clave privada del proxy de Pages.
- Neon en migración `0054_external_job_freshness`; copia verificada antes de la actualización. R2 privado responde desde AWS. No se migraron cuentas de demostración, vacantes ni postulaciones ficticias.
- Permiso Gmail de solo envío renovado y comprobado sin enviar otro mensaje de prueba. Trabajadores de correo, entrevistas y retención activos.
- 228 cursos editoriales de 18 proveedores publicados; modelos de comparación, OCR y extracción de entidades comprobados con datos sintéticos.
- Cookies Secure/HttpOnly, protección CSRF y cierre de sesión comprobados a través del dominio público. Registro sin aceptación legal rechazado. Retornos de Google, GitHub y Calendar guardados para el dominio público.
- El administrador debe configurar su autenticador en el primer acceso. El 29 de octubre se comprobó el acceso real con Google y Calendar con un evento privado temporal autorizado, retirado al terminar. GitHub OAuth queda pendiente por decisión del titular. La revisión de marca/permisos de Google sigue siendo independiente del despliegue. Estado completo en [INTEGRATIONS.md](INTEGRATIONS.md).
- Actualización del 29 de octubre: trabajador de vigencia de vacantes externas habilitado; Greenhouse y Lever consultados desde AWS sin nuevas claves ni importaciones de prueba. El OCR recuperó la formación de una página escaneada dentro de un PDF mixto sintético. Se conservó la versión anterior del código para recuperación; la comprobación local de salud usa un Host autorizado.

## Presupuesto y final del mes

Estimación conservadora para 744 horas: cómputo 71,25 USD, disco 3,20 USD, IPv4 3,72 USD y reserva de tráfico de 10 USD: **88,17 USD de crédito**. El tráfico real y los límites de los demás servicios pueden cambiar el consumo; no es alojamiento gratuito permanente. Conservar Free Plan y no activar Advanced features/Paid Plan.

Revisar saldo y continuidad **antes del 27 de noviembre de 2026**. No se ha creado una parada automática ni un recordatorio. Al retirar el servicio, exportar Neon y los archivos R2 necesarios; después terminar la instancia con eliminación del volumen raíz. Detener una VM conserva el disco y puede seguir consumiendo crédito. No eliminar Neon/R2 ni sus datos como parte de esa retirada sin revisar su conservación.

La IPv4 es efímera: un stop/start cambia potencialmente el nombre `sslip.io`, el certificado y `API_ORIGIN`. Reiniciar el sistema operativo conserva normalmente la dirección; antes de un stop/start planificar la actualización del origen. El despliegue tiene una sola VM y no promete alta disponibilidad.

## Publicación y mantenimiento

- `scripts/package-production-backend.py` empaqueta el código por lista permitida, sin `.env`, bases de datos, claves, CV ni modelos. Comprobar SHA256 antes de extraer una nueva versión bajo `/opt/talentsync/releases`, mantener la anterior para rollback y cambiar `/opt/talentsync/current` antes de reiniciar el servicio.
- Configuración privada: `/etc/talentsync/backend.env`, solo root; systemd la carga antes de ejecutar como `talentsync`. Mantener estable `SECRET_KEY`. No imprimir el archivo ni incorporarlo al paquete.
- Procesos separados: `/opt/talentsync/venv` para API/comparación; `/opt/talentsync/ocr-venv` para `requirements-ocr.txt`; `/opt/talentsync/cv-venv` para `requirements-cv-local.txt`. CPU PyTorch instalado desde el índice oficial. OCR mantiene Pillow compatible con Docling, separado de la versión de exportación de PDF.
- `CV_DOCLING_PYTHON` y `CV_ENTITY_PYTHON` deben apuntar a los ejecutables de sus entornos. No resolver sus enlaces simbólicos a `/usr/bin/python`, porque se perderían los paquetes aislados. Modelos descargados y verificados antes del arranque; inferencia offline, artefactos Docling bajo `/var/lib/talentsync/models/docling`.
- Comprobar `systemctl is-active talentsync`, reinicios, memoria y `/health/ready` después de cada cambio. API y trabajadores comparten una sola instancia. La renovación HTTPS está configurada por Certbot.
- `scripts/prepare-production-site.ps1` genera aplicación, HTML público/legal y `_worker.js`. `scripts/deploy-cloudflare.ps1` comprueba salud antes de publicar; `-AllowWorkingTree` permite publicar cambios revisados aún sin commit. Mantener `API_ORIGIN` y `API_PROXY_SECRET` como variables privadas de Pages, nunca como `VITE_*`.
- La copia de Neon anterior al despliegue está en `.local/backups`; no hay un sistema nuevo de copias externas programadas. Comprobar las opciones de recuperación de Neon y preparar una nueva copia antes de cada migración.

## Acceso administrativo a AWS

AWS CLI v2 oficial está extraído en `.tmp/aws-cli-v2`; firma de Amazon verificada. El perfil `talentsync` usa `aws login` con credenciales temporales fuera del repositorio. No exportar esas credenciales ni crear access keys permanentes para mantener el servidor: la aplicación no necesita IAM de EC2 para Neon, R2 o Gmail. La caducidad de la sesión CLI no detiene el backend.

`scripts/check-aws-free-plan.ps1` consulta el plan y el crédito sin crear recursos ni cambiar condiciones. Su umbral de 90 USD sirve para una nueva creación, no para autorizar despliegues duplicados cuando el servidor ya existe. Consultar inventario antes de cualquier provisión y reutilizar la instancia actual.

## Fuentes oficiales

- [Free Plan, elegibilidad y crédito](https://aws.amazon.com/free/free-tier-faqs/)
- [Comparación de los registros nuevo y avanzado](https://docs.aws.amazon.com/accounts/latest/reference/sign-up-for-aws.html)
- [Autenticación temporal de AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-sign-in.html)
- [Consulta de estado del plan y saldo](https://docs.aws.amazon.com/cli/latest/reference/freetier/get-account-plan-state.html)
