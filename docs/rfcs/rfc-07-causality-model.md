# RFC-07 — CAUSALITY_MODEL
**Sistema:** Tenon — Sistema de Verdad Financiera Operativa y Conciliación Multisistema  
**Estado:** DRAFT  
**Relación:** Depende de RFC-00_MANIFEST, RFC-01_CANONICAL_EVENT, RFC-01A_CANONICAL_IDS,
RFC-02_INGEST_APPEND_ONLY, RFC-03_NORMALIZATION_RULES, RFC-04_CORRELATION_ENGINE,
RFC-05_MONEY_STATE_MACHINE, RFC-06_DISCREPANCY_TAXONOMY

---

## Propósito

Definir el **modelo de causalidad explicable** de Tenon para atribuir
**por qué** ocurre una discrepancia, **dónde** se origina y **qué patrón**
la explica, sin inferencias implí­citas ni heurí­sticas opacas.

El modelo convierte discrepancias en **explicaciones defendibles**.

---

## No-Goals

- Priorizar impacto económico (RFC-08 posterior).
- Inferir intención, fraude o culpa humana.
- Ejecutar correcciones automáticas.
- “Aprender” causalidad sin evidencia registrada.
- Colapsar míºltiples causas en una sola por conveniencia.

---

## Invariantes

### 3.1 Causalidad basada en evidencia
- Toda causa debe estar respaldada por:
  - eventos,
  - estados,
  - reglas explí­citas,
  - versiones.

### 3.2 No unicidad forzada
- Una discrepancia puede tener **míºltiples causas plausibles**.
- Cada causa se registra por separado, con su evidencia.

### 3.3 Separación causa â†” severidad
- La causalidad explica el **origen**.
- La severidad/prioridad se define fuera (etapas posteriores).

### 3.4 Reproducibilidad
- Misma evidencia + mismas reglas â‡’ mismas causas atribuidas.

---

## Taxonomí­a de causas (cerrada)

### 4.1 Categorí­as principales

- `SOURCE_DELAY`
- `SOURCE_OMISSION`
- `SOURCE_DUPLICATION`
- `SOURCE_INCONSISTENCY`
- `INTEGRATION_MAPPING_ERROR`
- `NORMALIZATION_LOSS`
- `CORRELATION_AMBIGUITY`
- `STATE_TRANSITION_GAP`
- `EXTERNAL_SYSTEM_CHANGE`
- `UNKNOWN_CAUSE`

**Regla:**  
Toda causa debe pertenecer a **exactamente una** categorí­a primaria.

---

## Contratos (conceptuales)

### 5.1 CausalityAttribution

- `causality_id`
- `discrepancy_id`
- `cause_type` (enum cerrado)
- `confidence_level` (0.0–1.0)
- `supporting_events[]`
- `supporting_states[]`
- `supporting_rules[]`
- `explanation`
- `attributed_at`
- `model_version`

> Una discrepancia puede tener míºltiples `CausalityAttribution`.

---

## Flujo de atribución causal (alto nivel)

1. Selección de discrepancia.
2. Evaluación de reglas causales aplicables.
3. Recolección de evidencia.
4. Emisión de una o más atribuciones causales.
5. Registro append-only.

Nunca se elimina una causa previamente atribuida.

---

## Threat Model

### 7.1 Amenazas
- **Causa íºnica simplista** que oculta complejidad real.
- **Causalidad implí­cita** (“porque siempre pasa”).
- **Cambios retroactivos** que reescriben explicación histórica.
- **Confusión causa â†” sí­ntoma**.

### 7.2 Controles exigidos
- Enum cerrado y versionado.
- Evidencia explí­cita por causa.
- Posibilidad de míºltiples causas.
- Versionado del modelo causal.

---

## Pruebas

### 8.1 Unitarias
- Toda causa tiene tipo válido.
- Explicación obligatoria.
- Rechazo de causas fuera del enum.

### 8.2 Propiedades
- Determinismo: replay â‡’ mismas causas.
- No colapso: míºltiples causas se preservan.
- Conservadurismo: evidencia débil â‡’ `UNKNOWN_CAUSE`.

### 8.3 Sistémicas
- Discrepancias complejas con míºltiples fuentes.
- Evidencia parcial o contradictoria.
- Replay histórico completo.

---

## Criterios de Aceptación

Este RFC se considera cumplido cuando:
1. La causalidad es explí­cita, versionada y reproducible.
2. Míºltiples causas pueden coexistir sin colapsarse.
3. Toda causa tiene evidencia y explicación estructurada.
4. La atribución evita inferencias implí­citas.
5. El modelo resiste auditorí­a y revisión legal.

---

## Assumptions

- Las causas reales no siempre son íºnicas ni simples.
- Es preferible explicar incertidumbre que inventar certeza.
- La causalidad es diagnóstica, no punitiva.
