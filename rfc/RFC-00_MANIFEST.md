# RFC-00 — MANIFEST
**Sistema:** Tenon — Sistema de Verdad Financiera Operativa y Conciliación Multisistema  
**Estado:** DRAFT  
**Inmutabilidad:** Este RFC es constitucional. Cambios solo vía RFC-00A_* (Amendment) con justificación institucional.

---

## 1) Propósito

Constituir formalmente a **Tenon** como un sistema de **verdad financiera operativa**:
- observa eventos y estados financieros provenientes de múltiples sistemas,
- correlaciona y reconstruye “películas” operativas,
- detecta discrepancias,
- explica causalidad y prioriza acciones,
- produce evidencia forense reproducible.

Tenon existe para **reducir riesgo operativo y riesgo de integridad de datos financieros** mediante trazabilidad total, determinismo, y evidencia verificable.

---

## 2) No-Goals

Tenon **NO** es, ni será:
- un sistema de pagos / ejecución de transferencias / orquestación de movimientos de dinero.
- un libro contable oficial, ERP, GL, subledger oficial, ni reemplazo de contabilidad.
- un sistema que “corrige” contabilidad por su cuenta.
- un motor de pricing, facturación o cálculo fiscal como fuente oficial.
- una plataforma que dependa de “magia IA” para afirmar verdad sin evidencia.
- un data warehouse genérico ni un ETL generalista como producto.

---

## 3) Invariantes

1. **Append-only:** ningún dato ingerido o derivado se borra ni se sobrescribe; solo se agregan nuevas versiones/eventos.
2. **Trazabilidad total:** todo artefacto derivado referencia su origen (crudo) + transformaciones + versiones.
3. **Separación core/adapters:** el core define invariantes; adapters solo traducen y declaran, jamás imponen dominio.
4. **Explicabilidad por diseño:** toda discrepancia y correlación debe producir explicación estructurada + evidencia.
5. **Determinismo:** mismo input histórico ⇒ mismo output (ledger/evidencia/discrepancias) para una misma versión del sistema.
6. **Idempotencia obligatoria:** reintentos no pueden producir duplicados ni divergencia silenciosa.
7. **Fallos explícitos:** el sistema nunca “asume” verdad si falta evidencia; produce estado “insuficiente” y lo registra.
8. **Versionado institucional:** contratos y reglas que afecten semántica o reproducibilidad deben versionarse y quedar auditables.

---

## 4) Contratos (institucionales, no técnicos todavía)

**Ámbitos contractuales que quedan fijados desde hoy:**
- `/contracts` contendrá el canon y schemas versionados.
- Cualquier cambio de contrato que afecte interpretación o compatibilidad requiere RFC de control de cambios.
- Los adapters se consideran **no confiables**: Tenon valida, no confía.

**Promesa formal del sistema:**
- Tenon puede demostrar “cómo sabe lo que sabe” y reproducirlo.

---

## 5) Threat Model (institucional)

### 5.1 Amenazas principales
- **Manipulación/alteración posterior** de datos para encubrir discrepancias.
- **Reescritura silenciosa** de contratos o normalización que invalide la reproducibilidad.
- **Contaminación del core** con reglas de negocio externas (ERP-specific, PSP-specific).
- **Falsos positivos/negativos** por normalización interpretativa (p.ej., “arreglar” FX o impuestos sin evidencia).
- **Duplicación por reintentos** (sin idempotencia) generando “realidades paralelas”.
- **Dependencia de juicio implícito** (humano o IA) sin registro, sin evidencia, sin versión.

### 5.2 Controles exigidos por diseño (derivados)
- WORM/ledger inmutable para evidencia (etapas futuras).
- Hashing, firma, y cadena de custodia verificable (etapas futuras).
- Controles de versionado y CI que bloqueen cambios no autorizados al core/contratos (ETAPA 0 ya lo habilita).

---

## 6) Pruebas

### 6.1 Unitarias
- Para cada invariante implementado: tests que prueben que no se permite mutación destructiva.

### 6.2 Propiedades (property-based)
- **Determinismo:** misma secuencia de eventos ⇒ mismo resultado.
- **Idempotencia:** reintento N veces ⇒ 1 efecto lógico.
- **Monotonicidad append-only:** el historial crece; nunca se reduce.

### 6.3 Sistémicas
- Replay de historia: reconstrucción completa desde evidencia.
- Resistencia a eventos tardíos, duplicados, clocks skew.
- Split-brain: dos fuentes conflictivas ⇒ discrepancia explicada, no “arreglo silencioso”.

---

## 7) Criterios de Aceptación

RFC-00 se considera **aprobable** cuando:
1. Declara inequívocamente qué es Tenon y qué invalida el sistema.
2. Los No-Goals bloquean explícitamente pagos/contabilidad oficial/ejecución.
3. Invariantes están definidos como reglas verificables (no slogans).
4. Threat Model cubre manipulación, mutación de contratos, contaminación del core e idempotencia.
5. Queda explícito que toda verdad debe estar respaldada por evidencia y versión.

---

## 8) Assumptions

- Tenon operará en entornos donde existen múltiples “fuentes de verdad” incompatibles (ERP/PSP/Banco/Ledger interno).
- Existirá presión organizacional por convertir Tenon en sistema de ejecución/contabilidad; este RFC lo prohíbe.
- La adopción enterprise exige defensa legal y reconstrucción histórica (película), no reportes estáticos.
