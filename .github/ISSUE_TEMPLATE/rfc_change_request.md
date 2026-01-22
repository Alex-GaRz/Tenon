---
name: RFC Change Request
about: Solicitar cambio a /core, /contracts, o crear nuevo RFC
title: '[RFC-XX] '
labels: rfc-required
assignees: ''
---

## Tipo de Request

<!-- Marca una opción -->

- [ ] **Nuevo RFC** (proponer nueva funcionalidad/diseño)
- [ ] **Cambio a /core** (modificar lógica de invariantes)
- [ ] **Cambio a /contracts** (modificar contratos canónicos)
- [ ] **Enmienda a RFC-00** (modificar documento constitucional - muy raro)


## Propósito

<!-- Describe qué problema resuelve o qué capacidad agrega -->


## Justificación Institucional

<!-- 
Por qué es necesario este cambio para el sistema.
NO usar: "más fácil", "más rápido", "preferencia personal", "deadline"
SÍ usar: "necesario para cumplir invariante X", "requerido por threat model Y", "crítico para reproducibilidad"
-->


## Alcance del Cambio

### Rutas afectadas

- [ ] `/core/**` - especificar: _________________
- [ ] `/contracts/**` - especificar: _________________
- [ ] `docs/rfcs/RFC-00_MANIFEST.md` (enmienda)
- [ ] Otro RFC: _________________


### Invariantes impactados

<!-- Marca TODOS los invariantes que este cambio podría afectar -->

- [ ] Append-only
- [ ] Trazabilidad total
- [ ] Separación core/adapters
- [ ] Explicabilidad por diseño
- [ ] Determinismo
- [ ] Idempotencia obligatoria
- [ ] Fallos explícitos
- [ ] Versionado institucional

**Explicación del impacto:**

<!-- Para cada invariante marcado, explica cómo el cambio lo afecta y cómo se preservará -->


## No-Goals Check

<!-- Confirma que el cambio NO viola no-goals del RFC-00 -->

**¿Este cambio introduce alguna de las siguientes funcionalidades prohibidas?**

- [ ] Ejecución de pagos/transferencias
- [ ] Posteo a libro contable oficial (GL/ERP) como fuente
- [ ] Auto-corrección de contabilidad
- [ ] Cálculo de precios/impuestos como fuente oficial
- [ ] Dependencia de IA para afirmar verdad sin evidencia

<!-- Si marcaste alguna, debes justificar por qué es necesario relajar el no-goal (requiere RFC-00A_* enmienda) -->

**Justificación si aplica:**


## Propuesta Técnica (Opcional en esta etapa)

<!-- Esbozo técnico de cómo implementarías el cambio. Puede refinarse en el RFC formal -->


## Compatibilidad Retroactiva

**¿Este cambio es un breaking change?**

- [ ] Sí - rompe contratos/APIs existentes
- [ ] No - compatible con versión actual

**Si es breaking change:**
- ¿Qué se rompe?
- ¿Cuál es el plan de migración?
- ¿Cómo se mantiene reproducibilidad de evidencia histórica?


## Artefactos Requeridos

<!-- Checklist de lo que se necesitará producir si este RFC es aprobado -->

- [ ] Nuevo documento RFC (docs/rfcs/RFC-XX.md)
- [ ] Actualización de contratos con versionado (si aplica)
- [ ] Tests de invariantes
- [ ] Tests de property-based (si aplica)
- [ ] Documentación de migración (si breaking change)
- [ ] Actualización de adapters (si cambio de contratos)


## Timeline Propuesto

<!-- Urgencia y timeline esperado. NO es justificación para bypassear protocolo -->

- **Urgencia:** (Low / Medium / High)
- **Fecha deseada:** 
- **Bloqueadores conocidos:**


## Stakeholders

<!-- Quién debe revisar/aprobar este cambio -->

- **Arquitectos requeridos:** @________
- **Equipos afectados:** (ej: adapters team, core team, etc.)
- **Legal/Compliance:** (si aplica)


## Referencias

<!-- Links a documentos, issues, PRs relacionados -->

- Related issues: #___
- Related RFCs: RFC-XX
- External docs: ___


---

<!-- 
IMPORTANTE: Este issue NO autoriza cambios por sí solo.
Debe seguirse el proceso completo:
1. Crear RFC formal (docs/rfcs/RFC-XX.md)
2. Review institucional
3. Aprobación de CODEOWNERS
4. Implementación en PR separado con referencia a RFC aprobado

Ver: docs/governance/Protected_Paths_Policy.md
-->
