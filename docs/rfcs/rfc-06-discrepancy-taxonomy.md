# RFC-06 â€” DISCREPANCY_TAXONOMY
**Sistema:** Tenon â€” Sistema de Verdad Financiera Operativa y ConciliaciÃ³n Multisistema  
**Estado:** DRAFT  
**RelaciÃ³n:** Depende de RFC-00_MANIFEST, RFC-01_CANONICAL_EVENT, RFC-01A_CANONICAL_IDS,
RFC-02_INGEST_APPEND_ONLY, RFC-03_NORMALIZATION_RULES, RFC-04_CORRELATION_ENGINE,
RFC-05_MONEY_STATE_MACHINE

---

## PropÃ³sito

Definir una **taxonomÃ­a formal y cerrada de discrepancias** para que Tenon convierta
evidencia operativa en **diagnÃ³sticos accionables**, sin ruido ni ambigÃ¼edad semÃ¡ntica.

La taxonomÃ­a permite:
- clasificar discrepancias de forma consistente,
- distinguir retrasos normales de anomalÃ­as reales,
- soportar priorizaciÃ³n posterior (RFC-07),
- explicar por quÃ© algo es una discrepancia y no solo â€œno matchâ€.

---

## No-Goals

- Priorizar impacto econÃ³mico (RFC-07).
- Inferir culpabilidad, fraude o intenciÃ³n.
- Ejecutar correcciones automÃ¡ticas.
- Resolver discrepancias (Tenon diagnostica).
- Crear categorÃ­as ad-hoc por cliente o integraciÃ³n.

---

## Invariantes

### 3.1 TaxonomÃ­a cerrada
- El conjunto de tipos de discrepancia es **finito y versionado**.
- Prohibido crear â€œlabelsâ€ dinÃ¡micos o categorÃ­as libres.

### 3.2 DiagnÃ³stico basado en evidencia
- Ninguna discrepancia existe sin:
  - evidencia explÃ­cita,
  - referencia a estados y eventos,
  - regla diagnÃ³stica versionada.

### 3.3 SeparaciÃ³n estado â†” discrepancia
- Un `MoneyState` describe situaciÃ³n.
- Una `Discrepancy` describe **desviaciÃ³n respecto a lo esperado**.
- No se mezclan conceptos.

### 3.4 Conservadurismo
- Ante evidencia insuficiente â‡’ `INSUFFICIENT_EVIDENCE`.
- Prohibido â€œforzarâ€ clasificaciÃ³n.

---

## TaxonomÃ­a de discrepancias (cerrada)

### 4.1 CategorÃ­as principales

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
Toda discrepancia debe pertenecer **exactamente a una** categorÃ­a primaria.

---

### 4.2 Definiciones formales (ejemplos)

- **TIMING_DELAY**
  - Evidencia esperada no llegÃ³ aÃºn dentro de SLA configurable.
  - No implica error; puede resolverse con el tiempo.

- **MISSING_EVENT**
  - Se esperaba un evento (segÃºn mÃ¡quina de estados) y no existe evidencia.

- **DUPLICATE_EVENT**
  - Eventos mÃºltiples con misma identidad lÃ³gica (RFC-01A) y decisiÃ³n REJECT_DUPLICATE.

- **AMOUNT_MISMATCH**
  - Montos incompatibles entre eventos correlacionados.

- **ORPHAN_EVENT**
  - Evento sin correlaciÃ³n plausible dentro del flujo esperado.

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

> `severity_hint` es indicativo; la priorizaciÃ³n econÃ³mica se define en RFC-07.

---

## Flujo de diagnÃ³stico (alto nivel)

1. EvaluaciÃ³n de `MoneyState`.
2. ComparaciÃ³n contra expectativas formales.
3. AplicaciÃ³n de reglas diagnÃ³sticas.
4. EmisiÃ³n de `Discrepancy` append-only.
5. Registro de explicaciÃ³n y evidencia.

---

## Threat Model

### 7.1 Amenazas
- **Ruido excesivo** (todo es discrepancia).
- **ClasificaciÃ³n optimista** que oculta problemas reales.
- **Cambios semÃ¡nticos** que reetiquetan historia.
- **AmbigÃ¼edad forzada** para â€œsimplificarâ€ reportes.

### 7.2 Controles exigidos
- Enum cerrado y versionado.
- Evidencia obligatoria.
- `INSUFFICIENT_EVIDENCE` como salida segura.
- ProhibiciÃ³n de reclasificaciÃ³n retroactiva.

---

## Pruebas

### 8.1 Unitarias
- Toda discrepancia tiene tipo vÃ¡lido.
- Rechazo de tipos fuera del enum.
- ExplicaciÃ³n no vacÃ­a.

### 8.2 Propiedades
- Determinismo: replay â‡’ mismas discrepancias.
- Monotonicidad: discrepancias se agregan, no se borran.
- Conservadurismo: duda â‡’ INSUFFICIENT_EVIDENCE.

### 8.3 SistÃ©micas
- Flujos incompletos.
- Eventos contradictorios.
- Evidencia tardÃ­a que cambia diagnÃ³stico.
- Replay histÃ³rico completo.

---

## Criterios de AceptaciÃ³n

Este RFC se considera cumplido cuando:
1. Existe una taxonomÃ­a cerrada y explÃ­cita.
2. Cada discrepancia es diagnÃ³stica, no interpretativa.
3. Evidencia y explicaciÃ³n son obligatorias.
4. AmbigÃ¼edad es tratada como categorÃ­a vÃ¡lida.
5. La clasificaciÃ³n es reproducible y versionada.

---

## Assumptions

- No toda desviaciÃ³n es error.
- El mayor riesgo es clasificar mal, no clasificar lento.
- La taxonomÃ­a debe resistir auditorÃ­a y litigio.
