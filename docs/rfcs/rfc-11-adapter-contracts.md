# RFC-11 â€” ADAPTER_CONTRACTS
**Sistema:** Tenon â€” Sistema de Verdad Financiera Operativa y ConciliaciÃ³n Multisistema  
**Estado:** DRAFT  
**RelaciÃ³n:** Depende de RFC-00_MANIFEST, RFC-01_CANONICAL_EVENT, RFC-01A_CANONICAL_IDS,
RFC-02_INGEST_APPEND_ONLY, RFC-03_NORMALIZATION_RULES, RFC-08_EVENT_SOURCING_EVIDENCE,
RFC-09_IMMUTABLE_LEDGER_WORM, RFC-10_IDEMPOTENCY_GUARDIAN

---

## PropÃ³sito

Definir **fronteras estrictas de integraciÃ³n** para que todo sistema externo
(banco, ERP, PSP, marketplace, ledger interno) se conecte a Tenon **exclusivamente**
a travÃ©s de **adaptadores declarativos**, con contratos explÃ­citos y pruebas de conformidad.

El objetivo institucional es **crecer sin corrupciÃ³n del core**:
- los adaptadores **declaran** observaciones,
- el core **verifica, preserva y diagnostica**,
- ninguna integraciÃ³n introduce dominio, lÃ³gica o semÃ¡ntica propia en el nÃºcleo.

---

## No-Goals

- Implementar adaptadores concretos.
- Resolver autenticaciÃ³n/seguridad de transporte.
- Optimizar performance o batching.
- Permitir â€œshortcutsâ€ directos al core.
- Permitir que integraciones modifiquen contratos o reglas canÃ³nicas.

---

## Invariantes

### 3.1 Frontera inviolable core â†” adapters
- El core **no conoce** sistemas externos.
- Los adaptadores **no ejecutan** lÃ³gica de dominio del core.
- Prohibido que un adaptador:
  - escriba en `/core`,
  - modifique `/contracts`,
  - altere reglas canÃ³nicas o de normalizaciÃ³n.

### 3.2 Integraciones como declaraciones, no acciones
- Un adaptador **declara observaciones** (payload crudo + metadatos).
- Nunca declara â€œverdadâ€, â€œestado finalâ€ ni â€œresoluciÃ³nâ€.

### 3.3 Contratos obligatorios
- Todo adaptador debe cumplir contratos definidos en `/contracts`.
- Sin contrato vÃ¡lido â‡’ la ingesta es rechazada.

### 3.4 Conformidad verificable
- Cada adaptador pasa una **conformance suite** canÃ³nica.
- Sin conformidad â‡’ no se despliega ni ingiere.

---

## Contratos (conceptuales)

### 4.1 AdapterContract (abstracto)

Cada adaptador debe declarar:

- `adapter_id`
- `adapter_type` (BANK | ERP | PSP | MARKETPLACE | INTERNAL | OTHER)
- `supported_formats[]` (JSON | CSV | XML | PDF | OTHER)
- `declared_event_capabilities[]` (quÃ© tipos de eventos puede observar)
- `schema_version`
- `adapter_version`

---

### 4.2 IngestDeclaration (interfaz mÃ­nima)

Todo adaptador solo puede emitir:

- `source_system`
- `source_event_id` (si existe)
- `external_reference` (si existe)
- `payload_raw` (sin mutaciÃ³n)
- `payload_format`
- `source_timestamp` (si existe)
- `adapter_version`

**Reglas:**
- Prohibido emitir `event_type`, `state`, `discrepancy`, `cause`.
- Prohibido emitir campos derivados del canon.
- Prohibido â€œnormalizarâ€ o â€œarreglarâ€ datos.

---

### 4.3 UbicaciÃ³n contractual

- Definiciones de contratos viven en:
  - `/contracts/adapters/`
  - `/contracts/schemas/`
- Los adaptadores **consumen** contratos; no los definen.

---

## Flujo de integraciÃ³n (alto nivel)

1. El adaptador recibe datos del sistema externo.
2. Preserva el payload crudo sin mutar.
3. Declara una `IngestDeclaration`.
4. El core valida:
   - contrato,
   - esquema,
   - idempotencia,
   - append-only.
5. Si falla la validaciÃ³n â‡’ rechazo con evidencia registrada.
6. Si pasa â‡’ se continÃºa con RFC-02 (ingesta).

---

## Conformance Suite (obligatoria)

Cada adaptador debe pasar un set mÃ­nimo de pruebas canÃ³nicas:

### 6.1 Pruebas de contrato
- Cumplimiento de esquema.
- Versiones declaradas correctas.
- Campos prohibidos ausentes.

### 6.2 Pruebas de comportamiento
- No mutaciÃ³n de payload crudo.
- Reintentos â‡’ idempotencia preservada.
- EmisiÃ³n consistente bajo replay.

### 6.3 Pruebas negativas
- Intento de escribir campos canÃ³nicos â‡’ rechazado.
- Intento de ejecutar lÃ³gica de dominio â‡’ rechazado.
- Intento de bypass del Guardian â‡’ detectado.

Los resultados de la conformance suite son **artefactos auditables**.

---

## Threat Model

### 7.1 Amenazas
- **ContaminaciÃ³n del core** por lÃ³gica especÃ­fica de un proveedor.
- **Integraciones â€œinteligentesâ€** que alteran semÃ¡ntica.
- **Cambios silenciosos** en payloads externos.
- **Bypass contractual** para acelerar integraciones.
- **Vendor lock-in semÃ¡ntico**.

### 7.2 Controles exigidos
- Contratos explÃ­citos y versionados.
- Conformance suite obligatoria.
- Rechazo por defecto ante desviaciÃ³n.
- Evidencia de rechazo registrada.
- ProhibiciÃ³n tÃ©cnica de acceso al core.

---

## Pruebas

### 8.1 Unitarias
- ValidaciÃ³n estricta de esquemas.
- Rechazo de campos no permitidos.
- Versionado obligatorio.

### 8.2 Propiedades
- Determinismo: mismo input â‡’ misma declaraciÃ³n.
- No side-effects: el adaptador no altera estado del core.
- Monotonicidad: la historia de integraciones solo crece.

### 8.3 SistÃ©micas
- Integraciones mÃºltiples con contratos distintos.
- Fallos parciales del adaptador.
- Replay histÃ³rico con adaptadores versionados.
- Intentos de bypass del contrato.

---

## Criterios de AceptaciÃ³n

Este RFC se considera cumplido cuando:
1. NingÃºn adaptador puede introducir dominio o semÃ¡ntica.
2. Toda integraciÃ³n pasa por contratos explÃ­citos y pruebas de conformidad.
3. El core permanece inalterable ante crecimiento de integraciones.
4. Las violaciones quedan registradas como evidencia.
5. La arquitectura soporta auditorÃ­a y escalamiento institucional.

---

## Assumptions

- Los sistemas externos son inherentemente no confiables.
- La disciplina de fronteras es mÃ¡s valiosa que la velocidad inicial.
- Sin contratos estrictos, la verdad operativa se degrada con el tiempo.
