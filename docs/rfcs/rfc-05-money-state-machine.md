# RFC-05 â€” MONEY_STATE_MACHINE
**Sistema:** Tenon â€” Sistema de Verdad Financiera Operativa y ConciliaciÃ³n Multisistema  
**Estado:** DRAFT  
**RelaciÃ³n:** Depende de RFC-00_MANIFEST, RFC-01_CANONICAL_EVENT, RFC-01A_CANONICAL_IDS, RFC-02_INGEST_APPEND_ONLY, RFC-03_NORMALIZATION_RULES, RFC-04_CORRELATION_ENGINE

---

## PropÃ³sito

Definir la **mÃ¡quina de estados del dinero** de Tenon para:
- diagnosticar la situaciÃ³n operativa de flujos monetarios,
- separar observaciÃ³n de inferencia,
- producir estados explicables, reproducibles y auditables,
- evitar â€œmatch/no-matchâ€ simplista.

Esta mÃ¡quina **no ejecuta dinero** ni corrige sistemas externos: **diagnostica**.

---

## No-Goals

- Ejecutar pagos, reembolsos o compensaciones.
- Reemplazar contabilidad oficial o subledgers.
- Inferir fraude o intenciÃ³n.
- Resolver discrepancias (RFC-06).
- Priorizar impacto econÃ³mico (RFC-07).

---

## Invariantes

### 3.1 Estados como diagnÃ³stico, no como verdad absoluta
- Un estado expresa **lo que se observa dado el conjunto de evidencia disponible**.
- Estados pueden evolucionar con nueva evidencia; la historia **no se borra**.

### 3.2 Determinismo y versionado
- Misma evidencia + misma versiÃ³n â‡’ mismo estado.
- Cambios en reglas generan **nueva versiÃ³n de estado**, no reescritura.

### 3.3 SeparaciÃ³n evento â†” estado
- `CanonicalEvent` es un hecho observado.
- `MoneyState` es una inferencia **derivada**.
- Prohibido almacenar estado dentro del evento.

### 3.4 Explicabilidad obligatoria
- Todo estado debe poder explicar:
  - quÃ© evidencia lo sustenta,
  - quÃ© reglas se aplicaron,
  - quÃ© falta para avanzar o resolverse.

---

## Estados canÃ³nicos

### 4.1 Conjunto mÃ­nimo (cerrado)

- `EXPECTED` â€” se espera movimiento segÃºn contrato/flujo observado.
- `INITIATED` â€” intenciÃ³n registrada (p.ej., payment initiated).
- `AUTHORIZED` â€” autorizaciÃ³n observada.
- `IN_TRANSIT` â€” dinero en trÃ¡nsito entre sistemas.
- `SETTLED` â€” liquidaciÃ³n observada.
- `REFUNDED` â€” reembolso liquidado.
- `REVERSED` â€” reversiÃ³n aplicada.
- `FAILED` â€” fallo definitivo observado.
- `EXPIRED` â€” ventana temporal excedida sin evidencia.
- `AMBIGUOUS` â€” evidencia insuficiente o contradictoria.
- `UNKNOWN` â€” no clasificable con reglas actuales.

**Reglas:**
- No se agregan estados ad-hoc por integraciÃ³n.
- Extensiones requieren RFC.

---

## Contratos (conceptuales)

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

### 5.2 TransiciÃ³n de estados

Cada transiciÃ³n debe declarar:
- `from_state`
- `to_state`
- `required_evidence[]`
- `forbidden_evidence[]`
- `timeout_policy` (si aplica)
- `transition_rule_version`

---

## LÃ³gica de evaluaciÃ³n (alto nivel)

1. **RecolecciÃ³n de evidencia**
   - Eventos + correlaciones relevantes al flujo.
2. **EvaluaciÃ³n de reglas**
   - Se evalÃºan transiciones posibles.
3. **SelecciÃ³n conservadora**
   - Si mÃºltiples estados son plausibles â‡’ `AMBIGUOUS`.
4. **EmisiÃ³n**
   - Se registra `MoneyState` append-only con explicaciÃ³n.

Nunca se â€œfuerzaâ€ un estado final si la evidencia no lo permite.

---

## Threat Model

### 7.1 Amenazas
- **Estados optimistas** que ocultan riesgo (marcar SETTLED sin evidencia).
- **Colapso temporal** (ignorar eventos tardÃ­os).
- **Reescritura silenciosa** de estados pasados.
- **Dependencia implÃ­cita** de reglas no versionadas.

### 7.2 Controles exigidos
- Estados y transiciones versionadas.
- Evidencia explÃ­cita por estado.
- `AMBIGUOUS` como estado vÃ¡lido.
- Registro append-only de evaluaciones.

---

## Pruebas

### 8.1 Unitarias
- Transiciones invÃ¡lidas son rechazadas.
- Estados sin evidencia no se emiten.
- `AMBIGUOUS` se emite ante evidencia conflictiva.

### 8.2 Propiedades
- Determinismo: replay â‡’ mismos estados.
- Monotonicidad: nuevas evaluaciones no borran estados previos.
- Conservadurismo: ante duda â‡’ no â€œfinalâ€.

### 8.3 SistÃ©micas
- Eventos fuera de orden.
- Evidencia tardÃ­a que cambia diagnÃ³stico.
- Flujos incompletos o contradictorios.
- Replay histÃ³rico completo.

---

## Criterios de AceptaciÃ³n

Este RFC se considera cumplido cuando:
1. Existe una mÃ¡quina de estados cerrada y explÃ­cita.
2. Estados se derivan solo de evidencia registrada.
3. Toda transiciÃ³n es explicable y versionada.
4. AmbigÃ¼edad y desconocimiento son estados vÃ¡lidos.
5. La historia de estados es reproducible y auditable.

---

## Assumptions

- La realidad financiera es asÃ­ncrona e incompleta.
- El costo de marcar AMBIGUOUS es menor que el de afirmar falsamente SETTLED.
- La mÃ¡quina de estados es diagnÃ³stica, no ejecutora.
