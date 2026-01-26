# RFC-13 — RISK_OBSERVABILITY
**Sistema:** Tenon — Sistema de Verdad Financiera Operativa y Conciliación Multisistema  
**Estado:** DRAFT  
**Relación:** Depende de RFC-00_MANIFEST y de todos los RFCs funcionales previos (01–12)

---

## Propósito

Definir la **observabilidad institucional basada en riesgo** para gobernar Tenon como
infraestructura crí­tica viva, enfocada en **control y degradación de riesgo operativo**
—no en performance, throughput ni métricas vanity.

Esta capa permite:
- detectar degradaciones sistémicas antes de incidentes,
- priorizar intervención humana donde el riesgo lo exige,
- demostrar control continuo ante auditorí­a y comités de riesgo.

---

## No-Goals

- Métricas de performance (latencia, QPS, CPU).
- Observabilidad orientada a debugging técnico.
- Dashboards genéricos o “bonitos”.
- Alerting reactivo sin contexto institucional.
- Automatizar acciones correctivas.

---

## Invariantes

### 3.1 Riesgo sobre rendimiento
- Toda métrica debe mapear explí­citamente a **riesgo operativo, financiero o legal**.
- Métricas sin interpretación de riesgo están prohibidas.

### 3.2 Seí±ales derivadas, no crudas
- La observabilidad se construye sobre:
  - estados del dinero,
  - discrepancias,
  - causalidades,
  - idempotencia,
  - cambios de versión.
- No se basa directamente en eventos crudos.

### 3.3 Explicabilidad
- Toda alerta o indicador debe poder explicar:
  - qué cambió,
  - por qué es riesgoso,
  - qué evidencia lo sustenta.

### 3.4 No mutación
- La observabilidad **no altera** estados, eventos ni diagnósticos.
- Es estrictamente de lectura y agregación.

---

## Seí±ales institucionales (cerradas)

### 4.1 Riesgo de discrepancias
- Concentración de discrepancias `HIGH` por:
  - fuente,
  - tipo,
  - flujo.
- Tendencia temporal de discrepancias crí­ticas.
- Antigí¼edad promedio de discrepancias no resueltas.

### 4.2 Riesgo de correlación
- Degradación del `confidence_score` promedio.
- Aumento de correlaciones ambiguas por flujo.
- Crecimiento de `ORPHAN_EVENT`.

### 4.3 Riesgo de estados
- Acumulación de estados `AMBIGUOUS`, `UNKNOWN`, `IN_TRANSIT` fuera de SLA.
- Flujos “stale” (sin evolución pese a nueva evidencia).
- Divergencia entre estados esperados y observados.

### 4.4 Riesgo de idempotencia
- Incremento de `REJECT_DUPLICATE` o `FLAG_AMBIGUOUS`.
- Claves de idempotencia con colisiones recurrentes.
- Bypass o intentos fallidos del Guardian.

### 4.5 Riesgo de cambio
- Cambios recientes con impacto en:
  - correlación,
  - estados,
  - discrepancias.
- Versiones coexistentes con resultados divergentes.
- Incremento de discrepancias post-change.

### 4.6 Riesgo humano-operativo
- Sobreuso de intervención humana.
- Reapertura recurrente de discrepancias.
- Dependencia de overrides manuales.

---

## Contratos (conceptuales)

### 5.1 RiskSignal

- `risk_signal_id`
- `signal_type` (enum cerrado; ver sección 4)
- `scope` (GLOBAL | SOURCE | FLOW | COMPONENT)
- `severity_level` (LOW | MEDIUM | HIGH | CRITICAL)
- `supporting_metrics[]`
- `supporting_evidence[]`
- `explanation`
- `observed_at`
- `signal_version`

---

### 5.2 RiskAggregate

- `aggregate_id`
- `time_window`
- `risk_profile` (vector de seí±ales)
- `overall_risk_level`
- `drivers[]`
- `computed_at`
- `model_version`

---

## Umbrales institucionales

- Los umbrales:
  - son explí­citos,
  - versionados,
  - aprobados institucionalmente.
- Ejemplos:
  - >X% de flujos en `AMBIGUOUS` por >Y horas.
  - crecimiento anómalo (>ZÏƒ) de discrepancias crí­ticas.
  - degradación sostenida de correlación >N ventanas.

Los umbrales **no se auto-ajustan** sin cambio controlado (RFC-12).

---

## Alertas (no reactivas)

### 7.1 Principios
- Alertas indican **riesgo**, no “error”.
- Toda alerta incluye:
  - seí±al,
  - evidencia,
  - impacto potencial,
  - recomendación operativa.

### 7.2 Tipos
- **Early Warning** — degradación incipiente.
- **Risk Escalation** — riesgo material.
- **Institutional Breach** — violación de umbral crí­tico.

---

## Dashboards (criterios)

### 8.1 Ejecutivo
- Riesgo agregado del sistema.
- Top drivers de riesgo.
- Tendencias y comparativas pre/post cambio.
- No métricas técnicas.

### 8.2 Operativo
- Vistas por fuente / flujo.
- Backlog de discrepancias crí­ticas.
- Estados stale y ambigí¼edades.
- Evidencia navegable (“pelí­cula”).

---

## Threat Model

### 9.1 Amenazas
- **Ceguera institucional** (no ver riesgo emergente).
- **Ruido excesivo** que banaliza alertas.
- **Métricas vanity** que ocultan problemas reales.
- **Cambios sin monitoreo** de impacto.
- **Dependencia humana no detectada**.

### 9.2 Controles exigidos
- Seí±ales cerradas y versionadas.
- Evidencia obligatoria por seí±al.
- Umbrales explí­citos.
- Separación observación/acción.
- Auditorí­a de cambios en observabilidad.

---

## Pruebas

### 10.1 Unitarias
- Cálculo correcto de seí±ales.
- Severidad consistente con umbrales.
- Explicación no vací­a.

### 10.2 Propiedades
- Determinismo: mismo input â‡’ mismas seí±ales.
- No side-effects: lectura pura.
- Estabilidad temporal: replay reproduce seí±ales históricas.

### 10.3 Sistémicas
- Simulación de degradación progresiva.
- Incidente histórico reproducido.
- Cambios de versión con comparación de riesgo.
- Auditorí­a de alertas pasadas.

---

## Criterios de Aceptación

Este RFC se considera cumplido cuando:
1. La observabilidad refleja riesgo institucional, no performance.
2. Las seí±ales son explicables, versionadas y reproducibles.
3. Existen vistas ejecutivas y operativas basadas en riesgo.
4. Los umbrales son explí­citos y gobernados.
5. El sistema puede demostrar control continuo del riesgo.

---

## Assumptions

- Gobernar riesgo es más valioso que optimizar métricas técnicas.
- El sistema debe advertir antes de fallar.
- La observabilidad es parte de la defensa institucional.
