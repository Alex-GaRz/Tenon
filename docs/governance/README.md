# Governance — Políticas y Controles del Repositorio Tenon

Este directorio contiene las políticas formales de gobernanza, enforcement y control de cambios del proyecto Tenon.

---

## Mapa de Políticas y Gates

### Políticas de Control de Cambios

- **[RFC Amendment Policy](RFC_Amendment_Policy.md)** — Protocolo para modificar el RFC-00 constitucional vía RFC-00A_*
- **[Protected Paths Policy](Protected_Paths_Policy.md)** — Rutas protegidas (`/core`, `/contracts`) y condiciones para cambios
- **[Commit Policy](Commit_Policy.md)** — Convenciones de commits y obligación de referenciar RFCs
- **[Contracts Versioning Policy](Contracts_Versioning_Policy.md)** — Marco de versionado semántico y compatibilidad de contratos

### PR Gates y Enforcement

- **[PR Gate RFC-00](PR_Gate_RFC-00.md)** — Condiciones PASS/FAIL exactas para PRs (checklist ejecutable en CI)
- **[NoGoals Enforcement](NoGoals_Enforcement.md)** — Bloqueo de señales prohibidas (pagos/transferencias/ejecución contable)
- **[Review Checklist](Review_Checklist.md)** — Checklist institucional de revisión humana alineado a invariantes

### Configuración de CI/CD

- **[CI Status Checks](CI_Status_Checks.md)** — Lista de checks obligatorios que deben estar marcados como "required" en settings del repo
- **[Branch Protection Setup](BRANCH_PROTECTION_SETUP.md)** — Guía de configuración manual de branch protection en GitHub
- **[Labels Standard](Labels_Standard.md)** — Etiquetas estándar del repositorio para enforcement y tracking

### Estado y Registro

- **[RFC-00 STATUS](RFC-00_STATUS.md)** — Estado actual de implementación del RFC-00 (solo marca PASS cuando todos los gates existen)
- **[DECISIONS](DECISIONS.md)** — Registro de decisiones de gobernanza (ADR-lite) con fecha y motivo

---

## Propósito

Estas políticas convierten los **invariantes y threat model del RFC-00** en controles ejecutables y verificables.

El objetivo es:
- **Prevenir cambios no autorizados** a rutas críticas (`/core`, `/contracts`)
- **Asegurar trazabilidad institucional** de decisiones de diseño
- **Bloquear automáticamente** violaciones de no-goals e invariantes
- **Proveer evidencia auditable** de que el sistema cumple sus promesas constitucionales

---

## Enforcement Automático vs Manual

| Política | Enforcement |
|----------|-------------|
| Protected Paths | CI automático + CODEOWNERS |
| RFC Amendment | CI automático |
| NoGoals Tripwire | CI automático (detección temprana) |
| PR Template | CI automático |
| Review Checklist | Manual (humano) + CI reminder |
| Contracts Versioning | Documental (enforcement completo en RFC futuro) |
| CI Status Checks | Configuración repo (documentado) |
