# RFC-06 — DISCREPANCY_TAXONOMY
**Sistema:** Tenon — Sistema de Verdad Financiera Operativa y Conciliación Multisistema  
**Estado:** DRAFT  
**Relación:** Depende de RFC-00_MANIFEST, RFC-01_CANONICAL_EVENT, RFC-01A_CANONICAL_IDS,
RFC-02_INGEST_APPEND_ONLY, RFC-03_NORMALIZATION_RULES, RFC-04_CORRELATION_ENGINE,
RFC-05_MONEY_STATE_MACHINE

---

## 1) Propósito

Definir una **taxonomía formal y cerrada de discrepancias** para que Tenon convierta
evidencia operativa en **diagnósticos accionables**, sin ruido ni ambigüedad semántica.

La taxonomía permite:
- clasificar discrepancias de forma consistente,
- distinguir retrasos normales de anomalías reales,
- soportar priorización posterior (RFC-07),
- explicar por qué algo es una discrepancia y no solo “no match”.

---

## 2) No-Goals

- Priorizar impacto económico (RFC-07).
- Inferir culpabilidad, fraude o intención.
- Ejecutar correcciones automáticas.
- Resolver discrepancias (Tenon diagnostica).
- Crear categorías ad-hoc por cliente o integración.

---

## 3) Invariantes

### 3.1 Taxonomía cerrada
- El conjunto de tipos de discrepancia es **finito y versionado**.
- Prohibido crear “labels” dinámicos o categorías libres.

### 3.2 Diagnóstico basado en evidencia
- Ninguna discrepancia existe sin:
  - evidencia explícita,
  - referencia a estados y eventos,
  - regla diagnóstica versionada.

### 3.3 Separación estado ↔ discrepancia
- Un `MoneyState` describe situación.
- Una `Discrepancy` describe **desviación respecto a lo esperado**.
- No se mezclan conceptos.

### 3.4 Conservadurismo
- Ante evidencia insuficiente ⇒ `INSUFFICIENT_EVIDENCE`.
- Prohibido “forzar” clasificación.

---

## 4) Taxonomía de discrepancias (cerrada)

### 4.1 Categorías principales

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
Toda discrepancia debe pertenecer **exactamente a una** categoría primaria.

---

### 4.2 Definiciones formales (ejemplos)

- **TIMING_DELAY**
  - Evidencia esperada no llegó aún dentro de SLA configurable.
  - No implica error; puede resolverse con el tiempo.

- **MISSING_EVENT**
  - Se esperaba un evento (según máquina de estados) y no existe evidencia.

- **DUPLICATE_EVENT**
  - Eventos múltiples con misma identidad lógica (RFC-01A) y decisión REJECT_DUPLICATE.

- **AMOUNT_MISMATCH**
  - Montos incompatibles entre eventos correlacionados.

- **ORPHAN_EVENT**
  - Evento sin correlación plausible dentro del flujo esperado.

- **INSUFFICIENT_EVIDENCE**
  - No hay base suficiente para clasificar sin inventar.

---

## 5) Contratos (conceptuales)

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

## 6) Flujo de diagnóstico (alto nivel)

1. Evaluación de `MoneyState`.
2. Comparación contra expectativas formales.
3. Aplicación de reglas diagnósticas.
4. Emisión de `Discrepancy` append-only.
5. Registro de explicación y evidencia.

---

## 7) Threat Model

### 7.1 Amenazas
- **Ruido excesivo** (todo es discrepancia).
- **Clasificación optimista** que oculta problemas reales.
- **Cambios semánticos** que reetiquetan historia.
- **Ambigüedad forzada** para “simplificar” reportes.

### 7.2 Controles exigidos
- Enum cerrado y versionado.
- Evidencia obligatoria.
- `INSUFFICIENT_EVIDENCE` como salida segura.
- Prohibición de reclasificación retroactiva.

---

## 8) Pruebas

### 8.1 Unitarias
- Toda discrepancia tiene tipo válido.
- Rechazo de tipos fuera del enum.
- Explicación no vacía.

### 8.2 Propiedades
- Determinismo: replay ⇒ mismas discrepancias.
- Monotonicidad: discrepancias se agregan, no se borran.
- Conservadurismo: duda ⇒ INSUFFICIENT_EVIDENCE.

### 8.3 Sistémicas
- Flujos incompletos.
- Eventos contradictorios.
- Evidencia tardía que cambia diagnóstico.
- Replay histórico completo.

---

## 9) Criterios de Aceptación

Este RFC se considera cumplido cuando:
1. Existe una taxonomía cerrada y explícita.
2. Cada discrepancia es diagnóstica, no interpretativa.
3. Evidencia y explicación son obligatorias.
4. Ambigüedad es tratada como categoría válida.
5. La clasificación es reproducible y versionada.

---

## 10) Assumptions

- No toda desviación es error.
- El mayor riesgo es clasificar mal, no clasificar lento.
- La taxonomía debe resistir auditoría y litigio.
