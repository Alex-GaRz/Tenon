# RFC-16 — Infrastructure Deployment & Infrastructure as Code (IaC) (DRAFT)

## Propósito

Definir la **arquitectura de despliegue inmutable** y la **infraestructura como código (IaC)** que ejecuta TENON como **infraestructura financiera crí­tica**, garantizando:

* reproducibilidad entre entornos,
* cero acceso humano a producción,
* control total de cambios,
* y aislamiento operacional coherente con RFC-01 a RFC-15.

Este RFC responde **cómo corre TENON**, **dónde corre** y **cómo se gobiernan los cambios**, sin introducir lógica de negocio.

---

## No-Goals

Este RFC **NO**:

* Define endpoints, contratos o comportamiento del Runtime (RFC-14).
* Define persistencia lógica o WORM (RFC-17).
* Define dashboards o visualización (RFC-22).
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

3. **Separación Build vs Run**

   * Build-time â‰  Runtime.
   * Ningíºn secreto se inyecta en build.

4. **Despliegue Declarativo**

   * El estado deseado se define en IaC.
   * El runtime converge a ese estado o falla explí­citamente.

5. **Observabilidad de Vida**

   * El sistema debe poder declarar:

     * “estoy vivo”
     * “estoy listo”
   * sin exponer métricas técnicas.

---

## Contratos Impactados

* Ninguno funcional directo.
  Impacto **operacional** sobre:
* RFC-14 (Runtime API)
* RFC-15 (E2E ejecutable)
* RFC-13 (Risk Observability)

---

## Diseí±o Técnico

### Contenerización

#### Docker

* **Multi-stage build**

  * Stage 1: build (dependencias, compilación)
  * Stage 2: runtime mí­nimo
* Imagen base:

  * **Distroless** (o equivalente)
* Usuario no-root obligatorio.

**Propiedades**

* Tamaí±o mí­nimo
* Superficie de ataque reducida
* Sin shells interactivos

---

### Orquestación

#### Kubernetes (K8s)

* Cada componente corre como:

  * `Deployment` o `StatefulSet` (segíºn rol)
* Réplicas mí­nimas > 1 para runtime API.

---

### Probes Institucionales

#### Liveness Probe

* Endpoint: `/healthz`
* Verifica:

  * proceso activo
* **No** valida dependencias externas.

#### Readiness Probe

* Verifica:

  * conexión a base de datos
  * acceso a object storage
* Si falla:

  * el pod **no recibe tráfico**.

---

## Gestión de Configuración y Secretos

### Secret Management

* **Prohibido**:

  * secretos en código
  * secretos en variables de entorno en texto plano
* **Permitido**:

  * Vault
  * Cloud Secret Manager
  * Inyección en runtime ví­a volumen o sidecar

---

## Infrastructure as Code (IaC)

### Herramienta

* **Terraform** o **Pulumi**
* Estado remoto obligatorio.

### Recursos Gestionados

* VPC / Networking
* Bases de datos
* Buckets de Object Storage
* Clíºster Kubernetes
* IAM / Service Accounts

### Principios

* Un entorno = un stack
* Cambios auditables por PR
* Plan â†’ Review â†’ Apply

---

## Aislamiento por Entorno

| Entorno | Propósito               |
| ------- | ----------------------- |
| Dev     | Desarrollo activo       |
| Stage   | Validación E2E          |
| Prod    | Operación institucional |

**Regla**

* Misma imagen
* Distinta configuración y secretos

---

## Flujo de Despliegue

1. Commit aprobado en Git
2. CI construye imagen
3. Imagen firmada y versionada
4. IaC actualiza estado deseado
5. K8s converge
6. Probes validan
7. Tráfico habilitado

---

## Manejo de Fallos

| Escenario         | Comportamiento        |
| ----------------- | --------------------- |
| Imagen inválida   | Rollback automático   |
| Dependencia caí­da | Readiness = false     |
| Saturación        | Backpressure (RFC-14) |
| Config inválida   | Pod no entra en Ready |

Nunca:

* silencios
* degradación oculta

---

## Threat Model

### Riesgos

* Drift entre entornos
* Cambios manuales fuera de IaC

### Abusos

* Acceso humano “temporal”
* Hotfixes directos

### Fallos Sistémicos

* Clíºster inconsistente
* Secretos expuestos

**Mitigaciones**

* Branch protection
* Auditorí­a IaC
* Prohibición explí­cita de SSH

---

## Pruebas

### Unitarias

* Validación de manifiestos
* Lint de IaC

### Propiedades

* Inmutabilidad de imágenes
* Reproducibilidad de despliegue

### Sistémicas

* Despliegue limpio en entorno vací­o
* Rollback controlado

### Forenses

* Auditorí­a de cambios infra
* Trazabilidad Git â†’ Runtime

---

## Criterios de Aceptación

* Imagen idéntica en todos los entornos
* Ningíºn acceso humano a Prod
* IaC íºnico mecanismo de cambio
* Probes funcionales y verificables
* Rollback probado

---

## Assumptions

* Cloud provider soporta K8s y Object Storage
* El Core es determinista
* Persistencia lógica se define en RFC-17

---
