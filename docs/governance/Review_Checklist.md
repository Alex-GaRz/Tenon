# Review Checklist — Verificación Institucional de Invariantes

**Versión:** 1.0  
**Fecha:** 2026-01-21  
**Estado:** Activo

---

## Propósito

Proveer un **checklist auditable** para reviewers humanos que valida que un PR respeta los invariantes, no-goals y threat model del RFC-00, más allá de lo que CI puede verificar automáticamente.

Este checklist debe usarse especialmente en PRs que modifican `/core` o `/contracts`.

---

## Checklist de Invariantes

### ✅ 1. Append-Only

**Invariante:** Ningún dato ingerido o derivado se borra ni se sobrescribe; solo se agregan nuevas versiones/eventos.

**Verificar:**
- [ ] No hay `DELETE` statements o equivalentes en lógica de datos
- [ ] No hay mutación destructiva de registros existentes (ej: `UPDATE ... SET` sin crear nueva versión)
- [ ] Si hay "soft delete" o "mark as invalid", se implementa como **evento append** (ej: `TombstoneEvent`), no como mutación
- [ ] Logs/evidencia nunca se truncan o rotan destructivamente

**Señales de alerta:**
```python
# ❌ Violación
def delete_event(event_id):
    db.execute("DELETE FROM events WHERE id = ?", event_id)

# ✅ Correcto
def mark_event_invalid(event_id, reason):
    db.append(InvalidationEvent(event_id=event_id, reason=reason))
```

---

### ✅ 2. Trazabilidad Total

**Invariante:** Todo artefacto derivado referencia su origen (crudo) + transformaciones + versiones.

**Verificar:**
- [ ] Toda correlación/discrepancia/normalización incluye `source_events: [...]` o equivalente
- [ ] Transformaciones registran qué reglas/versión se aplicaron (ej: `normalization_version: "v1.2.3"`)
- [ ] Evidencia derivada puede reconstruirse desde inputs crudos sin ambigüedad

**Señales de alerta:**
```python
# ❌ Falta trazabilidad
def calculate_discrepancy(amount_a, amount_b):
    return abs(amount_a - amount_b)  # ¿De dónde vienen amount_a y amount_b?

# ✅ Trazabilidad completa
def calculate_discrepancy(event_a: Event, event_b: Event):
    return Discrepancy(
        amount_delta=abs(event_a.amount - event_b.amount),
        source_events=[event_a.id, event_b.id],
        detected_at=now(),
        detection_rule="RFC-06 rule 3.2",
        rule_version="v1.0.0"
    )
```

---

### ✅ 3. Separación Core/Adapters

**Invariante:** El core define invariantes; adapters solo traducen y declaran, jamás imponen dominio.

**Verificar:**
- [ ] `/core` NO contiene lógica específica de ERP/PSP/banco (ej: reglas de "Stripe refunds parciales" en core)
- [ ] Adapters NO introducen invariantes propios que contaminen core (ej: "SAP siempre tiene prioridad")
- [ ] Core define semántica canónica; adapters solo mapean a esa semántica

**Señales de alerta:**
```python
# ❌ Contaminación de core con lógica de negocio externo
# (en /core/normalization.py)
def normalize_amount(event):
    if event.source == "Stripe":
        # Stripe usa cents, convertir a decimal
        return event.amount / 100
    elif event.source == "SAP":
        # SAP usa formato europeo
        return parse_european_decimal(event.amount)
    # ❌ Core no debe conocer peculiaridades de sources

# ✅ Correcto: adapters hacen la traducción
# (en /adapters/stripe_adapter.py)
def to_canonical(stripe_event):
    return CanonicalEvent(
        amount=Money(stripe_event.amount / 100, "USD"),  # Adapter traduce
        ...
    )
```

---

### ✅ 4. Explicabilidad por Diseño

**Invariante:** Toda discrepancia y correlación debe producir explicación estructurada + evidencia.

**Verificar:**
- [ ] Discrepancias incluyen `explanation: str` o `reason: DiscrepancyReason`
- [ ] Correlaciones registran `correlation_method: str` y `confidence: float`
- [ ] Evidencia es estructurada (JSON/schema), no solo logs textuales

**Señales de alerta:**
```python
# ❌ Falta explicación
def detect_mismatch(a, b):
    if a != b:
        return Discrepancy(severity="HIGH")  # ¿Por qué? ¿Qué difiere?

# ✅ Explicabilidad completa
def detect_mismatch(a, b):
    if a.amount != b.amount:
        return Discrepancy(
            type="AMOUNT_MISMATCH",
            explanation=f"Expected {a.amount}, found {b.amount}",
            expected=a,
            actual=b,
            delta=b.amount - a.amount,
            severity="HIGH",
            evidence=[a.id, b.id]
        )
```

---

### ✅ 5. Determinismo

**Invariante:** Mismo input histórico → mismo output (ledger/evidencia/discrepancias) para una misma versión del sistema.

**Verificar:**
- [ ] NO hay dependencia de `random()`, timestamps "now()" en lógica de negocio (solo en metadata)
- [ ] NO hay dependencia de estado externo mutable (ej: llamadas a APIs externas que cambian)
- [ ] Ordenamiento de eventos es estable (ej: sort por timestamp + tiebreaker determinístico)
- [ ] Tests demuestran que replay produce mismo resultado

**Señales de alerta:**
```python
# ❌ No determinístico
def correlate_events(events):
    random.shuffle(events)  # ❌ resultado diferente cada vez
    return find_pairs(events)

# ❌ No determinístico
def assign_priority():
    return random.randint(1, 10)  # ❌

# ✅ Determinístico
def correlate_events(events):
    sorted_events = sorted(events, key=lambda e: (e.timestamp, e.id))  # stable
    return find_pairs(sorted_events)
```

---

### ✅ 6. Idempotencia Obligatoria

**Invariante:** Reintentos no pueden producir duplicados ni divergencia silenciosa.

**Verificar:**
- [ ] Ingest de eventos usa `idempotency_key` o equivalente
- [ ] Operaciones críticas (normalization, correlation) son idempotentes
- [ ] Duplicados detectados se marcan explícitamente, no se ignoran silenciosamente

**Señales de alerta:**
```python
# ❌ No idempotente
def ingest_event(event):
    db.append(event)  # Si se llama 2x con mismo event, crea duplicado ❌

# ✅ Idempotente
def ingest_event(event):
    if db.exists(event.idempotency_key):
        return DuplicateDetected(event.idempotency_key)
    db.append(event)
    return Success(event.id)
```

---

### ✅ 7. Fallos Explícitos

**Invariante:** El sistema nunca "asume" verdad si falta evidencia; produce estado "insuficiente" y lo registra.

**Verificar:**
- [ ] NO hay "default assumptions" silenciosas (ej: "si falta currency, asumir USD")
- [ ] Datos faltantes producen `InsufficientEvidence` o `MissingData` explícito
- [ ] Errores se registran como eventos (no solo logs que desaparecen)

**Señales de alerta:**
```python
# ❌ Asunción silenciosa
def normalize_amount(event):
    currency = event.currency or "USD"  # ❌ asume USD si falta
    return Money(event.amount, currency)

# ✅ Fallo explícito
def normalize_amount(event):
    if not event.currency:
        raise InsufficientDataError(
            field="currency",
            event_id=event.id,
            message="Cannot normalize without currency"
        )
    return Money(event.amount, event.currency)
```

---

### ✅ 8. Versionado Institucional

**Invariante:** Contratos y reglas que afecten semántica o reproducibilidad deben versionarse y quedar auditables.

**Verificar:**
- [ ] Cambios a `/contracts` incluyen actualización de versión
- [ ] Cambios a reglas de normalización/correlación registran nueva versión
- [ ] Evidencia generada incluye `rule_version` o `contract_version`

**Señales de alerta:**
```python
# ❌ Cambio de regla sin versionar
def detect_discrepancy(a, b):
    # Cambié lógica pero no versione
    if abs(a - b) > 10:  # antes era > 5
        return Discrepancy(...)

# ✅ Versionado explícito
DISCREPANCY_THRESHOLD = 10  # v1.2.0 (antes 5 en v1.1.0)

def detect_discrepancy(a, b):
    if abs(a - b) > DISCREPANCY_THRESHOLD:
        return Discrepancy(
            ...,
            detection_rule_version="v1.2.0"
        )
```

---

## Checklist de No-Goals

### ✅ No Ejecución de Pagos/Transferencias

**Verificar:**
- [ ] Código NO ejecuta movimientos de dinero (ver [`NoGoals_Enforcement.md`](NoGoals_Enforcement.md))
- [ ] Integración con PSPs es read-only (webhooks, API polling), no write

### ✅ No Contabilidad Oficial

**Verificar:**
- [ ] Código NO postea a GL/ledger oficial sin aprobación humana
- [ ] Campos como `suggested_entry` son opcionales y read-only

### ✅ No Auto-Corrección

**Verificar:**
- [ ] Discrepancias se detectan y reportan; NO se "arreglan" automáticamente
- [ ] No hay lógica de "if discrepancy < threshold, auto-resolve"

---

## Checklist de Threat Model

### ✅ Prevención de Manipulación Posterior

**Verificar:**
- [ ] Datos append-only + hashing/checksums (si implementado)
- [ ] Auditoría de cambios a evidencia (quién, cuándo, por qué)

### ✅ Prevención de Reescritura de Contratos

**Verificar:**
- [ ] Cambios a `/contracts` siguen [`Contracts_Versioning_Policy.md`](Contracts_Versioning_Policy.md)
- [ ] Versionado semántico aplicado correctamente

### ✅ Prevención de Contaminación del Core

**Verificar:**
- [ ] Core no depende de lógica de negocio externa (Invariante #3)

---

## Cómo Usar Este Checklist

1. **Reviewer abre PR** que toca `/core` o `/contracts`
2. **Copiar checklist** a comentario de review:
   ```markdown
   ## Invariantes Review Checklist
   - [ ] Append-Only
   - [ ] Trazabilidad Total
   - [ ] Separación Core/Adapters
   - [ ] Explicabilidad
   - [ ] Determinismo
   - [ ] Idempotencia
   - [ ] Fallos Explícitos
   - [ ] Versionado Institucional
   
   ## No-Goals
   - [ ] No Ejecución
   - [ ] No Contabilidad Oficial
   - [ ] No Auto-Corrección
   ```
3. **Revisar código** contra cada invariante
4. **Marcar ✅** o agregar comentario si hay issue
5. **Aprobar solo si checklist completo**

---

## Última Actualización

**2026-01-21:** Checklist inicial de revisión publicado con RFC-00.
