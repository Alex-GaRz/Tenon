# RFC-12 — CHANGE_CONTROL
**Sistema:** Tenon — Sistema de Verdad Financiera Operativa y Conciliación Multisistema  
**Estado:** DRAFT  
**Relación:** Depende de RFC-00_MANIFEST, RFC-01_CANONICAL_EVENT, RFC-01A_CANONICAL_IDS,
RFC-02_INGEST_APPEND_ONLY, RFC-03_NORMALIZATION_RULES, RFC-04_CORRELATION_ENGINE,
RFC-05_MONEY_STATE_MACHINE, RFC-06_DISCREPANCY_TAXONOMY, RFC-07_CAUSALITY_MODEL,
RFC-08_EVENT_SOURCING_EVIDENCE, RFC-09_IMMUTABLE_LEDGER_WORM,
RFC-10_IDEMPOTENCY_GUARDIAN, RFC-11_ADAPTER_CONTRACTS

---

## 1) Propósito

Definir el **control institucional de cambios** para que Tenon preserve
**reproducibilidad histórica, defensa legal y estabilidad semántica**
aun cuando evolucionen contratos, reglas, adaptadores o modelos.

Este RFC gobierna **cómo cambia el sistema sin romper su verdad pasada**.

---

## 2) No-Goals

- Acelerar desarrollo sacrificando disciplina.
- Permitir hotfixes silenciosos en producción.
- Reescribir historia para “alinear” resultados.
- Resolver gestión humana de aprobaciones.
- Definir tooling específico (GitHub, Jira, etc.).

---

## 3) Invariantes

### 3.1 Historia inmutable
- Ningún cambio puede:
  - alterar eventos históricos,
  - re-clasificar discrepancias pasadas,
  - modificar decisiones de idempotencia previas.

### 3.2 Cambios siempre versionados
- Todo cambio relevante introduce:
  - nueva versión de contrato / regla / modelo,
  - convivencia explícita con versiones previas,
  - fecha efectiva declarada.

### 3.3 Compatibilidad explícita
- Todo cambio declara si es:
  - backward-compatible,
  - forward-compatible,
  - breaking change.
- Los breaking changes requieren RFC explícito.

### 3.4 Gobernanza por RFC
- Ningún cambio estructural existe sin RFC aprobado.
- Prohibidos cambios “técnicos” sin impacto declarado.

---

## 4) Ámbitos de cambio gobernados

Este RFC aplica obligatoriamente a cambios en:

- `/contracts` (schemas, ontologías, enums)
- `/core` (reglas canónicas, motores, estados)
- `/adapters` (interfaces, declaraciones)
- Reglas de normalización
- Reglas de correlación
- Taxonomías de discrepancias
- Modelos de causalidad
- Reglas de idempotencia

---

## 5) Tipos de cambio

### 5.1 Patch Change
- Corrección sin impacto semántico.
- No altera resultados históricos.
- Ejemplo: fix de validación, typo en schema no efectivo.

### 5.2 Minor Change
- Extiende capacidad sin romper compatibilidad.
- Eventos históricos siguen siendo válidos.
- Ejemplo: nuevo `event_type` opcional.

### 5.3 Major (Breaking) Change
- Cambia interpretación o contratos.
- Requiere:
  - RFC dedicado,
  - versión nueva,
  - estrategia de convivencia,
  - justificación institucional.

---

## 6) Protocolo de cambio (alto nivel)

1. Identificación del cambio propuesto.
2. Clasificación (Patch / Minor / Major).
3. Redacción de RFC correspondiente.
4. Aprobación institucional.
5. Introducción de nueva versión (sin borrar la anterior).
6. Registro del cambio como evidencia (RFC-08).
7. Monitoreo post-cambio (RFC-13).

---

## 7) Evidencia de cambio

Todo cambio aprobado produce:

- `ChangeEvent` (EvidenceEvent)
- Referencia a:
  - RFC aprobado,
  - versiones afectadas,
  - fecha efectiva,
  - componentes impactados.

Estos eventos se escriben en el ledger WORM.

---

## 8) Threat Model

### 8.1 Amenazas
- **Cambios silenciosos** que rompen reproducibilidad.
- **Refactors disfrazados** de mejoras técnicas.
- **Version drift** no controlado.
- **Reprocesamiento retroactivo** de historia.
- **Presión operativa** para “arreglar resultados”.

### 8.2 Controles exigidos
- RFC obligatorio para cambios semánticos.
- Versionado coexistente.
- Prohibición de mutación histórica.
- Evidencia inmutable de cambios.
- Auditoría de compatibilidad.

---

## 9) Pruebas

### 9.1 Unitarias
- Validación de versionado correcto.
- Rechazo de cambios sin RFC.
- Convivencia de versiones activas.

### 9.2 Propiedades
- Replay histórico produce mismos resultados con versión original.
- Nuevas versiones solo afectan datos nuevos.
- No contaminación cruzada entre versiones.

### 9.3 Sistémicas
- Simulación de upgrade con historia extensa.
- Rollout parcial de nuevas reglas.
- Auditoría de cambio tras incidente simulado.
- Comparación before/after con explicación.

---

## 10) Criterios de Aceptación

Este RFC se considera cumplido cuando:
1. Todo cambio relevante está gobernado por RFC.
2. La historia permanece reproducible bajo versiones originales.
3. Los breaking changes son explícitos y justificados.
4. Existe evidencia inmutable de cada cambio.
5. El sistema resiste presión operativa sin degradar verdad.

---

## 11) Assumptions

- El cambio es inevitable; la corrupción no.
- La disciplina de versionado es más barata que el litigio.
- Gobernar cambios es parte del producto, no overhead.
