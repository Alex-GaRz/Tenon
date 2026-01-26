# RFC-02 — INGEST_APPEND_ONLY
**Sistema:** Tenon — Sistema de Verdad Financiera Operativa y Conciliación Multisistema  
**Estado:** DRAFT  
**Relación:** Depende de RFC-00_MANIFEST, RFC-01_CANONICAL_EVENT, RFC-01A_CANONICAL_IDS

---

## 1) Propósito

Definir el **mecanismo de ingesta append-only** de Tenon para garantizar que:
- ningún dato crudo ni canónico pueda ser borrado o sobrescrito,
- toda observación quede preservada como evidencia,
- la historia sea reproducible punto a punto,
- cualquier disputa futura pueda reconstruirse sin ambigüedad.

Este RFC fija la **frontera de no-retorno**: una vez ingerido, el hecho existe para siempre.

---

## 2) No-Goals

- Definir normalización semántica (RFC-03).
- Definir correlación o matching (RFC-04).
- Definir ledger WORM físico o firma criptográfica (RFC-09).
- Definir performance, particionado o costos de almacenamiento.
- Filtrar, deduplicar o “arreglar” datos en ingesta.

---

## 3) Invariantes

### 3.1 Append-only absoluto
- La ingesta **solo agrega** registros.
- Prohibido UPDATE, DELETE, UPSERT o reescritura lógica.
- Correcciones se expresan como **nuevos eventos** o **nuevos registros de decisión**.

### 3.2 Preservación del crudo
- Todo payload crudo ingerido se conserva íntegro.
- Se registra `raw_payload_hash` y un `raw_pointer` estable.
- El crudo nunca se normaliza “in place”.

### 3.3 Separación de capas
- **Ingesta ≠ Normalización ≠ Interpretación**.
- La ingesta no decide verdad; solo **registra observaciones**.

### 3.4 Observabilidad temporal
- Se distinguen explícitamente:
  - `observed_at` (cuando Tenon observó),
  - `source_timestamp` (cuando la fuente reporta),
  - `ingested_at` (cuando se persiste).
- Nunca se colapsan timestamps.

### 3.5 Idempotencia conservadora
- La ingesta debe ser **idempotente a nivel de registro**:
  - reintentos no duplican efectos,
  - duplicados se detectan y se **registran como decisión**, no se silencian.
- La ingesta jamás “descarta” sin dejar rastro.

---

## 4) Contratos (conceptuales)

### 4.1 Registro de ingesta (IngestRecord)

Cada llamada de ingesta produce un `IngestRecord` append-only con:

**Identidad**
- `ingest_id` (interno, inmutable)
- `event_id` (si se materializa `CanonicalEvent`)
- `idempotency_decision` (ACCEPT | REJECT_DUPLICATE | FLAG_AMBIGUOUS)

**Origen**
- `source_system`
- `source_connector`
- `source_environment`

**Tiempo**
- `observed_at`
- `ingested_at`
- `source_timestamp` (nullable)

**Crudo**
- `raw_payload_hash`
- `raw_pointer`
- `raw_format`
- `raw_size_bytes`

**Versionado**
- `ingest_protocol_version`
- `adapter_version`

**Resultado**
- `status` (RECORDED | RECORDED_WITH_WARNINGS)
- `warnings[]` (si aplica)

> Nota: `IngestRecord` es evidencia de **que algo fue observado**, independientemente de que luego se normalice o correlacione.

---

## 5) Flujo de ingesta (alto nivel)

1. **Recepción**
   - Llega payload crudo desde adapter.
2. **Preservación**
   - Se persiste crudo append-only.
   - Se calcula `raw_payload_hash`.
3. **Identidad preliminar**
   - Se evalúa idempotencia (RFC-01A).
4. **Registro**
   - Se crea `IngestRecord` con decisión explícita.
5. **Materialización canónica**
   - Si procede, se emite `CanonicalEvent` (append-only).
6. **Salida**
   - Se devuelve ACK técnico (no semántico).

En ningún punto se elimina información.

---

## 6) Threat Model

### 6.1 Amenazas
- **Reintentos silenciosos** que crean duplicados.
- **Pérdida de payload crudo** (solo se guarda lo “útil”).
- **Reescritura posterior** para “limpiar” datos incómodos.
- **Timestamps manipulados** para ocultar latencia o fraude.
- **Backfills destructivos** que alteran historia.

### 6.2 Controles exigidos
- Append-only enforced por diseño.
- Hash del crudo + puntero estable.
- Registro explícito de decisiones de idempotencia.
- Versionado del protocolo de ingesta.
- Distinción explícita de timestamps.

---

## 7) Pruebas

### 7.1 Unitarias
- Prohibición de UPDATE/DELETE en stores de ingesta.
- Rechazo de ingesta sin `raw_payload_hash`.
- Registro obligatorio de `ingest_id`.

### 7.2 Propiedades
- Monotonicidad: el número de registros solo crece.
- Idempotencia: mismo input ⇒ misma decisión.
- No colapso temporal: timestamps distintos permanecen distintos.

### 7.3 Sistémicas
- Reintentos masivos (simulación de fallos de red).
- Ingesta fuera de orden temporal.
- Backfill histórico (meses) sin alterar registros previos.
- Caída parcial del adapter y recuperación.

---

## 8) Criterios de Aceptación

Este RFC se considera cumplido cuando:
1. La ingesta es estrictamente append-only.
2. El payload crudo se preserva íntegro y referenciable.
3. Toda ingesta produce un `IngestRecord` verificable.
4. Las decisiones de idempotencia quedan registradas.
5. No existe ruta de borrado o sobrescritura lógica.

---

## 9) Assumptions

- El volumen de datos crecerá indefinidamente; la verdad no expira.
- El costo de almacenamiento es menor que el costo de perder evidencia.
- Las fuentes pueden fallar, mentir o retrasarse; Tenon registra, no juzga en ingesta.
