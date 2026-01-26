# RFC-17 — Hybrid Persistence Layer (PostgreSQL + WORM Object Storage) (DRAFT)

## Propósito

Definir la **capa de persistencia hí­brida** de TENON que reemplaza almacenes en memoria por una arquitectura **durable, auditable y legalmente defendible**, combinando:

* **SQL transaccional (hot data)** para metadatos, estados y consultas operativas.
* **Object Storage WORM (cold data)** para evidencia cruda inmutable.

Este RFC establece **qué se guarda**, **dónde**, **con qué garantí­as**, y **cómo se accede**, manteniendo al **Core completamente agnóstico** del backend fí­sico.

---

## No-Goals

Este RFC **NO**:

* Introduce lógica de negocio.
* Define endpoints de API (RFC-14).
* Define dashboards o visualización (RFC-22).
* Define infraestructura de despliegue (RFC-16).
* Optimiza costos de almacenamiento.

---

## Invariantes (No negociables)

1. **Integridad Referencial**

   * Todo registro SQL que referencia evidencia cruda **debe** apuntar a un objeto existente y verificable en Object Storage.

2. **WORM Fí­sico**

   * La evidencia cruda es **inalterable**:

     * sin overwrite,
     * sin delete,
     * sin truncado,
       durante el perí­odo de retención legal.

3. **Append-Only Semántico**

   * Ningíºn evento, estado o evidencia se modifica.
   * Las correcciones son **nuevos eventos** (RFC-08/09).

4. **Aislamiento Transaccional Fuerte**

   * Las mutaciones de estado usan **Serializable isolation**.
   * No se permiten lecturas sucias ni escrituras fantasma.

5. **Core Agnóstico**

   * El Core interactíºa solo ví­a **interfaces** (ports).
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

## Diseí±o Técnico

## Arquitectura Lógica

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

## Hot Data — PostgreSQL

### Alcance

* Metadatos de eventos
* Estados del dinero
* Discrepancias
* Seí±ales de riesgo
* índices de bíºsqueda

### Propiedades Técnicas

* **Isolation level**: `SERIALIZABLE`
* **Transacciones cortas**
* **Fail-fast** ante conflictos

### Esquema Operacional

* Tablas **append-only**
* Sin `UPDATE`
* Sin `DELETE`
* Versionado explí­cito

### Particionamiento

* Por tiempo (`YYYY_MM`)
* Evita full scans
* Facilita retención lógica

---

## Cold Data — Object Storage WORM

### Alcance

* RawPayload original
* Evidencia forense
* Snapshots históricos exportables

### Requisitos

* **Object Lock habilitado**
* **Compliance Mode**
* Retención mí­nima: **7 aí±os**

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
2. Verificar éxito y hash
3. Insertar metadatos en SQL (transacción)
4. Commit

**Regla**

* Si el objeto no existe â†’ SQL **no** comitea.

---

## Interfaces de Persistencia (Ports)

### AppendOnlyStore (Ejemplo Conceptual)

* `append(record)`
* `scan(criteria)`
* `count()`

**Garantí­as**

* No mutación
* Orden estable
* Idempotencia por hash (RFC-10)

Los adaptadores:

* SQLAdapter
* ObjectStorageAdapter

envuelven la lógica fí­sica.

---

## Manejo de Concurrencia

* Locks a nivel lógico (no mutex globales)
* Conflictos â‡’ retry explí­cito
* Nunca “last write wins”

---

## Retención & Legal Hold

* Retención WORM:

  * aplicada en bucket
  * no en aplicación
* Legal hold:

  * externo al Core
  * verificable por auditorí­a

---

## Threat Model

### Riesgos

* Inconsistencia SQL â†” Object
* Bypass de WORM
* Corrupción silenciosa

### Abusos

* Intentos de overwrite
* Eliminación temprana

### Fallos Sistémicos

* Caí­da parcial de storage
* Latencia elevada en escritura

**Mitigaciones**

* Escritura en dos fases
* Hash como verdad
* Fallo explí­cito y visible

---

## Pruebas

### Unitarias

* Adaptadores SQL y Object
* Validación de paths deterministas

### Propiedades

* Append-only estricto
* Integridad referencial
* Aislamiento Serializable

### Sistémicas

* Ingesta real â†’ persistencia hí­brida
* Replays completos desde evidencia

### Forenses

* Verificación WORM
* Recomputación de hashes
* Reconstrucción histórica completa

---

## Criterios de Aceptación

* Ningíºn UPDATE/DELETE posible
* WORM fí­sico verificable
* Core sin dependencias de DB
* Replay completo desde cold data
* Transacciones serializables comprobadas

---

## Assumptions

* Object Storage soporta Object Lock real
* PostgreSQL configurado para Serializable
* Infraestructura proveí­da por RFC-16

---
