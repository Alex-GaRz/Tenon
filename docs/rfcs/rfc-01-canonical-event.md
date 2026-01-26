# RFC-01 — CANONICAL_EVENT
**Sistema:** Tenon — Sistema de Verdad Financiera Operativa y Conciliación Multisistema  
**Estado:** DRAFT  
**Relación:** Depende de RFC-00_MANIFEST (constitucional)

---

## Propósito

Definir el **íºnico objeto canónico** del sistema: `CanonicalEvent`.

Este objeto:
- representa un **hecho observado** (no una interpretación contable),
- permite correlación multisistema,
- soporta append-only y trazabilidad total,
- habilita reconstrucción histórica (“pelí­cula”) y evidencia forense,
- evita que cada integración invente semántica distinta.

Tenon no concilia “formatos”; concilia **eventos canónicos**.

---

## No-Goals

- Definir reglas de correlación (eso pertenece a RFC-04).
- Definir máquina de estados del dinero (RFC-05).
- Definir discrepancias, causalidad o priorización (RFC-06/07).
- Definir ledger WORM, firma criptográfica o cadena de custodia (RFC-08/09).
- Calcular FX, impuestos, contabilidad oficial, o “correcciones” semánticas.
- Permitir míºltiples modelos canónicos o variantes por fuente.

---

## Invariantes

### 3.1 Unicidad del canon
- Existe **un solo** tipo de objeto canónico: `CanonicalEvent`.
- Prohibido crear `BankEvent`, `ErpEvent`, `PspEvent` como “canones paralelos”.

### 3.2 Append-only real
- Un `CanonicalEvent` nunca se edita ni se sobrescribe.
- Correcciones se expresan como **nuevos eventos** (p.ej., `event_type=ADJUSTMENT` o `REVERSAL`) con referencia explí­cita al evento anterior.

### 3.3 Separación “observación vs interpretación”
- `CanonicalEvent` registra lo observado y su contexto mí­nimo.
- No contiene “opiniones” del sistema (p.ej., “esto es fraude”, “esto ya está conciliado”).
- No contiene estados derivados. Estados viven fuera del evento.

### 3.4 Trazabilidad mí­nima obligatoria
- Todo evento canónico debe poder responder:
  - **de dónde vino** (source)
  - **qué lo originó** (external_reference / source_event_id)
  - **cuándo se observó** (observed_at)
  - **qué preserva como crudo** (raw_payload_hash + raw_pointer)

### 3.5 Determinismo de normalización
- El `CanonicalEvent` es resultado de una transformación determinista desde datos crudos.
- Misma entrada cruda + misma versión del normalizador â‡’ mismo `CanonicalEvent`.

### 3.6 Idempotencia (a nivel de identidad de evento)
- Debe existir una manera de detectar y rechazar duplicados lógicos del mismo hecho observado.
- El mecanismo exacto se fija en RFC-01A_CANONICAL_IDS, pero RFC-01 exige que el evento canónico sea “idempotency-aware”.

---

## Contratos (definición canónica)

### 4.1 Estructura conceptual (campos)
`CanonicalEvent` contiene, como mí­nimo, los siguientes campos conceptuales:

**Identidad y linaje**
- `event_id` (interno, estable)
- `source_event_id` (si existe en la fuente)
- `correlation_id` (para agrupar, si existe o se asigna determiní­sticamente)
- `lineage` (links hacia eventos relacionados; definido en RFC-01A)

**Fuente**
- `source_system` (enum cerrado: BANK, ERP, PSP, MARKETPLACE, INTERNAL_LEDGER, OTHER)
- `source_connector` (identificador del adaptador)
- `source_environment` (PROD, SANDBOX, UNKNOWN)

**Tiempo**
- `observed_at` (timestamp cuando Tenon observó/ingirió)
- `source_timestamp` (timestamp reportado por la fuente; puede ser null)
- `ingested_at` (timestamp interno de ingestión; puede igualar observed_at)

**Semántica mí­nima (ontologí­a cerrada)**
- `event_type` (enum cerrado; ver 4.2)
- `direction` (IN, OUT, NEUTRAL)
- `amount` (valor numérico)
- `currency` (ISO 4217; si no aplica, UNKNOWN)
- `status_hint` (opcional: AUTH, CAPTURE, SETTLE, REFUND, REVERSAL, ADJUSTMENT, UNKNOWN)  
  *(es “hint”, no estado oficial; el estado formal se modela en RFC-05)*

**Referencias externas mí­nimas**
- `external_reference` (string; invoice_id / payout_id / transfer_id / charge_id, etc.)
- `counterparty_hint` (string o null; nombre/identificador reportado sin interpretación)

**Preservación del crudo**
- `raw_payload_hash` (hash del payload crudo)
- `raw_pointer` (URI/path/locator al crudo append-only)
- `raw_format` (JSON, CSV, XML, PDF, OTHER)

**Auditorí­a de transformación**
- `normalizer_version` (versión de la regla/paquete)
- `adapter_version` (versión del adaptador)
- `schema_version` (versión del contrato)

### 4.2 Ontologí­a cerrada de `event_type` (mí­nimo)
El enum `event_type` debe ser cerrado y contener, como mí­nimo:

- `PAYMENT_INITIATED`
- `PAYMENT_AUTHORIZED`
- `PAYMENT_CAPTURED`
- `PAYMENT_SETTLED`
- `PAYOUT_INITIATED`
- `PAYOUT_SETTLED`
- `REFUND_INITIATED`
- `REFUND_SETTLED`
- `CHARGEBACK_OPENED`
- `CHARGEBACK_WON`
- `CHARGEBACK_LOST`
- `FEE_ASSESSED`
- `ADJUSTMENT_POSTED`
- `REVERSAL_POSTED`
- `BALANCE_SNAPSHOT` *(permitido solo como observación de saldo; no reemplaza ledger)*
- `UNKNOWN`

**Reglas:**
- No se agregan tipos ad-hoc por integración.
- Si falta semántica, se usa `UNKNOWN` + evidencia cruda intacta.
- Extensiones del enum requieren RFC (controlado).

---

## Threat Model

### 5.1 Amenazas
- **Contaminación semántica:** adaptadores inyectan “interpretación” (FX, impuestos, contabilidad).
- **Explosión de variantes:** cada fuente crea su “modelo” rompiendo conciliación.
- **Manipulación del crudo:** se altera el payload sin reflejo (rompe cadena de evidencia).
- **Doble ingestión:** el mismo hecho entra míºltiples veces con pequeí±as variaciones.
- **Timestamps engaí±osos:** clocks skew o timestamps maliciosos/falsos en fuente.

### 5.2 Controles exigidos por este RFC
- Raw preservation obligatoria (`raw_payload_hash` + `raw_pointer`).
- Ontologí­a cerrada para evitar semántica arbitraria.
- Campos de versión (`normalizer_version`, `adapter_version`, `schema_version`) obligatorios.
- Uso de `UNKNOWN` para evitar “inventar” verdad.

---

## Pruebas

### 6.1 Unitarias
- Validación de presencia de campos obligatorios.
- Rechazo de `event_type` fuera del enum.
- Rechazo de `currency` inválida (si no se conoce: UNKNOWN explí­cito).
- Prohibición de mutación: un evento “creado” no cambia.

### 6.2 Propiedades (property-based)
- Determinismo: mismo raw â‡’ mismo `CanonicalEvent` (mismas versiones).
- Monotonicidad append-only: eventos solo se agregan.
- Idempotency-awareness: duplicados exactos detectables por claves definidas (placeholder hasta RFC-01A).

### 6.3 Sistémicas
- Ingesta de míºltiples fuentes con colisiones de `external_reference`:
  - el sistema no “fusiona” sin evidencia; registra eventos separados.
- Replay: reconstrucción exacta del set canónico desde crudos (misma versión).

---

## Criterios de Aceptación

Este RFC se considera cumplido cuando:
1. Existe definición íºnica de `CanonicalEvent` con campos mí­nimos y ontologí­a cerrada.
2. Se prohí­ben explí­citamente canones paralelos por fuente.
3. Se exige preservación de crudo mediante hash + puntero.
4. Se exige versionado explí­cito (normalizer/adapter/schema).
5. Se define un enum mí­nimo de `event_type` y `direction`, con regla `UNKNOWN` como salida segura.
6. Las pruebas (unitarias + propiedades + sistémicas) están especificadas como requisitos verificables.

---

## Assumptions

- No siempre existirá `source_event_id` o `external_reference`; el sistema debe tolerarlo sin inventar.
- Algunas fuentes proveerán datos incompletos o incoherentes; el canon prioriza evidencia y trazabilidad.
- La semántica completa de identidad/correlación se fija en RFC-01A (siguiente).
