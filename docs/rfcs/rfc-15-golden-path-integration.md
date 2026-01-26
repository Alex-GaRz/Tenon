# RFC-15 â€” Golden Path Integration & End-to-End Testing (DRAFT)

## PropÃ³sito

Definir el **Golden Path institucional** de TENON y la **suite de pruebas End-to-End (E2E)** que valida, de forma **caja negra**, que el sistema completo preserva **integridad, trazabilidad y determinismo** desde la entrada por API hasta la detecciÃ³n final de riesgo.

Este RFC convierte la arquitectura en un **sistema demostrable**, no solo correcto por diseÃ±o.

---

## No-Goals

Este RFC **NO**:

* Introduce nuevas reglas de negocio.
* Ajusta lÃ³gica interna de correlaciÃ³n, estados o riesgo.
* Define infraestructura de despliegue.
* Define persistencia fÃ­sica.
* Optimiza performance tÃ©cnica fuera de SLOs explÃ­citos.

---

## Invariantes (No negociables)

1. **Integridad End-to-End**

   * Todo evento ingresado debe ser:

     * rastreable,
     * persistido,
     * correlacionado,
     * observable.
   * No existen â€œsaltos invisiblesâ€.

2. **Caja Negra**

   * Las pruebas E2E **no acceden** a `core/`.
   * Solo interactÃºan vÃ­a Runtime API (RFC-14).

3. **Determinismo Reproducible**

   * Mismo input + mismas versiones â‡’ mismo resultado observable.
   * Cualquier variaciÃ³n debe explicarse por versiÃ³n.

4. **Latencia Observable**

   * El tiempo de residencia (dwell time) en cada etapa es medible.
   * No existen â€œzonas oscurasâ€.

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

* RFC-01 â†’ RFC-13
* Versionado y compatibilidad por RFC-12

---

## DefiniciÃ³n del Golden Path

### Flujo CanÃ³nico

```
API Ingest
  â†“
Canonical Event Validation (RFC-01 / 01A)
  â†“
Raw Payload Persistence (RFC-02 / RFC-08)
  â†“
Normalization (RFC-03)
  â†“
Correlation Engine (RFC-04)
  â†“
Money State Machine (RFC-05)
  â†“
State Persistence (RFC-08 / RFC-09)
  â†“
Discrepancy Detection (RFC-06)
  â†“
Causality Attribution (RFC-07)
  â†“
Risk Evaluation (RFC-13)
```

Cada transiciÃ³n:

* deja evidencia,
* registra timestamps,
* es auditable.

---

## DiseÃ±o TÃ©cnico â€” Pruebas E2E

### Cliente de Pruebas Externo

* Proceso independiente del sistema TENON.
* Consume Ãºnicamente:

  * Runtime API (RFC-14).
* Sin acceso a DB, colas o core.

---

### Escenario CanÃ³nico de ValidaciÃ³n

**Caso base: conciliaciÃ³n parcial**

* InyecciÃ³n:

  * 100 eventos de pago
  * 98 con correlaciÃ³n completa
  * 2 con discrepancia esperada
* CaracterÃ­sticas:

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
* TipologÃ­a correcta (RFC-06).
* Causalidad explÃ­cita (RFC-07).
* Riesgo agregado coherente (RFC-13).

---

## Latencia & Observabilidad

### MÃ©tricas Institucionales

Por evento:

| Etapa            | MÃ©trica           |
| ---------------- | ----------------- |
| Ingest           | accepted_at       |
| CanonicalizaciÃ³n | canonicalized_at  |
| NormalizaciÃ³n    | normalized_at     |
| CorrelaciÃ³n      | correlated_at     |
| Estado           | state_resolved_at |
| Riesgo           | risk_emitted_at   |

> No son mÃ©tricas tÃ©cnicas: son **evidencia de flujo**.

---

## SLOs (Service Level Objectives)

* **Core processing**

  * p99 < 200 ms por evento (sin I/O externo)
* **Golden Path completo**

  * p95 < X segundos (configurable por entorno)

El incumplimiento:

* no rompe el sistema,
* **sÃ­ eleva riesgo operativo**.

---

## Manejo de Fallos en E2E

| Escenario        | Resultado Esperado          |
| ---------------- | --------------------------- |
| Evento invÃ¡lido  | Rechazo explÃ­cito           |
| Evento duplicado | Evidencia de idempotencia   |
| Eventos tardÃ­os  | Estado degradado, no error  |
| SaturaciÃ³n       | Backpressure observable     |
| Fallo parcial    | RecuperaciÃ³n sin corrupciÃ³n |

---

## Threat Model

### Riesgos

* Falsos positivos E2E
* Tests frÃ¡giles dependientes de timing

### Abusos

* Pruebas que â€œconocenâ€ el core
* Validaciones laxas

### Fallos SistÃ©micos

* Resultados no deterministas
* Estados colgantes

**Mitigaciones**

* OrÃ¡culos explÃ­citos
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

### SistÃ©micas

* Golden Path completo
* Escenarios degradados
* Replays completos

### Forenses

* ReconstrucciÃ³n del flujo completo
* VerificaciÃ³n de timestamps y hashes

---

## Criterios de AceptaciÃ³n

* Golden Path documentado y cerrado
* Suite E2E ejecutable en CI
* Resultados deterministas
* Discrepancias exactamente explicadas
* Riesgo coherente con seÃ±ales RFC-13

---

## Assumptions

* Runtime API existe y es estable (RFC-14)
* Persistencia garantiza durabilidad lÃ³gica
* Infraestructura soporta pruebas repetibles

---
