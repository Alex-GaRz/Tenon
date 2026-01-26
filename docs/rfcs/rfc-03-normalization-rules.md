# RFC-03 â€” NORMALIZATION_RULES
**Sistema:** Tenon â€” Sistema de Verdad Financiera Operativa y ConciliaciÃ³n Multisistema  
**Estado:** DRAFT  
**RelaciÃ³n:** Depende de RFC-00_MANIFEST, RFC-01_CANONICAL_EVENT, RFC-01A_CANONICAL_IDS, RFC-02_INGEST_APPEND_ONLY

---

## PropÃ³sito

Definir la **normalizaciÃ³n canÃ³nica determinista** que transforma datos crudos preservados
en `CanonicalEvent` **sin interpretar la realidad**.

La normalizaciÃ³n:
- reduce heterogeneidad estructural,
- preserva evidencia,
- es reproducible,
- no â€œarreglaâ€ datos,
- no decide verdad.

---

## No-Goals

- Corregir FX, impuestos, fees, contabilidad o pricing.
- Inferir estados del dinero o conciliaciÃ³n.
- Resolver discrepancias o causalidad.
- Enriquecer con fuentes externas.
- Optimizar performance o storage.
- â€œCompletarâ€ campos faltantes con heurÃ­sticas.

---

## Invariantes

### 3.1 Determinismo fuerte
- Misma entrada cruda + mismas versiones â‡’ mismo `CanonicalEvent`.
- Prohibido usar:
  - reloj del sistema,
  - llamadas externas,
  - randomness,
  - lookups no versionados.

### 3.2 Transparencia total
- Cada campo normalizado debe ser trazable al crudo:
  - por copia directa,
  - por regla explÃ­cita y versionada,
  - o marcado como `UNKNOWN`.

### 3.3 No interpretaciÃ³n
- La normalizaciÃ³n **no**:
  - reclasifica montos,
  - calcula FX,
  - reasigna impuestos,
  - decide â€œquÃ© deberÃ­a haber pasadoâ€.
- Si la fuente es ambigua, el canon **permanece ambiguo**.

### 3.4 PreservaciÃ³n de pÃ©rdida
- Si el crudo pierde informaciÃ³n al normalizar (p.ej., PDF â†’ campos),
  la pÃ©rdida debe quedar registrada como warning.
- Nunca se descarta el crudo original.

### 3.5 Versionado obligatorio
- Toda regla de normalizaciÃ³n tiene `normalizer_version`.
- Cambios de reglas **no** reescriben eventos previos.

---

## Contratos (conceptuales)

### 4.1 NormalizationRule
Cada regla define:

- `rule_id`
- `rule_version`
- `input_signature` (quÃ© formato/shape acepta)
- `mapping` (crudo â†’ campo canÃ³nico)
- `lossy_fields[]` (si aplica)
- `warnings[]` (condiciones de degradaciÃ³n)

### 4.2 NormalizationResult
Cada ejecuciÃ³n produce:

- `event_id` (si materializa `CanonicalEvent`)
- `normalizer_version`
- `applied_rules[]`
- `warnings[]`
- `diff_reference` (referencia al diff crudoâ†’canon)

---

## Flujo de normalizaciÃ³n (alto nivel)

1. **SelecciÃ³n de regla**
   - En funciÃ³n de `source_system`, `raw_format`, `schema_hint`.
2. **AplicaciÃ³n determinista**
   - Se mapean campos explÃ­citos.
3. **Marcado de ambigÃ¼edad**
   - Campos no inferibles â‡’ `UNKNOWN`.
4. **Registro**
   - Se emite `CanonicalEvent` append-only.
   - Se registra `NormalizationResult`.

No existe â€œfallback mÃ¡gicoâ€.

---

## Threat Model

### 6.1 Amenazas
- **NormalizaciÃ³n creativa** que altera semÃ¡ntica.
- **Cambios silenciosos** de reglas rompiendo reproducibilidad.
- **Dependencias ocultas** (APIs, tablas externas).
- **Correcciones retroactivas** que reescriben historia.
- **PÃ©rdida de evidencia** al â€œlimpiarâ€ datos.

### 6.2 Controles exigidos
- Reglas explÃ­citas y versionadas.
- Diff trazable crudoâ†’canon.
- Warnings obligatorios en pÃ©rdida.
- ProhibiciÃ³n de reescritura histÃ³rica.
- UNKNOWN como salida segura.

---

## Pruebas

### 7.1 Unitarias
- Cada regla mapea solo lo declarado.
- Campos fuera de regla â‡’ no se pueblan.
- `normalizer_version` siempre presente.

### 7.2 Propiedades
- Determinismo: N ejecuciones â‡’ mismo resultado.
- No side-effects: la normalizaciÃ³n no altera crudo.
- Estabilidad temporal: replay produce mismos eventos.

### 7.3 SistÃ©micas
- Cambios de versiÃ³n:
  - eventos nuevos usan regla nueva,
  - eventos viejos permanecen intactos.
- NormalizaciÃ³n con crudo incompleto/corrupto.
- Formatos mixtos (JSON, CSV, PDF).

---

## Criterios de AceptaciÃ³n

Este RFC se considera cumplido cuando:
1. La normalizaciÃ³n es determinista y versionada.
2. No existe interpretaciÃ³n semÃ¡ntica ni â€œarregloâ€ de datos.
3. Toda pÃ©rdida o ambigÃ¼edad queda registrada.
4. El crudo original siempre es accesible.
5. Replay histÃ³rico produce resultados idÃ©nticos.

---

## Assumptions

- Las fuentes enviarÃ¡n datos inconsistentes y, a veces, incorrectos.
- La presiÃ³n por â€œlimpiarâ€ datos existirÃ¡; este RFC lo prohÃ­be.
- La verdad operativa requiere aceptar ambigÃ¼edad antes que inventar precisiÃ³n.
