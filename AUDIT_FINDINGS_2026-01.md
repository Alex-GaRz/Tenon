# Tenon — AUDIT_FINDINGS_2026-01
**Fecha:** 2026-01  
**Tipo:** Auditoría externa de RFCs (contenido y aplicabilidad)  
**Alcance auditado:** RFC-00 a RFC-13 (arquitectura institucional de verdad operativa)  
**Resultado:** RFCs excelentes; 3 puntos de atención para implementación (no invalidantes)

---

## 0) Resumen ejecutivo

La auditoría externa identifica tres tensiones reales y esperables en un sistema de evidencia defendible:

1) **Costo de almacenamiento y latencia** por preservación de crudo + event sourcing + WORM.  
2) **Dificultad operativa** del estado `AMBIGUOUS` para usuarios que desean “cerrar el mes”.  
3) **Dependencia crítica de criptografía**: RFC-09 menciona aseguramiento criptográfico, pero la **gestión de claves** debe tratarse como disciplina operacional separada (SecOps).

**Decisión institucional:**  
- No se modifican RFCs del core por estos hallazgos.  
- Se activan acciones de producto (modelo económico), UX (resolución de ambigüedad) y planeación de seguridad operacional (RFC futuro).

---

## 1) Hallazgo A — Costo de almacenamiento y latencia (Trade-off)

### Descripción del hallazgo
La combinación de:
- RFC-02 (Raw Preservation)
- RFC-08 (Event Sourcing)
- RFC-09 (WORM / Ledger inmutable)

incrementará sustancialmente el volumen total (redundancia deliberada y probatoria), con impacto potencial en costos y latencia de operación.

### RFCs impactados
- RFC-02_INGEST_APPEND_ONLY
- RFC-08_EVENT_SOURCING_EVIDENCE
- RFC-09_IMMUTABLE_LEDGER_WORM

### Evaluación institucional
Este trade-off es **intencional**: la evidencia defendible requiere preservación + reconstrucción + inmutabilidad verificable. Optimizar almacenamiento sacrificando evidencia es inaceptable.

### Clasificación
**No Change Required (RFCs)**

### Acción recomendada (fuera del core)
**Modelo de negocio y límites de observación**:
- Definir pricing por **“Activos Bajo Observación”** o equivalente (scope cuantificable).
- Definir políticas de retención por clase (activa vs archivo frío) **sin eliminar evidencia**.
- Explicitar en el contrato comercial que la redundancia es parte del valor probatorio.

### Riesgo si se ignora
- Subfinanciar el costo probatorio → presión por “optimizar” evidencia → degradación legal/auditabilidad.

---

## 2) Hallazgo B — Complejidad operativa del estado AMBIGUOUS

### Descripción del hallazgo
RFC-05 permite estados `AMBIGUOUS`. Esto es técnicamente correcto (honestidad epistemológica), pero puede ser operativamente difícil para equipos que solo quieren una respuesta binaria para cierre de mes.

### RFCs impactados
- RFC-05_MONEY_STATE_MACHINE
- (dependencias) RFC-04_CORRELATION_ENGINE, RFC-06_DISCREPANCY_TAXONOMY, RFC-07_CAUSALITY_MODEL

### Evaluación institucional
Eliminar `AMBIGUOUS` en el core equivaldría a forzar verdad sin evidencia. El core debe conservar ambigüedad como estado válido.

### Clasificación
**Deferred to UI Layer**

### Acción recomendada (capa de interfaz / workflow)
Diseñar una experiencia que:
- muestre “qué evidencia falta” y “qué evidencia existe” por flujo,
- guíe resolución mediante **aportación de evidencia** o **acciones registradas** (append-only),
- evite cualquier mecanismo de “edición” o “override” que mute historia,
- use causalidad (RFC-07) como guía, no como sentencia.

### Riesgo si se ignora
- Usuarios intentarán “cerrar” ambigüedad con mutaciones manuales → corrupción del núcleo o pérdida de credibilidad.

---

## 3) Hallazgo C — Dependencia de criptografía y gestión de claves

### Descripción del hallazgo
RFC-09 menciona aseguramiento criptográfico (hashing/encadenamiento), pero no especifica la **gestión operacional de claves** (rotación, custodia, revocación, HSM/KMS, respaldo, control de acceso).

### RFCs impactados
- RFC-09_IMMUTABLE_LEDGER_WORM
- (operacionalmente ligado) RFC-08_EVENT_SOURCING_EVIDENCE, RFC-10_IDEMPOTENCY_GUARDIAN, RFC-12_CHANGE_CONTROL

### Evaluación institucional
La criptografía sin gobierno de claves es un punto único de fallo. Debe abordarse como disciplina SecOps separada del diseño del ledger.

### Clasificación
**Requires Future RFC**

### Acción recomendada (planeación)
Reservar RFC futuro para SecOps de claves, sin modificar verdad histórica:
- RFC-14_SECURITY_KEY_MANAGEMENT (futuro, post-core, operacional)

### Riesgo si se ignora
- Compromiso o pérdida de llaves → cuestionamiento de integridad/no repudio o incapacidad de verificar evidencia.

---

## 4) Decisiones y cierre

### Decisiones
- Los RFCs actuales se mantienen.
- Se documenta que:
  - Hallazgo A = monetización y límites de observación (producto / contrato)
  - Hallazgo B = UX y workflow de resolución (capa UI)
  - Hallazgo C = RFC futuro SecOps de llaves (planeación)

### Próximos pasos aprobados
1) (Hecho en este documento) Registro formal de hallazgos.  
2) Bloquear espacio de RFC futuro: RFC-14_SECURITY_KEY_MANAGEMENT (sin escribirlo aún).  
3) En etapa de UI: definir mecanismos de “resolución” sin mutación histórica.

---
