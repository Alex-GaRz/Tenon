# RFC-08 — EVENT_SOURCING_EVIDENCE
**Sistema:** Tenon — Sistema de Verdad Financiera Operativa y Conciliación Multisistema  
**Estado:** DRAFT  
**Relación:** Depende de RFC-00_MANIFEST, RFC-01_CANONICAL_EVENT, RFC-01A_CANONICAL_IDS,
RFC-02_INGEST_APPEND_ONLY, RFC-03_NORMALIZATION_RULES, RFC-04_CORRELATION_ENGINE,
RFC-05_MONEY_STATE_MACHINE, RFC-06_DISCREPANCY_TAXONOMY, RFC-07_CAUSALITY_MODEL

---

## 1) Propósito

Establecer **event sourcing como mecanismo probatorio** (no solo arquitectónico) para que Tenon
pueda **reconstruir cualquier estado pasado** a partir de hechos inmutables y **demostrar**
cómo y por qué se llegó a una conclusión operativa.

Este RFC define la “máquina del tiempo” del sistema.

---

## 2) No-Goals

- Definir el ledger WORM físico o firma criptográfica (RFC-09).
- Optimizar almacenamiento, compresión o retención.
- Exponer APIs de consulta o reporting.
- Reemplazar data lakes o warehouses.
- Ejecutar acciones a partir de eventos.

---

## 3) Invariantes

### 3.1 Hechos sobre estados
- El sistema persiste **eventos** que explican cambios, no snapshots mutables.
- Estados y diagnósticos son **derivados** y reproducibles desde eventos.

### 3.2 Inmutabilidad lógica
- Un evento emitido **no se modifica**.
- Correcciones se expresan como **nuevos eventos** que referencian hechos previos.

### 3.3 Orden y causalidad explícitos
- El orden de eventos se registra explícitamente.
- La causalidad entre eventos queda representada por referencias, no por suposición temporal.

### 3.4 Replay determinista
- Replay completo con la misma versión del sistema ⇒ mismos resultados.
- Replay con versiones distintas ⇒ resultados distintos **explicables por versión**.

---

## 4) Contratos (conceptuales)

### 4.1 EvidenceEvent (evento de evidencia)

Todo evento persistido en el store de evidencia contiene:

- `evidence_event_id`
- `event_type` (INGEST_RECORDED | CANONICAL_EVENT_EMITTED | CORRELATION_LINK_ADDED |
  MONEY_STATE_EVALUATED | DISCREPANCY_DETECTED | CAUSALITY_ATTRIBUTED | OTHER)
- `subject_id` (event_id, flow_id, discrepancy_id, etc.)
- `payload_ref` (referencia a datos estructurados/crudos)
- `caused_by[]` (lista de evidence_event_id previos)
- `schema_version`
- `producer` (componente/servicio)
- `produced_at`

> `EvidenceEvent` es el **hecho mínimo** que permite reconstrucción completa.

---

### 4.2 EvidenceLog (secuencia)

- Secuencia append-only de `EvidenceEvent`.
- Orden total por `produced_at` + secuencia interna.
- Nunca se trunca ni se reordena.

---

## 5) Flujo de event sourcing (alto nivel)

1. Ocurre una observación o decisión (ingesta, normalización, correlación, etc.).
2. Se emite un `EvidenceEvent` describiendo **qué pasó** y **por qué**.
3. El evento se persiste append-only en el `EvidenceLog`.
4. Estados, discrepancias y causalidades se derivan **exclusivamente** del replay del log.

---

## 6) Threat Model

### 6.1 Amenazas
- **Snapshots engañosos** que no permiten reconstrucción.
- **Reescritura de historia** para “arreglar” auditorías.
- **Eventos implícitos** no registrados (decisiones invisibles).
- **Dependencia temporal** sin causalidad explícita.

### 6.2 Controles exigidos
- Prohibición de snapshots como fuente de verdad.
- Persistencia de todos los eventos decisionales.
- Referencias causales explícitas (`caused_by`).
- Versionado de esquemas de eventos.

---

## 7) Pruebas

### 7.1 Unitarias
- Todo cambio de estado emite `EvidenceEvent`.
- Eventos no mutables tras persistencia.
- Referencias causales válidas.

### 7.2 Propiedades
- Replay completo ⇒ mismo resultado (misma versión).
- Monotonicidad: el log solo crece.
- No dependencia de estado externo.

### 7.3 Sistémicas
- Replay desde cero con meses de historia.
- Replay parcial hasta un punto en el tiempo.
- Cambio de versión y explicación de divergencias.
- Pérdida de stores derivados (reconstrucción total desde evidencia).

---

## 8) Criterios de Aceptación

Este RFC se considera cumplido cuando:
1. El sistema puede reconstruir cualquier diagnóstico pasado solo desde eventos.
2. No existen decisiones “fuera del log”.
3. El orden y la causalidad de eventos son explícitos.
4. Replay es determinista y versionado.
5. La evidencia producida es defendible ante auditoría.

---

## 9) Assumptions

- El costo de almacenar eventos es menor que el costo de perder historia.
- La defensa legal requiere “película”, no reportes estáticos.
- La complejidad del replay es aceptable a cambio de verdad reproducible.
