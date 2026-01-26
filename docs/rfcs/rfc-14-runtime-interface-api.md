# RFC-14 — Runtime Interface & API Gateway (DRAFT)

## Propósito

Definir la **interfaz de tiempo de ejecución** que expone el núcleo TENON como un **servicio web institucional**, transformando la librería `core/` en una **API consumible, segura y determinista**, sin introducir estado, lógica de negocio adicional ni acoplamientos no contractuales.

Este RFC establece **cómo se ejecuta TENON en producción**, **cómo se accede**, **cómo falla** y **cómo se gobierna el flujo de tráfico**.

---

## No-Goals

Este RFC **NO**:

* Define lógica de negocio financiera.
* Introduce reglas nuevas de ingestión, normalización, correlación o riesgo.
* Implementa dashboards, UI o visualización.
* Persiste estado en memoria del servidor.
* Define despliegue (ver RFC-16).
* Define almacenamiento (ver RFC-17).

---

## Invariantes (No negociables)

1. **Contract-First**

   * La API se define **únicamente** mediante una especificación **OpenAPI 3.1**.
   * El runtime **no acepta** requests fuera del contrato versionado.

2. **Statelessness**

   * El servidor API **no mantiene estado en memoria** entre requests.
   * Todo estado vive en colas, persistencia o servicios externos.

3. **Aislamiento de Fallos**

   * Cualquier excepción no controlada del Core:

     * se captura,
     * se registra como evento técnico,
     * retorna `HTTP 500`,
     * **no detiene** el proceso del servidor.

4. **Backpressure Institucional**

   * El runtime debe **rechazar tráfico** cuando el sistema interno esté degradado.
   * Nunca se acepta tráfico que no pueda procesarse con garantías.

5. **Observabilidad de Riesgo**

   * El runtime **no expone métricas técnicas** (CPU, RAM).
   * Solo expone **estado institucional** (RFC-13).

---

## Contratos Impactados

* `contracts/ingest/v1/*`
* `contracts/discrepancy/v1/*`
* `contracts/risk/v1/*`
* `contracts/adapter/v1/*`
  (Versiones **append-only**, gobernadas por RFC-12)

---

## Diseño Técnico

### Estilo de API

* **REST**
* **OpenAPI 3.1**
* Versionado explícito en path: `/v1/*`
* JSON estricto (no esquemas implícitos)

### Framework de Runtime

* **FastAPI (Python)** o equivalente asíncrono de alto rendimiento.
* Ejecución **async-first**.
* El runtime actúa como **Boundary Layer**, no como Core.

---

### Autenticación & Seguridad

#### Modos soportados

1. **X-API-KEY**

   * Header obligatorio: `X-API-KEY`
   * Asociado a:

     * tenant_id
     * límites de rate
     * scopes permitidos
   * Rotación obligatoria.

2. **mTLS (Mutual TLS)**

   * **Obligatorio** para integraciones bancarias directas.
   * Validación de certificado cliente en handshake.
   * El certificado identifica al tenant.

> El runtime **no mezcla** mTLS y API Key en un mismo request.

---

### Control de Flujo

* **Rate limiting por tenant**
* **Cola interna con umbral**

  * Si ocupación > 80% → rechazar con `HTTP 429`
* **Backpressure explícito**

  * Nunca se aceptan requests “a ciegas”

---

## Endpoints Canónicos

### `POST /v1/ingest`

**Propósito**
Entrada oficial de eventos crudos al sistema.

**Comportamiento**

* Validación **síncrona** de:

  * JSON válido
  * esquema contractual
* Procesamiento **asíncrono**.
* Nunca bloquea esperando correlación o estados.

**Respuesta**

* `202 Accepted`
* Payload:

  ```json
  {
    "ingest_id": "<uuid>",
    "status": "ACCEPTED"
  }
  ```

**Errores**

* `400` → esquema inválido
* `401/403` → auth
* `429` → backpressure
* `500` → fallo interno capturado

---

### `GET /v1/discrepancies/{id}`

**Propósito**
Consulta diagnóstica de una discrepancia específica.

**Garantías**

* Solo lectura.
* Retorna explicación, evidencia y causalidad (RFC-06/07).

---

### `GET /v1/risk/status`

**Propósito**
Exponer el **semáforo institucional de riesgo**.

**Fuente**

* Señales derivadas exclusivamente de RFC-13.

**Respuesta**

* Estado agregado:

  * GREEN / YELLOW / RED
* Breakdown por tipo de riesgo.

---

## Manejo de Errores

| Tipo              | Acción            |
| ----------------- | ----------------- |
| Error de contrato | `400`             |
| Auth              | `401 / 403`       |
| Saturación        | `429`             |
| Pánico Core       | `500` (capturado) |

* **Nunca** se exponen stacktraces.
* Todo error genera:

  * evento técnico
  * correlación con request_id

---

## Threat Model

### Riesgos

* Inyección de payloads inválidos
* Flood de tráfico malicioso
* Reintentos no idempotentes

### Abusos

* Replays masivos
* API key compartida

### Fallos Sistémicos

* Saturación de colas
* Caída parcial de persistencia

**Mitigaciones**

* Idempotency Guardian (RFC-10)
* Backpressure
* Circuit-breaker lógico (no técnico)

---

## Pruebas

### Unitarias

* Validación de contratos OpenAPI
* Auth & rate limiting

### Propiedades

* Statelessness (no memoria cruzada)
* Determinismo de respuestas

### Sistémicas

* Ingest → persistencia → consulta
* Backpressure bajo carga

### Forenses

* Registro de fallos sin pérdida de evidencia

---

## Criterios de Aceptación

* OpenAPI 3.1 publicado y versionado
* Ningún endpoint fuera del contrato
* Runtime sobrevive a pánicos del core
* Backpressure probado bajo estrés
* Sin estado en memoria

---

## Assumptions

* El Core TENON es **puro y determinista**
* Persistencia y despliegue se resuelven en RFC-16 / RFC-17
* El frontend consume esta API indirectamente (RFC-22)

---
