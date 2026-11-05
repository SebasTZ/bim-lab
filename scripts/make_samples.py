import ifcopenshell.api.aggregate
import ifcopenshell.api.context
import ifcopenshell.api.project
import ifcopenshell.api.pset
import ifcopenshell.api.root
import ifcopenshell.api.spatial
import ifcopenshell.api.unit


def build(path: str, compliant: bool) -> None:
    m = ifcopenshell.api.project.create_file(version="IFC4")
    project = ifcopenshell.api.root.create_entity(m, ifc_class="IfcProject", name="LAB01")
    ifcopenshell.api.unit.assign_unit(m)
    ifcopenshell.api.context.add_context(m, context_type="Model")

    site = ifcopenshell.api.root.create_entity(m, ifc_class="IfcSite", name="Terreno")
    building = ifcopenshell.api.root.create_entity(m, ifc_class="IfcBuilding", name="Bloque A")
    storey = ifcopenshell.api.root.create_entity(m, ifc_class="IfcBuildingStorey", name="Nivel 01")

    ifcopenshell.api.aggregate.assign_object(m, products=[site], relating_object=project)
    ifcopenshell.api.aggregate.assign_object(m, products=[building], relating_object=site)
    ifcopenshell.api.aggregate.assign_object(m, products=[storey], relating_object=building)

    wall = ifcopenshell.api.root.create_entity(m, ifc_class="IfcWall", name="MUR-001")
    ifcopenshell.api.spatial.assign_container(m, products=[wall], relating_structure=storey)

    if compliant:
        pset = ifcopenshell.api.pset.add_pset(m, product=wall, name="Pset_WallCommon")
        ifcopenshell.api.pset.edit_pset(
            m, pset=pset, properties={"IsExternal": True, "LoadBearing": True}
        )

    m.write(path)
    print(f"Generado: {path}")


if __name__ == "__main__":
    # Nombre ISO 19650 válido + contenido completo
    build("samples/LAB01-STZ-ZZ-01-M3-A-0001.ifc", compliant=True)
    # Nombre inválido + muro sin propiedades obligatorias
    build("samples/modelo_final_v2.ifc", compliant=False)
