# RFC-13 â€” RISK_OBSERVABILITY
**Sistema:** Tenon â€” Sistema de Verdad Financiera Operativa y ConciliaciÃ³n Multisistema  
**Estado:** DRAFT  
**RelaciÃ³n:** Depende de RFC-00_MANIFEST y de todos los RFCs funcionales previos (01â€“12)

---

## PropÃ³sito

Definir la **observabilidad institucional basada en riesgo** para gobernar Tenon como
infraestructura crÃ­tica viva, enfocada en **control y degradaciÃ³n de riesgo operativo**
â€”no en performance, throughput ni mÃ©tricas vanity.

Esta capa permite:
- detectar degradaciones sistÃ©micas antes de incidentes,
- priorizar intervenciÃ³n humana donde el riesgo lo exige,
- demostrar control continuo ante auditorÃ­a y comitÃ©s de riesgo.

---

## No-Goals

- MÃ©tricas de performance (latencia, QPS, CPU).
- Observabilidad orientada a debugging tÃ©cnico.
- Dashboards genÃ©ricos o â€œbonitosâ€.
- Alerting reactivo sin contexto institucional.
- Automatizar acciones correctivas.

---

## Invariantes

### 3.1 Riesgo sobre rendimiento
- Toda mÃ©trica debe mapear explÃ­citamente a **riesgo operativo, financiero o legal**.
- MÃ©tricas sin interpretaciÃ³n de riesgo estÃ¡n prohibidas.

### 3.2 SeÃ±ales derivadas, no crudas
- La observabilidad se construye sobre:
  - estados del dinero,
  - discrepancias,
  - causalidades,
  - idempotencia,
  - cambios de versiÃ³n.
- No se basa directamente en eventos crudos.

### 3.3 Explicabilidad
- Toda alerta o indicador debe poder explicar:
  - quÃ© cambiÃ³,
  - por quÃ© es riesgoso,
  - quÃ© evidencia lo sustenta.

### 3.4 No mutaciÃ³n
- La observabilidad **no altera** estados, eventos ni diagnÃ³sticos.
- Es estrictamente de lectura y agregaciÃ³n.

---

## SeÃ±ales institucionales (cerradas)

### 4.1 Riesgo de discrepancias
- ConcentraciÃ³n de discrepancias `HIGH` por:
  - fuente,
  - tipo,
  - flujo.
- Tendencia temporal de discrepancias crÃ­ticas.
- AntigÃ¼edad promedio de discrepancias no resueltas.

### 4.2 Riesgo de correlaciÃ³n
- DegradaciÃ³n del `confidence_score` promedio.
- Aumento de correlaciones ambiguas por flujo.
- Crecimiento de `ORPHAN_EVENT`.

### 4.3 Riesgo de estados
- AcumulaciÃ³n de estados `AMBIGUOUS`, `UNKNOWN`, `IN_TRANSIT` fuera de SLA.
- Flujos â€œstaleâ€ (sin evoluciÃ³n pese a nueva evidencia).
- Divergencia entre estados esperados y observados.

### 4.4 Riesgo de idempotencia
- Incremento de `REJECT_DUPLICATE` o `FLAG_AMBIGUOUS`.
- Claves de idempotencia con colisiones recurrentes.
- Bypass o intentos fallidos del Guardian.

### 4.5 Riesgo de cambio
- Cambios recientes con impacto en:
  - correlaciÃ³n,
  - estados,
  - discrepancias.
- Versiones coexistentes con resultados divergentes.
- Incremento de discrepancias post-change.

### 4.6 Riesgo humano-operativo
- Sobreuso de intervenciÃ³n humana.
- Reapertura recurrente de discrepancias.
- Dependencia de overrides manuales.

---

## Contratos (conceptuales)

### 5.1 RiskSignal

- `risk_signal_id`
- `signal_type` (enum cerrado; ver secciÃ³n 4)
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
- `risk_profile` (vector de seÃ±ales)
- `overall_risk_level`
- `drivers[]`
- `computed_at`
- `model_version`

---

## Umbrales institucionales

- Los umbrales:
  - son explÃ­citos,
  - versionados,
  - aprobados institucionalmente.
- Ejemplos:
  - >X% de flujos en `AMBIGUOUS` por >Y horas.
  - crecimiento anÃ³malo (>ZÏƒ) de discrepancias crÃ­ticas.
  - degradaciÃ³n sostenida de correlaciÃ³n >N ventanas.

Los umbrales **no se auto-ajustan** sin cambio controlado (RFC-12).

---

## Alertas (no reactivas)

### 7.1 Principios
- Alertas indican **riesgo**, no â€œerrorâ€.
- Toda alerta incluye:
  - seÃ±al,
  - evidencia,
  - impacto potencial,
  - recomendaciÃ³n operativa.

### 7.2 Tipos
- **Early Warning** â€” degradaciÃ³n incipiente.
- **Risk Escalation** â€” riesgo material.
- **Institutional Breach** â€” violaciÃ³n de umbral crÃ­tico.

---

## Dashboards (criterios)

### 8.1 Ejecutivo
- Riesgo agregado del sistema.
- Top drivers de riesgo.
- Tendencias y comparativas pre/post cambio.
- No mÃ©tricas tÃ©cnicas.

### 8.2 Operativo
- Vistas por fuente / flujo.
- Backlog de discrepancias crÃ­ticas.
- Estados stale y ambigÃ¼edades.
- Evidencia navegable (â€œpelÃ­culaâ€).

---

## Threat Model

### 9.1 Amenazas
- **Ceguera institucional** (no ver riesgo emergente).
- **Ruido excesivo** que banaliza alertas.
- **MÃ©tricas vanity** que ocultan problemas reales.
- **Cambios sin monitoreo** de impacto.
- **Dependencia humana no detectada**.

### 9.2 Controles exigidos
- SeÃ±ales cerradas y versionadas.
- Evidencia obligatoria por seÃ±al.
- Umbrales explÃ­citos.
- SeparaciÃ³n observaciÃ³n/acciÃ³n.
- AuditorÃ­a de cambios en observabilidad.

---

## Pruebas

### 10.1 Unitarias
- CÃ¡lculo correcto de seÃ±ales.
- Severidad consistente con umbrales.
- ExplicaciÃ³n no vacÃ­a.

### 10.2 Propiedades
- Determinismo: mismo input â‡’ mismas seÃ±ales.
- No side-effects: lectura pura.
- Estabilidad temporal: replay reproduce seÃ±ales histÃ³ricas.

### 10.3 SistÃ©micas
- SimulaciÃ³n de degradaciÃ³n progresiva.
- Incidente histÃ³rico reproducido.
- Cambios de versiÃ³n con comparaciÃ³n de riesgo.
- AuditorÃ­a de alertas pasadas.

---

## Criterios de AceptaciÃ³n

Este RFC se considera cumplido cuando:
1. La observabilidad refleja riesgo institucional, no performance.
2. Las seÃ±ales son explicables, versionadas y reproducibles.
3. Existen vistas ejecutivas y operativas basadas en riesgo.
4. Los umbrales son explÃ­citos y gobernados.
5. El sistema puede demostrar control continuo del riesgo.

---

## Assumptions

- Gobernar riesgo es mÃ¡s valioso que optimizar mÃ©tricas tÃ©cnicas.
- El sistema debe advertir antes de fallar.
- La observabilidad es parte de la defensa institucional.
