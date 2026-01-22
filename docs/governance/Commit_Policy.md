# Commit Policy — Convenciones de Commits y Trazabilidad

**Versión:** 1.0  
**Fecha:** 2026-01-21  
**Estado:** Activo

---

## Propósito

Asegurar que todos los commits en el repositorio Tenon sean **trazables, auditables y explicables**, manteniendo coherencia con el RFC-00 que exige evidencia y trazabilidad total.

---

## Formato Obligatorio de Commits

Todos los commits **deben** seguir el formato:

```
<type>(<scope>): <subject>

[optional body]

[optional footer: RFC-XX, Refs #issue]
```

### Components

#### 1. Type (obligatorio)

| Type | Descripción | Ejemplo |
|------|-------------|---------|
| `feat` | Nueva funcionalidad | `feat(correlation): add causality chain builder` |
| `fix` | Corrección de bug | `fix(ingest): handle duplicate events correctly` |
| `refactor` | Cambio de código sin alterar comportamiento | `refactor(core): extract discrepancy detector` |
| `test` | Agregar/modificar tests | `test(append-only): add property-based tests` |
| `docs` | Documentación solamente | `docs(rfc): clarify determinism invariant` |
| `chore` | Cambios de tooling/config | `chore(ci): update workflow triggers` |
| `perf` | Mejora de performance sin cambio de comportamiento | `perf(normalization): optimize currency conversion` |

#### 2. Scope (opcional pero recomendado)

Indica qué parte del sistema se modifica:

- `core` — lógica de invariantes
- `contracts` — schemas/semántica canónica
- `adapters` — integraciones externas
- `governance` — políticas/documentación de control
- `ci` — workflows/validadores
- `rfc` — documentos de diseño

**Ejemplos:**
```
feat(core): implement append-only event store
fix(adapters): correct timestamp parsing in SAP adapter
docs(rfc): publish RFC-02 Ingest specification
```

#### 3. Subject (obligatorio)

- Imperativo, presente: "add", "fix", "update" (no "added", "fixes", "updating")
- Lowercase
- Sin punto final
- Máximo 72 caracteres

#### 4. Body (opcional)

- Explicar **por qué** se hace el cambio, no qué (el diff ya lo muestra)
- Separar con línea en blanco del subject
- Wrap a 72 caracteres

#### 5. Footer (obligatorio si aplica)

**Obligatorio cuando:**
- El commit modifica `/core/**` o `/contracts/**` → debe incluir `RFC-XX`
- El commit cierra un issue → debe incluir `Closes #123`
- El commit es parte de un PR → incluir `Refs #PR-num`

**Formato:**
```
RFC-04
Refs #234
Closes #123
```

---

## Reglas Específicas para Rutas Protegidas

### Commits que tocan `/core/**` o `/contracts/**`

**DEBEN incluir en el footer:**
```
RFC-XX
```

**Ejemplo completo:**
```
feat(core): add idempotency key validation

Implements RFC-10 Section 2.3 idempotency guardian.
Ensures duplicate events are detected and deduplicated
before entering the append-only store.

RFC-10
Refs #456
```

**Validation:** CI bloqueará commits a rutas protegidas sin referencia RFC.

### Commits de enmienda (RFC-00A_*)

Si el commit modifica `docs/rfcs/RFC-00_MANIFEST.md`:

**DEBE incluir:**
```
RFC-00A-001
```

Y el PR debe estar etiquetado `amendment`.

---

## Plantilla Local de Commit

Para facilitar el cumplimiento, usar plantilla local:

**Instalar:**
```bash
git config --local commit.template .gitmessage
```

**Contenido de `.gitmessage`:**
```
# <type>(<scope>): <subject> (max 72 chars)

# Body: Explain WHY (not what). Wrap at 72 chars.

# Footer (if applicable):
# RFC-XX
# Refs #issue
# Closes #issue
```

---

## Ejemplos Válidos

### Ejemplo 1: Feature en core
```
feat(core): implement Money state machine

Adds state transitions for money lifecycle tracking
as defined in RFC-05. Supports INITIATED, COMMITTED,
SETTLED, FAILED states with explicit event triggers.

RFC-05
Refs #789
```

### Ejemplo 2: Bugfix en adapter
```
fix(adapters): handle null merchant_id in Stripe events

Stripe webhook can send null merchant_id for certain
event types (refunds, disputes). Adapter now handles
this gracefully and maps to UNKNOWN_MERCHANT canonical ID.

Refs #234
```

### Ejemplo 3: Docs
```
docs(governance): clarify CODEOWNERS enforcement

Updates Protected_Paths_Policy.md to explain that
CODEOWNERS review is required even for "safe" refactors.
```

### Ejemplo 4: Refactor (safe)
```
refactor(core): extract correlation logic to separate module

Zero behavior change. Extracted CorrelationEngine from
monolithic normalizer.py to improve testability.
All existing tests pass.

RFC-04
Refs #567
```

---

## Ejemplos Inválidos ❌

### ❌ Sin type
```
add new feature
```

### ❌ Subject en pasado
```
feat(core): added idempotency check
```

### ❌ Cambio a /core sin RFC
```
fix(core): update normalization rules

(FAIL: falta RFC-XX en footer)
```

### ❌ Subject demasiado largo
```
feat(core): implement complete correlation engine with causality chain builder and discrepancy detector
```

---

## Enforcement

### Local (Best-Effort)

**Pre-commit hook** (`.githooks/pre-commit`) valida formato básico y presencia de RFC para rutas protegidas.

**Instalación:** Ver `scripts/hooks/install_hooks.md`

### CI (Obligatorio)

**Workflow:** `.github/workflows/rfc00-guardrails.yml`

**Validaciones:**
- Formato de commit messages (`scripts/rfc00/validate_commit_messages`)
- Presencia de RFC en commits a rutas protegidas
- Longitud de subject <= 72 chars
- Type válido

**FAIL si:** algún commit no cumple.

---

## Configuración Recomendada

### Git Hooks

```bash
# Install local hooks
cp .githooks/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit

# Set commit template
git config --local commit.template .gitmessage
```

### Editor Integration

**VSCode:**
```json
{
  "git.inputValidationLength": 72,
  "git.inputValidationSubjectLength": 72
}
```

---

## Excepciones

**Merge commits automáticos** (generados por GitHub) están exentos de validación.

**Commits de CI/bots** (ejemplo: auto-format, dependabot) deben seguir formato pero pueden omitir RFC si no tocan rutas protegidas.

---

## Última Actualización

**2026-01-21:** Política inicial de commits publicada con RFC-00.
