def integration_readiness(*, neural_active, local_mail, smtp, providers, catalog, resend=False, learn=False, github_projects=False):
    """Report only explicit capabilities; configuration is not proof of delivery."""
    rows = [
        {"name": "Modelo de compatibilidad local", "state": "local_ready" if neural_active else "local_fallback", "status": "Modelo neuronal activo en esta máquina." if neural_active else "Compatibilidad léxica disponible; el modelo neuronal no está activo.", "next_steps": "Revisar afinidad y brechas con los escenarios de candidato."},
        {"name": "Correo y avisos", "state": "local_ready" if local_mail else "configured" if smtp else "disabled", "status": "Bandeja de desarrollo local; no entrega correo externo." if local_mail else "SMTP configurado; entrega externa pendiente de comprobar." if smtp else "Correo desactivado.", "next_steps": "Revisar invitaciones y recuperación en la bandeja local." if local_mail else "Configurar un transporte y comprobar la entrega con una cuenta autorizada."},
        {"name": "Acceso social", "state": "configured" if any(providers.get(key) for key in ("google", "github", "linkedin")) else "provider_required", "status": "Proveedores habilitados: " + (", ".join(key for key in ("google", "github", "linkedin") if providers.get(key)) or "ninguno") + ". Configuración comprobada, sin iniciar sesiones externas.", "next_steps": "Registrar una aplicación del proveedor, configurar el retorno y comprobar el acceso con cuentas autorizadas."},
        {"name": "SSO administrativo", "state": "configured" if any(providers.get(key) for key in ("workspace", "entra")) else "provider_required", "status": "Proveedores habilitados: " + (", ".join(key for key in ("workspace", "entra") if providers.get(key)) or "ninguno") + ".", "next_steps": "Configurar la organización y aprovisionar las identidades administrativas antes de exigir SSO."},
        {"name": "Vacantes externas", "state": "configured" if catalog else "local_manual", "status": "Adaptador de catálogo configurado; no se realizó sincronización externa en esta comprobación." if catalog else "Importación manual CSV/Excel disponible. Sin proveedor externo configurado.", "next_steps": "Probar los archivos de ejemplo desde administración o conectar una fuente autorizada."},
        {"name": "Cursos y certificados", "state": "local_manual", "status": "Catálogo, planes y registro de certificados por enlace disponibles. La autenticidad no se verifica automáticamente.", "next_steps": "Completar un plan y registrar un certificado aportado; para sincronizar se necesita acceso del proveedor.", "action_url": "/admin/aprendizaje", "action_label": "Revisar catálogo"},
        {"name": "Verificación empresarial", "state": "local_manual", "status": "Solicitud y revisión manual con soportes disponibles. Sin consulta a registros oficiales.", "next_steps": "Revisar la solicitud y sus soportes. La comprobación automática requiere un registro autorizado.", "action_url": "/admin/verificaciones", "action_label": "Revisar organizaciones"},
        {"name": "Referencia salarial", "state": "local_manual", "status": "Comparación de ofertas locales con muestra mínima de cinco empresas. Sin datos del mercado externo.", "next_steps": "Revisar las condiciones comparadas; una fuente externa requiere cobertura y permisos de uso."},
        {"name": "Calidad y redacción de ofertas", "state": "local_ready", "status": "Puntuación, misiones, borradores editables y orden por calidad disponibles sin servicios de pago.", "next_steps": "Probar las ofertas de demostración desde una cuenta de empresa."},
        {"name": "Evaluaciones prácticas", "state": "local_ready", "status": "Retos guiados y SQL restringido disponibles. No se ejecuta código arbitrario de otros lenguajes.", "next_steps": "Recorrer los escenarios de aprendizaje y comprobar resultados y evidencias."},
    ]
    if resend:
        rows[1].update(state="configured", status="Resend configurado; entrega externa pendiente de comprobar con un dominio verificado.")
    rows.extend([
        {"name": "Microsoft Learn", "state": "configured" if learn else "provider_required",
         "status": "Conector autenticado configurado; consulta manual con vista previa." if learn else "Conector preparado. Falta registrar una aplicación de Microsoft Entra y configurar sus credenciales.",
         "next_steps": "Consultar módulos o rutas, importar borradores y revisar habilidades antes de publicar. El catálogo no verifica certificados personales.",
         "action_url": "/admin/aprendizaje", "action_label": "Importar formación"},
        {"name": "Proyectos públicos de GitHub", "state": "configured" if github_projects else "disabled",
         "status": "Consulta pública disponible por solicitud del candidato, con caché y presupuesto de peticiones." if github_projects else "Lector preparado, pendiente de habilitar. No requiere credenciales para repositorios públicos.",
         "next_steps": "El candidato elige un repositorio desde su perfil. Los archivos aportan indicios técnicos; no prueban autoría ni dominio profesional."},
    ])
    return rows
