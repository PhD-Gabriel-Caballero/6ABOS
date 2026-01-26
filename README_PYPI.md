# 6ABOS: 6S-based Atmospheric Background Offset Subtraction

6ABOS (6S-based Atmospheric Background Offset Subtraction) is an efficient atmospheric correction (AC) framework designed specifically for aquatic remote sensing. It leverages the 6S (Second Simulation of the Satellite Signal in the Solar Spectrum) radiative transfer model to retrieve accurate water surface reflectance from hyperspectral sensors, specifically validated for PRISMA and EnMAP imagery.

## Installation

For a stable installation of geospatial dependencies (GDAL) and the atmospheric engine (Py6S), we recommend using Mamba or Conda to handle binary requirements:

### 1. Create a dedicated environment
```bash
mamba create -n sixabos_env python=3.10 gdal py6s -c conda-forge
mamba activate sixabos_env
```
### 2. Install 6ABOS from PyPI
```bash
pip install sixabos
```
## Usage (Command Line Interface)

6ABOS is designed to be used directly from the terminal. Once installed, the sixabos-run command is available:

# Basic processing
sixabos-run --input "path/to/EnMAP_scene" --output "path/to/output_folder"

# Processing with a specific aerosol profile
sixabos-run --input "path/to/EnMAP_scene" --output "path/to/output_folder" --aerosol Maritime

### Available Aerosol Profiles:
Continental, Maritime, Urban, Desert, BiomassBurning.
For a full list of arguments, run: sixabos-run --help

## Key Features
** Physics-based: Built upon the robust 6S radiative transfer model version 1.1.
** Aquatic Optimized: Specifically tuned for the weak water-leaving signal in inland water bodies.
** Parallel Processing: Uses multi-core execution to process hyperspectral bands efficiently.
** GEE Integration: Capable of fetching dynamic atmospheric parameters (NCEP/MODIS) via Google Earth Engine.

## Links & Documentation
Full Documentation & Source Code: https://github.com/PhD-Gabriel-Caballero/6ABOS

Affiliation: Laboratory for Earth Observation (LEO) - Universitat de València (https://ipl.uv.es/leo/)

## Citation
If you use this software in your research, please cite:

Caballero Cañas, G. R., Sòria Perpinyà, X., Alvado Arranz, B., & Ruiz-Verdú, A. (2026). 6ABOS: 6S-based Atmospheric Background Offset Subtraction v1.1.0 - Modular Architecture. Zenodo. https://doi.org/10.5281/zenodo.18300277
