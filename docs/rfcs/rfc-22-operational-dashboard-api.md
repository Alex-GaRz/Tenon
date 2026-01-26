# RFC-22 — Operational Dashboard API (DRAFT)

## Propósito

Proveer una **API especializada de visualización operativa y ejecutiva** que expone el **estado financiero y técnico institucional** de TENON de forma:

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
* Introduce métricas técnicas (CPU, RAM, QPS).
* Define frontend o UX.

---

## Invariantes (No negociables)

1. **Solo Lectura**

   * Ningíºn endpoint permite mutación.
   * Prohibidos POST/PUT/PATCH/DELETE.

2. **Agregación Institucional**

   * Respuestas **pre-agregadas** y acotadas.
   * Nunca dumps de datos crudos.

3. **Coherencia con Evidencia**

   * Toda métrica se deriva de:

     * estados,
     * discrepancias,
     * riesgo,
     * evidencia persistida.
   * No inferencias “en tiempo real” sin respaldo.

4. **Determinismo**

   * Mismo rango temporal + misma versión â‡’ mismo resultado.

5. **Aislamiento del Core**

   * La API consume **read models**.
   * No accede a lógica core ni escribe en persistencia.

---

## Contratos Impactados

* `contracts/risk/v1/*`
* `contracts/discrepancy/v1/*`
* `contracts/money_state/v1/*`
* `contracts/causality/v1/*`

Gobernados por:

* RFC-12 (versionado)
* RFC-13 (seí±ales de riesgo)

---

## Diseí±o Técnico

### Estilo de API

* **REST**
* **OpenAPI 3.1**
* Versionado explí­cito: `/v1/dashboard/*`
* JSON estrictamente tipado

### Autenticación

* Hereda mecanismos de RFC-14:

  * `X-API-KEY`
  * mTLS (si aplica)
* Scopes **read-only** dedicados a dashboard.

---

## Read Models (Vista de Lectura)

* Construidos a partir de:

  * PostgreSQL (hot data agregada)
  * snapshots derivados (no crudos)
* Actualización:

  * incremental
  * determinista
* Sin joins complejos en tiempo de request.

---

## Endpoints Canónicos

### `GET /v1/dashboard/risk-matrix`

**Propósito**
Exponer la **matriz de calor de riesgo institucional**.

**Contenido**

* Riesgo por:

  * tipo,
  * severidad,
  * antigí¼edad,
  * impacto económico.

**Fuente**

* Seí±ales RFC-13 agregadas.

---

### `GET /v1/dashboard/flow-lineage/{id}`

**Propósito**
Visualizar la **trazabilidad completa** de un flujo de dinero especí­fico.

**Contenido**

* Grafo de MoneyFlow:

  * nodos (eventos)
  * aristas (correlaciones)
* Estados históricos
* Evidencia asociada (referencias, no payloads)

**Garantí­a**

* La vista es una **proyección**, no el core.

---

### `GET /v1/dashboard/discrepancy-trend`

**Propósito**
Mostrar la **evolución temporal de discrepancias**.

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
| Auth inválida        | 401 / 403       |
| Parámetros inválidos | 400             |
| Datos no disponibles | 404             |
| Fallo interno        | 500 (capturado) |

* Nunca stacktraces.
* Nunca respuestas parciales silenciosas.

---

## Threat Model

### Riesgos

* Uso del dashboard como API operativa
* Exposición excesiva de datos

### Abusos

* Scraping agresivo
* Inferencia indirecta de datos sensibles

### Fallos Sistémicos

* Read models desfasados
* Agregaciones inconsistentes

**Mitigaciones**

* Rate limiting
* TTL explí­cito en agregaciones
* Versionado de vistas

---

## Pruebas

### Unitarias

* Validación de contratos OpenAPI
* Autorización read-only

### Propiedades

* Determinismo de agregaciones
* Inmutabilidad de vistas históricas

### Sistémicas

* Consistencia con RFC-13
* Coherencia riesgo â†” discrepancias

### Forenses

* Trazabilidad desde vista â†’ evidencia
* Reproducibilidad por replay

---

## Criterios de Aceptación

* API solo lectura certificada
* Ningíºn acceso a datos crudos
* Agregaciones estables y deterministas
* Integrable sin backend custom
* Coherente con riesgo institucional

---

## Assumptions

* Persistencia hí­brida operativa (RFC-17)
* Runtime estable (RFC-14)
* Seí±ales de riesgo activas (RFC-13)

---
