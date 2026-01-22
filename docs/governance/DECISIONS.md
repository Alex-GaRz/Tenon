# Governance Decisions — Registro de Decisiones

**Propósito:** Mantener registro auditable de decisiones de gobernanza, enmiendas y excepciones en el proyecto Tenon.

**Formato:** ADR-lite (Lightweight Architecture Decision Records) enfocado en governance.

---

## Template

```markdown
### Decision: [Título Breve]

- **Fecha:** YYYY-MM-DD
- **Tipo:** [Amendment / Exception / Policy Change / Emergency]
- **Decisión:** [Descripción en 1-2 líneas]
- **Contexto:** [Por qué fue necesario]
- **Aprobado por:** [@username1, @username2]
- **Artefactos:** [Links a PRs, RFCs, issues relevantes]
- **Impacto:** [Qué cambia en el sistema]
```

---

## Registro de Decisiones

### Decision: Publicación Inicial de RFC-00 y Políticas de Gobernanza

- **Fecha:** 2026-01-21
- **Tipo:** Initial Governance Setup
- **Decisión:** Publicar RFC-00 como constitución del sistema + conjunto inicial de políticas de enforcement
- **Contexto:** Necesidad de establecer invariantes, no-goals, y controles formales antes de comenzar desarrollo de features
- **Aprobado por:** [Pendiente: CODEOWNERS a asignar]
- **Artefactos:**
  - RFC-00: [docs/rfcs/RFC-00_MANIFEST.md](../rfcs/RFC-00_MANIFEST.md)
  - Políticas: [docs/governance/](.)
- **Impacto:** Todas las rutas críticas (`/core`, `/contracts`) quedan protegidas desde hoy

---

## RFC-00 Amendments

*(No amendments yet)*

---

## NoGoals Exceptions

*(No exceptions yet)*

---

## Emergency Fixes

*(No emergency fixes yet)*

---

## Protected Paths Changes

*(Registro se poblará cuando haya PRs aprobados que toquen `/core` o `/contracts`)*

---

## Policy Changes

*(Cambios a políticas de gobernanza se registrarán aquí)*

---

## Última Actualización

**2026-01-21:** Archivo de decisiones creado con RFC-00 governance setup.
