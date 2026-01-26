# RFC-15 — Golden Path Integration & End-to-End Testing (DRAFT)

## Propósito

Definir el **Golden Path institucional** de TENON y la **suite de pruebas End-to-End (E2E)** que valida, de forma **caja negra**, que el sistema completo preserva **integridad, trazabilidad y determinismo** desde la entrada por API hasta la detección final de riesgo.

Este RFC convierte la arquitectura en un **sistema demostrable**, no solo correcto por diseño.

---

## No-Goals

Este RFC **NO**:

* Introduce nuevas reglas de negocio.
* Ajusta lógica interna de correlación, estados o riesgo.
* Define infraestructura de despliegue.
* Define persistencia física.
* Optimiza performance técnica fuera de SLOs explícitos.

---

## Invariantes (No negociables)

1. **Integridad End-to-End**

   * Todo evento ingresado debe ser:

     * rastreable,
     * persistido,
     * correlacionado,
     * observable.
   * No existen “saltos invisibles”.

2. **Caja Negra**

   * Las pruebas E2E **no acceden** a `core/`.
   * Solo interactúan vía Runtime API (RFC-14).

3. **Determinismo Reproducible**

   * Mismo input + mismas versiones ⇒ mismo resultado observable.
   * Cualquier variación debe explicarse por versión.

4. **Latencia Observable**

   * El tiempo de residencia (dwell time) en cada etapa es medible.
   * No existen “zonas oscuras”.

5. **Resultados Finitos**

   * El sistema **siempre converge** a un estado observable:

     * discrepancia,
     * estado final,
     * riesgo.

---

## Contratos Impactados

* `contracts/ingest/v1/*`
* `contracts/canonical_event/v1/*`
* `contracts/correlation/v1/*`
* `contracts/money_state/v1/*`
* `contracts/discrepancy/v1/*`
* `contracts/risk/v1/*`

Todos gobernados por:

* RFC-01 → RFC-13
* Versionado y compatibilidad por RFC-12

---

## Definición del Golden Path

### Flujo Canónico

```
API Ingest
  ↓
Canonical Event Validation (RFC-01 / 01A)
  ↓
Raw Payload Persistence (RFC-02 / RFC-08)
  ↓
Normalization (RFC-03)
  ↓
Correlation Engine (RFC-04)
  ↓
Money State Machine (RFC-05)
  ↓
State Persistence (RFC-08 / RFC-09)
  ↓
Discrepancy Detection (RFC-06)
  ↓
Causality Attribution (RFC-07)
  ↓
Risk Evaluation (RFC-13)
```

Cada transición:

* deja evidencia,
* registra timestamps,
* es auditable.

---

## Diseño Técnico — Pruebas E2E

### Cliente de Pruebas Externo

* Proceso independiente del sistema TENON.
* Consume únicamente:

  * Runtime API (RFC-14).
* Sin acceso a DB, colas o core.

---

### Escenario Canónico de Validación

**Caso base: conciliación parcial**

* Inyección:

  * 100 eventos de pago
  * 98 con correlación completa
  * 2 con discrepancia esperada
* Características:

  * eventos fuera de orden
  * timestamps reales
  * referencias externas duplicadas controladas

**Flujo**

1. POST `/v1/ingest` (batch controlado)
2. Espera `T` segundos (configurable)
3. GET `/v1/discrepancies`
4. GET `/v1/risk/status`

**Validaciones**

* Existen **exactamente** 2 discrepancias.
* Tipología correcta (RFC-06).
* Causalidad explícita (RFC-07).
* Riesgo agregado coherente (RFC-13).

---

## Latencia & Observabilidad

### Métricas Institucionales

Por evento:

| Etapa            | Métrica           |
| ---------------- | ----------------- |
| Ingest           | accepted_at       |
| Canonicalización | canonicalized_at  |
| Normalización    | normalized_at     |
| Correlación      | correlated_at     |
| Estado           | state_resolved_at |
| Riesgo           | risk_emitted_at   |

> No son métricas técnicas: son **evidencia de flujo**.

---

## SLOs (Service Level Objectives)

* **Core processing**

  * p99 < 200 ms por evento (sin I/O externo)
* **Golden Path completo**

  * p95 < X segundos (configurable por entorno)

El incumplimiento:

* no rompe el sistema,
* **sí eleva riesgo operativo**.

---

## Manejo de Fallos en E2E

| Escenario        | Resultado Esperado          |
| ---------------- | --------------------------- |
| Evento inválido  | Rechazo explícito           |
| Evento duplicado | Evidencia de idempotencia   |
| Eventos tardíos  | Estado degradado, no error  |
| Saturación       | Backpressure observable     |
| Fallo parcial    | Recuperación sin corrupción |

---

## Threat Model

### Riesgos

* Falsos positivos E2E
* Tests frágiles dependientes de timing

### Abusos

* Pruebas que “conocen” el core
* Validaciones laxas

### Fallos Sistémicos

* Resultados no deterministas
* Estados colgantes

**Mitigaciones**

* Oráculos explícitos
* Ventanas temporales definidas
* Replays controlados

---

## Pruebas

### Unitarias

* Cliente E2E
* Validadores de respuesta

### Propiedades

* Determinismo del resultado final
* Inmutabilidad del historial

### Sistémicas

* Golden Path completo
* Escenarios degradados
* Replays completos

### Forenses

* Reconstrucción del flujo completo
* Verificación de timestamps y hashes

---

## Criterios de Aceptación

* Golden Path documentado y cerrado
* Suite E2E ejecutable en CI
* Resultados deterministas
* Discrepancias exactamente explicadas
* Riesgo coherente con señales RFC-13

---

## Assumptions

* Runtime API existe y es estable (RFC-14)
* Persistencia garantiza durabilidad lógica
* Infraestructura soporta pruebas repetibles

---
