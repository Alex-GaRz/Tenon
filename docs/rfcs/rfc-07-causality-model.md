# RFC-07 â€” CAUSALITY_MODEL
**Sistema:** Tenon â€” Sistema de Verdad Financiera Operativa y ConciliaciÃ³n Multisistema  
**Estado:** DRAFT  
**RelaciÃ³n:** Depende de RFC-00_MANIFEST, RFC-01_CANONICAL_EVENT, RFC-01A_CANONICAL_IDS,
RFC-02_INGEST_APPEND_ONLY, RFC-03_NORMALIZATION_RULES, RFC-04_CORRELATION_ENGINE,
RFC-05_MONEY_STATE_MACHINE, RFC-06_DISCREPANCY_TAXONOMY

---

## PropÃ³sito

Definir el **modelo de causalidad explicable** de Tenon para atribuir
**por quÃ©** ocurre una discrepancia, **dÃ³nde** se origina y **quÃ© patrÃ³n**
la explica, sin inferencias implÃ­citas ni heurÃ­sticas opacas.

El modelo convierte discrepancias en **explicaciones defendibles**.

---

## No-Goals

- Priorizar impacto econÃ³mico (RFC-08 posterior).
- Inferir intenciÃ³n, fraude o culpa humana.
- Ejecutar correcciones automÃ¡ticas.
- â€œAprenderâ€ causalidad sin evidencia registrada.
- Colapsar mÃºltiples causas en una sola por conveniencia.

---

## Invariantes

### 3.1 Causalidad basada en evidencia
- Toda causa debe estar respaldada por:
  - eventos,
  - estados,
  - reglas explÃ­citas,
  - versiones.

### 3.2 No unicidad forzada
- Una discrepancia puede tener **mÃºltiples causas plausibles**.
- Cada causa se registra por separado, con su evidencia.

### 3.3 SeparaciÃ³n causa â†” severidad
- La causalidad explica el **origen**.
- La severidad/prioridad se define fuera (etapas posteriores).

### 3.4 Reproducibilidad
- Misma evidencia + mismas reglas â‡’ mismas causas atribuidas.

---

## TaxonomÃ­a de causas (cerrada)

### 4.1 CategorÃ­as principales

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
Toda causa debe pertenecer a **exactamente una** categorÃ­a primaria.

---

## Contratos (conceptuales)

### 5.1 CausalityAttribution

- `causality_id`
- `discrepancy_id`
- `cause_type` (enum cerrado)
- `confidence_level` (0.0â€“1.0)
- `supporting_events[]`
- `supporting_states[]`
- `supporting_rules[]`
- `explanation`
- `attributed_at`
- `model_version`

> Una discrepancia puede tener mÃºltiples `CausalityAttribution`.

---

## Flujo de atribuciÃ³n causal (alto nivel)

1. SelecciÃ³n de discrepancia.
2. EvaluaciÃ³n de reglas causales aplicables.
3. RecolecciÃ³n de evidencia.
4. EmisiÃ³n de una o mÃ¡s atribuciones causales.
5. Registro append-only.

Nunca se elimina una causa previamente atribuida.

---

## Threat Model

### 7.1 Amenazas
- **Causa Ãºnica simplista** que oculta complejidad real.
- **Causalidad implÃ­cita** (â€œporque siempre pasaâ€).
- **Cambios retroactivos** que reescriben explicaciÃ³n histÃ³rica.
- **ConfusiÃ³n causa â†” sÃ­ntoma**.

### 7.2 Controles exigidos
- Enum cerrado y versionado.
- Evidencia explÃ­cita por causa.
- Posibilidad de mÃºltiples causas.
- Versionado del modelo causal.

---

## Pruebas

### 8.1 Unitarias
- Toda causa tiene tipo vÃ¡lido.
- ExplicaciÃ³n obligatoria.
- Rechazo de causas fuera del enum.

### 8.2 Propiedades
- Determinismo: replay â‡’ mismas causas.
- No colapso: mÃºltiples causas se preservan.
- Conservadurismo: evidencia dÃ©bil â‡’ `UNKNOWN_CAUSE`.

### 8.3 SistÃ©micas
- Discrepancias complejas con mÃºltiples fuentes.
- Evidencia parcial o contradictoria.
- Replay histÃ³rico completo.

---

## Criterios de AceptaciÃ³n

Este RFC se considera cumplido cuando:
1. La causalidad es explÃ­cita, versionada y reproducible.
2. MÃºltiples causas pueden coexistir sin colapsarse.
3. Toda causa tiene evidencia y explicaciÃ³n estructurada.
4. La atribuciÃ³n evita inferencias implÃ­citas.
5. El modelo resiste auditorÃ­a y revisiÃ³n legal.

---

## Assumptions

- Las causas reales no siempre son Ãºnicas ni simples.
- Es preferible explicar incertidumbre que inventar certeza.
- La causalidad es diagnÃ³stica, no punitiva.
