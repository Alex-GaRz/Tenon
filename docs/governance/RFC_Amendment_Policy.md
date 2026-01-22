# RFC Amendment Policy — Protocolo de Enmiendas Constitucionales

**Versión:** 1.0  
**Fecha:** 2026-01-21  
**Estado:** Activo

---

## Propósito

El **RFC-00 — MANIFEST** es el documento constitucional del sistema Tenon y define invariantes, no-goals, threat model y contratos institucionales que rigen todo el proyecto.

Por diseño, **RFC-00_MANIFEST.md es inmutable**. Cualquier cambio debe seguir un protocolo formal de enmienda para preservar la integridad institucional y trazabilidad histórica.

---

## Cuándo se Permite una Enmienda (RFC-00A_*)

Una enmienda al RFC-00 **solo es válida** si:

1. **Existe una justificación institucional crítica** que demuestre que:
   - Los invariantes actuales impiden una capacidad necesaria del sistema, O
   - Un no-goal debe ser relajado por requisitos de negocio verificables, O
   - El threat model debe expandirse para cubrir una amenaza nueva y crítica, O
   - Hay un error conceptual grave en el RFC-00 que invalida la coherencia del sistema.

2. **No es simplemente "conveniencia de implementación":**
   - Presión de deadline no justifica una enmienda.
   - Preferencias de arquitectura específica no justifican una enmienda.
   - "Más fácil si cambiamos X" no es justificación válida.

3. **El cambio es compatible con la promesa fundamental del sistema:**
   - Tenon sigue siendo un sistema de **verdad financiera operativa** (observación, correlación, evidencia).
   - Tenon **no se convierte en sistema de ejecución, pagos, o contabilidad oficial**.

---

## Proceso de Enmienda

### Paso 1: Crear RFC de Enmienda (RFC-00A_NNN)

- Numerar secuencialmente: RFC-00A_001, RFC-00A_002, etc.
- Ubicar en `docs/rfcs/RFC-00A_NNN.md`
- Incluir obligatoriamente:
  - **Justificación institucional:** qué problema crítico resuelve la enmienda
  - **Cambio propuesto:** qué texto/sección del RFC-00 se modifica, y cómo
  - **Impacto en invariantes/no-goals:** qué garantías cambian y por qué sigue siendo seguro
  - **Compatibilidad retroactiva:** cómo afecta a código/contratos ya existentes
  - **Evidencia de consenso:** aprobación de stakeholders institucionales (arquitectos/legal/producto según aplique)

### Paso 2: PR de Enmienda

- El PR debe:
  - Incluir el nuevo RFC-00A_NNN.md
  - **NO** modificar `docs/rfcs/RFC-00_MANIFEST.md` directamente (se actualiza después de aprobación)
  - Estar etiquetado con `amendment` y `rfc-required`
  - Pasar todos los gates de CI (excepto el bloqueo de inmutabilidad, que se excepciona solo para PRs etiquetados correctamente)

### Paso 3: Revisión Institucional

- **Requiere aprobación de CODEOWNERS** de `docs/rfcs/**`
- Revisión debe verificar:
  - Justificación institucional es válida
  - Cambio no viola la promesa fundamental del sistema
  - No existe alternativa que evite modificar RFC-00
- **Registro de decisión:** agregar entrada en `docs/governance/DECISIONS.md` documentando la aprobación

### Paso 4: Aplicar Enmienda

Una vez aprobado el RFC-00A_NNN:
1. Merge del PR con el RFC de enmienda
2. **Nuevo PR separado** que actualice `docs/rfcs/RFC-00_MANIFEST.md`:
   - Agregar sección `## Enmiendas` al final del RFC-00 listando todas las RFC-00A_* aplicadas
   - O actualizar el texto original con nota `(modificado por RFC-00A_NNN — [fecha])`
3. Este PR debe referenciar explícitamente el RFC-00A_NNN aprobado

---

## Enforcement Automático

**CI bloqueará automáticamente:**
- Cualquier PR que modifique `docs/rfcs/RFC-00_MANIFEST.md` **sin estar etiquetado como enmienda** (`amendment` label)
- Cualquier PR de enmienda que no incluya un RFC-00A_*.md válido

**Validation script:** `scripts/rfc00/validate_rfc_amendments`

---

## Ejemplos de Justificaciones Válidas vs Inválidas

### ✅ Válidas

- "RFC-00 prohíbe contabilidad oficial, pero necesitamos habilitar 'ledger sugerido' opcional para uso de auditoría interna. RFC-00A_001 propone relajar no-goal solo para modo read-only/sugerencias."
- "Threat model no cubre ataques de timing por clock skew distribuido. RFC-00A_002 expande threat model para incluir Byzantine clock failures."
- "Invariante de append-only impide soft-deletes necesarios por GDPR. RFC-00A_003 propone agregar 'tombstone append-only' como excepción controlada."

### ❌ Inválidas

- "Queremos agregar auto-posting porque el ERP lo necesita urgente" → viola no-goal sin justificación institucional
- "Determinismo es muy difícil de implementar" → conveniencia técnica, no crisis institucional
- "Mejor cambiar invariantes para usar librería X" → preferencia de implementación

---

## Registro de Enmiendas Aplicadas

Mantener lista actualizada en `docs/governance/DECISIONS.md`:

```markdown
### RFC-00 Amendments

- **RFC-00A_001** (2026-XX-XX): [Descripción breve del cambio]
  - Motivo: [1 línea]
  - Aprobado por: [stakeholders]
```

---

## Última Actualización

**2026-01-21:** Política inicial de enmiendas publicada con RFC-00.
