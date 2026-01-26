# RFC-04 â€” CORRELATION_ENGINE
**Sistema:** Tenon â€” Sistema de Verdad Financiera Operativa y ConciliaciÃ³n Multisistema  
**Estado:** DRAFT  
**RelaciÃ³n:** Depende de RFC-00_MANIFEST, RFC-01_CANONICAL_EVENT, RFC-01A_CANONICAL_IDS, RFC-02_INGEST_APPEND_ONLY, RFC-03_NORMALIZATION_RULES

---

## PropÃ³sito

Definir el **motor de correlaciÃ³n** de Tenon para unir eventos canÃ³nicos
provenientes de mÃºltiples fuentes en **flujos explicables de dinero**
sin colapsar ambigÃ¼edad ni introducir interpretaciÃ³n silenciosa.

El motor:
- **propone vÃ­nculos**, no â€œresuelve verdadâ€,
- produce **evidencia explÃ­cita** por cada vÃ­nculo,
- asigna **score de confianza** reproducible,
- preserva **versionado** de reglas y resultados.

---

## No-Goals

- Determinar estados finales del dinero (RFC-05).
- Clasificar discrepancias o priorizarlas (RFC-06).
- Ejecutar acciones correctivas.
- â€œForzarâ€ match perfecto cuando falta evidencia.
- Optimizar performance o latencia.

---

## Invariantes

### 3.1 CorrelaciÃ³n â‰  conciliaciÃ³n
- Correlacionar es **proponer relaciones** entre eventos.
- Conciliar es **diagnosticar estados y discrepancias** (etapas posteriores).

### 3.2 Evidencia primero
- NingÃºn vÃ­nculo existe sin:
  - regla aplicada,
  - evidencia observada,
  - versiÃ³n del motor.
- Prohibido â€œmatch implÃ­citoâ€.

### 3.3 No colapso de identidad
- Eventos distintos **no se fusionan**.
- La correlaciÃ³n agrega **aristas**, no modifica nodos.

### 3.4 AmbigÃ¼edad preservada
- Si mÃºltiples correlaciones son plausibles:
  - todas se registran,
  - cada una con su score y evidencia.
- El sistema **no elige** silenciosamente.

### 3.5 Determinismo y versionado
- Misma entrada + misma versiÃ³n â‡’ mismos vÃ­nculos y scores.
- Cambios de reglas **no reescriben** correlaciones previas.

---

## Contratos (conceptuales)

### 4.1 CorrelationRule
Cada regla define:

- `rule_id`
- `rule_version`
- `applicability` (quÃ© tipos de eventos considera)
- `evidence_required[]`
- `scoring_function` (determinista)
- `explanation_template`

Ejemplos de reglas:
- Mismo `external_reference` + mismo `amount` Â± tolerancia.
- Secuencia temporal vÃ¡lida (AUTH â†’ CAPTURE â†’ SETTLE).
- Refund con referencia explÃ­cita al payment original.

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
- `confidence_score` (0.0â€“1.0)
- `engine_version`
- `created_at`

> Un `CorrelationLink` **no afirma verdad**; afirma â€œesta relaciÃ³n es plausible bajo estas reglasâ€.

---

### 4.3 MoneyFlow (estructura resultante)
- Grafo dirigido:
  - **Nodos:** `CanonicalEvent`
  - **Aristas:** `CorrelationLink`
- El grafo es **acumulativo** y **versionado**.

---

## Flujo del motor (alto nivel)

1. **SelecciÃ³n de candidatos**
   - Eventos canÃ³nicos relevantes por ventana temporal y tipo.
2. **AplicaciÃ³n de reglas**
   - Cada regla evalÃºa evidencia requerida.
3. **Scoring**
   - Se calcula score determinista.
4. **EmisiÃ³n**
   - Se registran `CorrelationLink` append-only.
5. **Persistencia**
   - Se actualiza el `MoneyFlow` (sin borrar aristas previas).

---

## Threat Model

### 6.1 Amenazas
- **Matching agresivo** que oculta discrepancias reales.
- **Reglas opacas** (caja negra).
- **Cambios de reglas retroactivos** que reescriben historia.
- **Bias temporal** (preferir eventos â€œmÃ¡s recientesâ€ sin evidencia).
- **Colisiones de referencias externas**.

### 6.2 Controles exigidos
- Reglas explÃ­citas y versionadas.
- Scores reproducibles.
- Registro de todas las correlaciones plausibles.
- ProhibiciÃ³n de borrar o modificar vÃ­nculos histÃ³ricos.
- Explicaciones estructuradas por vÃ­nculo.

---

## Pruebas

### 7.1 Unitarias
- Cada regla produce explicaciÃ³n cuando genera vÃ­nculo.
- Rechazo de reglas sin `evidence_required`.
- Score siempre en rango [0,1].

### 7.2 Propiedades
- Determinismo: replay â‡’ mismos vÃ­nculos y scores.
- Monotonicidad: el grafo solo crece.
- SimetrÃ­a controlada: reglas direccionales se comportan como se define.

### 7.3 SistÃ©micas
- MÃºltiples fuentes con datos contradictorios.
- Eventos fuera de orden temporal.
- Colisiones masivas de `external_reference`.
- Replay completo con cambio de versiÃ³n del motor:
  - correlaciones viejas intactas,
  - nuevas correlaciones versionadas.

---

## Criterios de AceptaciÃ³n

Este RFC se considera cumplido cuando:
1. La correlaciÃ³n produce **links explicables**, no fusiones.
2. Toda correlaciÃ³n tiene evidencia, regla y score versionados.
3. La ambigÃ¼edad se preserva explÃ­citamente.
4. El grafo (MoneyFlow) es reproducible y append-only.
5. Cambios de reglas no reescriben historia.

---

## Assumptions

- HabrÃ¡ datos incompletos, tardÃ­os y contradictorios.
- La correlaciÃ³n perfecta no existe; la evidencia sÃ­.
- Es preferible mÃºltiples hipÃ³tesis explÃ­citas a una â€œverdadâ€ implÃ­cita.
