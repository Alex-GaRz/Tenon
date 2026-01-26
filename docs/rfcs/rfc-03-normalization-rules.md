# RFC-03 — NORMALIZATION_RULES
**Sistema:** Tenon — Sistema de Verdad Financiera Operativa y Conciliación Multisistema  
**Estado:** DRAFT  
**Relación:** Depende de RFC-00_MANIFEST, RFC-01_CANONICAL_EVENT, RFC-01A_CANONICAL_IDS, RFC-02_INGEST_APPEND_ONLY

---

## Propósito

Definir la **normalización canónica determinista** que transforma datos crudos preservados
en `CanonicalEvent` **sin interpretar la realidad**.

La normalización:
- reduce heterogeneidad estructural,
- preserva evidencia,
- es reproducible,
- no “arregla” datos,
- no decide verdad.

---

## No-Goals

- Corregir FX, impuestos, fees, contabilidad o pricing.
- Inferir estados del dinero o conciliación.
- Resolver discrepancias o causalidad.
- Enriquecer con fuentes externas.
- Optimizar performance o storage.
- “Completar” campos faltantes con heurí­sticas.

---

## Invariantes

### 3.1 Determinismo fuerte
- Misma entrada cruda + mismas versiones â‡’ mismo `CanonicalEvent`.
- Prohibido usar:
  - reloj del sistema,
  - llamadas externas,
  - randomness,
  - lookups no versionados.

### 3.2 Transparencia total
- Cada campo normalizado debe ser trazable al crudo:
  - por copia directa,
  - por regla explí­cita y versionada,
  - o marcado como `UNKNOWN`.

### 3.3 No interpretación
- La normalización **no**:
  - reclasifica montos,
  - calcula FX,
  - reasigna impuestos,
  - decide “qué deberí­a haber pasado”.
- Si la fuente es ambigua, el canon **permanece ambiguo**.

### 3.4 Preservación de pérdida
- Si el crudo pierde información al normalizar (p.ej., PDF â†’ campos),
  la pérdida debe quedar registrada como warning.
- Nunca se descarta el crudo original.

### 3.5 Versionado obligatorio
- Toda regla de normalización tiene `normalizer_version`.
- Cambios de reglas **no** reescriben eventos previos.

---

## Contratos (conceptuales)

### 4.1 NormalizationRule
Cada regla define:

- `rule_id`
- `rule_version`
- `input_signature` (qué formato/shape acepta)
- `mapping` (crudo â†’ campo canónico)
- `lossy_fields[]` (si aplica)
- `warnings[]` (condiciones de degradación)

### 4.2 NormalizationResult
Cada ejecución produce:

- `event_id` (si materializa `CanonicalEvent`)
- `normalizer_version`
- `applied_rules[]`
- `warnings[]`
- `diff_reference` (referencia al diff crudoâ†’canon)

---

## Flujo de normalización (alto nivel)

1. **Selección de regla**
   - En función de `source_system`, `raw_format`, `schema_hint`.
2. **Aplicación determinista**
   - Se mapean campos explí­citos.
3. **Marcado de ambigí¼edad**
   - Campos no inferibles â‡’ `UNKNOWN`.
4. **Registro**
   - Se emite `CanonicalEvent` append-only.
   - Se registra `NormalizationResult`.

No existe “fallback mágico”.

---

## Threat Model

### 6.1 Amenazas
- **Normalización creativa** que altera semántica.
- **Cambios silenciosos** de reglas rompiendo reproducibilidad.
- **Dependencias ocultas** (APIs, tablas externas).
- **Correcciones retroactivas** que reescriben historia.
- **Pérdida de evidencia** al “limpiar” datos.

### 6.2 Controles exigidos
- Reglas explí­citas y versionadas.
- Diff trazable crudoâ†’canon.
- Warnings obligatorios en pérdida.
- Prohibición de reescritura histórica.
- UNKNOWN como salida segura.

---

## Pruebas

### 7.1 Unitarias
- Cada regla mapea solo lo declarado.
- Campos fuera de regla â‡’ no se pueblan.
- `normalizer_version` siempre presente.

### 7.2 Propiedades
- Determinismo: N ejecuciones â‡’ mismo resultado.
- No side-effects: la normalización no altera crudo.
- Estabilidad temporal: replay produce mismos eventos.

### 7.3 Sistémicas
- Cambios de versión:
  - eventos nuevos usan regla nueva,
  - eventos viejos permanecen intactos.
- Normalización con crudo incompleto/corrupto.
- Formatos mixtos (JSON, CSV, PDF).

---

## Criterios de Aceptación

Este RFC se considera cumplido cuando:
1. La normalización es determinista y versionada.
2. No existe interpretación semántica ni “arreglo” de datos.
3. Toda pérdida o ambigí¼edad queda registrada.
4. El crudo original siempre es accesible.
5. Replay histórico produce resultados idénticos.

---

## Assumptions

- Las fuentes enviarán datos inconsistentes y, a veces, incorrectos.
- La presión por “limpiar” datos existirá; este RFC lo prohí­be.
- La verdad operativa requiere aceptar ambigí¼edad antes que inventar precisión.
