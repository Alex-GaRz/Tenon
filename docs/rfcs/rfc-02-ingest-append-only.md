# RFC-02 â€” INGEST_APPEND_ONLY
**Sistema:** Tenon â€” Sistema de Verdad Financiera Operativa y ConciliaciÃ³n Multisistema  
**Estado:** DRAFT  
**RelaciÃ³n:** Depende de RFC-00_MANIFEST, RFC-01_CANONICAL_EVENT, RFC-01A_CANONICAL_IDS

---

## PropÃ³sito

Definir el **mecanismo de ingesta append-only** de Tenon para garantizar que:
- ningÃºn dato crudo ni canÃ³nico pueda ser borrado o sobrescrito,
- toda observaciÃ³n quede preservada como evidencia,
- la historia sea reproducible punto a punto,
- cualquier disputa futura pueda reconstruirse sin ambigÃ¼edad.

Este RFC fija la **frontera de no-retorno**: una vez ingerido, el hecho existe para siempre.

---

## No-Goals

- Definir normalizaciÃ³n semÃ¡ntica (RFC-03).
- Definir correlaciÃ³n o matching (RFC-04).
- Definir ledger WORM fÃ­sico o firma criptogrÃ¡fica (RFC-09).
- Definir performance, particionado o costos de almacenamiento.
- Filtrar, deduplicar o â€œarreglarâ€ datos en ingesta.

---

## Invariantes

### 3.1 Append-only absoluto
- La ingesta **solo agrega** registros.
- Prohibido UPDATE, DELETE, UPSERT o reescritura lÃ³gica.
- Correcciones se expresan como **nuevos eventos** o **nuevos registros de decisiÃ³n**.

### 3.2 PreservaciÃ³n del crudo
- Todo payload crudo ingerido se conserva Ã­ntegro.
- Se registra `raw_payload_hash` y un `raw_pointer` estable.
- El crudo nunca se normaliza â€œin placeâ€.

### 3.3 SeparaciÃ³n de capas
- **Ingesta â‰  NormalizaciÃ³n â‰  InterpretaciÃ³n**.
- La ingesta no decide verdad; solo **registra observaciones**.

### 3.4 Observabilidad temporal
- Se distinguen explÃ­citamente:
  - `observed_at` (cuando Tenon observÃ³),
  - `source_timestamp` (cuando la fuente reporta),
  - `ingested_at` (cuando se persiste).
- Nunca se colapsan timestamps.

### 3.5 Idempotencia conservadora
- La ingesta debe ser **idempotente a nivel de registro**:
  - reintentos no duplican efectos,
  - duplicados se detectan y se **registran como decisiÃ³n**, no se silencian.
- La ingesta jamÃ¡s â€œdescartaâ€ sin dejar rastro.

---

## Contratos (conceptuales)

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

## Flujo de ingesta (alto nivel)

1. **RecepciÃ³n**
   - Llega payload crudo desde adapter.
2. **PreservaciÃ³n**
   - Se persiste crudo append-only.
   - Se calcula `raw_payload_hash`.
3. **Identidad preliminar**
   - Se evalÃºa idempotencia (RFC-01A).
4. **Registro**
   - Se crea `IngestRecord` con decisiÃ³n explÃ­cita.
5. **MaterializaciÃ³n canÃ³nica**
   - Si procede, se emite `CanonicalEvent` (append-only).
6. **Salida**
   - Se devuelve ACK tÃ©cnico (no semÃ¡ntico).

En ningÃºn punto se elimina informaciÃ³n.

---

## Threat Model

### 6.1 Amenazas
- **Reintentos silenciosos** que crean duplicados.
- **PÃ©rdida de payload crudo** (solo se guarda lo â€œÃºtilâ€).
- **Reescritura posterior** para â€œlimpiarâ€ datos incÃ³modos.
- **Timestamps manipulados** para ocultar latencia o fraude.
- **Backfills destructivos** que alteran historia.

### 6.2 Controles exigidos
- Append-only enforced por diseÃ±o.
- Hash del crudo + puntero estable.
- Registro explÃ­cito de decisiones de idempotencia.
- Versionado del protocolo de ingesta.
- DistinciÃ³n explÃ­cita de timestamps.

---

## Pruebas

### 7.1 Unitarias
- ProhibiciÃ³n de UPDATE/DELETE en stores de ingesta.
- Rechazo de ingesta sin `raw_payload_hash`.
- Registro obligatorio de `ingest_id`.

### 7.2 Propiedades
- Monotonicidad: el nÃºmero de registros solo crece.
- Idempotencia: mismo input â‡’ misma decisiÃ³n.
- No colapso temporal: timestamps distintos permanecen distintos.

### 7.3 SistÃ©micas
- Reintentos masivos (simulaciÃ³n de fallos de red).
- Ingesta fuera de orden temporal.
- Backfill histÃ³rico (meses) sin alterar registros previos.
- CaÃ­da parcial del adapter y recuperaciÃ³n.

---

## Criterios de AceptaciÃ³n

Este RFC se considera cumplido cuando:
1. La ingesta es estrictamente append-only.
2. El payload crudo se preserva Ã­ntegro y referenciable.
3. Toda ingesta produce un `IngestRecord` verificable.
4. Las decisiones de idempotencia quedan registradas.
5. No existe ruta de borrado o sobrescritura lÃ³gica.

---

## Assumptions

- El volumen de datos crecerÃ¡ indefinidamente; la verdad no expira.
- El costo de almacenamiento es menor que el costo de perder evidencia.
- Las fuentes pueden fallar, mentir o retrasarse; Tenon registra, no juzga en ingesta.
