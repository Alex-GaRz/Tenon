# RFC-08 â€” EVENT_SOURCING_EVIDENCE
**Sistema:** Tenon â€” Sistema de Verdad Financiera Operativa y ConciliaciÃ³n Multisistema  
**Estado:** DRAFT  
**RelaciÃ³n:** Depende de RFC-00_MANIFEST, RFC-01_CANONICAL_EVENT, RFC-01A_CANONICAL_IDS,
RFC-02_INGEST_APPEND_ONLY, RFC-03_NORMALIZATION_RULES, RFC-04_CORRELATION_ENGINE,
RFC-05_MONEY_STATE_MACHINE, RFC-06_DISCREPANCY_TAXONOMY, RFC-07_CAUSALITY_MODEL

---

## PropÃ³sito

Establecer **event sourcing como mecanismo probatorio** (no solo arquitectÃ³nico) para que Tenon
pueda **reconstruir cualquier estado pasado** a partir de hechos inmutables y **demostrar**
cÃ³mo y por quÃ© se llegÃ³ a una conclusiÃ³n operativa.

Este RFC define la â€œmÃ¡quina del tiempoâ€ del sistema.

---

## No-Goals

- Definir el ledger WORM fÃ­sico o firma criptogrÃ¡fica (RFC-09).
- Optimizar almacenamiento, compresiÃ³n o retenciÃ³n.
- Exponer APIs de consulta o reporting.
- Reemplazar data lakes o warehouses.
- Ejecutar acciones a partir de eventos.

---

## Invariantes

### 3.1 Hechos sobre estados
- El sistema persiste **eventos** que explican cambios, no snapshots mutables.
- Estados y diagnÃ³sticos son **derivados** y reproducibles desde eventos.

### 3.2 Inmutabilidad lÃ³gica
- Un evento emitido **no se modifica**.
- Correcciones se expresan como **nuevos eventos** que referencian hechos previos.

### 3.3 Orden y causalidad explÃ­citos
- El orden de eventos se registra explÃ­citamente.
- La causalidad entre eventos queda representada por referencias, no por suposiciÃ³n temporal.

### 3.4 Replay determinista
- Replay completo con la misma versiÃ³n del sistema â‡’ mismos resultados.
- Replay con versiones distintas â‡’ resultados distintos **explicables por versiÃ³n**.

---

## Contratos (conceptuales)

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

> `EvidenceEvent` es el **hecho mÃ­nimo** que permite reconstrucciÃ³n completa.

---

### 4.2 EvidenceLog (secuencia)

- Secuencia append-only de `EvidenceEvent`.
- Orden total por `produced_at` + secuencia interna.
- Nunca se trunca ni se reordena.

---

## Flujo de event sourcing (alto nivel)

1. Ocurre una observaciÃ³n o decisiÃ³n (ingesta, normalizaciÃ³n, correlaciÃ³n, etc.).
2. Se emite un `EvidenceEvent` describiendo **quÃ© pasÃ³** y **por quÃ©**.
3. El evento se persiste append-only en el `EvidenceLog`.
4. Estados, discrepancias y causalidades se derivan **exclusivamente** del replay del log.

---

## Threat Model

### 6.1 Amenazas
- **Snapshots engaÃ±osos** que no permiten reconstrucciÃ³n.
- **Reescritura de historia** para â€œarreglarâ€ auditorÃ­as.
- **Eventos implÃ­citos** no registrados (decisiones invisibles).
- **Dependencia temporal** sin causalidad explÃ­cita.

### 6.2 Controles exigidos
- ProhibiciÃ³n de snapshots como fuente de verdad.
- Persistencia de todos los eventos decisionales.
- Referencias causales explÃ­citas (`caused_by`).
- Versionado de esquemas de eventos.

---

## Pruebas

### 7.1 Unitarias
- Todo cambio de estado emite `EvidenceEvent`.
- Eventos no mutables tras persistencia.
- Referencias causales vÃ¡lidas.

### 7.2 Propiedades
- Replay completo â‡’ mismo resultado (misma versiÃ³n).
- Monotonicidad: el log solo crece.
- No dependencia de estado externo.

### 7.3 SistÃ©micas
- Replay desde cero con meses de historia.
- Replay parcial hasta un punto en el tiempo.
- Cambio de versiÃ³n y explicaciÃ³n de divergencias.
- PÃ©rdida de stores derivados (reconstrucciÃ³n total desde evidencia).

---

## Criterios de AceptaciÃ³n

Este RFC se considera cumplido cuando:
1. El sistema puede reconstruir cualquier diagnÃ³stico pasado solo desde eventos.
2. No existen decisiones â€œfuera del logâ€.
3. El orden y la causalidad de eventos son explÃ­citos.
4. Replay es determinista y versionado.
5. La evidencia producida es defendible ante auditorÃ­a.

---

## Assumptions

- El costo de almacenar eventos es menor que el costo de perder historia.
- La defensa legal requiere â€œpelÃ­culaâ€, no reportes estÃ¡ticos.
- La complejidad del replay es aceptable a cambio de verdad reproducible.
