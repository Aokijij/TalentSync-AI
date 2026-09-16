# Changelog

All notable changes to the "TalentSync AI" project will be documented in this file.

## [Unreleased] - 2026-09-15

### Changed
- Simplified candidate tracking with explicit confirmation of movements and notifications.
- Added deliberate vacancy closure and reopening with preserved history or a new process.
- Unified company/candidate compatibility, with separate language requirements and levels.
- Improved talent search, mobile recommendations, company identity, and resume styles/colors.
- Replaced native language suggestions with searchable, themed, keyboard-accessible controls.
- Show uploaded candidate photos in the company's candidate profile view.

### Production
- Persist profile photos, company logos and covers in private Azure Blob Storage when configured.
- Serialize PostgreSQL migrations across simultaneous container replicas.
- Update vulnerable frontend, API, multipart, PDF and JWT dependencies.
- Exclude local credentials, uploads and test caches from Git and Docker build contexts.
- Add CI checks and a versioned, confirmation-gated update script for existing Azure resources.
- Prepare Cloudflare Pages publication with an absolute Azure API URL and explicit CORS origin.

## [Unreleased] - 2026-09-07

### Changed
- Separated HTTP routes, application use cases, repository contracts, and SQLAlchemy adapters.
- Moved matching rules and skill normalization into domain services.
- Organized React contexts, hooks, and theme controls; shared recommendation selection across screens.
- Removed unused modules, imports, auxiliary directories, and temporary renders.
- Consolidated production, lightweight, and test dependency manifests.
- Added standalone setup instructions and environment templates.
- Removed unused container configuration and preloaded account utilities.
- Added interactive administrator provisioning and verified fresh database migrations.
- Added API regression, matching, frontend selection, and architecture boundary tests.

## [2026-09-02]

### Added
- Updated global CSS (`frontend/src/styles/index.css`) with refined design tokens, semantic colors, base layers, and dark mode preparation.
- Created reusable `Button.jsx` component with variants (primary, secondary, outline, ghost), sizes, loading/disabled states.
- Created accessible `Input.jsx` component with focus, error, disabled states, ready for React Hook Form integration.

### Changed
- Refactored existing Tailwind base configuration to follow a design-token approach with CSS variables.
- Enhanced component styling consistency and accessibility foundations.
- Fixed dark mode CSS by replacing invalid Tailwind arbitrary value syntax with proper HSL/CSS variable usage to resolve PostCSS build error.

### Fixed
- Authentication connection issue: Frontend was attempting to connect to port 8002 while backend runs on port 8000
- Created `.env` file in frontend with correct `VITE_API_URL=http://localhost:8000/api/v1`
- Resolved `net::ERR_CONNECTION_REFUSED` error when attempting to login
- PostCSS build error: `border-error` class not defined - replaced with proper CSS variable usage
- PostCSS build error: `bg-success/10` etc. arbitrary value syntax - replaced with proper HSL/CSS variable usage

### Refactored (Today)
- **`frontend/src/styles/index.css`**: Completely refactored to implement a sophisticated design system with shared design tokens:
  - Introduced semantic CSS variables for colors, shadows, and typography
  - Enhanced utility classes with hover-lift, pressed states, focus rings, and balanced text wrapping
  - Redefined component base styles (buttons, inputs, cards) using Tailwind's @layer components
  - Implemented advanced microinteractions: hover lifts, pressed states, focus rings, and smooth transitions
  - Improved visual hierarchy with elevated cards, better contrast, and thoughtful spacing
  - Prepared dark mode support with proper CSS variable fallback
  - Fixed all PostCSS build errors by using valid CSS syntax
- **`frontend/src/components/Button.jsx`**: Refactored to use semantic CSS classes from index.css, removing hardcoded styles and leveraging the design system
- **`frontend/src/components/Input.jsx`**: Refactored to use semantic CSS classes from index.css, improving maintainability and design consistency
- **`frontend/src/components/CompatibilityBar.jsx`**: Updated to use the new design tokens and visual language
- **`frontend/src/components/MetricCard.jsx`**: Updated to align with the new card styles and elevation

## Nuevo Concepto Visual Implementado

El proyecto TalentSync AI ahora cuenta con un sistema de diseño refinado basado en componentes y variables de diseño compartidos:

### Paleta de Colores y Tokens
- **Neutrales cálidos** (`--canvas: #f4f3ef`, `--surface: #ffffff`) para reducir fatiga visual
- **Texto jerarquizado**: `--ink: #101828` (primario), `--muted: #475467` (secundario)
- **Acentos con propósito**: `--navy: #0b1220` (confianza profesional), `--accent: #1d4ed8` (interactividad)
- **Colores semánticos** para estados (éxito, advertencia, error) con ratios de contraste accesibles

### Tipografía Estratégica
- **Cuerpo**: IBM Plex Sans - optimizada para interfaces digitales, excelente legibilidad en tamaños pequeños
- **Encabezados**: Source Serif 4 - aporta autoridad y calidez, crea contraste táctil sin romper armonía

### Microinteracciones y Jerarquía
- **Hover Lift**: Elementos se elevan sutilmente al interactuar (-0.5px en Y)
- **States Presionados**: Escala ligeramente al hacer clic (0.97x) para feedback táctil
- **Focus Rings**: Anillos de enfoque visibles y accesibles siguiendo WCAG
- **Transiciones Suaves**: Todas las propiedades cambian con cubic-bezier(0.4, 0, 0.2, 1) y 150ms
- **Espaciado Consciente**: Sistema de espacio basado en 4px (Tailwind's spacing scale) aplicado de forma consistente

### Componentes Refactorizados
- **Botones**: 4 variantes (primary, secondary, outline, ghost) con 3 tamaños, estados de loading y disabled
- **Inputs**: Listos para React Hook Form con estados de foco, error y disabled
- **Tarjetas**: Elevación suave, bordes definidos, hover states para indicar interactividad
- **CompatibilityBar y MetricCard**: Actualizados para usar el lenguaje visual unificado
- **CandidateDashboard.jsx**: Completamente refactorizado para usar el nuevo sistema de diseño, reemplazando todos los componentes legacy con Button y Input componentes del sistema de diseño

## ✅ Estado Actual
Todos los errores de PostCSS han sido resueltos y el sistema de diseño está listo para usar. El frontend debería compilar correctamente y las nuevas variables de entorno deberían resolver el problema de conexión al backend.

