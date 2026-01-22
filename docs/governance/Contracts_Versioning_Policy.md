# Contracts Versioning Policy — Marco de Versionado Semántico

**Versión:** 1.0  
**Fecha:** 2026-01-21  
**Estado:** Activo (enforcement completo pendiente de RFC de change-control)

---

## Propósito

Definir el marco de versionado semántico y compatibilidad para contratos canónicos (`/contracts`) para asegurar que cambios no invaliden reproducibilidad histórica ni rompan adapters existentes silenciosamente.

**Nota:** Esta política define el estándar institucional. El enforcement técnico completo (suite de conformidad, validadores automáticos) se implementará en un RFC futuro de control de cambios.

---

## Principio Fundamental

Los contratos canónicos definen la **semántica de eventos, entidades y relaciones** que Tenon entiende.

**Cambiar un contrato puede:**
- Invalidar reproducibilidad de evidencia histórica
- Romper adapters que dependen de la semántica anterior
- Generar discrepancias artificiales por incompatibilidad de versiones

**Por lo tanto:** todo cambio a `/contracts/**` debe versionarse, documentarse y validarse.

---

## Esquema de Versionado Semántico

Usar **SemVer** (MAJOR.MINOR.PATCH) para contratos:

```
v1.2.3
│ │ └─ PATCH: correcciones, clarificaciones de docs, no afectan semántica
│ └─── MINOR: adiciones compatibles (nuevos campos opcionales, nuevos eventos)
└───── MAJOR: cambios incompatibles (campos requeridos eliminados, semántica modificada)
```

### Ejemplos

| Cambio | Versión | Tipo |
|--------|---------|------|
| Agregar campo opcional `merchant_id?` a evento `Payment` | v1.1.0 | MINOR |
| Cambiar `amount` de required a optional | v2.0.0 | MAJOR |
| Corregir typo en documentación de campo | v1.0.1 | PATCH |
| Agregar nuevo evento `Refund` | v1.2.0 | MINOR |
| Eliminar evento `Transfer` | v2.0.0 | MAJOR |
| Cambiar semántica de `status` (ej: renombrar `PENDING` → `INITIATED`) | v2.0.0 | MAJOR |

---

## Compatibilidad y Breaking Changes

### Cambios Compatibles (MINOR/PATCH)

**Permitidos sin romper reproducibilidad:**
- Agregar nuevos campos **opcionales**
- Agregar nuevos eventos o entidades
- Agregar valores a enums (si los consumers ya manejan unknown values)
- Clarificar documentación sin cambiar semántica

**Requisitos:**
- Adapters existentes deben seguir funcionando sin modificación
- Evidencia histórica debe seguir siendo interpretable

### Cambios Incompatibles (MAJOR — Breaking)

**Requieren versión MAJOR nueva:**
- Eliminar campos requeridos
- Cambiar tipos de datos (string → int)
- Cambiar semántica de campos existentes
- Renombrar eventos/entidades
- Eliminar valores de enums
- Cambiar reglas de validación que rechazan datos antes válidos

**Requisitos:**
- **RFC obligatorio** que documente:
  - Motivo del breaking change
  - Plan de migración para adapters
  - Estrategia de compatibilidad histórica (ej: mantener v1 y v2 en paralelo)
- **Pruebas de conformidad:** demostrar que adapters migrados pasan suite de tests
- **Deprecation period:** si es posible, mantener v1 activa durante período de transición

---

## Proceso de Cambio de Contratos

### 1. Cambio Compatible (MINOR/PATCH)

```markdown
1. Proponer cambio en PR
2. Incrementar versión en metadata del contrato
3. Actualizar changelog del contrato
4. Validar que adapters existentes pasan tests (sin modificación)
5. PR review por CODEOWNERS de /contracts
6. Merge
```

### 2. Breaking Change (MAJOR)

```markdown
1. Crear RFC documentando:
   - Motivo del breaking change
   - Plan de migración
   - Impacto en reproducibilidad
2. Incrementar versión MAJOR en nueva carpeta (ej: /contracts/v2/)
3. Mantener v1 activa (deprecated)
4. Actualizar adapters para soportar v2
5. Crear tests de conformidad v1 → v2
6. PR con aprobación de CODEOWNERS + stakeholders institucionales
7. Merge con docs de migración
8. Comunicar deprecation timeline para v1
```

---

## Estructura de Versionado en `/contracts`

**Propuesta de estructura (a implementar en RFC futuro):**

```
/contracts
  /canonical
    /v1
      /events
        Payment.schema.json
        Refund.schema.json
      /entities
        Money.schema.json
      metadata.json  # version: "1.2.3"
    /v2  # solo existe si hay breaking change
      /events
        ...
      metadata.json  # version: "2.0.0"
  /versioning
    CHANGELOG.md
    MIGRATION_v1_to_v2.md
```

**Metadata example:**
```json
{
  "version": "1.2.3",
  "released": "2026-01-15",
  "status": "active",
  "compatibility": "backward-compatible with v1.2.x"
}
```

---

## Changelog de Contratos

Mantener `CHANGELOG.md` en `/contracts/canonical/`:

```markdown
# Canonical Contracts Changelog

## v1.2.3 (2026-01-21)
- PATCH: Corregir docs de campo `currency` en Money entity

## v1.2.0 (2026-01-15)
- MINOR: Agregar evento `Refund`
- MINOR: Agregar campo opcional `merchant_category_code` a Payment

## v1.1.0 (2026-01-10)
- MINOR: Agregar campo opcional `merchant_id` a Payment

## v1.0.0 (2026-01-01)
- MAJOR: Release inicial de contratos canónicos
```

---

## Enforcement (Estado Actual)

### Actual (RFC-00):
- ✅ Cambios a `/contracts/**` requieren PR con protocolo (Protected Paths Policy)
- ✅ PR debe incluir referencia RFC
- ✅ CODEOWNERS debe aprobar

### Futuro (RFC de change-control):
- Validador automático de breaking changes (schema diff)
- Suite de conformidad que verifica compatibilidad
- Enforcement de deprecation periods
- Validación de metadata de versión

---

## Compatibilidad con Evidencia Histórica

**Regla crítica:** Tenon debe poder **reproducir evidencia histórica** incluso después de breaking changes.

**Estrategias:**
1. **Mantener versiones antiguas:** contratos v1 siguen disponibles para replay histórico
2. **Transformadores de versión:** adapters pueden traducir v1 → v2 si es necesario
3. **Metadata de versión en eventos:** cada evento ingestado guarda qué versión de contrato usó

**Enforcement:** al implementar breaking change, debe existir test que demuestre que eventos históricos (v1) siguen siendo reproducibles.

---

## Última Actualización

**2026-01-21:** Política inicial de versionado de contratos publicada con RFC-00 (enforcement completo pendiente).
