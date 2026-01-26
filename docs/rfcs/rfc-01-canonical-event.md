# RFC-01 â€” CANONICAL_EVENT
**Sistema:** Tenon â€” Sistema de Verdad Financiera Operativa y ConciliaciÃ³n Multisistema  
**Estado:** DRAFT  
**RelaciÃ³n:** Depende de RFC-00_MANIFEST (constitucional)

---

## PropÃ³sito

Definir el **Ãºnico objeto canÃ³nico** del sistema: `CanonicalEvent`.

Este objeto:
- representa un **hecho observado** (no una interpretaciÃ³n contable),
- permite correlaciÃ³n multisistema,
- soporta append-only y trazabilidad total,
- habilita reconstrucciÃ³n histÃ³rica (â€œpelÃ­culaâ€) y evidencia forense,
- evita que cada integraciÃ³n invente semÃ¡ntica distinta.

Tenon no concilia â€œformatosâ€; concilia **eventos canÃ³nicos**.

---

## No-Goals

- Definir reglas de correlaciÃ³n (eso pertenece a RFC-04).
- Definir mÃ¡quina de estados del dinero (RFC-05).
- Definir discrepancias, causalidad o priorizaciÃ³n (RFC-06/07).
- Definir ledger WORM, firma criptogrÃ¡fica o cadena de custodia (RFC-08/09).
- Calcular FX, impuestos, contabilidad oficial, o â€œcorreccionesâ€ semÃ¡nticas.
- Permitir mÃºltiples modelos canÃ³nicos o variantes por fuente.

---

## Invariantes

### 3.1 Unicidad del canon
- Existe **un solo** tipo de objeto canÃ³nico: `CanonicalEvent`.
- Prohibido crear `BankEvent`, `ErpEvent`, `PspEvent` como â€œcanones paralelosâ€.

### 3.2 Append-only real
- Un `CanonicalEvent` nunca se edita ni se sobrescribe.
- Correcciones se expresan como **nuevos eventos** (p.ej., `event_type=ADJUSTMENT` o `REVERSAL`) con referencia explÃ­cita al evento anterior.

### 3.3 SeparaciÃ³n â€œobservaciÃ³n vs interpretaciÃ³nâ€
- `CanonicalEvent` registra lo observado y su contexto mÃ­nimo.
- No contiene â€œopinionesâ€ del sistema (p.ej., â€œesto es fraudeâ€, â€œesto ya estÃ¡ conciliadoâ€).
- No contiene estados derivados. Estados viven fuera del evento.

### 3.4 Trazabilidad mÃ­nima obligatoria
- Todo evento canÃ³nico debe poder responder:
  - **de dÃ³nde vino** (source)
  - **quÃ© lo originÃ³** (external_reference / source_event_id)
  - **cuÃ¡ndo se observÃ³** (observed_at)
  - **quÃ© preserva como crudo** (raw_payload_hash + raw_pointer)

### 3.5 Determinismo de normalizaciÃ³n
- El `CanonicalEvent` es resultado de una transformaciÃ³n determinista desde datos crudos.
- Misma entrada cruda + misma versiÃ³n del normalizador â‡’ mismo `CanonicalEvent`.

### 3.6 Idempotencia (a nivel de identidad de evento)
- Debe existir una manera de detectar y rechazar duplicados lÃ³gicos del mismo hecho observado.
- El mecanismo exacto se fija en RFC-01A_CANONICAL_IDS, pero RFC-01 exige que el evento canÃ³nico sea â€œidempotency-awareâ€.

---

## Contratos (definiciÃ³n canÃ³nica)

### 4.1 Estructura conceptual (campos)
`CanonicalEvent` contiene, como mÃ­nimo, los siguientes campos conceptuales:

**Identidad y linaje**
- `event_id` (interno, estable)
- `source_event_id` (si existe en la fuente)
- `correlation_id` (para agrupar, si existe o se asigna determinÃ­sticamente)
- `lineage` (links hacia eventos relacionados; definido en RFC-01A)

**Fuente**
- `source_system` (enum cerrado: BANK, ERP, PSP, MARKETPLACE, INTERNAL_LEDGER, OTHER)
- `source_connector` (identificador del adaptador)
- `source_environment` (PROD, SANDBOX, UNKNOWN)

**Tiempo**
- `observed_at` (timestamp cuando Tenon observÃ³/ingiriÃ³)
- `source_timestamp` (timestamp reportado por la fuente; puede ser null)
- `ingested_at` (timestamp interno de ingestiÃ³n; puede igualar observed_at)

**SemÃ¡ntica mÃ­nima (ontologÃ­a cerrada)**
- `event_type` (enum cerrado; ver 4.2)
- `direction` (IN, OUT, NEUTRAL)
- `amount` (valor numÃ©rico)
- `currency` (ISO 4217; si no aplica, UNKNOWN)
- `status_hint` (opcional: AUTH, CAPTURE, SETTLE, REFUND, REVERSAL, ADJUSTMENT, UNKNOWN)  
  *(es â€œhintâ€, no estado oficial; el estado formal se modela en RFC-05)*

**Referencias externas mÃ­nimas**
- `external_reference` (string; invoice_id / payout_id / transfer_id / charge_id, etc.)
- `counterparty_hint` (string o null; nombre/identificador reportado sin interpretaciÃ³n)

**PreservaciÃ³n del crudo**
- `raw_payload_hash` (hash del payload crudo)
- `raw_pointer` (URI/path/locator al crudo append-only)
- `raw_format` (JSON, CSV, XML, PDF, OTHER)

**AuditorÃ­a de transformaciÃ³n**
- `normalizer_version` (versiÃ³n de la regla/paquete)
- `adapter_version` (versiÃ³n del adaptador)
- `schema_version` (versiÃ³n del contrato)

### 4.2 OntologÃ­a cerrada de `event_type` (mÃ­nimo)
El enum `event_type` debe ser cerrado y contener, como mÃ­nimo:

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
- `BALANCE_SNAPSHOT` *(permitido solo como observaciÃ³n de saldo; no reemplaza ledger)*
- `UNKNOWN`

**Reglas:**
- No se agregan tipos ad-hoc por integraciÃ³n.
- Si falta semÃ¡ntica, se usa `UNKNOWN` + evidencia cruda intacta.
- Extensiones del enum requieren RFC (controlado).

---

## Threat Model

### 5.1 Amenazas
- **ContaminaciÃ³n semÃ¡ntica:** adaptadores inyectan â€œinterpretaciÃ³nâ€ (FX, impuestos, contabilidad).
- **ExplosiÃ³n de variantes:** cada fuente crea su â€œmodeloâ€ rompiendo conciliaciÃ³n.
- **ManipulaciÃ³n del crudo:** se altera el payload sin reflejo (rompe cadena de evidencia).
- **Doble ingestiÃ³n:** el mismo hecho entra mÃºltiples veces con pequeÃ±as variaciones.
- **Timestamps engaÃ±osos:** clocks skew o timestamps maliciosos/falsos en fuente.

### 5.2 Controles exigidos por este RFC
- Raw preservation obligatoria (`raw_payload_hash` + `raw_pointer`).
- OntologÃ­a cerrada para evitar semÃ¡ntica arbitraria.
- Campos de versiÃ³n (`normalizer_version`, `adapter_version`, `schema_version`) obligatorios.
- Uso de `UNKNOWN` para evitar â€œinventarâ€ verdad.

---

## Pruebas

### 6.1 Unitarias
- ValidaciÃ³n de presencia de campos obligatorios.
- Rechazo de `event_type` fuera del enum.
- Rechazo de `currency` invÃ¡lida (si no se conoce: UNKNOWN explÃ­cito).
- ProhibiciÃ³n de mutaciÃ³n: un evento â€œcreadoâ€ no cambia.

### 6.2 Propiedades (property-based)
- Determinismo: mismo raw â‡’ mismo `CanonicalEvent` (mismas versiones).
- Monotonicidad append-only: eventos solo se agregan.
- Idempotency-awareness: duplicados exactos detectables por claves definidas (placeholder hasta RFC-01A).

### 6.3 SistÃ©micas
- Ingesta de mÃºltiples fuentes con colisiones de `external_reference`:
  - el sistema no â€œfusionaâ€ sin evidencia; registra eventos separados.
- Replay: reconstrucciÃ³n exacta del set canÃ³nico desde crudos (misma versiÃ³n).

---

## Criterios de AceptaciÃ³n

Este RFC se considera cumplido cuando:
1. Existe definiciÃ³n Ãºnica de `CanonicalEvent` con campos mÃ­nimos y ontologÃ­a cerrada.
2. Se prohÃ­ben explÃ­citamente canones paralelos por fuente.
3. Se exige preservaciÃ³n de crudo mediante hash + puntero.
4. Se exige versionado explÃ­cito (normalizer/adapter/schema).
5. Se define un enum mÃ­nimo de `event_type` y `direction`, con regla `UNKNOWN` como salida segura.
6. Las pruebas (unitarias + propiedades + sistÃ©micas) estÃ¡n especificadas como requisitos verificables.

---

## Assumptions

- No siempre existirÃ¡ `source_event_id` o `external_reference`; el sistema debe tolerarlo sin inventar.
- Algunas fuentes proveerÃ¡n datos incompletos o incoherentes; el canon prioriza evidencia y trazabilidad.
- La semÃ¡ntica completa de identidad/correlaciÃ³n se fija en RFC-01A (siguiente).
