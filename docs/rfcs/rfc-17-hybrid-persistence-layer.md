# RFC-17 â€” Hybrid Persistence Layer (PostgreSQL + WORM Object Storage) (DRAFT)

## PropÃ³sito

Definir la **capa de persistencia hÃ­brida** de TENON que reemplaza almacenes en memoria por una arquitectura **durable, auditable y legalmente defendible**, combinando:

* **SQL transaccional (hot data)** para metadatos, estados y consultas operativas.
* **Object Storage WORM (cold data)** para evidencia cruda inmutable.

Este RFC establece **quÃ© se guarda**, **dÃ³nde**, **con quÃ© garantÃ­as**, y **cÃ³mo se accede**, manteniendo al **Core completamente agnÃ³stico** del backend fÃ­sico.

---

## No-Goals

Este RFC **NO**:

* Introduce lÃ³gica de negocio.
* Define endpoints de API (RFC-14).
* Define dashboards o visualizaciÃ³n (RFC-22).
* Define infraestructura de despliegue (RFC-16).
* Optimiza costos de almacenamiento.

---

## Invariantes (No negociables)

1. **Integridad Referencial**

   * Todo registro SQL que referencia evidencia cruda **debe** apuntar a un objeto existente y verificable en Object Storage.

2. **WORM FÃ­sico**

   * La evidencia cruda es **inalterable**:

     * sin overwrite,
     * sin delete,
     * sin truncado,
       durante el perÃ­odo de retenciÃ³n legal.

3. **Append-Only SemÃ¡ntico**

   * NingÃºn evento, estado o evidencia se modifica.
   * Las correcciones son **nuevos eventos** (RFC-08/09).

4. **Aislamiento Transaccional Fuerte**

   * Las mutaciones de estado usan **Serializable isolation**.
   * No se permiten lecturas sucias ni escrituras fantasma.

5. **Core AgnÃ³stico**

   * El Core interactÃºa solo vÃ­a **interfaces** (ports).
   * No conoce SQL, buckets ni SDKs cloud.

---

## Contratos Impactados

* `contracts/ingest/v1/*`
* `contracts/evidence/v1/*`
* `contracts/money_state/v1/*`
* `contracts/discrepancy/v1/*`
* `contracts/risk/v1/*`

Todos:

* append-only,
* versionados,
* gobernados por RFC-12.

---

## DiseÃ±o TÃ©cnico

## Arquitectura LÃ³gica

```
Core (Pure Logic)
  â†“
Persistence Interfaces (Ports)
  â†“
--------------------------------
| SQL Adapter | Object Adapter |
--------------------------------
  â†“                 â†“
PostgreSQL        WORM Storage
```

---

## Hot Data â€” PostgreSQL

### Alcance

* Metadatos de eventos
* Estados del dinero
* Discrepancias
* SeÃ±ales de riesgo
* Ãndices de bÃºsqueda

### Propiedades TÃ©cnicas

* **Isolation level**: `SERIALIZABLE`
* **Transacciones cortas**
* **Fail-fast** ante conflictos

### Esquema Operacional

* Tablas **append-only**
* Sin `UPDATE`
* Sin `DELETE`
* Versionado explÃ­cito

### Particionamiento

* Por tiempo (`YYYY_MM`)
* Evita full scans
* Facilita retenciÃ³n lÃ³gica

---

## Cold Data â€” Object Storage WORM

### Alcance

* RawPayload original
* Evidencia forense
* Snapshots histÃ³ricos exportables

### Requisitos

* **Object Lock habilitado**
* **Compliance Mode**
* RetenciÃ³n mÃ­nima: **7 aÃ±os**

### Naming Determinista

```
s3://<bucket>/v1/YYYY/MM/DD/{raw_payload_hash}.json
```

Propiedades:

* Path predecible
* Idempotente
* Verificable por hash

---

## Consistencia entre SQL y Object Storage

### Flujo de Escritura

1. Persistir objeto crudo en WORM
2. Verificar Ã©xito y hash
3. Insertar metadatos en SQL (transacciÃ³n)
4. Commit

**Regla**

* Si el objeto no existe â†’ SQL **no** comitea.

---

## Interfaces de Persistencia (Ports)

### AppendOnlyStore (Ejemplo Conceptual)

* `append(record)`
* `scan(criteria)`
* `count()`

**GarantÃ­as**

* No mutaciÃ³n
* Orden estable
* Idempotencia por hash (RFC-10)

Los adaptadores:

* SQLAdapter
* ObjectStorageAdapter

envuelven la lÃ³gica fÃ­sica.

---

## Manejo de Concurrencia

* Locks a nivel lÃ³gico (no mutex globales)
* Conflictos â‡’ retry explÃ­cito
* Nunca â€œlast write winsâ€

---

## RetenciÃ³n & Legal Hold

* RetenciÃ³n WORM:

  * aplicada en bucket
  * no en aplicaciÃ³n
* Legal hold:

  * externo al Core
  * verificable por auditorÃ­a

---

## Threat Model

### Riesgos

* Inconsistencia SQL â†” Object
* Bypass de WORM
* CorrupciÃ³n silenciosa

### Abusos

* Intentos de overwrite
* EliminaciÃ³n temprana

### Fallos SistÃ©micos

* CaÃ­da parcial de storage
* Latencia elevada en escritura

**Mitigaciones**

* Escritura en dos fases
* Hash como verdad
* Fallo explÃ­cito y visible

---

## Pruebas

### Unitarias

* Adaptadores SQL y Object
* ValidaciÃ³n de paths deterministas

### Propiedades

* Append-only estricto
* Integridad referencial
* Aislamiento Serializable

### SistÃ©micas

* Ingesta real â†’ persistencia hÃ­brida
* Replays completos desde evidencia

### Forenses

* VerificaciÃ³n WORM
* RecomputaciÃ³n de hashes
* ReconstrucciÃ³n histÃ³rica completa

---

## Criterios de AceptaciÃ³n

* NingÃºn UPDATE/DELETE posible
* WORM fÃ­sico verificable
* Core sin dependencias de DB
* Replay completo desde cold data
* Transacciones serializables comprobadas

---

## Assumptions

* Object Storage soporta Object Lock real
* PostgreSQL configurado para Serializable
* Infraestructura proveÃ­da por RFC-16

---
