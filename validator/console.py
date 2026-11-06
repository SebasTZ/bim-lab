"""Salida en consola del reporte de auditoría."""
from __future__ import annotations

import os
import sys

from .models import AuditReport

# Activa los códigos de color ANSI en la consola clásica de Windows
if os.name == "nt":
    os.system("")

_USE_COLOR = sys.stdout.isatty() and "NO_COLOR" not in os.environ


def _c(text: str, code: str) -> str:
    return f"\033[{code}m{text}\033[0m" if _USE_COLOR else text


def _tag(passed: bool) -> str:
    return _c("[PASS]", "1;32") if passed else _c("[FAIL]", "1;31")


def print_report(report: AuditReport) -> None:
    line = "─" * 72
    print(_c(line, "90"))
    print(_c(f"AUDITORÍA: {report.file.name}", "1;36"))
    print(f"Esquema IFC: {report.schema or 'desconocido'}")
    print(_c(line, "90"))

    for source, title in (("contenedor", "Reglas del contenedor"), ("ids", "Reglas IDS (contenido)")):
        checks = [c for c in report.checks if c.source == source]
        if not checks:
            continue
        print(_c(title, "1"))
        for check in checks:
            counts = f"  ({check.applicable - check.failed}/{check.applicable})" if source == "ids" else ""
            print(f"  {_tag(check.passed)} {check.code}  {check.name}{_c(counts, '90')}")
            for detail in check.details:
                print(_c(f"         • {detail}", "33"))
            if not check.passed and check.trace:
                print(_c(f"         ↳ {check.trace}", "36"))
            if not check.passed and check.fix:
                print(_c(f"         ↳ Cómo corregir: {check.fix}", "36"))

    total = len(report.checks)
    ok = sum(c.passed for c in report.checks)
    print(_c(line, "90"))
    verdict = _c("ENTREGABLE APROBADO", "1;30;42") if report.passed else _c("ENTREGABLE RECHAZADO", "1;37;41")
    print(f"{verdict}  {ok}/{total} reglas cumplidas")
    print()
