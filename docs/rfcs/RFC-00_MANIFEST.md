# RFC-00 â€” MANIFEST
**Sistema:** Tenon â€” Sistema de Verdad Financiera Operativa y ConciliaciÃ³n Multisistema  
**Estado:** DRAFT  
**Inmutabilidad:** Este RFC es constitucional. Cambios solo vÃ­a RFC-00A_* (Amendment) con justificaciÃ³n institucional.

---

## PropÃ³sito

Constituir formalmente a **Tenon** como un sistema de **verdad financiera operativa**:
- observa eventos y estados financieros provenientes de mÃºltiples sistemas,
- correlaciona y reconstruye â€œpelÃ­culasâ€ operativas,
- detecta discrepancias,
- explica causalidad y prioriza acciones,
- produce evidencia forense reproducible.

Tenon existe para **reducir riesgo operativo y riesgo de integridad de datos financieros** mediante trazabilidad total, determinismo, y evidencia verificable.

---

## No-Goals

Tenon **NO** es, ni serÃ¡:
- un sistema de pagos / ejecuciÃ³n de transferencias / orquestaciÃ³n de movimientos de dinero.
- un libro contable oficial, ERP, GL, subledger oficial, ni reemplazo de contabilidad.
- un sistema que â€œcorrigeâ€ contabilidad por su cuenta.
- un motor de pricing, facturaciÃ³n o cÃ¡lculo fiscal como fuente oficial.
- una plataforma que dependa de â€œmagia IAâ€ para afirmar verdad sin evidencia.
- un data warehouse genÃ©rico ni un ETL generalista como producto.

---

## Invariantes

1. **Append-only:** ningÃºn dato ingerido o derivado se borra ni se sobrescribe; solo se agregan nuevas versiones/eventos.
2. **Trazabilidad total:** todo artefacto derivado referencia su origen (crudo) + transformaciones + versiones.
3. **SeparaciÃ³n core/adapters:** el core define invariantes; adapters solo traducen y declaran, jamÃ¡s imponen dominio.
4. **Explicabilidad por diseÃ±o:** toda discrepancia y correlaciÃ³n debe producir explicaciÃ³n estructurada + evidencia.
5. **Determinismo:** mismo input histÃ³rico â‡’ mismo output (ledger/evidencia/discrepancias) para una misma versiÃ³n del sistema.
6. **Idempotencia obligatoria:** reintentos no pueden producir duplicados ni divergencia silenciosa.
7. **Fallos explÃ­citos:** el sistema nunca â€œasumeâ€ verdad si falta evidencia; produce estado â€œinsuficienteâ€ y lo registra.
8. **Versionado institucional:** contratos y reglas que afecten semÃ¡ntica o reproducibilidad deben versionarse y quedar auditables.

---

## Contratos (institucionales, no tÃ©cnicos todavÃ­a)

**Ãmbitos contractuales que quedan fijados desde hoy:**
- `/contracts` contendrÃ¡ el canon y schemas versionados.
- Cualquier cambio de contrato que afecte interpretaciÃ³n o compatibilidad requiere RFC de control de cambios.
- Los adapters se consideran **no confiables**: Tenon valida, no confÃ­a.

**Promesa formal del sistema:**
- Tenon puede demostrar â€œcÃ³mo sabe lo que sabeâ€ y reproducirlo.

---

## Threat Model (institucional)

### 5.1 Amenazas principales
- **ManipulaciÃ³n/alteraciÃ³n posterior** de datos para encubrir discrepancias.
- **Reescritura silenciosa** de contratos o normalizaciÃ³n que invalide la reproducibilidad.
- **ContaminaciÃ³n del core** con reglas de negocio externas (ERP-specific, PSP-specific).
- **Falsos positivos/negativos** por normalizaciÃ³n interpretativa (p.ej., â€œarreglarâ€ FX o impuestos sin evidencia).
- **DuplicaciÃ³n por reintentos** (sin idempotencia) generando â€œrealidades paralelasâ€.
- **Dependencia de juicio implÃ­cito** (humano o IA) sin registro, sin evidencia, sin versiÃ³n.

### 5.2 Controles exigidos por diseÃ±o (derivados)
- WORM/ledger inmutable para evidencia (etapas futuras).
- Hashing, firma, y cadena de custodia verificable (etapas futuras).
- Controles de versionado y CI que bloqueen cambios no autorizados al core/contratos (ETAPA 0 ya lo habilita).

---

## Pruebas

### 6.1 Unitarias
- Para cada invariante implementado: tests que prueben que no se permite mutaciÃ³n destructiva.

### 6.2 Propiedades (property-based)
- **Determinismo:** misma secuencia de eventos â‡’ mismo resultado.
- **Idempotencia:** reintento N veces â‡’ 1 efecto lÃ³gico.
- **Monotonicidad append-only:** el historial crece; nunca se reduce.

### 6.3 SistÃ©micas
- Replay de historia: reconstrucciÃ³n completa desde evidencia.
- Resistencia a eventos tardÃ­os, duplicados, clocks skew.
- Split-brain: dos fuentes conflictivas â‡’ discrepancia explicada, no â€œarreglo silenciosoâ€.

---

## Criterios de AceptaciÃ³n

RFC-00 se considera **aprobable** cuando:
1. Declara inequÃ­vocamente quÃ© es Tenon y quÃ© invalida el sistema.
2. Los No-Goals bloquean explÃ­citamente pagos/contabilidad oficial/ejecuciÃ³n.
3. Invariantes estÃ¡n definidos como reglas verificables (no slogans).
4. Threat Model cubre manipulaciÃ³n, mutaciÃ³n de contratos, contaminaciÃ³n del core e idempotencia.
5. Queda explÃ­cito que toda verdad debe estar respaldada por evidencia y versiÃ³n.

---

## Assumptions

- Tenon operarÃ¡ en entornos donde existen mÃºltiples â€œfuentes de verdadâ€ incompatibles (ERP/PSP/Banco/Ledger interno).
- ExistirÃ¡ presiÃ³n organizacional por convertir Tenon en sistema de ejecuciÃ³n/contabilidad; este RFC lo prohÃ­be.
- La adopciÃ³n enterprise exige defensa legal y reconstrucciÃ³n histÃ³rica (pelÃ­cula), no reportes estÃ¡ticos.
