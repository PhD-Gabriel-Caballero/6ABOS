=======
History
=======
1.1.5 (2026-03-04)
------------------
AddedLakeWater Reflectance Model: New support for aquatic surfaces. Users can now enable specific water-scattering physics using the --lakewater CLI flag.Dynamic CLI Progress Bar: Implementation of a real-time progress tracker with ETA (Estimated Time of Arrival) and band-specific status updates for the RTM engine.Physical Range Clipping: Added a safety clipping layer $[0, 1.1]$ to the physical inversion output to prevent negative reflectance values while preserving specular highlights.Maritime Aerosol Logic: Added internal logic to prioritize Maritime aerosol profiles when LakeWater mode is active for better physical consistency.ChangedRefactored Core Engine: Standardized variable naming and updated all docstrings to English following PEP 8 guidelines.Improved Metadata Parsing: Enhanced datetime handling for EnMAP XML files to support both UTC ISO strings and standard date formats.Parallel Engine Optimization: Refined task distribution in ProcessPoolExecutor to ensure 100% CPU utilization across all available cores.FixedFixed a bug where very low gas transmittance values could cause a division by zero in the inversion formula.Corrected the Earth-Sun distance calculation to improve precision in seasonal radiative transfer.

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
