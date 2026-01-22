# RFC-00 Guardrails — Scripts de Validación

Este directorio contiene los scripts de validación que enfuerzan las políticas del RFC-00 en CI y localmente.

---

## Validadores Disponibles

| Script | Propósito | Uso |
|--------|-----------|-----|
| `validate_repo_policies.py` | Verifica que políticas y plantillas existan | CI + Local |
| `validate_protected_paths.py` | Valida cambios a `/core`, `/contracts`, RFC-00 | CI + Local |
| `validate_rfc_references.py` | Verifica referencias RFC en PRs/commits | CI |
| `validate_commit_messages.py` | Valida formato de commits | CI + Hook |
| `validate_nogoals.py` | Detecta señales de funcionalidad prohibida | CI + Local |

---

## Uso Local

### Validar todo antes de push:

```bash
# Validar políticas del repo
python scripts/rfc00/validate_repo_policies.py

# Validar cambios locales
python scripts/rfc00/validate_protected_paths.py --diff HEAD

# Validar commits
python scripts/rfc00/validate_commit_messages.py --commits HEAD~3..HEAD

# Validar no-goals
python scripts/rfc00/validate_nogoals.py --diff HEAD
```

### Validar un PR específico:

```bash
# Simular validación de PR antes de abrir
python scripts/rfc00/validate_protected_paths.py --diff main..feature-branch
python scripts/rfc00/validate_nogoals.py --diff main..feature-branch
```

---

## Uso en CI

Los workflows en `.github/workflows/` ejecutan estos scripts automáticamente en cada PR.

Ver: `docs/governance/CI_Status_Checks.md` para lista de checks obligatorios.

---

## Hooks Locales

Para ejecutar validaciones automáticamente antes de commit/push, instalar hooks:

```bash
# Ver instrucciones de instalación
cat scripts/hooks/install_hooks.md
```

---

## Dependencias

**Python 3.8+** requerido.

**Librerías (si se usan):**
- `gitpython` (opcional, para parsing de diffs avanzado)
- `pyyaml` (para parsing de configs)

**Instalar dependencias:**
```bash
pip install -r scripts/rfc00/requirements.txt
```

---

## Exit Codes

Todos los scripts usan exit codes estándar:

- `0` — PASS (sin violaciones)
- `1` — FAIL (violaciones detectadas)
- `2` — ERROR (script failure, bad args, etc.)

---

## Testing de Validadores

Para probar que los validadores funcionan:

```bash
# Crear branch de test
git checkout -b test-validators

# Hacer cambio que viola reglas (ej: modificar /core sin RFC)
echo "# test" >> core/test.py
git add core/test.py
git commit -m "test: violate protected paths"

# Ejecutar validador (debe FAIL)
python scripts/rfc00/validate_protected_paths.py --diff HEAD~1..HEAD
# Esperado: Exit code 1, mensaje de error

# Limpiar
git reset --hard HEAD~1
git checkout main
git branch -D test-validators
```

---

## Logs y Debugging

Los scripts escriben a stderr para errores y stdout para resultados.

**Modo verbose:**
```bash
python scripts/rfc00/validate_protected_paths.py --diff HEAD --verbose
```

---

## Última Actualización

**2026-01-21:** Scripts de validación creados para RFC-00 enforcement.
