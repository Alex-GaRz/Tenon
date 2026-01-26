# RFC-05 — MONEY_STATE_MACHINE
**Sistema:** Tenon — Sistema de Verdad Financiera Operativa y Conciliación Multisistema  
**Estado:** DRAFT  
**Relación:** Depende de RFC-00_MANIFEST, RFC-01_CANONICAL_EVENT, RFC-01A_CANONICAL_IDS, RFC-02_INGEST_APPEND_ONLY, RFC-03_NORMALIZATION_RULES, RFC-04_CORRELATION_ENGINE

---

## 1) Propósito

Definir la **máquina de estados del dinero** de Tenon para:
- diagnosticar la situación operativa de flujos monetarios,
- separar observación de inferencia,
- producir estados explicables, reproducibles y auditables,
- evitar “match/no-match” simplista.

Esta máquina **no ejecuta dinero** ni corrige sistemas externos: **diagnostica**.

---

## 2) No-Goals

- Ejecutar pagos, reembolsos o compensaciones.
- Reemplazar contabilidad oficial o subledgers.
- Inferir fraude o intención.
- Resolver discrepancias (RFC-06).
- Priorizar impacto económico (RFC-07).

---

## 3) Invariantes

### 3.1 Estados como diagnóstico, no como verdad absoluta
- Un estado expresa **lo que se observa dado el conjunto de evidencia disponible**.
- Estados pueden evolucionar con nueva evidencia; la historia **no se borra**.

### 3.2 Determinismo y versionado
- Misma evidencia + misma versión ⇒ mismo estado.
- Cambios en reglas generan **nueva versión de estado**, no reescritura.

### 3.3 Separación evento ↔ estado
- `CanonicalEvent` es un hecho observado.
- `MoneyState` es una inferencia **derivada**.
- Prohibido almacenar estado dentro del evento.

### 3.4 Explicabilidad obligatoria
- Todo estado debe poder explicar:
  - qué evidencia lo sustenta,
  - qué reglas se aplicaron,
  - qué falta para avanzar o resolverse.

---

## 4) Estados canónicos

### 4.1 Conjunto mínimo (cerrado)

- `EXPECTED` — se espera movimiento según contrato/flujo observado.
- `INITIATED` — intención registrada (p.ej., payment initiated).
- `AUTHORIZED` — autorización observada.
- `IN_TRANSIT` — dinero en tránsito entre sistemas.
- `SETTLED` — liquidación observada.
- `REFUNDED` — reembolso liquidado.
- `REVERSED` — reversión aplicada.
- `FAILED` — fallo definitivo observado.
- `EXPIRED` — ventana temporal excedida sin evidencia.
- `AMBIGUOUS` — evidencia insuficiente o contradictoria.
- `UNKNOWN` — no clasificable con reglas actuales.

**Reglas:**
- No se agregan estados ad-hoc por integración.
- Extensiones requieren RFC.

---

## 5) Contratos (conceptuales)

### 5.1 MoneyState

- `money_state_id`
- `flow_id` (referencia al MoneyFlow / grafo)
- `current_state`
- `state_version`
- `supporting_events[]` (event_ids)
- `supporting_links[]` (correlation link_ids)
- `rule_version`
- `confidence_level`
- `explanation`
- `evaluated_at`

### 5.2 Transición de estados

Cada transición debe declarar:
- `from_state`
- `to_state`
- `required_evidence[]`
- `forbidden_evidence[]`
- `timeout_policy` (si aplica)
- `transition_rule_version`

---

## 6) Lógica de evaluación (alto nivel)

1. **Recolección de evidencia**
   - Eventos + correlaciones relevantes al flujo.
2. **Evaluación de reglas**
   - Se evalúan transiciones posibles.
3. **Selección conservadora**
   - Si múltiples estados son plausibles ⇒ `AMBIGUOUS`.
4. **Emisión**
   - Se registra `MoneyState` append-only con explicación.

Nunca se “fuerza” un estado final si la evidencia no lo permite.

---

## 7) Threat Model

### 7.1 Amenazas
- **Estados optimistas** que ocultan riesgo (marcar SETTLED sin evidencia).
- **Colapso temporal** (ignorar eventos tardíos).
- **Reescritura silenciosa** de estados pasados.
- **Dependencia implícita** de reglas no versionadas.

### 7.2 Controles exigidos
- Estados y transiciones versionadas.
- Evidencia explícita por estado.
- `AMBIGUOUS` como estado válido.
- Registro append-only de evaluaciones.

---

## 8) Pruebas

### 8.1 Unitarias
- Transiciones inválidas son rechazadas.
- Estados sin evidencia no se emiten.
- `AMBIGUOUS` se emite ante evidencia conflictiva.

### 8.2 Propiedades
- Determinismo: replay ⇒ mismos estados.
- Monotonicidad: nuevas evaluaciones no borran estados previos.
- Conservadurismo: ante duda ⇒ no “final”.

### 8.3 Sistémicas
- Eventos fuera de orden.
- Evidencia tardía que cambia diagnóstico.
- Flujos incompletos o contradictorios.
- Replay histórico completo.

---

## 9) Criterios de Aceptación

Este RFC se considera cumplido cuando:
1. Existe una máquina de estados cerrada y explícita.
2. Estados se derivan solo de evidencia registrada.
3. Toda transición es explicable y versionada.
4. Ambigüedad y desconocimiento son estados válidos.
5. La historia de estados es reproducible y auditable.

---

## 10) Assumptions

- La realidad financiera es asíncrona e incompleta.
- El costo de marcar AMBIGUOUS es menor que el de afirmar falsamente SETTLED.
- La máquina de estados es diagnóstica, no ejecutora.
