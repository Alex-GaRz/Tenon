# RFCs â€” Tenon System Design Documents

Este directorio contiene los RFCs (Request for Comments) que definen la arquitectura, invariantes y contratos del sistema Tenon.

---

## Ãndice de RFCs

- **[RFC-00 â€” MANIFEST](RFC-00_MANIFEST.md)** â€” Documento constitucional del sistema. Define propÃ³sito, no-goals, invariantes, threat model y contratos institucionales.

---

## Regla de Inmutabilidad Constitucional

**RFC-00_MANIFEST.md es el documento fundacional del sistema y es INMUTABLE.**

Cualquier modificaciÃ³n al RFC-00 **solo puede realizarse mediante un RFC de enmienda** (RFC-00A_*) que siga el protocolo definido en [`docs/governance/RFC_Amendment_Policy.md`](../governance/RFC_Amendment_Policy.md).

**Cambios directos al RFC-00 sin protocolo de enmienda estÃ¡n prohibidos y deben ser bloqueados por CI.**

---

## RFCs Adicionales

Los RFCs numerados (RFC-01, RFC-02, etc.) extienden y especifican aspectos tÃ©cnicos del sistema, pero todos deben respetar los invariantes y no-goals establecidos en RFC-00.

Cualquier RFC que proponga violar un invariante o no-goal del RFC-00 **requiere primero una enmienda formal (RFC-00A_*)**.
