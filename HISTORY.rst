=======
History
=======
1.1.5 (2026-03-04)
------------------
### Added
* **LakeWater Reflectance Model**: Se ha implementado soporte para superficies acuáticas. Los usuarios ahora pueden activar la física de dispersión específica para agua mediante el flag `--lakewater` en la CLI.
* **Dynamic CLI Progress Bar**: Nueva barra de progreso en tiempo real que incluye el **ETA (Tiempo estimado de finalización)** y actualizaciones de estado por banda para el motor RTM.
* **Physical Range Clipping**: Añadida una capa de recorte físico $[0, 1.1]$ a la salida de la inversión para eliminar ruido atmosférico (reflectancias negativas) en bandas de absorción, manteniendo el detalle en píxeles de alto brillo.
* **Maritime Aerosol Logic**: Lógica interna para priorizar perfiles de aerosol tipo 'Maritime' cuando el modo LakeWater está activo, mejorando la consistencia física del modelo.

### Changed
* **Refactored Core Engine**: Estandarización de nombres de variables y actualización de todos los *docstrings* al inglés siguiendo las normativas PEP 8.
* **Improved Metadata Parsing**: Mejora en la gestión de objetos `datetime` en los metadatos XML de EnMAP, soportando ahora tanto cadenas ISO UTC como formatos de fecha estándar.
* **Parallel Engine Optimization**: Refinamiento en la distribución de tareas del `ProcessPoolExecutor` para asegurar una utilización del 100% de los núcleos de CPU disponibles.

### Fixed
* Corregido un error donde valores extremadamente bajos de transmitancia de gas podían causar una división por cero en la fórmula de inversión.
* Mejora en la precisión del cálculo de la distancia Tierra-Sol para corregir variaciones estacionales en la transferencia radiativa.

1.1.0 (2026-01-19)
------------------

* **Refactoring (Major Architecture Change)**
    * Migrated from a monolithic "spaghetti code" script to a professional modular structure.
    * Reorganized project into dedicated modules: ``core.py`` (RTM logic), ``main.py`` (workflow execution), ``utils.py`` (helper functions), ``atmospheric.py`` (atmospheric constituents retrieval module) and ``config.py`` (global settings).
    * Implemented the **src-layout** structure to follow Python packaging standards.

* **New Features**
    * Added **CLI (Command Line Interface)** support via the ``sixabos-run`` entry point.
    * Integrated ``pyproject.toml`` for PEP 517 compliant installation.
    * Added automated output directory creation and improved input validation logic.
    * Implemented flexible aerosol profile selection (Continental, Maritime, Urban, Desert, BiomassBurning) via CLI arguments.

* **Improvements & Bug Fixes**
    * Enhanced error handling for missing EnMAP metadata or spectral image files.
    * Optimized parallel processing worker initialization to prevent redundant module imports.
    * Fixed a ``TypeError`` occurring when the output directory was not explicitly defined.

1.0.0 (2026-01-12)
------------------

* **Initial Release**
    * First functional version of 6ABOS released on Zenodo.
    * Basic implementation of 6S-based atmospheric correction for EnMAP L1C data.
