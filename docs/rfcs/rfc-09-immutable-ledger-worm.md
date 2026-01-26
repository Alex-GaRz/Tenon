# RFC-09 â€” IMMUTABLE_LEDGER_WORM
**Sistema:** Tenon â€” Sistema de Verdad Financiera Operativa y ConciliaciÃ³n Multisistema  
**Estado:** DRAFT  
**RelaciÃ³n:** Depende de RFC-00_MANIFEST, RFC-01_CANONICAL_EVENT, RFC-01A_CANONICAL_IDS,
RFC-02_INGEST_APPEND_ONLY, RFC-03_NORMALIZATION_RULES, RFC-04_CORRELATION_ENGINE,
RFC-05_MONEY_STATE_MACHINE, RFC-06_DISCREPANCY_TAXONOMY, RFC-07_CAUSALITY_MODEL,
RFC-08_EVENT_SOURCING_EVIDENCE

---

## PropÃ³sito

Definir el **ledger inmutable tipo WORM (Write Once, Read Many)** como sustrato probatorio
para la evidencia de Tenon, garantizando:
- no repudio,
- inalterabilidad verificable,
- reconstrucciÃ³n histÃ³rica confiable,
- defensa legal y auditorÃ­a forense.

Este RFC fija **propiedades**, no una tecnologÃ­a especÃ­fica.

---

## No-Goals

- Elegir proveedor o tecnologÃ­a concreta (S3 Object Lock, HDFS WORM, blockchain, etc.).
- Optimizar costos o latencia.
- Exponer APIs de consulta.
- Ejecutar polÃ­ticas de retenciÃ³n especÃ­ficas por jurisdicciÃ³n.
- Reemplazar sistemas regulatorios existentes.

---

## Invariantes

### 3.1 Inmutabilidad verificable
- Una vez escrito, un registro **no puede ser modificado ni eliminado** dentro de su periodo de retenciÃ³n.
- Cualquier intento de mutaciÃ³n debe ser **detectable**.

### 3.2 Append-only fÃ­sico
- El ledger solo acepta **append**.
- No existen operaciones UPDATE/DELETE ni â€œcompaction destructivaâ€.

### 3.3 Identidad y direccionamiento estable
- Cada entrada del ledger tiene un **identificador estable** y direccionable.
- Las referencias (`raw_pointer`, `payload_ref`) deben resolverse de forma determinista.

### 3.4 Integridad criptogrÃ¡fica
- Cada entrada incluye **hash criptogrÃ¡fico** del contenido.
- Las entradas forman una **cadena de integridad** (hash encadenado o estructura equivalente).

### 3.5 SeparaciÃ³n de control
- NingÃºn componente de Tenon puede:
  - borrar,
  - truncar,
  - reescribir
  el ledger una vez sellado.
- Las llaves/roles de escritura y lectura estÃ¡n separados.

---

## Contratos (conceptuales)

### 4.1 LedgerEntry

Cada entrada WORM contiene:

- `ledger_entry_id`
- `entry_type` (RAW_PAYLOAD | EVIDENCE_EVENT | DERIVED_ARTIFACT | OTHER)
- `content_hash`
- `content_pointer` (ubicaciÃ³n fÃ­sica)
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

> La polÃ­tica se **referencia**; el enforcement fÃ­sico se valida externamente.

---

## Flujo de escritura (alto nivel)

1. ProducciÃ³n de evidencia (`EvidenceEvent`, crudo, artefactos).
2. CÃ¡lculo de hash criptogrÃ¡fico.
3. Escritura append-only en ledger WORM.
4. Encadenamiento con entrada previa.
5. VerificaciÃ³n de persistencia.
6. EmisiÃ³n de referencia estable (`content_pointer`).

---

## Threat Model

### 6.1 Amenazas
- **Borrado retroactivo** para ocultar evidencia.
- **Reescritura parcial** (bit rot, corrupciÃ³n silenciosa).
- **Acceso privilegiado indebido**.
- **Ataques de sustituciÃ³n** (reemplazar contenido por otro con mismo nombre).
- **Dependencia de snapshots no inmutables**.

### 6.2 Controles exigidos
- WORM enforceable por infraestructura.
- Hash criptogrÃ¡fico + cadena de integridad.
- VerificaciÃ³n periÃ³dica de integridad.
- SeparaciÃ³n de roles (write/read/admin).
- AuditorÃ­a externa del ledger.

---

## Pruebas

### 7.1 Unitarias
- Escritura Ãºnica por `ledger_entry_id`.
- Rechazo de escrituras mutables.
- ValidaciÃ³n de hash al leer.

### 7.2 Propiedades
- Inmutabilidad: una entrada no cambia entre lecturas.
- Integridad: alteraciÃ³n â‡’ hash invÃ¡lido.
- Monotonicidad: el ledger solo crece.

### 7.3 SistÃ©micas
- SimulaciÃ³n de intento de borrado/modificaciÃ³n.
- VerificaciÃ³n de cadena completa de hashes.
- RecuperaciÃ³n tras fallo parcial.
- AuditorÃ­a cruzada (re-cÃ¡lculo independiente de hashes).

---

## Criterios de AceptaciÃ³n

Este RFC se considera cumplido cuando:
1. Existe un ledger WORM con append-only fÃ­sico.
2. Toda evidencia crÃ­tica se escribe en el ledger.
3. La integridad es verificable criptogrÃ¡ficamente.
4. No existe ruta tÃ©cnica de borrado o reescritura.
5. El ledger soporta defensa legal y auditorÃ­a externa.

---

## Assumptions

- La infraestructura WORM puede ser auditada externamente.
- La latencia adicional es aceptable para evidencia.
- La inmutabilidad es prioritaria sobre conveniencia operativa.
