# RFC-11 — ADAPTER_CONTRACTS
**Sistema:** Tenon — Sistema de Verdad Financiera Operativa y Conciliación Multisistema  
**Estado:** DRAFT  
**Relación:** Depende de RFC-00_MANIFEST, RFC-01_CANONICAL_EVENT, RFC-01A_CANONICAL_IDS,
RFC-02_INGEST_APPEND_ONLY, RFC-03_NORMALIZATION_RULES, RFC-08_EVENT_SOURCING_EVIDENCE,
RFC-09_IMMUTABLE_LEDGER_WORM, RFC-10_IDEMPOTENCY_GUARDIAN

---

## Propósito

Definir **fronteras estrictas de integración** para que todo sistema externo
(banco, ERP, PSP, marketplace, ledger interno) se conecte a Tenon **exclusivamente**
a través de **adaptadores declarativos**, con contratos explí­citos y pruebas de conformidad.

El objetivo institucional es **crecer sin corrupción del core**:
- los adaptadores **declaran** observaciones,
- el core **verifica, preserva y diagnostica**,
- ninguna integración introduce dominio, lógica o semántica propia en el níºcleo.

---

## No-Goals

- Implementar adaptadores concretos.
- Resolver autenticación/seguridad de transporte.
- Optimizar performance o batching.
- Permitir “shortcuts” directos al core.
- Permitir que integraciones modifiquen contratos o reglas canónicas.

---

## Invariantes

### 3.1 Frontera inviolable core â†” adapters
- El core **no conoce** sistemas externos.
- Los adaptadores **no ejecutan** lógica de dominio del core.
- Prohibido que un adaptador:
  - escriba en `/core`,
  - modifique `/contracts`,
  - altere reglas canónicas o de normalización.

### 3.2 Integraciones como declaraciones, no acciones
- Un adaptador **declara observaciones** (payload crudo + metadatos).
- Nunca declara “verdad”, “estado final” ni “resolución”.

### 3.3 Contratos obligatorios
- Todo adaptador debe cumplir contratos definidos en `/contracts`.
- Sin contrato válido â‡’ la ingesta es rechazada.

### 3.4 Conformidad verificable
- Cada adaptador pasa una **conformance suite** canónica.
- Sin conformidad â‡’ no se despliega ni ingiere.

---

## Contratos (conceptuales)

### 4.1 AdapterContract (abstracto)

Cada adaptador debe declarar:

- `adapter_id`
- `adapter_type` (BANK | ERP | PSP | MARKETPLACE | INTERNAL | OTHER)
- `supported_formats[]` (JSON | CSV | XML | PDF | OTHER)
- `declared_event_capabilities[]` (qué tipos de eventos puede observar)
- `schema_version`
- `adapter_version`

---

### 4.2 IngestDeclaration (interfaz mí­nima)

Todo adaptador solo puede emitir:

- `source_system`
- `source_event_id` (si existe)
- `external_reference` (si existe)
- `payload_raw` (sin mutación)
- `payload_format`
- `source_timestamp` (si existe)
- `adapter_version`

**Reglas:**
- Prohibido emitir `event_type`, `state`, `discrepancy`, `cause`.
- Prohibido emitir campos derivados del canon.
- Prohibido “normalizar” o “arreglar” datos.

---

### 4.3 Ubicación contractual

- Definiciones de contratos viven en:
  - `/contracts/adapters/`
  - `/contracts/schemas/`
- Los adaptadores **consumen** contratos; no los definen.

---

## Flujo de integración (alto nivel)

1. El adaptador recibe datos del sistema externo.
2. Preserva el payload crudo sin mutar.
3. Declara una `IngestDeclaration`.
4. El core valida:
   - contrato,
   - esquema,
   - idempotencia,
   - append-only.
5. Si falla la validación â‡’ rechazo con evidencia registrada.
6. Si pasa â‡’ se continíºa con RFC-02 (ingesta).

---

## Conformance Suite (obligatoria)

Cada adaptador debe pasar un set mí­nimo de pruebas canónicas:

### 6.1 Pruebas de contrato
- Cumplimiento de esquema.
- Versiones declaradas correctas.
- Campos prohibidos ausentes.

### 6.2 Pruebas de comportamiento
- No mutación de payload crudo.
- Reintentos â‡’ idempotencia preservada.
- Emisión consistente bajo replay.

### 6.3 Pruebas negativas
- Intento de escribir campos canónicos â‡’ rechazado.
- Intento de ejecutar lógica de dominio â‡’ rechazado.
- Intento de bypass del Guardian â‡’ detectado.

Los resultados de la conformance suite son **artefactos auditables**.

---

## Threat Model

### 7.1 Amenazas
- **Contaminación del core** por lógica especí­fica de un proveedor.
- **Integraciones “inteligentes”** que alteran semántica.
- **Cambios silenciosos** en payloads externos.
- **Bypass contractual** para acelerar integraciones.
- **Vendor lock-in semántico**.

### 7.2 Controles exigidos
- Contratos explí­citos y versionados.
- Conformance suite obligatoria.
- Rechazo por defecto ante desviación.
- Evidencia de rechazo registrada.
- Prohibición técnica de acceso al core.

---

## Pruebas

### 8.1 Unitarias
- Validación estricta de esquemas.
- Rechazo de campos no permitidos.
- Versionado obligatorio.

### 8.2 Propiedades
- Determinismo: mismo input â‡’ misma declaración.
- No side-effects: el adaptador no altera estado del core.
- Monotonicidad: la historia de integraciones solo crece.

### 8.3 Sistémicas
- Integraciones míºltiples con contratos distintos.
- Fallos parciales del adaptador.
- Replay histórico con adaptadores versionados.
- Intentos de bypass del contrato.

---

## Criterios de Aceptación

Este RFC se considera cumplido cuando:
1. Ningíºn adaptador puede introducir dominio o semántica.
2. Toda integración pasa por contratos explí­citos y pruebas de conformidad.
3. El core permanece inalterable ante crecimiento de integraciones.
4. Las violaciones quedan registradas como evidencia.
5. La arquitectura soporta auditorí­a y escalamiento institucional.

---

## Assumptions

- Los sistemas externos son inherentemente no confiables.
- La disciplina de fronteras es más valiosa que la velocidad inicial.
- Sin contratos estrictos, la verdad operativa se degrada con el tiempo.
