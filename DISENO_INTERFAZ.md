# Criterios compartidos de interfaz

Alcance de esta revisión: diseño y usabilidad de las funciones existentes de candidato, empresa y administración. La landing, nuevas bienvenidas y preparación de producción se trabajan después.

## Componentes y jerarquía

- Los colores de cada rol se conservan. Los controles usan `--accent`, `--on-accent`, `--error`, `--on-danger` y `--control-border`; no se fija texto blanco sobre un acento claro del tema oscuro.
- `design-system.css` define geometría, navegación, ayudas y estados compartidos. `index.css` contiene las paletas y los controles base. Los estilos de página organizan sus componentes y evitan duplicar esas reglas.
- `surface-card`, `elevated-card` y `ui-panel` comparten el radio estándar de 16 px. Los bloques de presentación pueden utilizar un contorno mayor; las etiquetas e indicadores no son tarjetas.
- La altura normal de botones y campos es 44 px. Los botones compactos usan `button-sm`, de 40 px. Los iconos no se encogen cuando el texto ocupa varias líneas.
- `PageHeader` mantiene título, descripción y acciones; `WorkspaceTabs` proporciona navegación con flechas, Inicio y Fin. La navegación de secciones usa el mismo tratamiento de selección en los tres roles.
- Los contenedores de página usan separación explícita y permiten encoger columnas. Una tabla ancha conserva su región de desplazamiento; no se oculta un desbordamiento del documento para simular que está corregido.

## Formularios y contenido

- Cada campo tiene una etiqueta visible. El placeholder explica brevemente qué escribir; no incluye personas, empresas, enlaces, salarios o respuestas ficticias.
- Las restricciones y formatos importantes permanecen como ayuda visible. El placeholder desaparece durante la edición y no sustituye esa explicación.
- Los errores se relacionan mediante `aria-invalid` y `aria-describedby`. En perfil, la ayuda y el error pueden mostrarse juntos. El nombre accesible del control no incorpora el mensaje de error.
- Solo lectura y deshabilitado son estados diferentes. Un campo guardado de solo lectura continúa siendo legible y seleccionable.
- La información sobre una notificación al candidato describe el efecto real de confirmar la acción; elegir una etapa no se presenta como un guardado.

## Confirmaciones y avisos

- Una confirmación abre con el foco en Cancelar, explica su efecto y conserva el texto específico de su acción.
- `ConfirmModal` espera las promesas devueltas por `onConfirm`, bloquea envíos repetidos y cierre mientras se procesa, y permite reintentar tras un error. La pantalla llamadora decide cuándo cerrar después de guardar.
- El componente llamador debe devolver la promesa de su operación. No debe lanzar una petición sin devolverla si espera que el diálogo controle el estado pendiente.
- Los avisos de error no desaparecen automáticamente. Los controles para cerrarlos tienen un área de 40 px y el conjunto de avisos respeta el alto de la pantalla.

## Móvil, teclado y temas

- Se revisan ambos temas y los tres roles. Las pruebas comprueban contraste de texto de botones y placeholders, límites de campos, teclado y ampliación del texto al 200 %; no representan una certificación completa de accesibilidad.
- En móvil, los campos conservan un tamaño de texto legible; las acciones se redistribuyen sin perder su orden ni recurrir a desplazamientos internos innecesarios.
- El menú móvil usa un diálogo modal, mantiene el foco dentro, permite salir con Escape, devuelve el foco al abrir/cerrar y restaura el desplazamiento. Si la pantalla pasa al ancho de escritorio, el menú se cierra.
- El enlace Saltar al contenido permite evitar la navegación repetida. El foco usa el color del rol y se conserva la preferencia de movimiento reducido.

## Validación

`npm run lint`, `npm test` y `npm run build` comprueban código y compilación. `npm run quality:ui` revisa recorridos con datos sintéticos. `design-closure.spec.js` monta el layout y controles reales para comprobar foco, contraste, ampliación y recuperación de confirmaciones fallidas.

Las referencias de imagen se actualizan únicamente después de revisar el cambio intencionado, siguiendo `frontend/quality/README.md`. No se toman datos personales para las capturas versionadas.
