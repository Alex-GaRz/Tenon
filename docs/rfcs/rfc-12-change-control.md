# RFC-12 â€” CHANGE_CONTROL
**Sistema:** Tenon â€” Sistema de Verdad Financiera Operativa y ConciliaciÃ³n Multisistema  
**Estado:** DRAFT  
**RelaciÃ³n:** Depende de RFC-00_MANIFEST, RFC-01_CANONICAL_EVENT, RFC-01A_CANONICAL_IDS,
RFC-02_INGEST_APPEND_ONLY, RFC-03_NORMALIZATION_RULES, RFC-04_CORRELATION_ENGINE,
RFC-05_MONEY_STATE_MACHINE, RFC-06_DISCREPANCY_TAXONOMY, RFC-07_CAUSALITY_MODEL,
RFC-08_EVENT_SOURCING_EVIDENCE, RFC-09_IMMUTABLE_LEDGER_WORM,
RFC-10_IDEMPOTENCY_GUARDIAN, RFC-11_ADAPTER_CONTRACTS

---

## PropÃ³sito

Definir el **control institucional de cambios** para que Tenon preserve
**reproducibilidad histÃ³rica, defensa legal y estabilidad semÃ¡ntica**
aun cuando evolucionen contratos, reglas, adaptadores o modelos.

Este RFC gobierna **cÃ³mo cambia el sistema sin romper su verdad pasada**.

---

## No-Goals

- Acelerar desarrollo sacrificando disciplina.
- Permitir hotfixes silenciosos en producciÃ³n.
- Reescribir historia para â€œalinearâ€ resultados.
- Resolver gestiÃ³n humana de aprobaciones.
- Definir tooling especÃ­fico (GitHub, Jira, etc.).

---

## Invariantes

### 3.1 Historia inmutable
- NingÃºn cambio puede:
  - alterar eventos histÃ³ricos,
  - re-clasificar discrepancias pasadas,
  - modificar decisiones de idempotencia previas.

### 3.2 Cambios siempre versionados
- Todo cambio relevante introduce:
  - nueva versiÃ³n de contrato / regla / modelo,
  - convivencia explÃ­cita con versiones previas,
  - fecha efectiva declarada.

### 3.3 Compatibilidad explÃ­cita
- Todo cambio declara si es:
  - backward-compatible,
  - forward-compatible,
  - breaking change.
- Los breaking changes requieren RFC explÃ­cito.

### 3.4 Gobernanza por RFC
- NingÃºn cambio estructural existe sin RFC aprobado.
- Prohibidos cambios â€œtÃ©cnicosâ€ sin impacto declarado.

---

## Ãmbitos de cambio gobernados

Este RFC aplica obligatoriamente a cambios en:

- `/contracts` (schemas, ontologÃ­as, enums)
- `/core` (reglas canÃ³nicas, motores, estados)
- `/adapters` (interfaces, declaraciones)
- Reglas de normalizaciÃ³n
- Reglas de correlaciÃ³n
- TaxonomÃ­as de discrepancias
- Modelos de causalidad
- Reglas de idempotencia

---

## Tipos de cambio

### 5.1 Patch Change
- CorrecciÃ³n sin impacto semÃ¡ntico.
- No altera resultados histÃ³ricos.
- Ejemplo: fix de validaciÃ³n, typo en schema no efectivo.

### 5.2 Minor Change
- Extiende capacidad sin romper compatibilidad.
- Eventos histÃ³ricos siguen siendo vÃ¡lidos.
- Ejemplo: nuevo `event_type` opcional.

### 5.3 Major (Breaking) Change
- Cambia interpretaciÃ³n o contratos.
- Requiere:
  - RFC dedicado,
  - versiÃ³n nueva,
  - estrategia de convivencia,
  - justificaciÃ³n institucional.

---

## Protocolo de cambio (alto nivel)

1. IdentificaciÃ³n del cambio propuesto.
2. ClasificaciÃ³n (Patch / Minor / Major).
3. RedacciÃ³n de RFC correspondiente.
4. AprobaciÃ³n institucional.
5. IntroducciÃ³n de nueva versiÃ³n (sin borrar la anterior).
6. Registro del cambio como evidencia (RFC-08).
7. Monitoreo post-cambio (RFC-13).

---

## Evidencia de cambio

Todo cambio aprobado produce:

- `ChangeEvent` (EvidenceEvent)
- Referencia a:
  - RFC aprobado,
  - versiones afectadas,
  - fecha efectiva,
  - componentes impactados.

Estos eventos se escriben en el ledger WORM.

---

## Threat Model

### 8.1 Amenazas
- **Cambios silenciosos** que rompen reproducibilidad.
- **Refactors disfrazados** de mejoras tÃ©cnicas.
- **Version drift** no controlado.
- **Reprocesamiento retroactivo** de historia.
- **PresiÃ³n operativa** para â€œarreglar resultadosâ€.

### 8.2 Controles exigidos
- RFC obligatorio para cambios semÃ¡nticos.
- Versionado coexistente.
- ProhibiciÃ³n de mutaciÃ³n histÃ³rica.
- Evidencia inmutable de cambios.
- AuditorÃ­a de compatibilidad.

---

## Pruebas

### 9.1 Unitarias
- ValidaciÃ³n de versionado correcto.
- Rechazo de cambios sin RFC.
- Convivencia de versiones activas.

### 9.2 Propiedades
- Replay histÃ³rico produce mismos resultados con versiÃ³n original.
- Nuevas versiones solo afectan datos nuevos.
- No contaminaciÃ³n cruzada entre versiones.

### 9.3 SistÃ©micas
- SimulaciÃ³n de upgrade con historia extensa.
- Rollout parcial de nuevas reglas.
- AuditorÃ­a de cambio tras incidente simulado.
- ComparaciÃ³n before/after con explicaciÃ³n.

---

## Criterios de AceptaciÃ³n

Este RFC se considera cumplido cuando:
1. Todo cambio relevante estÃ¡ gobernado por RFC.
2. La historia permanece reproducible bajo versiones originales.
3. Los breaking changes son explÃ­citos y justificados.
4. Existe evidencia inmutable de cada cambio.
5. El sistema resiste presiÃ³n operativa sin degradar verdad.

---

## Assumptions

- El cambio es inevitable; la corrupciÃ³n no.
- La disciplina de versionado es mÃ¡s barata que el litigio.
- Gobernar cambios es parte del producto, no overhead.
