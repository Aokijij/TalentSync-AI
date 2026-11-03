# Documentos aceptados al registrar una cuenta

`current.json` identifica las versiones vigentes y las dos declaraciones mostradas
al usuario. Lo consumen React y el servidor; las casillas empiezan desmarcadas.
Los documentos completos se publican en `/privacidad` y `/terminos`.
La fecha específica `privacy_effective_date` permite actualizar privacidad sin
cambiar la fecha ni la versión de los términos. `archive/` conserva el contenido
público de versiones anteriores; no contiene autorizaciones ni datos de cuentas.

El servidor exige booleanos explícitos y versiones exactas. Guarda en
`users.legal_acceptance` la fecha UTC del servidor, versiones, canal, declaraciones
y SHA-256 de esas declaraciones. No acepta evidencia aportada por el navegador.
El hash identifica las declaraciones, no el texto completo de las páginas.
La exportación de datos incluye esta evidencia. Los consentimientos para Calendar,
proveedores o publicidad no se incorporan a estas casillas.

La migración `0053_registration_consent` añade el campo sin fabricar autorizaciones
para cuentas anteriores. El registro social pendiente no puede completarse sin
las mismas dos decisiones; la autorización de Google/GitHub no las sustituye.

Al modificar sustancialmente la política o los términos, conservar la versión
anterior en el historial del repositorio, actualizar el identificador correspondiente
y desplegar frontend y backend coordinadamente. Un formulario antiguo recibirá
422 para que se revisen los documentos vigentes. Este cambio exige aceptación
en registros nuevos; no implementa una campaña de renovación para usuarios antiguos.
