=======
History
=======

1.1.0 (2026-01-19)
------------------

* **Refactoring (Major Architecture Change)**
    * Migrated from a monolithic "spaghetti code" script to a professional modular structure.
    * Reorganized project into dedicated modules: ``core.py`` (RTM logic), ``main.py`` (workflow execution), ``utils.py`` (helper functions), and ``config.py`` (global settings).
    * Implemented the **src-layout** structure to follow modern Python packaging standards.

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
