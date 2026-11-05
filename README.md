# bim-lab · Validador automático de entregables BIM

Laboratorio openBIM para aplicar la gestión de la información de **ISO 19650** y el **Plan BIM Perú** desde la ingeniería de sistemas: arquitectura de datos, automatización y control de versiones.

**Proyecto 1:** un validador que audita un modelo `.ifc` y emite un veredicto **APROBADO / RECHAZADO** con el detalle de cada incumplimiento.

---

## El problema

Cuando una entidad pública contrata un proyecto con BIM, define *qué información* necesita recibir y en qué forma. Revisar a mano cada modelo entregado es lento, inconsistente y difícil de auditar.

Este validador convierte esos requisitos en **reglas ejecutables** y sirve a los dos lados del proceso, según los roles de ISO 19650:

| Rol | Quién es | Cómo usa el validador |
|---|---|---|
| **Parte que designa** | La entidad contratante (p. ej. un Gobierno Regional) | Compuerta de aceptación: decide si un entregable se acepta o se observa |
| **Parte designada** | El consultor o contratista | Autoverificación antes de entregar, para evitar observaciones |

## Cómo funciona

La validación ocurre en dos capas, porque el estándar **IDS** (Information Delivery Specification, de buildingSMART) solo describe el *contenido* del modelo y no puede evaluar el archivo en sí.

```
                 ┌──────────────────────────────────────────────┐
  modelo.ifc ──▶ │ Capa 1 · Contenedor (Python)                 │
                 │   N01  Nomenclatura del archivo (ISO 19650)  │
                 │   E01  El archivo es un IFC legible          │
                 ├──────────────────────────────────────────────┤
                 │ Capa 2 · Contenido (IDS + ifctester)         │
                 │   R01…Rn  Clases, atributos y propiedades    │
                 └──────────────────────────────────────────────┘
                                      │
                         Consola (PASS/FAIL) + JSON
```

- **Las reglas son datos, no código.** La nomenclatura vive en `lab.toml` y los requisitos de contenido en archivos `.ids`. Ambos se versionan en Git: cambiar una regla no requiere tocar Python.
- **Un IDS escrito para IFC4 rechaza un modelo IFC2X3** en lugar de dejarlo pasar en silencio.
- **Un archivo corrupto no detiene la auditoría:** se reporta como incumplimiento.

## Inicio rápido

Requisitos: Python 3.11 o superior.

**Windows (PowerShell)**

```powershell
git clone https://github.com/SebasTZ/bim-lab.git
cd bim-lab
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**Linux / macOS**

```bash
git clone https://github.com/SebasTZ/bim-lab.git
cd bim-lab
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Luego genera los modelos de prueba y audítalos:

```bash
python scripts/make_samples.py
python -m validator samples/
python -m validator samples/ --json reports/auditoria.json
```

## Ejemplo de salida

```
────────────────────────────────────────────────────────────────────────
AUDITORÍA: modelo_final_v2.ifc
Esquema IFC: IFC4
────────────────────────────────────────────────────────────────────────
Reglas del contenedor
  [FAIL] N01  Nomenclatura ISO 19650 del archivo
         • Se esperaban 7 campos (proyecto-originador-volumen-nivel-tipo-rol-numero), se encontraron 1 en 'modelo_final_v2'
  [PASS] E01  Archivo IFC legible
Reglas IDS (contenido)
  [PASS] R01  Código de proyecto  (1/1)
  [PASS] R02  Niveles definidos  (1/1)
  [PASS] R03  Nomenclatura de muros  (1/1)
  [FAIL] R04  Propiedades obligatorias de muros  (0/1)
         • IfcWall 'MUR-001' [...]: IsExternal data shall be provided in the dataset Pset_WallCommon → The required property set does not exist
         • IfcWall 'MUR-001' [...]: LoadBearing data shall be provided in the dataset Pset_WallCommon → The required property set does not exist
────────────────────────────────────────────────────────────────────────
ENTREGABLE RECHAZADO  4/6 reglas cumplidas
```

## Uso

```
python -m validator RUTA [RUTA ...] [--ids ARCHIVO.ids] [--config lab.toml] [--json SALIDA.json]
```

| Argumento | Descripción |
|---|---|
| `RUTA` | Uno o más archivos `.ifc`, o carpetas (se auditan todos sus `.ifc`) |
| `--ids` | IDS a aplicar. Por defecto, el definido en `lab.toml` |
| `--config` | Archivo de configuración. Por defecto, `lab.toml` |
| `--json` | Guarda además el reporte en JSON |

**Códigos de salida**, pensados para integración continua o hooks de Git:

| Código | Significado |
|---|---|
| `0` | Todos los entregables aprobados |
| `1` | Al menos un entregable rechazado |
| `2` | Error de uso o de configuración |

## Reglas incluidas

### Nomenclatura del archivo (`lab.toml`)

Estructura basada en los campos de ISO 19650-2, tomando el Anexo Nacional del Reino Unido como referencia:

```
Proyecto-Originador-Volumen-Nivel-Tipo-Rol-Número
  LAB01 -   STZ    -   ZZ  -  01 - M3 - A - 0001 .ifc
```

Cada campo se valida con una expresión regular. Los códigos actuales son de ejemplo: deben ajustarse a lo que defina el estándar de información del proyecto y su Plan de Ejecución BIM (BEP).

### Contenido del modelo (`ids/LAB01-requisitos-minimos.ids`)

> **Reglas didácticas.** R01 a R04 son ejemplos creados para el laboratorio. No provienen de un EIR real ni de una norma. En un proyecto real, cada especificación IDS debe trazarse a la cláusula del requisito de intercambio de información (EIR) que la origina.

| Código | Regla | Técnica IDS |
|---|---|---|
| R01 | El `IfcProject` lleva el código del proyecto (`LAB01`) | Atributo con patrón (`xs:pattern`) |
| R02 | Existe al menos un `IfcBuildingStorey`, y todos tienen nombre | Presencia de clase + atributo obligatorio |
| R03 | Existen muros, y todos se nombran `MUR-###` | Presencia de clase + nomenclatura de elementos |
| R04 | Todo `IfcWall` declara `Pset_WallCommon.IsExternal` y `LoadBearing` | Propiedades obligatorias con tipo de dato |

El archivo es válido contra el esquema XSD oficial de IDS 1.0.

## Estructura del proyecto

```
bim-lab/
├── ids/                  # Requisitos de contenido (IDS 1.0)
├── samples/              # Modelos IFC de prueba (uno válido, uno inválido)
├── scripts/
│   └── make_samples.py   # Genera los modelos de prueba con IfcOpenShell
├── validator/
│   ├── __main__.py       # CLI
│   ├── audit.py          # Orquestador de las dos capas
│   ├── naming.py         # Capa 1: nomenclatura ISO 19650
│   ├── ids_check.py      # Capa 2: ejecución del IDS con ifctester
│   ├── models.py         # CheckResult / AuditReport
│   └── console.py        # Reporte en consola
├── lab.toml              # Configuración de reglas
└── requirements.txt
```

## Contexto: BIM en la inversión pública peruana

La Resolución Directoral N° 0007-2025-EF/63.01 de la DGPMI del MEF aprueba el listado de 14 tipologías de proyectos del Gobierno Nacional y de los gobiernos regionales que se desarrollarán aplicando BIM. Su artículo 3, que establece la obligatoriedad, entra en vigor a los 12 meses de su publicación (agosto de 2026). La obligación alcanza las fases de Formulación y Evaluación y de Ejecución, esta última desde la elaboración del expediente técnico o documento equivalente.

Este laboratorio busca entender esa adopción desde la ingeniería de sistemas: cómo un requisito de información se vuelve verificable, auditable y automatizable.

### Fuentes oficiales

Fecha de consulta: 2026-11-05.

| Fuente | Emisor | Uso en este repositorio |
|---|---|---|
| [RD N° 0007-2025-EF/63.01 (nota oficial)](https://mef.gob.pe/planbimperu/novedadesbim/novedad-20250813.html) | MEF · Plan BIM Perú | Tipologías y obligatoriedad de BIM |
| [Plazos de adopción para Gobierno Nacional y GORE](https://mef.gob.pe/planbimperu/novedadesbim/novedad-20250902-2.html) | MEF · Plan BIM Perú | Fases y plazos de aplicación |
| [Recursos BIM: Guía Nacional BIM y plantillas](https://mef.gob.pe/planbimperu/recursosbim.html) | MEF · Plan BIM Perú | Marco de gestión de información y plantillas EIR, BEP, MIDP y TIDP |
| ISO 19650-1 e ISO 19650-2 | ISO · INACAL | Procesos de entrega y estados del CDE. Norma de pago: se cita, no se reproduce |

Este repositorio no reproduce el texto de las normas. Ante cualquier discrepancia, prevalece la fuente oficial.

## Limitaciones conocidas

- **IDS no valida el nombre del archivo.** Por eso la nomenclatura se resuelve en Python, en la capa 1.
- **ifctester 0.9 no lee el atributo `identifier`** de las especificaciones IDS. El código de cada regla se toma del inicio de su nombre (`"R04 - ..."`).
- **Los modelos de prueba son mínimos.** Los modelos exportados desde software de autoría (Revit, Archicad) suelen presentar incumplimientos que no aparecen aquí.

## Hoja de ruta

- [x] **Etapa 1:** validación de entregables (nomenclatura + IDS)
- [ ] **Etapa 2:** traducir requisitos de información reales (de EIR a IDS)
- [ ] **Etapa 3:** auditar modelos reales exportados desde software de autoría
- [ ] **Etapa 4:** versionado y líneas base de la información con Git (tags y releases) y su relación con un CDE institucional
- [ ] **Etapa 5:** microservicio (API + Docker) e integración continua

## Versionado y CDE

Este repositorio **no se declara como Entorno de Datos Común (CDE)**. El CDE es el sistema institucional donde la información cambia de estado (en progreso, compartido, publicado, archivado). Git cumple otro papel: conserva el historial y fija líneas base.

- El trabajo vigente vive en rutas y nombres estables. No se crean carpetas por estado ni archivos `final`, `final2` o con fecha.
- Las versiones siguen versionado semántico: `0.x` para borradores y `1.0.0` para la primera línea base aprobada.
- Cada línea base se marca con un tag anotado (por ejemplo, `v0.1.0`) y una release.

## Tecnologías

- [IfcOpenShell](https://ifcopenshell.org/): lectura y generación de modelos IFC
- [IfcTester](https://pypi.org/project/ifctester/): ejecución de especificaciones IDS
- [IDS 1.0](https://github.com/buildingSMART/IDS) de buildingSMART International

## Autor

**Juan Sebastian Trujillo Zevallos**, Ingeniero de Sistemas · [sebastz.com](https://sebastz.com) · [GitHub](https://github.com/SebasTZ)
