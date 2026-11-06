"""Estructuras de datos compartidas por todos los chequeos del validador."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class CheckResult:
    """Resultado de una regla individual (nomenclatura, lectura o IDS)."""

    code: str            # Ej. "N01", "R04"
    name: str            # Descripción corta de la regla
    passed: bool
    source: str          # "contenedor" o "ids"
    applicable: int = 0  # Elementos evaluados (solo reglas IDS)
    failed: int = 0      # Elementos que no cumplen (solo reglas IDS)
    details: list[str] = field(default_factory=list)
    trace: str | None = None   # A qué necesidad de la entidad responde (desde la descripción del IDS)
    fix: str | None = None     # Cómo corregirlo (desde las instrucciones del IDS)


@dataclass
class AuditReport:
    """Reporte de auditoría de un archivo entregable."""

    file: Path
    schema: str | None
    checks: list[CheckResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(c.passed for c in self.checks)

    def to_dict(self) -> dict:
        return {
            "file": self.file.name,
            "schema": self.schema,
            "verdict": "PASS" if self.passed else "FAIL",
            "checks": [asdict(c) for c in self.checks],
        }
