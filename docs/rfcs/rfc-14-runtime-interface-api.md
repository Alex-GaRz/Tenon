# RFC-14 â€” Runtime Interface & API Gateway (DRAFT)

## PropÃ³sito

Definir la **interfaz de tiempo de ejecuciÃ³n** que expone el nÃºcleo TENON como un **servicio web institucional**, transformando la librerÃ­a `core/` en una **API consumible, segura y determinista**, sin introducir estado, lÃ³gica de negocio adicional ni acoplamientos no contractuales.

Este RFC establece **cÃ³mo se ejecuta TENON en producciÃ³n**, **cÃ³mo se accede**, **cÃ³mo falla** y **cÃ³mo se gobierna el flujo de trÃ¡fico**.

---

## No-Goals

Este RFC **NO**:

* Define lÃ³gica de negocio financiera.
* Introduce reglas nuevas de ingestiÃ³n, normalizaciÃ³n, correlaciÃ³n o riesgo.
* Implementa dashboards, UI o visualizaciÃ³n.
* Persiste estado en memoria del servidor.
* Define despliegue (ver RFC-16).
* Define almacenamiento (ver RFC-17).

---

## Invariantes

1. **Contract-First**

   * La API se define **Ãºnicamente** mediante una especificaciÃ³n **OpenAPI 3.1**.
   * El runtime **no acepta** requests fuera del contrato versionado.

2. **Statelessness**

   * El servidor API **no mantiene estado en memoria** entre requests.
   * Todo estado vive en colas, persistencia o servicios externos.

3. **Aislamiento de Fallos**

   * Cualquier excepciÃ³n no controlada del Core:

     * se captura,
     * se registra como evento tÃ©cnico,
     * retorna `HTTP 500`,
     * **no detiene** el proceso del servidor.

4. **Backpressure Institucional**

   * El runtime debe **rechazar trÃ¡fico** cuando el sistema interno estÃ© degradado.
   * Nunca se acepta trÃ¡fico que no pueda procesarse con garantÃ­as.

5. **Observabilidad de Riesgo**

   * El runtime **no expone mÃ©tricas tÃ©cnicas** (CPU, RAM).
   * Solo expone **estado institucional** (RFC-13).

---

## Contratos Impactados

* `contracts/ingest/v1/*`
* `contracts/discrepancy/v1/*`
* `contracts/risk/v1/*`
* `contracts/adapter/v1/*`
  (Versiones **append-only**, gobernadas por RFC-12)

---

## DiseÃ±o TÃ©cnico

### Estilo de API

* **REST**
* **OpenAPI 3.1**
* Versionado explÃ­cito en path: `/v1/*`
* JSON estricto (no esquemas implÃ­citos)

### Framework de Runtime

* **FastAPI (Python)** o equivalente asÃ­ncrono de alto rendimiento.
* EjecuciÃ³n **async-first**.
* El runtime actÃºa como **Boundary Layer**, no como Core.

---

### AutenticaciÃ³n & Seguridad

#### Modos soportados

1. **X-API-KEY**

   * Header obligatorio: `X-API-KEY`
   * Asociado a:

     * tenant_id
     * lÃ­mites de rate
     * scopes permitidos
   * RotaciÃ³n obligatoria.

2. **mTLS (Mutual TLS)**

   * **Obligatorio** para integraciones bancarias directas.
   * ValidaciÃ³n de certificado cliente en handshake.
   * El certificado identifica al tenant.

> El runtime **no mezcla** mTLS y API Key en un mismo request.

---

### Control de Flujo

* **Rate limiting por tenant**
* **Cola interna con umbral**

  * Si ocupaciÃ³n > 80% â†’ rechazar con `HTTP 429`
* **Backpressure explÃ­cito**

  * Nunca se aceptan requests â€œa ciegasâ€

---

## Endpoints CanÃ³nicos

### `POST /v1/ingest`

**PropÃ³sito**
Entrada oficial de eventos crudos al sistema.

**Comportamiento**

* ValidaciÃ³n **sÃ­ncrona** de:

  * JSON vÃ¡lido
  * esquema contractual
* Procesamiento **asÃ­ncrono**.
* Nunca bloquea esperando correlaciÃ³n o estados.

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

* `400` â†’ esquema invÃ¡lido
* `401/403` â†’ auth
* `429` â†’ backpressure
* `500` â†’ fallo interno capturado

---

### `GET /v1/discrepancies/{id}`

**PropÃ³sito**
Consulta diagnÃ³stica de una discrepancia especÃ­fica.

**GarantÃ­as**

* Solo lectura.
* Retorna explicaciÃ³n, evidencia y causalidad (RFC-06/07).

---

### `GET /v1/risk/status`

**PropÃ³sito**
Exponer el **semÃ¡foro institucional de riesgo**.

**Fuente**

* SeÃ±ales derivadas exclusivamente de RFC-13.

**Respuesta**

* Estado agregado:

  * GREEN / YELLOW / RED
* Breakdown por tipo de riesgo.

---

## Manejo de Errores

| Tipo              | AcciÃ³n            |
| ----------------- | ----------------- |
| Error de contrato | `400`             |
| Auth              | `401 / 403`       |
| SaturaciÃ³n        | `429`             |
| PÃ¡nico Core       | `500` (capturado) |

* **Nunca** se exponen stacktraces.
* Todo error genera:

  * evento tÃ©cnico
  * correlaciÃ³n con request_id

---

## Threat Model

### Riesgos

* InyecciÃ³n de payloads invÃ¡lidos
* Flood de trÃ¡fico malicioso
* Reintentos no idempotentes

### Abusos

* Replays masivos
* API key compartida

### Fallos SistÃ©micos

* SaturaciÃ³n de colas
* CaÃ­da parcial de persistencia

**Mitigaciones**

* Idempotency Guardian (RFC-10)
* Backpressure
* Circuit-breaker lÃ³gico (no tÃ©cnico)

---

## Pruebas

### Unitarias

* ValidaciÃ³n de contratos OpenAPI
* Auth & rate limiting

### Propiedades

* Statelessness (no memoria cruzada)
* Determinismo de respuestas

### SistÃ©micas

* Ingest â†’ persistencia â†’ consulta
* Backpressure bajo carga

### Forenses

* Registro de fallos sin pÃ©rdida de evidencia

---

## Criterios de AceptaciÃ³n

* OpenAPI 3.1 publicado y versionado
* NingÃºn endpoint fuera del contrato
* Runtime sobrevive a pÃ¡nicos del core
* Backpressure probado bajo estrÃ©s
* Sin estado en memoria

---

## Assumptions

* El Core TENON es **puro y determinista**
* Persistencia y despliegue se resuelven en RFC-16 / RFC-17
* El frontend consume esta API indirectamente (RFC-22)

---
