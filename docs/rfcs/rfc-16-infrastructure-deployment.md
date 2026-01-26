# RFC-16 â€” Infrastructure Deployment & Infrastructure as Code (IaC) (DRAFT)

## PropÃ³sito

Definir la **arquitectura de despliegue inmutable** y la **infraestructura como cÃ³digo (IaC)** que ejecuta TENON como **infraestructura financiera crÃ­tica**, garantizando:

* reproducibilidad entre entornos,
* cero acceso humano a producciÃ³n,
* control total de cambios,
* y aislamiento operacional coherente con RFC-01 a RFC-15.

Este RFC responde **cÃ³mo corre TENON**, **dÃ³nde corre** y **cÃ³mo se gobiernan los cambios**, sin introducir lÃ³gica de negocio.

---

## No-Goals

Este RFC **NO**:

* Define endpoints, contratos o comportamiento del Runtime (RFC-14).
* Define persistencia lÃ³gica o WORM (RFC-17).
* Define dashboards o visualizaciÃ³n (RFC-22).
* Optimiza costos cloud.
* Permite accesos manuales a nodos.

---

## Invariantes

1. **Inmutabilidad de Artefactos**

   * Un artefacto construido (imagen de contenedor) **no cambia** entre Dev / Stage / Prod.
   * Cambios â‡’ nueva imagen + nuevo despliegue.

2. **Cero Acceso Humano**

   * Prohibido SSH / RDP / exec manual en nodos productivos.
   * Todo cambio pasa por:

     * Git
     * CI
     * IaC
     * despliegue controlado

3. **SeparaciÃ³n Build vs Run**

   * Build-time â‰  Runtime.
   * NingÃºn secreto se inyecta en build.

4. **Despliegue Declarativo**

   * El estado deseado se define en IaC.
   * El runtime converge a ese estado o falla explÃ­citamente.

5. **Observabilidad de Vida**

   * El sistema debe poder declarar:

     * â€œestoy vivoâ€
     * â€œestoy listoâ€
   * sin exponer mÃ©tricas tÃ©cnicas.

---

## Contratos Impactados

* Ninguno funcional directo.
  Impacto **operacional** sobre:
* RFC-14 (Runtime API)
* RFC-15 (E2E ejecutable)
* RFC-13 (Risk Observability)

---

## DiseÃ±o TÃ©cnico

### ContenerizaciÃ³n

#### Docker

* **Multi-stage build**

  * Stage 1: build (dependencias, compilaciÃ³n)
  * Stage 2: runtime mÃ­nimo
* Imagen base:

  * **Distroless** (o equivalente)
* Usuario no-root obligatorio.

**Propiedades**

* TamaÃ±o mÃ­nimo
* Superficie de ataque reducida
* Sin shells interactivos

---

### OrquestaciÃ³n

#### Kubernetes (K8s)

* Cada componente corre como:

  * `Deployment` o `StatefulSet` (segÃºn rol)
* RÃ©plicas mÃ­nimas > 1 para runtime API.

---

### Probes Institucionales

#### Liveness Probe

* Endpoint: `/healthz`
* Verifica:

  * proceso activo
* **No** valida dependencias externas.

#### Readiness Probe

* Verifica:

  * conexiÃ³n a base de datos
  * acceso a object storage
* Si falla:

  * el pod **no recibe trÃ¡fico**.

---

## GestiÃ³n de ConfiguraciÃ³n y Secretos

### Secret Management

* **Prohibido**:

  * secretos en cÃ³digo
  * secretos en variables de entorno en texto plano
* **Permitido**:

  * Vault
  * Cloud Secret Manager
  * InyecciÃ³n en runtime vÃ­a volumen o sidecar

---

## Infrastructure as Code (IaC)

### Herramienta

* **Terraform** o **Pulumi**
* Estado remoto obligatorio.

### Recursos Gestionados

* VPC / Networking
* Bases de datos
* Buckets de Object Storage
* ClÃºster Kubernetes
* IAM / Service Accounts

### Principios

* Un entorno = un stack
* Cambios auditables por PR
* Plan â†’ Review â†’ Apply

---

## Aislamiento por Entorno

| Entorno | PropÃ³sito               |
| ------- | ----------------------- |
| Dev     | Desarrollo activo       |
| Stage   | ValidaciÃ³n E2E          |
| Prod    | OperaciÃ³n institucional |

**Regla**

* Misma imagen
* Distinta configuraciÃ³n y secretos

---

## Flujo de Despliegue

1. Commit aprobado en Git
2. CI construye imagen
3. Imagen firmada y versionada
4. IaC actualiza estado deseado
5. K8s converge
6. Probes validan
7. TrÃ¡fico habilitado

---

## Manejo de Fallos

| Escenario         | Comportamiento        |
| ----------------- | --------------------- |
| Imagen invÃ¡lida   | Rollback automÃ¡tico   |
| Dependencia caÃ­da | Readiness = false     |
| SaturaciÃ³n        | Backpressure (RFC-14) |
| Config invÃ¡lida   | Pod no entra en Ready |

Nunca:

* silencios
* degradaciÃ³n oculta

---

## Threat Model

### Riesgos

* Drift entre entornos
* Cambios manuales fuera de IaC

### Abusos

* Acceso humano â€œtemporalâ€
* Hotfixes directos

### Fallos SistÃ©micos

* ClÃºster inconsistente
* Secretos expuestos

**Mitigaciones**

* Branch protection
* AuditorÃ­a IaC
* ProhibiciÃ³n explÃ­cita de SSH

---

## Pruebas

### Unitarias

* ValidaciÃ³n de manifiestos
* Lint de IaC

### Propiedades

* Inmutabilidad de imÃ¡genes
* Reproducibilidad de despliegue

### SistÃ©micas

* Despliegue limpio en entorno vacÃ­o
* Rollback controlado

### Forenses

* AuditorÃ­a de cambios infra
* Trazabilidad Git â†’ Runtime

---

## Criterios de AceptaciÃ³n

* Imagen idÃ©ntica en todos los entornos
* NingÃºn acceso humano a Prod
* IaC Ãºnico mecanismo de cambio
* Probes funcionales y verificables
* Rollback probado

---

## Assumptions

* Cloud provider soporta K8s y Object Storage
* El Core es determinista
* Persistencia lÃ³gica se define en RFC-17

---
