# RFC-04 — CORRELATION_ENGINE
**Sistema:** Tenon — Sistema de Verdad Financiera Operativa y Conciliación Multisistema  
**Estado:** DRAFT  
**Relación:** Depende de RFC-00_MANIFEST, RFC-01_CANONICAL_EVENT, RFC-01A_CANONICAL_IDS, RFC-02_INGEST_APPEND_ONLY, RFC-03_NORMALIZATION_RULES

---

## Propósito

Definir el **motor de correlación** de Tenon para unir eventos canónicos
provenientes de míºltiples fuentes en **flujos explicables de dinero**
sin colapsar ambigí¼edad ni introducir interpretación silenciosa.

El motor:
- **propone ví­nculos**, no “resuelve verdad”,
- produce **evidencia explí­cita** por cada ví­nculo,
- asigna **score de confianza** reproducible,
- preserva **versionado** de reglas y resultados.

---

## No-Goals

- Determinar estados finales del dinero (RFC-05).
- Clasificar discrepancias o priorizarlas (RFC-06).
- Ejecutar acciones correctivas.
- “Forzar” match perfecto cuando falta evidencia.
- Optimizar performance o latencia.

---

## Invariantes

### 3.1 Correlación â‰  conciliación
- Correlacionar es **proponer relaciones** entre eventos.
- Conciliar es **diagnosticar estados y discrepancias** (etapas posteriores).

### 3.2 Evidencia primero
- Ningíºn ví­nculo existe sin:
  - regla aplicada,
  - evidencia observada,
  - versión del motor.
- Prohibido “match implí­cito”.

### 3.3 No colapso de identidad
- Eventos distintos **no se fusionan**.
- La correlación agrega **aristas**, no modifica nodos.

### 3.4 Ambigí¼edad preservada
- Si míºltiples correlaciones son plausibles:
  - todas se registran,
  - cada una con su score y evidencia.
- El sistema **no elige** silenciosamente.

### 3.5 Determinismo y versionado
- Misma entrada + misma versión â‡’ mismos ví­nculos y scores.
- Cambios de reglas **no reescriben** correlaciones previas.

---

## Contratos (conceptuales)

### 4.1 CorrelationRule
Cada regla define:

- `rule_id`
- `rule_version`
- `applicability` (qué tipos de eventos considera)
- `evidence_required[]`
- `scoring_function` (determinista)
- `explanation_template`

Ejemplos de reglas:
- Mismo `external_reference` + mismo `amount` ± tolerancia.
- Secuencia temporal válida (AUTH â†’ CAPTURE â†’ SETTLE).
- Refund con referencia explí­cita al payment original.

---

### 4.2 CorrelationLink
Resultado append-only del motor:

- `link_id`
- `from_event_id`
- `to_event_id`
- `link_type` (POTENTIAL_MATCH | SEQUENCE | REVERSAL | REFUND | RELATED)
- `rule_id`
- `rule_version`
- `evidence[]`
- `confidence_score` (0.0–1.0)
- `engine_version`
- `created_at`

> Un `CorrelationLink` **no afirma verdad**; afirma “esta relación es plausible bajo estas reglas”.

---

### 4.3 MoneyFlow (estructura resultante)
- Grafo dirigido:
  - **Nodos:** `CanonicalEvent`
  - **Aristas:** `CorrelationLink`
- El grafo es **acumulativo** y **versionado**.

---

## Flujo del motor (alto nivel)

1. **Selección de candidatos**
   - Eventos canónicos relevantes por ventana temporal y tipo.
2. **Aplicación de reglas**
   - Cada regla evalíºa evidencia requerida.
3. **Scoring**
   - Se calcula score determinista.
4. **Emisión**
   - Se registran `CorrelationLink` append-only.
5. **Persistencia**
   - Se actualiza el `MoneyFlow` (sin borrar aristas previas).

---

## Threat Model

### 6.1 Amenazas
- **Matching agresivo** que oculta discrepancias reales.
- **Reglas opacas** (caja negra).
- **Cambios de reglas retroactivos** que reescriben historia.
- **Bias temporal** (preferir eventos “más recientes” sin evidencia).
- **Colisiones de referencias externas**.

### 6.2 Controles exigidos
- Reglas explí­citas y versionadas.
- Scores reproducibles.
- Registro de todas las correlaciones plausibles.
- Prohibición de borrar o modificar ví­nculos históricos.
- Explicaciones estructuradas por ví­nculo.

---

## Pruebas

### 7.1 Unitarias
- Cada regla produce explicación cuando genera ví­nculo.
- Rechazo de reglas sin `evidence_required`.
- Score siempre en rango [0,1].

### 7.2 Propiedades
- Determinismo: replay â‡’ mismos ví­nculos y scores.
- Monotonicidad: el grafo solo crece.
- Simetrí­a controlada: reglas direccionales se comportan como se define.

### 7.3 Sistémicas
- Míºltiples fuentes con datos contradictorios.
- Eventos fuera de orden temporal.
- Colisiones masivas de `external_reference`.
- Replay completo con cambio de versión del motor:
  - correlaciones viejas intactas,
  - nuevas correlaciones versionadas.

---

## Criterios de Aceptación

Este RFC se considera cumplido cuando:
1. La correlación produce **links explicables**, no fusiones.
2. Toda correlación tiene evidencia, regla y score versionados.
3. La ambigí¼edad se preserva explí­citamente.
4. El grafo (MoneyFlow) es reproducible y append-only.
5. Cambios de reglas no reescriben historia.

---

## Assumptions

- Habrá datos incompletos, tardí­os y contradictorios.
- La correlación perfecta no existe; la evidencia sí­.
- Es preferible míºltiples hipótesis explí­citas a una “verdad” implí­cita.
