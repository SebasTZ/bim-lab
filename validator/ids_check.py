"""Capa 2 — Reglas de contenido: ejecuta un IDS con ifctester y normaliza el resultado."""
from __future__ import annotations

import re
from pathlib import Path

import ifcopenshell
from ifctester import ids

from .models import CheckResult

# ifctester 0.9 no lee el atributo `identifier` del IDS, así que el código
# de la regla se toma del inicio del nombre: "R04 - Propiedades ..." -> R04
_CODE_IN_NAME = re.compile(r"^\s*([A-Za-z]+\d+)\s*-\s*(.+)$")
MAX_DETAILS = 10


def _trace(description: str | None) -> str | None:
    """Extrae el tramo 'Responde a ...' que generar_ids.py escribe en la descripción."""
    for part in (description or "").split(" | "):
        if part.startswith("Responde a"):
            return part
    return None


def check_ids(model: ifcopenshell.file, ids_path: Path) -> list[CheckResult]:
    spec_set = ids.open(str(ids_path), validate=True)
    spec_set.validate(model)

    results: list[CheckResult] = []
    for index, spec in enumerate(spec_set.specifications, start=1):
        match = _CODE_IN_NAME.match(spec.name or "")
        code, name = (match.group(1), match.group(2)) if match else (f"IDS{index:02d}", spec.name)

        details: list[str] = []
        applicable = len(spec.applicable_entities)

        if not spec.is_ifc_version:
            details.append(
                f"El modelo es {model.schema} pero la regla exige {', '.join(spec.ifcVersion)}"
            )
        elif spec.minOccurs and applicable < spec.minOccurs:
            details.append(
                f"Se requiere al menos {spec.minOccurs} elemento(s) aplicable(s); se encontraron {applicable}"
            )
        elif spec.maxOccurs != "unbounded" and applicable > int(spec.maxOccurs):
            details.append(
                f"Se permiten como máximo {spec.maxOccurs} elemento(s); se encontraron {applicable}"
            )

        for requirement in spec.requirements:
            for failure in requirement.failures or []:
                element = failure["element"]
                details.append(
                    f"{element.is_a()} '{getattr(element, 'Name', None) or '-'}' "
                    f"[{getattr(element, 'GlobalId', '#' + str(element.id()))}]: "
                    f"{requirement.to_string('requirement', spec, requirement)} → {failure['reason']}"
                )

        # Un IDS con un esquema distinto al del modelo no debe contar como PASS
        passed = bool(spec.status) and spec.is_ifc_version is not False
        if len(details) > MAX_DETAILS:
            extra = len(details) - MAX_DETAILS
            details = details[:MAX_DETAILS] + [f"... y {extra} incidencia(s) más"]

        results.append(
            CheckResult(
                code=code,
                name=name,
                passed=passed,
                source="ids",
                applicable=applicable,
                failed=len(spec.failed_entities),
                details=details,
                trace=_trace(spec.description),
                fix=spec.instructions or None,
            )
        )
    return results
