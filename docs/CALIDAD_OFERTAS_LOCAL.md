# Consultor local de ofertas

La empresa accede desde **Calidad de ofertas** o **Mis vacantes → Publicar vacante**.
El creador tiene cinco pasos: condiciones, responsabilidades y misiones, requisitos,
proceso, y vista del candidato antes de publicar.

## Revisión

El panel se recalcula al editar, sin guardar ni publicar automáticamente. Son reglas
explicables que funcionan localmente y no realizan llamadas a servicios generativos.
Las sugerencias de redacción requieren que la empresa concrete la información.

La puntuación distribuye 100 puntos: condiciones 30, responsabilidades 25,
requisitos 20, proceso 15 y lenguaje 10. Una puntuación alta no sustituye los
requisitos obligatorios. Nivel A exige 90 puntos o más, requisitos completos y
ninguna contradicción crítica ni expresión genérica señalada.

Las ofertas guiadas pueden guardarse como borrador con campos pendientes. Para
publicarlas, el servidor exige salario positivo, contrato, jornada, ubicación,
responsabilidades concretas, misiones evaluables, experiencia y habilidades
priorizadas, entrevistas, duración estimada y respuesta por avance. La verificación
de empresa sigue siendo independiente. Las ofertas anteriores mantienen su flujo
de gestión hasta que se incorporan a la revisión guiada; no se retiran al consultar.
No se permite quitar las condiciones estructuradas para evadir la validación.

## Integraciones

- `salary` conserva el mínimo fijo mensual en COP; el máximo y los pagos variables
  se guardan por separado. Preferencias y filtros comparan el mínimo fijo.
- Las habilidades esenciales y sus pesos alimentan la compatibilidad existente.
  Las habilidades aprendibles se muestran como acompañamiento al ingreso.
- Misiones, evaluación y plazos aparecen en el detalle y en el seguimiento de la
  postulación, donde también pueden consultarlos los entrevistadores asignados.
- Las etapas del Kanban y los plazos de respuesta existentes se conservan. La
  duración total es una estimación independiente desde la postulación.
- Los cambios materiales incrementan una versión y notifican a las personas con
  procesos en curso. El evento guarda la versión, sin copiar contenido privado.
- La puntuación de calidad no modifica el índice de compatibilidad ni reordena
  automáticamente las recomendaciones.

## Opiniones y referencia salarial

El candidato puede indicar un motivo voluntario desde el detalle de una oferta
activa, cambiarlo o retirarlo. No requiere activar la personalización y no se
interpreta la navegación como una decisión. La empresa recibe cantidades y
orientaciones desde cinco respuestas de la versión actual, sin identidad ni texto
libre. Al cambiar la oferta comienza una muestra nueva; las opiniones anteriores
no se mezclan con las actuales. Eliminar una cuenta también elimina sus opiniones.

La referencia usa ofertas estructuradas de los últimos 180 días, comparando ciudad
o territorio, modalidad, sector, dedicación, contrato, nivel, experiencia y horario.
Agrupa por empresa y exige cinco empresas distintas. Excluye estos ejemplos.
Se presenta como muestra local, sin afirmar que representa el mercado ni inventar
probabilidades de contratación. No bloquea por una comparación salarial orientativa.

## Ejemplos y puesta en marcha

```powershell
backend/.venv/Scripts/python.exe scripts/local.py setup
backend/.venv/Scripts/python.exe scripts/local.py seed-quality
```

El segundo comando exige el entorno aislado `.local/talentsync.sqlite3` y los
escenarios previos. Añade tres ofertas a la empresa ficticia Horizonte Producto:
una incompleta, una clara y una con cinco opiniones simuladas. Es idempotente y
no restablece usuarios ni reemplaza vacantes. Los enlaces se guardan en
`.local/quality-offers.json`; los accesos continúan en la guía privada de escenarios.

La migración `0039_offer_quality` añade condiciones, versión y opiniones. Antes
de aplicarla a la revisión local se hizo una copia de SQLite en `.local/backups/`.
Este trabajo no publica cambios ni modifica recursos de Azure.
