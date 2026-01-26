# RFC-10 — IDEMPOTENCY_GUARDIAN
**Sistema:** Tenon — Sistema de Verdad Financiera Operativa y Conciliación Multisistema  
**Estado:** DRAFT  
**Relación:** Depende de RFC-00_MANIFEST, RFC-01_CANONICAL_EVENT, RFC-01A_CANONICAL_IDS,
RFC-02_INGEST_APPEND_ONLY, RFC-03_NORMALIZATION_RULES, RFC-08_EVENT_SOURCING_EVIDENCE,
RFC-09_IMMUTABLE_LEDGER_WORM

---

## 1) Propósito

Definir el **Guardian de Idempotencia** como control institucional para garantizar que:
- reintentos, fallos distribuidos y duplicados no produzcan “realidades paralelas”,
- la unicidad sea demostrable como evidencia (no solo “best effort”),
- Tenon pueda probar, ante auditoría/litigio, que una misma intención/observación
  no generó múltiples efectos lógicos dentro del sistema.

El Guardian convierte idempotencia en **propiedad probatoria**.

---

## 2) No-Goals

- Ejecutar pagos o efectos externos.
- Resolver correlación probabilística (RFC-04).
- Corregir datos crudos o canon.
- Definir tecnología concreta de almacenamiento.
- Garantizar unicidad en sistemas externos (solo en Tenon).

---

## 3) Invariantes

### 3.1 Idempotencia obligatoria para todo “write lógico”
Cualquier operación que:
- registre ingesta,
- materialice CanonicalEvent,
- emita EvidenceEvent,
- emita vínculos de correlación,
- produzca estados o discrepancias,

debe estar cubierta por un mecanismo idempotente verificable.

### 3.2 Unicidad demostrable
Para cada acción idempotente existe:
- una **clave determinista**,
- un **registro append-only** de decisión,
- evidencia de que “ya ocurrió” o “no ocurrió”.

### 3.3 Decisiones explícitas (no silenciosas)
El Guardian produce una decisión formal:
- `ACCEPT_FIRST` (primera vez)
- `REJECT_DUPLICATE` (duplicado exacto)
- `FLAG_AMBIGUOUS` (colisión/ambigüedad; no se ejecuta efecto)

### 3.4 Append-only + WORM
Los registros de idempotencia:
- son append-only,
- se escriben en el ledger WORM (RFC-09) como evidencia.

### 3.5 Determinismo
Mismo input + misma versión de reglas ⇒ misma clave y misma decisión.

---

## 4) Contratos

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

### 4.3 Scopes mínimos obligatorios
El Guardian debe cubrir como mínimo:
- `INGEST` (RFC-02)
- `CANONICALIZE` (RFC-03)
- `EVIDENCE_WRITE` (RFC-08)
- (Opcional por etapa futura) `CORRELATE`, `STATE_EVAL`, `DISCREPANCY_EVAL`

> Este RFC exige el marco general; la ampliación por scope se valida en los RFCs respectivos.

---

## 5) Modelo operativo (alto nivel)

1. Se calcula `idempotency_key` determinista para la operación.
2. Se consulta el registro de idempotencia (append-only):
   - si no existe → `ACCEPT_FIRST`
   - si existe match exacto → `REJECT_DUPLICATE`
   - si existe colisión/ambigüedad → `FLAG_AMBIGUOUS`
3. Se registra un `IdempotencyRecord` en el ledger WORM.
4. Solo si `ACCEPT_FIRST` se permite continuar con el write lógico.

---

## 6) Threat Model

### 6.1 Amenazas
- **Retries masivos** provocan duplicados (doble registro, doble vínculo, doble discrepancia).
- **Race conditions** producen aceptaciones múltiples.
- **Colisiones de claves** por mala construcción de idempotency_key.
- **Bypass** del Guardian (código que escribe sin pasar por él).
- **Reescritura** de registros de idempotencia para “limpiar” duplicados.

### 6.2 Controles exigidos
- Registro de decisión inmutable (WORM).
- Separación de “decidir” y “ejecutar”.
- Detección de bypass (tests + CI gates).
- Versionado de reglas de claves y scopes.
- Ambigüedad detiene efecto (FLAG_AMBIGUOUS), nunca “accept por conveniencia”.

---

## 7) Pruebas

### 7.1 Unitarias
- Misma operación → misma `idempotency_key`.
- Primer intento → `ACCEPT_FIRST`.
- Reintento exacto → `REJECT_DUPLICATE`.
- Colisión controlada → `FLAG_AMBIGUOUS`.
- Todo record incluye `rule_version` y referencias a evidencia.

### 7.2 Propiedades (property-based)
- **At-most-once lógico:** N reintentos ⇒ exactamente 1 `ACCEPT_FIRST`.
- **Determinismo:** misma entrada ⇒ misma decisión.
- **Monotonicidad:** registros de idempotencia solo crecen.

### 7.3 Sistémicas
- Retries masivos concurrentes (simulación de fallos parciales).
- Reordenamiento temporal de eventos.
- Replay completo desde ledger WORM:
  - reproduce decisiones del Guardian idénticas.
- Ataque de bypass:
  - intento de escribir sin Guardian ⇒ detectado y bloqueado.

---

## 8) Criterios de Aceptación

Este RFC se considera cumplido cuando:
1. Existe contrato de `IdempotencyKey` + `IdempotencyRecord` con decisiones explícitas.
2. Las decisiones se registran append-only y son exportables como evidencia.
3. El sistema puede demostrar “at-most-once lógico” bajo retries y concurrencia.
4. La ambigüedad detiene efectos y queda registrada.
5. Replay desde ledger reproduce las decisiones de idempotencia.

---

## 9) Assumptions

- La idempotencia en Tenon es más importante que throughput.
- El costo de detener por ambigüedad es menor que el costo de duplicar “verdad”.
- El ledger WORM es el ancla probatoria para decisiones del Guardian.
