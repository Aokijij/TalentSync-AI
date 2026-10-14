# Radar laboral implementado

Disponible en **Mi desarrollo → Radar laboral**, con acceso desde la ayuda del perfil. Conserva el enlace `#que-aprender` y admite `#radar-laboral`. Los cálculos son locales, sin API de IA ni servicios de pago.

## Tres vistas

- **Habilidades:** demanda observada en ofertas activas de los últimos 90 días. Muestra conteos, periodo, fuentes, ofertas consultadas y recursos del catálogo. Con menos de cinco ofertas oculta porcentajes. Elimina duplicados por empresa, cargo y ciudad y demos identificables por fuente, título, empresa, descripción o dominio reservado.
- **Perfiles comparables:** participantes voluntarios del área, nivel declarado y ciudad seleccionados. Excluye la propia cuenta, correos no verificados, dominios reservados, duplicados, participaciones retiradas y elecciones de más de 180 días. Requiere 20 participantes elegibles; por debajo del umbral no devuelve tamaño exacto ni habilidades. Publica solo habilidades mencionadas por al menos cinco personas y ausentes en al menos otras cinco, con porcentajes redondeados a cinco puntos. No afirma dominio ni devuelve nombres, correos, CV o integrantes. Texto, sector y modalidad no crean subgrupos privados. Los datos autodeclarados no son una muestra representativa de toda la ciudad.
- **Salarios:** mínimos fijos brutos publicados en COP al mes, no remuneraciones pagadas. Requiere área, nivel, ciudad, unidades explícitas y al menos 20 empresas distintas dentro del mismo contrato, modalidad, jornada y horas semanales. Calcula primero la mediana por empresa y después mediana y percentiles 25–75 entre empresas. No infiere unidades ni horas ausentes. Muestra cobertura y explica la falta de muestra. La comparación privada con la aspiración se activa al confirmar que tiene las mismas unidades y condiciones; nunca la modifica automáticamente.

Los filtros se aplican al pulsar **Explorar mercado**. La clasificación de ofertas usa familias de cargos reconocibles y nivel explícitamente publicado. No clasifica candidatos por atributos protegidos. No promete «1.000 perfiles» ni sustituye una ciudad por otra.

## Participación y acciones

El panel de perfiles permite elegir área y nivel, confirmar datos reales y retirarse. Se guarda en preferencias privadas. Sin ciudad no se puede activar. Un correo pendiente puede guardar su elección, pero no cuenta hasta verificarlo. El consentimiento vigente se consulta en cada petición, sin caché privada que retrase una retirada.

**La conozco** exige confirmación antes de añadir una habilidad declarada y normaliza duplicados. **Ver formación** abre el catálogo filtrado, sin inventar gratuidad o duración. El radar no cambia automáticamente experiencia, formación, aspiración ni compatibilidad.

La publicación guiada indica salario bruto mensual COP y admite horas semanales opcionales. Las ofertas antiguas sin unidades o jornada completas quedan fuera de salarios hasta que la empresa revise los datos. No se rellenan masivamente condiciones desconocidas.

## Implementación y validación

API candidata autenticada: `GET /profiles/me/market`, `PUT /profiles/me/market/participation`, `POST /profiles/me/market/skills`. Consultas SQL de campos necesarios, sin embeddings de vacantes, CV de competidores ni ejecución de modelos. Respuestas privadas con `Cache-Control: no-store`. Sin proveedores externos ni tareas de refresco nuevas.

Pruebas de permisos, consentimiento/retirada, correo y dominios reservados, umbrales/supresión, grupos fijos, deduplicación/periodo, separación salarial, empresas independientes, unidades ausentes y habilidad explícita. Los datos ficticios para probar grupos suficientes viven solo en bases temporales de pruebas; no se cargan como mercado real.

El entorno local contiene demostraciones y puede mostrar **muestra insuficiente** hasta disponer de datos elegibles. Para crecimiento futuro: evaluar representatividad, abuso de múltiples cuentas y protección estadística más avanzada antes de ampliar filtros o afirmar precisión poblacional.
