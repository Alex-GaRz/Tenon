## Referencia a RFC
- RFC: RFC-00

## Tipo de cambio
- [x] Tooling / CI
- [x] RFC
- [ ] Contracts
- [ ] Core

## Descripción del Cambio (máx 5 líneas)
Se agregan guardrails de gobernanza (docs/policies/templates/scripts/CI) para RFC-00.
No se toca lógica de producto. No se toca /core ni /contracts.

## Rutas Tocadas
- docs/**
- .github/**
- scripts/**
- .githooks/**

## Impacto en Invariantes
- [x] No hay cambios en /core
- [x] No hay cambios en /contracts
- [x] No se introduce ejecución de dinero (No-Goals)

## Evidencia de tests
- GitHub Actions en este PR (checks deben quedar en verde)

## Riesgo institucional
Bajo: cambios solo de gobernanza/CI.
