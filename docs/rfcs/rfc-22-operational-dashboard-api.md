# RFC-22 â€” Operational Dashboard API (DRAFT)

## PropÃ³sito

Proveer una **API especializada de visualizaciÃ³n operativa y ejecutiva** que expone el **estado financiero y tÃ©cnico institucional** de TENON de forma:

* **solo lectura**,
* **pre-agregada**,
* **determinista**,
* y **alineada con evidencia**,

para ser consumida por herramientas **low-code / BI** (Retool, Grafana, Streamlit) sin acceder al Core ni a datos crudos.

---

## No-Goals

Este RFC **NO**:

* Modifica datos, reglas o estados.
* Expone eventos crudos o millones de registros.
* Reemplaza sistemas BI corporativos.
* Introduce mÃ©tricas tÃ©cnicas (CPU, RAM, QPS).
* Define frontend o UX.

---

## Invariantes (No negociables)

1. **Solo Lectura**

   * NingÃºn endpoint permite mutaciÃ³n.
   * Prohibidos POST/PUT/PATCH/DELETE.

2. **AgregaciÃ³n Institucional**

   * Respuestas **pre-agregadas** y acotadas.
   * Nunca dumps de datos crudos.

3. **Coherencia con Evidencia**

   * Toda mÃ©trica se deriva de:

     * estados,
     * discrepancias,
     * riesgo,
     * evidencia persistida.
   * No inferencias â€œen tiempo realâ€ sin respaldo.

4. **Determinismo**

   * Mismo rango temporal + misma versiÃ³n â‡’ mismo resultado.

5. **Aislamiento del Core**

   * La API consume **read models**.
   * No accede a lÃ³gica core ni escribe en persistencia.

---

## Contratos Impactados

* `contracts/risk/v1/*`
* `contracts/discrepancy/v1/*`
* `contracts/money_state/v1/*`
* `contracts/causality/v1/*`

Gobernados por:

* RFC-12 (versionado)
* RFC-13 (seÃ±ales de riesgo)

---

## DiseÃ±o TÃ©cnico

### Estilo de API

* **REST**
* **OpenAPI 3.1**
* Versionado explÃ­cito: `/v1/dashboard/*`
* JSON estrictamente tipado

### AutenticaciÃ³n

* Hereda mecanismos de RFC-14:

  * `X-API-KEY`
  * mTLS (si aplica)
* Scopes **read-only** dedicados a dashboard.

---

## Read Models (Vista de Lectura)

* Construidos a partir de:

  * PostgreSQL (hot data agregada)
  * snapshots derivados (no crudos)
* ActualizaciÃ³n:

  * incremental
  * determinista
* Sin joins complejos en tiempo de request.

---

## Endpoints CanÃ³nicos

### `GET /v1/dashboard/risk-matrix`

**PropÃ³sito**
Exponer la **matriz de calor de riesgo institucional**.

**Contenido**

* Riesgo por:

  * tipo,
  * severidad,
  * antigÃ¼edad,
  * impacto econÃ³mico.

**Fuente**

* SeÃ±ales RFC-13 agregadas.

---

### `GET /v1/dashboard/flow-lineage/{id}`

**PropÃ³sito**
Visualizar la **trazabilidad completa** de un flujo de dinero especÃ­fico.

**Contenido**

* Grafo de MoneyFlow:

  * nodos (eventos)
  * aristas (correlaciones)
* Estados histÃ³ricos
* Evidencia asociada (referencias, no payloads)

**GarantÃ­a**

* La vista es una **proyecciÃ³n**, no el core.

---

### `GET /v1/dashboard/discrepancy-trend`

**PropÃ³sito**
Mostrar la **evoluciÃ³n temporal de discrepancias**.

**Agregaciones**

* Por:

  * tipo (RFC-06)
  * severidad
  * ventana temporal
* Histogramas y series.

---

## Manejo de Errores

| Escenario            | Respuesta       |
| -------------------- | --------------- |
| Auth invÃ¡lida        | 401 / 403       |
| ParÃ¡metros invÃ¡lidos | 400             |
| Datos no disponibles | 404             |
| Fallo interno        | 500 (capturado) |

* Nunca stacktraces.
* Nunca respuestas parciales silenciosas.

---

## Threat Model

### Riesgos

* Uso del dashboard como API operativa
* ExposiciÃ³n excesiva de datos

### Abusos

* Scraping agresivo
* Inferencia indirecta de datos sensibles

### Fallos SistÃ©micos

* Read models desfasados
* Agregaciones inconsistentes

**Mitigaciones**

* Rate limiting
* TTL explÃ­cito en agregaciones
* Versionado de vistas

---

## Pruebas

### Unitarias

* ValidaciÃ³n de contratos OpenAPI
* AutorizaciÃ³n read-only

### Propiedades

* Determinismo de agregaciones
* Inmutabilidad de vistas histÃ³ricas

### SistÃ©micas

* Consistencia con RFC-13
* Coherencia riesgo â†” discrepancias

### Forenses

* Trazabilidad desde vista â†’ evidencia
* Reproducibilidad por replay

---

## Criterios de AceptaciÃ³n

* API solo lectura certificada
* NingÃºn acceso a datos crudos
* Agregaciones estables y deterministas
* Integrable sin backend custom
* Coherente con riesgo institucional

---

## Assumptions

* Persistencia hÃ­brida operativa (RFC-17)
* Runtime estable (RFC-14)
* SeÃ±ales de riesgo activas (RFC-13)

---
