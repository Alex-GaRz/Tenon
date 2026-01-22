# CI Status Checks — Lista de Checks Obligatorios

**Versión:** 1.0  
**Fecha:** 2026-01-21  
**Estado:** Activo

---

## Propósito

Definir la **lista exacta de CI status checks** que deben estar marcados como **"required"** en la configuración del repositorio GitHub para asegurar que ningún PR puede hacer merge sin pasar los gates de RFC-00.

---

## Status Checks Obligatorios

Estos checks deben estar configurados como **"Require status checks to pass before merging"** en:

**GitHub Settings → Branches → Branch protection rules → `main`**

---

### 1. RFC-00 Guardrails

**Workflow:** `.github/workflows/rfc00-guardrails.yml`  
**Job names:**
- `validate-pr-template`
- `validate-commit-messages`
- `validate-repo-policies`

**Qué valida:**
- PR template está completo
- Commits siguen [`Commit_Policy.md`](Commit_Policy.md)
- Políticas y plantillas del repo existen y son válidas

**Status check names (en GitHub):**
```
RFC-00 Guardrails / validate-pr-template
RFC-00 Guardrails / validate-commit-messages
RFC-00 Guardrails / validate-repo-policies
```

---

### 2. Protected Paths

**Workflow:** `.github/workflows/protected-paths.yml`  
**Job names:**
- `validate-protected-paths`
- `validate-rfc-references`

**Qué valida:**
- Cambios a `/core/**`, `/contracts/**`, `docs/rfcs/RFC-00_MANIFEST.md` cumplen protocolo
- PRs que tocan rutas protegidas incluyen referencia RFC válida
- Enmiendas al RFC-00 siguen [`RFC_Amendment_Policy.md`](RFC_Amendment_Policy.md)

**Status check names (en GitHub):**
```
Protected Paths / validate-protected-paths
Protected Paths / validate-rfc-references
```

---

### 3. NoGoals Enforcement (Opcional en ITERACIÓN 1)

**Workflow:** `.github/workflows/nogoals-tripwire.yml` (cuando se implemente en ITERACIÓN 4)  
**Job name:**
- `validate-nogoals`

**Qué valida:**
- No hay señales de ejecución de pagos/contabilidad oficial en `/core`
- Keywords prohibidos no aparecen en rutas críticas

**Status check name (en GitHub):**
```
NoGoals Tripwire / validate-nogoals
```

---

### 4. Tests (cuando existan)

**Workflow:** `.github/workflows/tests.yml` (futuro)  
**Job names:**
- `unit-tests`
- `property-tests` (si aplica)
- `integration-tests` (si aplica)

**Status check names (en GitHub):**
```
Tests / unit-tests
Tests / property-tests
Tests / integration-tests
```

---

### 5. Linters y Formatters (futuro)

**Workflow:** `.github/workflows/lint.yml` (cuando se configure)  
**Job names:**
- `python-lint` (o equivalente)
- `format-check`

**Status check names (en GitHub):**
```
Lint / python-lint
Lint / format-check
```

---

## Configuración en GitHub Settings

### Paso a Paso

1. **Ir a:** `Settings → Branches → Branch protection rules`
2. **Crear/editar regla para `main`:**
   - ✅ **Require a pull request before merging**
     - ✅ Require approvals: **1** (mínimo)
     - ✅ Dismiss stale pull request approvals when new commits are pushed
     - ✅ Require review from Code Owners
   - ✅ **Require status checks to pass before merging**
     - ✅ Require branches to be up to date before merging
     - **Add status checks:**
       - `RFC-00 Guardrails / validate-pr-template`
       - `RFC-00 Guardrails / validate-commit-messages`
       - `RFC-00 Guardrails / validate-repo-policies`
       - `Protected Paths / validate-protected-paths`
       - `Protected Paths / validate-rfc-references`
       - (Agregar `Tests / *` y `Lint / *` cuando existan)
   - ✅ **Require conversation resolution before merging**
   - ⚠️ **Do not allow bypassing the above settings** (recomendado)
   - ✅ **Restrict who can push to matching branches** (opcional: solo maintainers)

3. **Guardar cambios**

---

## Validación de Configuración

**Script:** `scripts/rfc00/validate_repo_settings.py` (futuro)

**Uso:**
```bash
python scripts/rfc00/validate_repo_settings.py
```

**Output esperado:**
```
✅ Branch protection enabled for 'main'
✅ Required status checks configured:
   - RFC-00 Guardrails / validate-pr-template
   - RFC-00 Guardrails / validate-commit-messages
   - RFC-00 Guardrails / validate-repo-policies
   - Protected Paths / validate-protected-paths
   - Protected Paths / validate-rfc-references
✅ CODEOWNERS review required
✅ All CI Status Checks configured correctly
```

```
❌ FAIL: Missing required status checks:
   - Protected Paths / validate-rfc-references
   
Recommendation: Add missing checks in Settings → Branches → Branch protection rules
```

---

## Excepciones y Emergencias

**Admins del repo** pueden tener permisos de bypass para emergencias (outage, security fix crítico).

**Requisitos si se bypasea:**
1. Documentar en `docs/governance/DECISIONS.md`
2. Crear "follow-up PR" dentro de 48h con protocolo completo
3. Notificar a CODEOWNERS

---

## Estado Actual (RFC-00 Implementation)

| Status Check | Estado | ITERACIÓN |
|--------------|--------|-----------|
| `RFC-00 Guardrails / validate-pr-template` | Pendiente | 4 |
| `RFC-00 Guardrails / validate-commit-messages` | Pendiente | 4 |
| `RFC-00 Guardrails / validate-repo-policies` | Pendiente | 4 |
| `Protected Paths / validate-protected-paths` | Pendiente | 4 |
| `Protected Paths / validate-rfc-references` | Pendiente | 4 |
| `NoGoals Tripwire / validate-nogoals` | Pendiente | 4 |

**Nota:** Workflows se crean en ITERACIÓN 4. Este documento define el **estándar** que deben cumplir.

---

## Última Actualización

**2026-01-21:** Definición inicial de CI Status Checks publicada con RFC-00.
