# RFC-09 — IMMUTABLE_LEDGER_WORM
**Sistema:** Tenon — Sistema de Verdad Financiera Operativa y Conciliación Multisistema  
**Estado:** DRAFT  
**Relación:** Depende de RFC-00_MANIFEST, RFC-01_CANONICAL_EVENT, RFC-01A_CANONICAL_IDS,
RFC-02_INGEST_APPEND_ONLY, RFC-03_NORMALIZATION_RULES, RFC-04_CORRELATION_ENGINE,
RFC-05_MONEY_STATE_MACHINE, RFC-06_DISCREPANCY_TAXONOMY, RFC-07_CAUSALITY_MODEL,
RFC-08_EVENT_SOURCING_EVIDENCE

---

## Propósito

Definir el **ledger inmutable tipo WORM (Write Once, Read Many)** como sustrato probatorio
para la evidencia de Tenon, garantizando:
- no repudio,
- inalterabilidad verificable,
- reconstrucción histórica confiable,
- defensa legal y auditorí­a forense.

Este RFC fija **propiedades**, no una tecnologí­a especí­fica.

---

## No-Goals

- Elegir proveedor o tecnologí­a concreta (S3 Object Lock, HDFS WORM, blockchain, etc.).
- Optimizar costos o latencia.
- Exponer APIs de consulta.
- Ejecutar polí­ticas de retención especí­ficas por jurisdicción.
- Reemplazar sistemas regulatorios existentes.

---

## Invariantes

### 3.1 Inmutabilidad verificable
- Una vez escrito, un registro **no puede ser modificado ni eliminado** dentro de su periodo de retención.
- Cualquier intento de mutación debe ser **detectable**.

### 3.2 Append-only fí­sico
- El ledger solo acepta **append**.
- No existen operaciones UPDATE/DELETE ni “compaction destructiva”.

### 3.3 Identidad y direccionamiento estable
- Cada entrada del ledger tiene un **identificador estable** y direccionable.
- Las referencias (`raw_pointer`, `payload_ref`) deben resolverse de forma determinista.

### 3.4 Integridad criptográfica
- Cada entrada incluye **hash criptográfico** del contenido.
- Las entradas forman una **cadena de integridad** (hash encadenado o estructura equivalente).

### 3.5 Separación de control
- Ningíºn componente de Tenon puede:
  - borrar,
  - truncar,
  - reescribir
  el ledger una vez sellado.
- Las llaves/roles de escritura y lectura están separados.

---

## Contratos (conceptuales)

### 4.1 LedgerEntry

Cada entrada WORM contiene:

- `ledger_entry_id`
- `entry_type` (RAW_PAYLOAD | EVIDENCE_EVENT | DERIVED_ARTIFACT | OTHER)
- `content_hash`
- `content_pointer` (ubicación fí­sica)
- `schema_version`
- `previous_entry_hash` (para encadenamiento)
- `writer_identity`
- `written_at`
- `retention_policy_id`

---

### 4.2 RetentionPolicy (referencial)

- `retention_policy_id`
- `retention_period`
- `legal_basis` (AUDIT | CONTRACT | REGULATORY | INTERNAL)
- `immutable_until`

> La polí­tica se **referencia**; el enforcement fí­sico se valida externamente.

---

## Flujo de escritura (alto nivel)

1. Producción de evidencia (`EvidenceEvent`, crudo, artefactos).
2. Cálculo de hash criptográfico.
3. Escritura append-only en ledger WORM.
4. Encadenamiento con entrada previa.
5. Verificación de persistencia.
6. Emisión de referencia estable (`content_pointer`).

---

## Threat Model

### 6.1 Amenazas
- **Borrado retroactivo** para ocultar evidencia.
- **Reescritura parcial** (bit rot, corrupción silenciosa).
- **Acceso privilegiado indebido**.
- **Ataques de sustitución** (reemplazar contenido por otro con mismo nombre).
- **Dependencia de snapshots no inmutables**.

### 6.2 Controles exigidos
- WORM enforceable por infraestructura.
- Hash criptográfico + cadena de integridad.
- Verificación periódica de integridad.
- Separación de roles (write/read/admin).
- Auditorí­a externa del ledger.

---

## Pruebas

### 7.1 Unitarias
- Escritura íºnica por `ledger_entry_id`.
- Rechazo de escrituras mutables.
- Validación de hash al leer.

### 7.2 Propiedades
- Inmutabilidad: una entrada no cambia entre lecturas.
- Integridad: alteración â‡’ hash inválido.
- Monotonicidad: el ledger solo crece.

### 7.3 Sistémicas
- Simulación de intento de borrado/modificación.
- Verificación de cadena completa de hashes.
- Recuperación tras fallo parcial.
- Auditorí­a cruzada (re-cálculo independiente de hashes).

---

## Criterios de Aceptación

Este RFC se considera cumplido cuando:
1. Existe un ledger WORM con append-only fí­sico.
2. Toda evidencia crí­tica se escribe en el ledger.
3. La integridad es verificable criptográficamente.
4. No existe ruta técnica de borrado o reescritura.
5. El ledger soporta defensa legal y auditorí­a externa.

---

## Assumptions

- La infraestructura WORM puede ser auditada externamente.
- La latencia adicional es aceptable para evidencia.
- La inmutabilidad es prioritaria sobre conveniencia operativa.
