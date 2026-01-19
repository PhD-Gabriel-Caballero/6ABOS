=======
History
=======

1.1.0 (2026-01-19)
------------------

* **Added**
    * New ``aerosol_profile`` key in ``DEFAULT_CONF`` to support Maritime, Continental, Urban, and Desert models.
    * Support for dynamic Aerosol Optical Thickness (AOT) configuration per scene.
    * Console logging for 6S engine parameters (AOT, Water Vapor, Ozone) during initialization.
    * Added ``pyproject.toml`` for modern PEP 517 packaging and installation.

* **Changed**
    * Refactored ``run_single_6s_band`` to accept a single task tuple to fix ``ProcessPoolExecutor`` compatibility.
    * Updated project layout to a standard ``src/`` structure.
    * Improved English documentation and comments across the core modules.

* **Fixed**
    * Fixed ``TypeError`` in parallel processing caused by incorrect argument passing to worker threads.
    * Resolved git synchronization issues (rejected pushes) by performing a rebase with the remote origin.

1.0.0 (2025-12-01)
------------------

* **Added**
    * Initial implementation of the 6ABOS core logic for EnMAP L1C data.
    * Support for reading EnMAP XML metadata and spectral response functions.
