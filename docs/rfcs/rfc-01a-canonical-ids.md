# RFC-01A â€” CANONICAL_IDS
**Sistema:** Tenon â€” Sistema de Verdad Financiera Operativa y ConciliaciÃ³n Multisistema  
**Estado:** DRAFT  
**RelaciÃ³n:** Enmienda directa y dependiente de RFC-01_CANONICAL_EVENT

---

## PropÃ³sito

Definir **identidad, correlaciÃ³n y linaje** de los eventos canÃ³nicos para que Tenon pueda:
- detectar duplicados lÃ³gicos,
- reconstruir la â€œpelÃ­culaâ€ completa de una unidad monetaria,
- sostener idempotencia como evidencia,
- defender reconstrucciones histÃ³ricas ante auditorÃ­a o litigio.

Este RFC existe porque **sin identidad persistente no hay verdad reproducible**.

---

## No-Goals

- Definir reglas de correlaciÃ³n probabilÃ­stica (RFC-04).
- Definir estados del dinero (RFC-05).
- Definir discrepancias o causalidad (RFC-06/07).
- Definir almacenamiento fÃ­sico, Ã­ndices o performance.
- Resolver identidad â€œperfectaâ€ en presencia de datos corruptos (se registra, no se inventa).

---

## Invariantes

### 3.1 Identidad interna inmutable
- Todo `CanonicalEvent` tiene un `event_id` **Ãºnico, estable e inmutable**.
- `event_id` **no depende** de la fuente externa.
- `event_id` jamÃ¡s se reutiliza ni se reescribe.

### 3.2 Identidad externa preservada
- Si la fuente provee identidad (`source_event_id`), se **preserva sin normalizar**.
- Identidades externas contradictorias **no se corrigen**; se registran como evidencia.

### 3.3 Idempotencia como propiedad observable
- El sistema debe poder **probar** que dos ingestas representan el mismo hecho observado.
- La idempotencia se expresa como **decisiÃ³n explÃ­cita**: ACCEPT / REJECT_DUPLICATE / FLAG_AMBIGUOUS.

### 3.4 Linaje explÃ­cito
- Relaciones entre eventos (p.ej., refund â†’ payment, reversal â†’ payout) se modelan como **links explÃ­citos**, no como campos implÃ­citos.
- El linaje es **append-only**: se agregan vÃ­nculos; no se reescribe historia.

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

**CorrelaciÃ³n**
- `correlation_id` (string | null)
  - Puede ser provista por la fuente o asignada por Tenon de forma determinista.
  - No es obligatoria para la ingestiÃ³n inicial.

**Idempotencia**
- `idempotency_key` (derivable; ver 4.2)
- `idempotency_decision` (ACCEPT | REJECT_DUPLICATE | FLAG_AMBIGUOUS)

**Linaje**
- `lineage_links[]` (lista de relaciones explÃ­citas)
  - `type` (DERIVES_FROM | REVERSAL_OF | REFUND_OF | ADJUSTMENT_OF | RELATED_TO)
  - `target_event_id`
  - `evidence` (quÃ© regla/observaciÃ³n justificÃ³ el vÃ­nculo)
  - `version`

---

### 4.2 Clave de idempotencia (definiciÃ³n conceptual)

La **idempotency_key** se define como una funciÃ³n determinista de:
- `source_system`
- `source_event_id` (si existe)
- `event_type`
- `amount`
- `currency`
- `source_timestamp` (si existe)
- `raw_payload_hash`

**Reglas:**
- Si `source_event_id` existe, tiene prioridad.
- Si no existe, la clave se deriva del conjunto mÃ­nimo de evidencia disponible.
- Si la evidencia es insuficiente para afirmar unicidad:
  - la decisiÃ³n es `FLAG_AMBIGUOUS`, nunca â€œACCEPTâ€ por conveniencia.

> La fÃ³rmula exacta (hashing, concatenaciÃ³n) se fija en contratos tÃ©cnicos posteriores; aquÃ­ se fija el **principio**.

---

## Modelo de decisiones de identidad

Ante una nueva ingesta:

1. **MATCH EXACTO**
   - Misma `idempotency_key` que un evento previo.
   - DecisiÃ³n: `REJECT_DUPLICATE`
   - Evidencia registrada.

2. **MATCH PARCIAL**
   - Coincidencia incompleta (p.ej., mismo `external_reference` pero distinto monto).
   - DecisiÃ³n: `FLAG_AMBIGUOUS`
   - No se colapsa identidad; ambos eventos persisten.

3. **SIN MATCH**
   - DecisiÃ³n: `ACCEPT`
   - Se crea nuevo `event_id`.

Todas las decisiones se registran como eventos/metadata append-only.

---

## Threat Model

### 6.1 Amenazas
- **DuplicaciÃ³n silenciosa** por reintentos o race conditions.
- **ColisiÃ³n de referencias externas** (IDs reciclados o mal usados).
- **NormalizaciÃ³n agresiva** que â€œfuerzaâ€ unicidad falsa.
- **Borrado de historia** al colapsar eventos distintos como uno solo.

### 6.2 Controles exigidos
- DecisiÃ³n de idempotencia explÃ­cita y registrable.
- ProhibiciÃ³n de colapsar eventos sin evidencia suficiente.
- Linaje como estructura explÃ­cita (no inferida a posteriori).
- Versionado de reglas de identidad.

---

## Pruebas

### 7.1 Unitarias
- Un `event_id` no puede cambiar.
- Rechazo de reutilizaciÃ³n de `event_id`.
- Registro obligatorio de `idempotency_decision`.

### 7.2 Propiedades
- Idempotencia fuerte: N reintentos del mismo hecho â‡’ 1 ACCEPT + (Nâˆ’1) REJECT_DUPLICATE.
- AmbigÃ¼edad conservadora: evidencia insuficiente â‡’ FLAG_AMBIGUOUS.

### 7.3 SistÃ©micas
- Replay completo: mismas decisiones de identidad en re-ejecuciÃ³n.
- Escenarios de colisiÃ³n de `external_reference` entre fuentes distintas.
- Eventos fuera de orden temporal.

---

## Criterios de AceptaciÃ³n

Este RFC se considera cumplido cuando:
1. La identidad interna (`event_id`) es inmutable y no dependiente de la fuente.
2. La idempotencia es una decisiÃ³n explÃ­cita, no implÃ­cita.
3. Existe definiciÃ³n formal de linaje como links append-only.
4. AmbigÃ¼edad se preserva como estado vÃ¡lido (no se â€œarreglaâ€).
5. Las decisiones de identidad son reproducibles y versionables.

---

## Assumptions

- HabrÃ¡ fuentes con IDs pobres o inexistentes.
- HabrÃ¡ colisiones reales de referencias externas.
- La prioridad es **no perder verdad**, aunque se pierda comodidad operativa.
