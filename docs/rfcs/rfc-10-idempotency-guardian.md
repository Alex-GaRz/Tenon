# RFC-10 â€” IDEMPOTENCY_GUARDIAN
**Sistema:** Tenon â€” Sistema de Verdad Financiera Operativa y ConciliaciÃ³n Multisistema  
**Estado:** DRAFT  
**RelaciÃ³n:** Depende de RFC-00_MANIFEST, RFC-01_CANONICAL_EVENT, RFC-01A_CANONICAL_IDS,
RFC-02_INGEST_APPEND_ONLY, RFC-03_NORMALIZATION_RULES, RFC-08_EVENT_SOURCING_EVIDENCE,
RFC-09_IMMUTABLE_LEDGER_WORM

---

## PropÃ³sito

Definir el **Guardian de Idempotencia** como control institucional para garantizar que:
- reintentos, fallos distribuidos y duplicados no produzcan â€œrealidades paralelasâ€,
- la unicidad sea demostrable como evidencia (no solo â€œbest effortâ€),
- Tenon pueda probar, ante auditorÃ­a/litigio, que una misma intenciÃ³n/observaciÃ³n
  no generÃ³ mÃºltiples efectos lÃ³gicos dentro del sistema.

El Guardian convierte idempotencia en **propiedad probatoria**.

---

## No-Goals

- Ejecutar pagos o efectos externos.
- Resolver correlaciÃ³n probabilÃ­stica (RFC-04).
- Corregir datos crudos o canon.
- Definir tecnologÃ­a concreta de almacenamiento.
- Garantizar unicidad en sistemas externos (solo en Tenon).

---

## Invariantes

### 3.1 Idempotencia obligatoria para todo â€œwrite lÃ³gicoâ€
Cualquier operaciÃ³n que:
- registre ingesta,
- materialice CanonicalEvent,
- emita EvidenceEvent,
- emita vÃ­nculos de correlaciÃ³n,
- produzca estados o discrepancias,

debe estar cubierta por un mecanismo idempotente verificable.

### 3.2 Unicidad demostrable
Para cada acciÃ³n idempotente existe:
- una **clave determinista**,
- un **registro append-only** de decisiÃ³n,
- evidencia de que â€œya ocurriÃ³â€ o â€œno ocurriÃ³â€.

### 3.3 Decisiones explÃ­citas (no silenciosas)
El Guardian produce una decisiÃ³n formal:
- `ACCEPT_FIRST` (primera vez)
- `REJECT_DUPLICATE` (duplicado exacto)
- `FLAG_AMBIGUOUS` (colisiÃ³n/ambigÃ¼edad; no se ejecuta efecto)

### 3.4 Append-only + WORM
Los registros de idempotencia:
- son append-only,
- se escriben en el ledger WORM (RFC-09) como evidencia.

### 3.5 Determinismo
Mismo input + misma versiÃ³n de reglas â‡’ misma clave y misma decisiÃ³n.

---

## Contratos

### 4.1 IdempotencyKey (concepto)
Una `IdempotencyKey` es una representaciÃ³n determinista (normalizada) de:
- `scope` (quÃ© tipo de operaciÃ³n protege)
- `principal/source` (quÃ© actor o fuente originÃ³ la operaciÃ³n)
- `subject` (sobre quÃ© entidad opera: raw, event, flow, etc.)
- `payload_hash` (hash de contenido relevante)
- `version` (versiÃ³n del esquema/regla de clave)

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

### 4.3 Scopes mÃ­nimos obligatorios
El Guardian debe cubrir como mÃ­nimo:
- `INGEST` (RFC-02)
- `CANONICALIZE` (RFC-03)
- `EVIDENCE_WRITE` (RFC-08)
- (Opcional por etapa futura) `CORRELATE`, `STATE_EVAL`, `DISCREPANCY_EVAL`

> Este RFC exige el marco general; la ampliaciÃ³n por scope se valida en los RFCs respectivos.

---

## Modelo operativo (alto nivel)

1. Se calcula `idempotency_key` determinista para la operaciÃ³n.
2. Se consulta el registro de idempotencia (append-only):
   - si no existe â†’ `ACCEPT_FIRST`
   - si existe match exacto â†’ `REJECT_DUPLICATE`
   - si existe colisiÃ³n/ambigÃ¼edad â†’ `FLAG_AMBIGUOUS`
3. Se registra un `IdempotencyRecord` en el ledger WORM.
4. Solo si `ACCEPT_FIRST` se permite continuar con el write lÃ³gico.

---

## Threat Model

### 6.1 Amenazas
- **Retries masivos** provocan duplicados (doble registro, doble vÃ­nculo, doble discrepancia).
- **Race conditions** producen aceptaciones mÃºltiples.
- **Colisiones de claves** por mala construcciÃ³n de idempotency_key.
- **Bypass** del Guardian (cÃ³digo que escribe sin pasar por Ã©l).
- **Reescritura** de registros de idempotencia para â€œlimpiarâ€ duplicados.

### 6.2 Controles exigidos
- Registro de decisiÃ³n inmutable (WORM).
- SeparaciÃ³n de â€œdecidirâ€ y â€œejecutarâ€.
- DetecciÃ³n de bypass (tests + CI gates).
- Versionado de reglas de claves y scopes.
- AmbigÃ¼edad detiene efecto (FLAG_AMBIGUOUS), nunca â€œaccept por convenienciaâ€.

---

## Pruebas

### 7.1 Unitarias
- Misma operaciÃ³n â†’ misma `idempotency_key`.
- Primer intento â†’ `ACCEPT_FIRST`.
- Reintento exacto â†’ `REJECT_DUPLICATE`.
- ColisiÃ³n controlada â†’ `FLAG_AMBIGUOUS`.
- Todo record incluye `rule_version` y referencias a evidencia.

### 7.2 Propiedades (property-based)
- **At-most-once lÃ³gico:** N reintentos â‡’ exactamente 1 `ACCEPT_FIRST`.
- **Determinismo:** misma entrada â‡’ misma decisiÃ³n.
- **Monotonicidad:** registros de idempotencia solo crecen.

### 7.3 SistÃ©micas
- Retries masivos concurrentes (simulaciÃ³n de fallos parciales).
- Reordenamiento temporal de eventos.
- Replay completo desde ledger WORM:
  - reproduce decisiones del Guardian idÃ©nticas.
- Ataque de bypass:
  - intento de escribir sin Guardian â‡’ detectado y bloqueado.

---

## Criterios de AceptaciÃ³n

Este RFC se considera cumplido cuando:
1. Existe contrato de `IdempotencyKey` + `IdempotencyRecord` con decisiones explÃ­citas.
2. Las decisiones se registran append-only y son exportables como evidencia.
3. El sistema puede demostrar â€œat-most-once lÃ³gicoâ€ bajo retries y concurrencia.
4. La ambigÃ¼edad detiene efectos y queda registrada.
5. Replay desde ledger reproduce las decisiones de idempotencia.

---

## Assumptions

- La idempotencia en Tenon es mÃ¡s importante que throughput.
- El costo de detener por ambigÃ¼edad es menor que el costo de duplicar â€œverdadâ€.
- El ledger WORM es el ancla probatoria para decisiones del Guardian.
