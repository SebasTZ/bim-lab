"""Orquestador: combina las capas de validación en un AuditReport."""
from __future__ import annotations

from pathlib import Path

import ifcopenshell

from .ids_check import check_ids
from .models import AuditReport, CheckResult
from .naming import check_filename


def audit_file(path: Path, ids_path: Path, naming_cfg: dict) -> AuditReport:
    report = AuditReport(file=path, schema=None)

    # Capa 1: contenedor (no requiere abrir el modelo)
    report.checks.append(check_filename(path, naming_cfg))

    # Capa 1b: el archivo debe ser un IFC legible
    try:
        model = ifcopenshell.open(str(path))
    except Exception as exc:  # archivo corrupto, no-IFC, etc.
        report.checks.append(
            CheckResult(
                code="E01",
                name="Archivo IFC legible",
                passed=False,
                source="contenedor",
                details=[f"No se pudo leer el modelo: {exc}"],
            )
        )
        return report  # sin modelo no hay validación de contenido

    report.schema = model.schema
    report.checks.append(
        CheckResult(code="E01", name="Archivo IFC legible", passed=True, source="contenedor")
    )

    # Capa 2: contenido (IDS)
    report.checks.extend(check_ids(model, ids_path))
    return report
