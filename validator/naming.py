"""Capa 1 — Reglas del contenedor: nomenclatura del archivo según ISO 19650.

IDS no puede evaluar el nombre del archivo, así que esta validación vive aquí.
Las reglas no están en el código: se leen de lab.toml para poder versionarlas.
"""
from __future__ import annotations

import re
from pathlib import Path

from .models import CheckResult


def check_filename(path: Path, cfg: dict) -> CheckResult:
    sep: str = cfg.get("separator", "-")
    fields: list[str] = cfg["fields"]
    rules: dict[str, str] = cfg.get("rules", {})
    details: list[str] = []

    if path.suffix.lower() != ".ifc":
        details.append(f"Extensión '{path.suffix}' no permitida (se espera .ifc)")

    parts = path.stem.split(sep)
    if len(parts) != len(fields):
        details.append(
            f"Se esperaban {len(fields)} campos ({sep.join(fields)}), "
            f"se encontraron {len(parts)} en '{path.stem}'"
        )
    else:
        for field_name, value in zip(fields, parts):
            pattern = rules.get(field_name)
            if pattern and not re.fullmatch(pattern, value):
                details.append(f"Campo '{field_name}' = '{value}' no cumple /{pattern}/")

    return CheckResult(
        code="N01",
        name="Nomenclatura ISO 19650 del archivo",
        passed=not details,
        source="contenedor",
        details=details,
    )
