# RFC-06 — DISCREPANCY_TAXONOMY
**Sistema:** Tenon — Sistema de Verdad Financiera Operativa y Conciliación Multisistema  
**Estado:** DRAFT  
**Relación:** Depende de RFC-00_MANIFEST, RFC-01_CANONICAL_EVENT, RFC-01A_CANONICAL_IDS,
RFC-02_INGEST_APPEND_ONLY, RFC-03_NORMALIZATION_RULES, RFC-04_CORRELATION_ENGINE,
RFC-05_MONEY_STATE_MACHINE

---

## Propósito

Definir una **taxonomí­a formal y cerrada de discrepancias** para que Tenon convierta
evidencia operativa en **diagnósticos accionables**, sin ruido ni ambigí¼edad semántica.

La taxonomí­a permite:
- clasificar discrepancias de forma consistente,
- distinguir retrasos normales de anomalí­as reales,
- soportar priorización posterior (RFC-07),
- explicar por qué algo es una discrepancia y no solo “no match”.

---

## No-Goals

- Priorizar impacto económico (RFC-07).
- Inferir culpabilidad, fraude o intención.
- Ejecutar correcciones automáticas.
- Resolver discrepancias (Tenon diagnostica).
- Crear categorí­as ad-hoc por cliente o integración.

---

## Invariantes

### 3.1 Taxonomí­a cerrada
- El conjunto de tipos de discrepancia es **finito y versionado**.
- Prohibido crear “labels” dinámicos o categorí­as libres.

### 3.2 Diagnóstico basado en evidencia
- Ninguna discrepancia existe sin:
  - evidencia explí­cita,
  - referencia a estados y eventos,
  - regla diagnóstica versionada.

### 3.3 Separación estado â†” discrepancia
- Un `MoneyState` describe situación.
- Una `Discrepancy` describe **desviación respecto a lo esperado**.
- No se mezclan conceptos.

### 3.4 Conservadurismo
- Ante evidencia insuficiente â‡’ `INSUFFICIENT_EVIDENCE`.
- Prohibido “forzar” clasificación.

---

## Taxonomí­a de discrepancias (cerrada)

### 4.1 Categorí­as principales

- `NO_DISCREPANCY`
- `TIMING_DELAY`
- `MISSING_EVENT`
- `DUPLICATE_EVENT`
- `AMOUNT_MISMATCH`
- `CURRENCY_MISMATCH`
- `STATUS_CONFLICT`
- `UNEXPECTED_REVERSAL`
- `ORPHAN_EVENT`
- `INCONSISTENT_FLOW`
- `INSUFFICIENT_EVIDENCE`

**Regla:**  
Toda discrepancia debe pertenecer **exactamente a una** categorí­a primaria.

---

### 4.2 Definiciones formales (ejemplos)

- **TIMING_DELAY**
  - Evidencia esperada no llegó aíºn dentro de SLA configurable.
  - No implica error; puede resolverse con el tiempo.

- **MISSING_EVENT**
  - Se esperaba un evento (segíºn máquina de estados) y no existe evidencia.

- **DUPLICATE_EVENT**
  - Eventos míºltiples con misma identidad lógica (RFC-01A) y decisión REJECT_DUPLICATE.

- **AMOUNT_MISMATCH**
  - Montos incompatibles entre eventos correlacionados.

- **ORPHAN_EVENT**
  - Evento sin correlación plausible dentro del flujo esperado.

- **INSUFFICIENT_EVIDENCE**
  - No hay base suficiente para clasificar sin inventar.

---

## Contratos (conceptuales)

### 5.1 Discrepancy

- `discrepancy_id`
- `flow_id`
- `discrepancy_type` (enum cerrado)
- `severity_hint` (LOW | MEDIUM | HIGH | UNKNOWN)
- `supporting_states[]`
- `supporting_events[]`
- `supporting_links[]`
- `rule_id`
- `rule_version`
- `explanation`
- `detected_at`

> `severity_hint` es indicativo; la priorización económica se define en RFC-07.

---

## Flujo de diagnóstico (alto nivel)

1. Evaluación de `MoneyState`.
2. Comparación contra expectativas formales.
3. Aplicación de reglas diagnósticas.
4. Emisión de `Discrepancy` append-only.
5. Registro de explicación y evidencia.

---

## Threat Model

### 7.1 Amenazas
- **Ruido excesivo** (todo es discrepancia).
- **Clasificación optimista** que oculta problemas reales.
- **Cambios semánticos** que reetiquetan historia.
- **Ambigí¼edad forzada** para “simplificar” reportes.

### 7.2 Controles exigidos
- Enum cerrado y versionado.
- Evidencia obligatoria.
- `INSUFFICIENT_EVIDENCE` como salida segura.
- Prohibición de reclasificación retroactiva.

---

## Pruebas

### 8.1 Unitarias
- Toda discrepancia tiene tipo válido.
- Rechazo de tipos fuera del enum.
- Explicación no vací­a.

### 8.2 Propiedades
- Determinismo: replay â‡’ mismas discrepancias.
- Monotonicidad: discrepancias se agregan, no se borran.
- Conservadurismo: duda â‡’ INSUFFICIENT_EVIDENCE.

### 8.3 Sistémicas
- Flujos incompletos.
- Eventos contradictorios.
- Evidencia tardí­a que cambia diagnóstico.
- Replay histórico completo.

---

## Criterios de Aceptación

Este RFC se considera cumplido cuando:
1. Existe una taxonomí­a cerrada y explí­cita.
2. Cada discrepancia es diagnóstica, no interpretativa.
3. Evidencia y explicación son obligatorias.
4. Ambigí¼edad es tratada como categorí­a válida.
5. La clasificación es reproducible y versionada.

---

## Assumptions

- No toda desviación es error.
- El mayor riesgo es clasificar mal, no clasificar lento.
- La taxonomí­a debe resistir auditorí­a y litigio.
