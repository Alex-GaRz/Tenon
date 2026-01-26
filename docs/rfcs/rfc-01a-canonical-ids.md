# RFC-01A — CANONICAL_IDS
**Sistema:** Tenon — Sistema de Verdad Financiera Operativa y Conciliación Multisistema  
**Estado:** DRAFT  
**Relación:** Enmienda directa y dependiente de RFC-01_CANONICAL_EVENT

---

## Propósito

Definir **identidad, correlación y linaje** de los eventos canónicos para que Tenon pueda:
- detectar duplicados lógicos,
- reconstruir la “pelí­cula” completa de una unidad monetaria,
- sostener idempotencia como evidencia,
- defender reconstrucciones históricas ante auditorí­a o litigio.

Este RFC existe porque **sin identidad persistente no hay verdad reproducible**.

---

## No-Goals

- Definir reglas de correlación probabilí­stica (RFC-04).
- Definir estados del dinero (RFC-05).
- Definir discrepancias o causalidad (RFC-06/07).
- Definir almacenamiento fí­sico, í­ndices o performance.
- Resolver identidad “perfecta” en presencia de datos corruptos (se registra, no se inventa).

---

## Invariantes

### 3.1 Identidad interna inmutable
- Todo `CanonicalEvent` tiene un `event_id` **íºnico, estable e inmutable**.
- `event_id` **no depende** de la fuente externa.
- `event_id` jamás se reutiliza ni se reescribe.

### 3.2 Identidad externa preservada
- Si la fuente provee identidad (`source_event_id`), se **preserva sin normalizar**.
- Identidades externas contradictorias **no se corrigen**; se registran como evidencia.

### 3.3 Idempotencia como propiedad observable
- El sistema debe poder **probar** que dos ingestas representan el mismo hecho observado.
- La idempotencia se expresa como **decisión explí­cita**: ACCEPT / REJECT_DUPLICATE / FLAG_AMBIGUOUS.

### 3.4 Linaje explí­cito
- Relaciones entre eventos (p.ej., refund â†’ payment, reversal â†’ payout) se modelan como **links explí­citos**, no como campos implí­citos.
- El linaje es **append-only**: se agregan ví­nculos; no se reescribe historia.

### 3.5 Determinismo
- Dado el mismo set de eventos y las mismas versiones del sistema, las decisiones de identidad y linaje son reproducibles.

---

## Contratos (conceptuales)

### 4.1 Campos de identidad obligatorios

**Identidad primaria**
- `event_id` (UUID/ULID u otro identificador interno estable)

**Identidad externa**
- `source_event_id` (string | null)
- `external_reference` (string | null)

**Correlación**
- `correlation_id` (string | null)
  - Puede ser provista por la fuente o asignada por Tenon de forma determinista.
  - No es obligatoria para la ingestión inicial.

**Idempotencia**
- `idempotency_key` (derivable; ver 4.2)
- `idempotency_decision` (ACCEPT | REJECT_DUPLICATE | FLAG_AMBIGUOUS)

**Linaje**
- `lineage_links[]` (lista de relaciones explí­citas)
  - `type` (DERIVES_FROM | REVERSAL_OF | REFUND_OF | ADJUSTMENT_OF | RELATED_TO)
  - `target_event_id`
  - `evidence` (qué regla/observación justificó el ví­nculo)
  - `version`

---

### 4.2 Clave de idempotencia (definición conceptual)

La **idempotency_key** se define como una función determinista de:
- `source_system`
- `source_event_id` (si existe)
- `event_type`
- `amount`
- `currency`
- `source_timestamp` (si existe)
- `raw_payload_hash`

**Reglas:**
- Si `source_event_id` existe, tiene prioridad.
- Si no existe, la clave se deriva del conjunto mí­nimo de evidencia disponible.
- Si la evidencia es insuficiente para afirmar unicidad:
  - la decisión es `FLAG_AMBIGUOUS`, nunca “ACCEPT” por conveniencia.

> La fórmula exacta (hashing, concatenación) se fija en contratos técnicos posteriores; aquí­ se fija el **principio**.

---

## Modelo de decisiones de identidad

Ante una nueva ingesta:

1. **MATCH EXACTO**
   - Misma `idempotency_key` que un evento previo.
   - Decisión: `REJECT_DUPLICATE`
   - Evidencia registrada.

2. **MATCH PARCIAL**
   - Coincidencia incompleta (p.ej., mismo `external_reference` pero distinto monto).
   - Decisión: `FLAG_AMBIGUOUS`
   - No se colapsa identidad; ambos eventos persisten.

3. **SIN MATCH**
   - Decisión: `ACCEPT`
   - Se crea nuevo `event_id`.

Todas las decisiones se registran como eventos/metadata append-only.

---

## Threat Model

### 6.1 Amenazas
- **Duplicación silenciosa** por reintentos o race conditions.
- **Colisión de referencias externas** (IDs reciclados o mal usados).
- **Normalización agresiva** que “fuerza” unicidad falsa.
- **Borrado de historia** al colapsar eventos distintos como uno solo.

### 6.2 Controles exigidos
- Decisión de idempotencia explí­cita y registrable.
- Prohibición de colapsar eventos sin evidencia suficiente.
- Linaje como estructura explí­cita (no inferida a posteriori).
- Versionado de reglas de identidad.

---

## Pruebas

### 7.1 Unitarias
- Un `event_id` no puede cambiar.
- Rechazo de reutilización de `event_id`.
- Registro obligatorio de `idempotency_decision`.

### 7.2 Propiedades
- Idempotencia fuerte: N reintentos del mismo hecho â‡’ 1 ACCEPT + (Nâˆ’1) REJECT_DUPLICATE.
- Ambigí¼edad conservadora: evidencia insuficiente â‡’ FLAG_AMBIGUOUS.

### 7.3 Sistémicas
- Replay completo: mismas decisiones de identidad en re-ejecución.
- Escenarios de colisión de `external_reference` entre fuentes distintas.
- Eventos fuera de orden temporal.

---

## Criterios de Aceptación

Este RFC se considera cumplido cuando:
1. La identidad interna (`event_id`) es inmutable y no dependiente de la fuente.
2. La idempotencia es una decisión explí­cita, no implí­cita.
3. Existe definición formal de linaje como links append-only.
4. Ambigí¼edad se preserva como estado válido (no se “arregla”).
5. Las decisiones de identidad son reproducibles y versionables.

---

## Assumptions

- Habrá fuentes con IDs pobres o inexistentes.
- Habrá colisiones reales de referencias externas.
- La prioridad es **no perder verdad**, aunque se pierda comodidad operativa.
