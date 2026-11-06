"""Genera un archivo IDS a partir de una matriz de requisitos (TOML).

La matriz es la fuente maestra; el .ids es un derivado reproducible.

Uso:
    python scripts/generar_ids.py requisitos/LAB01-requisitos.toml
    python scripts/generar_ids.py requisitos/LAB01-requisitos.toml --check

--check no escribe nada: falla (código 1) si el .ids versionado no coincide
con lo que produciría la matriz. Sirve para detectar ediciones manuales del
derivado o una matriz modificada sin regenerar.

Códigos de salida: 0 = correcto, 1 = desactualizado, 2 = error en la matriz.
"""
from __future__ import annotations

import argparse
import sys
import tomllib
from pathlib import Path

from ifctester import ids

TIPOS_EXIGENCIA = {"atributo", "propiedad"}
CLASES = {"DIDACTICO", "NORMATIVO", "PROPUESTA"}


class MatrizInvalida(Exception):
    pass


def _validar(matriz: dict) -> None:
    """Comprueba la coherencia de la matriz antes de generar nada."""
    errores: list[str] = []
    necesidades = {n["id"] for n in matriz.get("necesidad", [])}
    vistos: set[str] = set()

    for req in matriz.get("requisito", []):
        rid = req.get("id", "?")
        if rid in vistos:
            errores.append(f"{rid}: id duplicado")
        vistos.add(rid)
        for campo in ("nombre", "responde_a", "clase", "fuente", "aplica_a", "exige"):
            if not req.get(campo):
                errores.append(f"{rid}: falta el campo '{campo}'")
        if req.get("responde_a") and req["responde_a"] not in necesidades:
            errores.append(f"{rid}: responde_a '{req['responde_a']}' no existe en [[necesidad]]")
        if req.get("clase") and req["clase"] not in CLASES:
            errores.append(f"{rid}: clase '{req['clase']}' no válida ({', '.join(sorted(CLASES))})")
        for ex in req.get("exige", []):
            if ex.get("tipo") not in TIPOS_EXIGENCIA:
                errores.append(f"{rid}: exigencia con tipo '{ex.get('tipo')}' no soportado")
            if ex.get("tipo") == "propiedad" and not ex.get("pset"):
                errores.append(f"{rid}: la propiedad '{ex.get('nombre')}' necesita 'pset'")

    usadas = {r.get("responde_a") for r in matriz.get("requisito", [])}
    for sin_uso in sorted(necesidades - usadas):
        errores.append(f"{sin_uso}: necesidad sin ningún requisito que la responda")

    if errores:
        raise MatrizInvalida("\n".join(f"  • {e}" for e in errores))


def _facet(ex: dict):
    valor = None
    if ex.get("patron"):
        valor = ids.Restriction(options={"pattern": ex["patron"]}, base="string")
    elif "valor" in ex:
        valor = ex["valor"]

    if ex["tipo"] == "atributo":
        return ids.Attribute(name=ex["nombre"], value=valor, cardinality="required")
    return ids.Property(
        propertySet=ex["pset"],
        baseName=ex["nombre"],
        value=valor,
        dataType=ex.get("tipo_dato"),
        cardinality="required",
    )


def construir(matriz: dict) -> ids.Ids:
    meta = matriz["meta"]
    necesidades = {n["id"]: n for n in matriz["necesidad"]}

    documento = ids.Ids(
        title=meta["titulo"],
        version=meta.get("version"),
        description=(
            f"Generado desde la matriz de requisitos de {meta['proyecto']}. Clase: {meta['clase']}. "
            "No editar a mano: modificar la matriz y regenerar."
        ),
        author=meta.get("autor"),
        date=meta.get("fecha"),
        purpose=meta.get("proposito"),
        milestone=meta.get("hito"),
    )

    for req in matriz["requisito"]:
        nec = necesidades[req["responde_a"]]
        maximo = req.get("max_ocurrencias", "unbounded")
        spec = ids.Specification(
            # ifctester 0.9 no conserva `identifier` al leer: el código va al inicio del nombre
            name=f"{req['id']} - {req['nombre']}",
            identifier=req["id"],
            ifcVersion=meta["ifc_version"],
            minOccurs=req.get("min_ocurrencias", 0),
            maxOccurs=maximo,
            # La descripción lleva la trazabilidad: el reporte la muestra en cada FAIL
            description=(
                f"{req['descripcion']} | Responde a {nec['id']}: {nec['pregunta']} "
                f"| Fuente: {req['fuente']} ({req['clase']})"
            ),
            instructions=req.get("instrucciones"),
        )
        spec.applicability.append(ids.Entity(name=req["aplica_a"]))
        for ex in req["exige"]:
            spec.requirements.append(_facet(ex))
        documento.specifications.append(spec)

    return documento


def main() -> int:
    parser = argparse.ArgumentParser(description="Genera un IDS desde una matriz de requisitos")
    parser.add_argument("matriz", help="Archivo .toml de requisitos")
    parser.add_argument("--check", action="store_true", help="Solo comprobar que el .ids está al día")
    args = parser.parse_args()

    ruta = Path(args.matriz)
    try:
        matriz = tomllib.loads(ruta.read_text(encoding="utf-8"))
        _validar(matriz)
    except FileNotFoundError:
        print(f"Error: no existe la matriz '{ruta}'", file=sys.stderr)
        return 2
    except tomllib.TOMLDecodeError as exc:
        print(f"Error de sintaxis TOML en '{ruta}': {exc}", file=sys.stderr)
        return 2
    except MatrizInvalida as exc:
        print(f"La matriz '{ruta}' tiene errores:\n{exc}", file=sys.stderr)
        return 2

    salida = Path(matriz["meta"]["salida"])
    nuevo = construir(matriz).to_string()

    if args.check:
        actual = salida.read_text(encoding="utf-8") if salida.exists() else ""
        if actual.replace("\r\n", "\n") == nuevo.replace("\r\n", "\n"):
            print(f"OK: '{salida}' está al día con '{ruta.name}'")
            return 0
        print(f"DESACTUALIZADO: '{salida}' no coincide con '{ruta.name}'. Regenera con:")
        print(f"  python scripts/generar_ids.py {args.matriz}")
        return 1

    salida.parent.mkdir(parents=True, exist_ok=True)
    salida.write_text(nuevo, encoding="utf-8")
    # Valida el resultado contra el XSD oficial de IDS 1.0
    ids.open(str(salida), validate=True)
    total = len(matriz["requisito"])
    print(f"Generado: {salida}  ({total} reglas, válido contra IDS 1.0)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
