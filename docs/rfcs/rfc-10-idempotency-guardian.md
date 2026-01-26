# RFC-10 — IDEMPOTENCY_GUARDIAN
**Sistema:** Tenon — Sistema de Verdad Financiera Operativa y Conciliación Multisistema  
**Estado:** DRAFT  
**Relación:** Depende de RFC-00_MANIFEST, RFC-01_CANONICAL_EVENT, RFC-01A_CANONICAL_IDS,
RFC-02_INGEST_APPEND_ONLY, RFC-03_NORMALIZATION_RULES, RFC-08_EVENT_SOURCING_EVIDENCE,
RFC-09_IMMUTABLE_LEDGER_WORM

---

## Propósito

Definir el **Guardian de Idempotencia** como control institucional para garantizar que:
- reintentos, fallos distribuidos y duplicados no produzcan “realidades paralelas”,
- la unicidad sea demostrable como evidencia (no solo “best effort”),
- Tenon pueda probar, ante auditorí­a/litigio, que una misma intención/observación
  no generó míºltiples efectos lógicos dentro del sistema.

El Guardian convierte idempotencia en **propiedad probatoria**.

---

## No-Goals

- Ejecutar pagos o efectos externos.
- Resolver correlación probabilí­stica (RFC-04).
- Corregir datos crudos o canon.
- Definir tecnologí­a concreta de almacenamiento.
- Garantizar unicidad en sistemas externos (solo en Tenon).

---

## Invariantes

### 3.1 Idempotencia obligatoria para todo “write lógico”
Cualquier operación que:
- registre ingesta,
- materialice CanonicalEvent,
- emita EvidenceEvent,
- emita ví­nculos de correlación,
- produzca estados o discrepancias,

debe estar cubierta por un mecanismo idempotente verificable.

### 3.2 Unicidad demostrable
Para cada acción idempotente existe:
- una **clave determinista**,
- un **registro append-only** de decisión,
- evidencia de que “ya ocurrió” o “no ocurrió”.

### 3.3 Decisiones explí­citas (no silenciosas)
El Guardian produce una decisión formal:
- `ACCEPT_FIRST` (primera vez)
- `REJECT_DUPLICATE` (duplicado exacto)
- `FLAG_AMBIGUOUS` (colisión/ambigí¼edad; no se ejecuta efecto)

### 3.4 Append-only + WORM
Los registros de idempotencia:
- son append-only,
- se escriben en el ledger WORM (RFC-09) como evidencia.

### 3.5 Determinismo
Mismo input + misma versión de reglas â‡’ misma clave y misma decisión.

---

## Contratos

### 4.1 IdempotencyKey (concepto)
Una `IdempotencyKey` es una representación determinista (normalizada) de:
- `scope` (qué tipo de operación protege)
- `principal/source` (qué actor o fuente originó la operación)
- `subject` (sobre qué entidad opera: raw, event, flow, etc.)
- `payload_hash` (hash de contenido relevante)
- `version` (versión del esquema/regla de clave)

**Regla:** la clave debe ser estable y verificable.

---

### 4.2 IdempotencyRecord (evidencia)
Registro append-only que contiene:

- `idempotency_record_id`
- `idempotency_key`
- `scope` (INGEST | CANONICALIZE | EVIDENCE_WRITE | CORRELATE | STATE_EVAL | DISCREPANCY_EVAL)
- `decision` (ACCEPT_FIRST | REJECT_DUPLICATE | FLAG_AMBIGUOUS)
- `first_seen_at`
- `decided_at`
- `evidence_refs[]` (pointers a ledger entries / evidence events)
- `rule_version`
- `notes` (si aplica)

---

### 4.3 Scopes mí­nimos obligatorios
El Guardian debe cubrir como mí­nimo:
- `INGEST` (RFC-02)
- `CANONICALIZE` (RFC-03)
- `EVIDENCE_WRITE` (RFC-08)
- (Opcional por etapa futura) `CORRELATE`, `STATE_EVAL`, `DISCREPANCY_EVAL`

> Este RFC exige el marco general; la ampliación por scope se valida en los RFCs respectivos.

---

## Modelo operativo (alto nivel)

1. Se calcula `idempotency_key` determinista para la operación.
2. Se consulta el registro de idempotencia (append-only):
   - si no existe â†’ `ACCEPT_FIRST`
   - si existe match exacto â†’ `REJECT_DUPLICATE`
   - si existe colisión/ambigí¼edad â†’ `FLAG_AMBIGUOUS`
3. Se registra un `IdempotencyRecord` en el ledger WORM.
4. Solo si `ACCEPT_FIRST` se permite continuar con el write lógico.

---

## Threat Model

### 6.1 Amenazas
- **Retries masivos** provocan duplicados (doble registro, doble ví­nculo, doble discrepancia).
- **Race conditions** producen aceptaciones míºltiples.
- **Colisiones de claves** por mala construcción de idempotency_key.
- **Bypass** del Guardian (código que escribe sin pasar por él).
- **Reescritura** de registros de idempotencia para “limpiar” duplicados.

### 6.2 Controles exigidos
- Registro de decisión inmutable (WORM).
- Separación de “decidir” y “ejecutar”.
- Detección de bypass (tests + CI gates).
- Versionado de reglas de claves y scopes.
- Ambigí¼edad detiene efecto (FLAG_AMBIGUOUS), nunca “accept por conveniencia”.

---

## Pruebas

### 7.1 Unitarias
- Misma operación â†’ misma `idempotency_key`.
- Primer intento â†’ `ACCEPT_FIRST`.
- Reintento exacto â†’ `REJECT_DUPLICATE`.
- Colisión controlada â†’ `FLAG_AMBIGUOUS`.
- Todo record incluye `rule_version` y referencias a evidencia.

### 7.2 Propiedades (property-based)
- **At-most-once lógico:** N reintentos â‡’ exactamente 1 `ACCEPT_FIRST`.
- **Determinismo:** misma entrada â‡’ misma decisión.
- **Monotonicidad:** registros de idempotencia solo crecen.

### 7.3 Sistémicas
- Retries masivos concurrentes (simulación de fallos parciales).
- Reordenamiento temporal de eventos.
- Replay completo desde ledger WORM:
  - reproduce decisiones del Guardian idénticas.
- Ataque de bypass:
  - intento de escribir sin Guardian â‡’ detectado y bloqueado.

---

## Criterios de Aceptación

Este RFC se considera cumplido cuando:
1. Existe contrato de `IdempotencyKey` + `IdempotencyRecord` con decisiones explí­citas.
2. Las decisiones se registran append-only y son exportables como evidencia.
3. El sistema puede demostrar “at-most-once lógico” bajo retries y concurrencia.
4. La ambigí¼edad detiene efectos y queda registrada.
5. Replay desde ledger reproduce las decisiones de idempotencia.

---

## Assumptions

- La idempotencia en Tenon es más importante que throughput.
- El costo de detener por ambigí¼edad es menor que el costo de duplicar “verdad”.
- El ledger WORM es el ancla probatoria para decisiones del Guardian.
