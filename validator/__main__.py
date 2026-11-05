"""CLI del validador de entregables BIM.

Uso:
    python -m validator samples\\                      (todos los .ifc de la carpeta)
    python -m validator modelo.ifc --ids ids\\otra.ids
    python -m validator samples\\ --json reports\\auditoria.json

Códigos de salida (útiles para CI / hooks de Git):
    0 = todos los entregables aprobados
    1 = al menos un entregable rechazado
    2 = error de uso o configuración
"""
from __future__ import annotations

import argparse
import json
import sys
import tomllib
from datetime import datetime
from pathlib import Path

from .audit import audit_file
from .console import print_report


def _collect(paths: list[str]) -> list[Path]:
    files: list[Path] = []
    for raw in paths:
        p = Path(raw)
        if p.is_dir():
            files.extend(sorted(p.glob("*.ifc")))
        elif p.exists():
            files.append(p)
        else:
            print(f"Aviso: no existe '{p}'", file=sys.stderr)
    return files


def main() -> int:
    parser = argparse.ArgumentParser(prog="validator", description="Validador de entregables BIM (ISO 19650 + IDS)")
    parser.add_argument("paths", nargs="+", help="Archivos .ifc o carpetas")
    parser.add_argument("--config", default="lab.toml", help="Configuración de reglas (default: lab.toml)")
    parser.add_argument("--ids", help="Archivo .ids (por defecto, el definido en la configuración)")
    parser.add_argument("--json", help="Guardar el reporte también en JSON")
    args = parser.parse_args()

    try:
        config = tomllib.loads(Path(args.config).read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"Error: no se encontró la configuración '{args.config}'", file=sys.stderr)
        return 2

    ids_path = Path(args.ids or config["ids"]["default"])
    if not ids_path.exists():
        print(f"Error: no se encontró el IDS '{ids_path}'", file=sys.stderr)
        return 2

    files = _collect(args.paths)
    if not files:
        print("Error: no hay archivos .ifc para auditar", file=sys.stderr)
        return 2

    reports = [audit_file(f, ids_path, config["naming"]) for f in files]
    for report in reports:
        print_report(report)

    approved = sum(r.passed for r in reports)
    print(f"Resumen: {approved}/{len(reports)} entregable(s) aprobado(s) con '{ids_path.name}'")

    if args.json:
        out = Path(args.json)
        out.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "ids": ids_path.name,
            "reports": [r.to_dict() for r in reports],
        }
        out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Reporte JSON: {out}")

    return 0 if approved == len(reports) else 1


if __name__ == "__main__":
    sys.exit(main())
