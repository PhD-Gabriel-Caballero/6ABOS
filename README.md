[![Py6S](https://img.shields.io/badge/Powered%20by-Py6S-blue.svg)](https://py6s.readthedocs.io/en/latest/)[![DOI](https://zenodo.org/badge/1130957972.svg)](https://doi.org/10.5281/zenodo.18232368)

# 6ABOS: 6S-based Atmospheric Background Offset Subtraction
<p align="center">
  <img src="assets/6ABOS.png" alt="6ABOS Header" width="100%">
</p>

**6ABOS** is a novel, efficient, and generic atmospheric correction (AC) framework designed specifically for **aquatic remote sensing**. It leverages a radiative transfer modeling (RTM) approach based on the **6S (Second Simulation of the Satellite Signal in the Solar Spectrum)** model to retrieve accurate water surface reflectance from hyperspectral sensors.

## The Challenge
In aquatic remote sensing, accurately retrieving water quality parameters (e.g., chlorophyll-a, turbidity, CDOM) is a significant challenge. Light interaction with both the atmosphere and the water column is complex, and for inland water bodies, the water-leaving signal is often extremely weak compared to the atmospheric contribution. 

## Objectives
The objective of 6ABOS is to bridge the gap between complex RTMs and practical application by providing a method that is:
* **Efficient:** Reducing the computational burden of traditional pixel-by-pixel inversions.
* **Generic:** Applicable to various hyperspectral platforms, specifically validated for **Level 1 PRISMA and EnMAP** imagery.
* **Simple:** Utilizing a streamlined RTM scheme that remains accessible while maintaining scientific rigor.

## Key Features
* **6S Engine Integration:** Built upon the robust 6S radiative transfer model version 1.1.
* **Multi-Sensor Support:** Optimized for the high spectral resolution of **PRISMA** and **EnMAP** missions.
* **Atmospheric Physics:** The atmospheric correction engine is powered by [Py6S](https://py6s.readthedocs.io/en/master/), employing a Homogeneous Lambertian + Water Lake ground reflectance model.

## Methodology
6ABOS implements a atmospheric background offset subtraction framework. By modeling the atmospheric path radiance and solar irradiance through 6S, the system leverages simulated atmospheric parameters to solve the radiative transfer equation, enabling the conversion of Top-of-Atmosphere (TOA) radiance into Bottom-of-Atmosphere (BOA) reflectance.

### Physics-based Retrieval
The 6ABOS model treats the atmosphere as a series of filters and reflectors. The workflow implemented in this repository follows these steps:

1. **Gaseous Correction:** The raw $L_{TOA}$ is first corrected for absorption by atmospheric gases (primarily $O_{3}$) using the transmittance factor $T_{g}$.
2. **Substraction of Path Radiance:** We remove the light scattered directly by the atmosphere toward the sensor, represented by $L_{path}$.
3. **Normalization:** The remaining signal is normalized by the downwelling solar irradiance ($E_{s}$) and the upward transmittance ($T_{\uparrow}$).
4. **Adjacency & Albedo Correction:** The formula accounts for the multiple interactions between the surface and the atmosphere via the spherical albedo ($S_{atm}$).

The model follows this physical relationship:

$$\rho_{BOA}(\lambda) = \frac{\left( \frac{L_{TOA}(\lambda)}{T_{g,O_{3}}(\lambda)} - L_{path}(\lambda) \right)}{\frac{E_{s}(\lambda) \cdot T_{\uparrow}(\lambda)}{\pi} + S_{atm}(\lambda) \left( \frac{L_{TOA}(\lambda)}{T_{g,O_{3}}(\lambda)} - L_{path}(\lambda) \right)}$$

Where:

* $L_{TOA}(\lambda)$: TOA radiance.
* $T_{g,O_{3}}(\lambda)$: Ozone transmittance.
* $L_{path}(\lambda)$: Atmospheric path radiance (Rayleigh + Aerosol scattering).
* $E_{s}(\lambda)$: Solar irradiance at TOA.
* $T_{\uparrow}(\lambda)$: Upward atmospheric transmittance.
* $S_{atm}(\lambda)$: Spherical albedo of the atmosphere.

## Atmospheric Correction Results
![Atmospheric Correction Results](assets/Rrs_graph.png)

This figure illustrates the performance of the **6ABOS** atmospheric correction algorithm applied to EnMAP data. 

* **Green dashed line:** TOA Radiance ($L_{TOA}$), containing atmospheric noise and scattering.
* **Black continuous line:** BOA Remote Sensing Reflectance ($R_{rs}$) after the 6S-based correction, revealing the true spectral signature of the target.

The correction effectively removes aerosol scattering and absorption effects, which is a critical preprocessing step for accurately estimating water quality parameters or land surface properties.

## Repository Structure
* `/src/sixabos`: Core 6ABOS Python scripts.
* `/data`: Example metadata and spectral response functions (SRF) for PRISMA/EnMAP.
* `/docs`: Technical documentation and 6S compilation guides.
* `/notebooks`: Tutorials on how to process a sample EnMAP tile.

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/PhD-Gabriel-Caballero/6ABOS/blob/main/notebooks/EnMAP/6ABOS_EnMAP_AC_v1.2_Dic_2025.ipynb)

## Arquitectura del Software

6ABOS is designed as a modular Python package, ensuring high interoperability with Earth Observation pipelines like EnPT. The architecture follows a decoupled functional design:

* **Orchestration (`main.py`):** Acts as the entry point, handling configuration parsing and parallel execution management.
* **Physics Engine (`core.py`):** Encapsulates the 6S Radiative Transfer Modeling (RTM) logic and the atmospheric correction physics.
* **Data Retrieval (`atmospheric.py`):** A dedicated interface for Google Earth Engine (GEE) to fetch dynamic atmospheric parameters (NCEP/MODIS).
* **Utility Layer (`utils.py`):** Handles EnMAP-specific I/O, XML metadata parsing, and GDAL-based raster processing.

The framework utilizes a `ProcessPoolExecutor` to distribute the 242 EnMAP spectral bands across multiple CPU cores, significantly reducing processing time.

```mermaid
classDiagram
    class run_6abos {
        <<Orchestrator>>
        +user_config: dict
        +execute_pipeline()
    }

    class DEFAULT_CONF {
        <<Configuration>>
        +GEE: bool
        +aerosol_profile: str
        +output_rrs: bool
        +tgas_threshold: float
    }

    class SixABOSEngine {
        <<Core Physics Engine>>
        +conf: dict
        +results_6s: dict
        +earth_sun_d: float
        +compute_earth_sun_distance(dt)
        +prepare_rtm_tasks(scene_meta, df_srf)
        +apply_atmospheric_correction(toa_rad, band_id)
    }

    class Atmospheric {
        <<GEE Integration>>
        +initialize_gee(project_id)
        +water(geom, date)
        +ozone(geom, date)
        +aerosol(geom, date)
    }

    class Utils {
        <<Helper Functions>>
        +parse_xml(xml_path)
        +get_enmap_band_parameters()
        +calculate_gaussian_srf()
        +save_enmap_tiff()
    }

    class run_single_6s_band {
        <<Parallel Task>>
        +simulate_physics(task_tuple)
    }

    %% Relationships
    run_6abos ..> DEFAULT_CONF : clones & updates
    run_6abos --> Utils : calls for metadata/IO
    run_6abos --> Atmospheric : fetches H2O/O3/AOT
    run_6abos --> SixABOSEngine : instantiates
    
    SixABOSEngine ..> run_single_6s_band : creates tasks for
    
    run_6abos ..> ProcessPoolExecutor : manages parallelism
    ProcessPoolExecutor --> run_single_6s_band : executes
    
    run_single_6s_band --> Py6S_Library : calls RTM
    SixABOSEngine --> GDAL_Library : writes final TIF
```
## Installation & Environment Setup

This project requires a specific environment to handle geospatial libraries (GDAL) and atmospheric physics simulations (Py6S). We recommend using **Miniforge** (a lightweight distribution of Mamba/Conda) for faster dependency resolution.

### 1. Install Miniforge
If you don't have it yet, download and install the version for your OS:
- **Windows/macOS/Linux:** [Miniforge Download Page](https://github.com/conda-forge/miniforge#miniforge3)

### 2. Create the Mamba Environment
Open your terminal (or Miniforge Prompt on Windows) and run the following commands to create and activate the environment:

```console
# 1. Clone the repository
git clone [https://github.com/PhD-Gabriel-Caballero/6ABOS.git](https://github.com/PhD-Gabriel-Caballero/6ABOS.git)
cd 6ABOS

# 2. Create the environment from the provided file
mamba env create -f environment.yml
conda activate sixabos_env

# 3. Install the package in editable mode
pip install -e .
```
## Usage

6ABOS v1.1.0 can be used either as a standalone command-line tool or as a Python library integrated into your workflows.

### 1. Command Line Interface (CLI)
After installation, you can run the atmospheric correction from any terminal without opening a Python script. 

**Basic command:**
```console
sixabos-run --input "path/to/EnMAP_scene" --output "path/to/output_folder"
```
### 2. Advanced options: 
You can specify the aerosol profile if needed:
```console
sixabos-run -input "path/to/EnMAP_scene" --output "path/to/output_folder" --aerosol maritime
```
Run ```sixabos-run --help``` to see all available arguments.

## Changelog
See [HISTORY.rst](https://github.com/PhD-Gabriel-Caballero/6ABOS/blob/main/HISTORY.rst) for a detailed list of changes and version evolution.

## Affiliation & Support

This project is developed at the [Laboratory for Earth Observation (LEO)](https://ipl.uv.es/leo/), part of the **Image Processing Laboratory (IPL)** at the **Universitat de València**.

### Project Context
**6ABOS** is built within the framework of the **RESSBIO** (*Remote Sensing Spectroscopy for wetlands BIOdiversity*) project (**CIPROM/2021/49**).

### Funding
This work is supported by the **PROMETEO Program** of the **Generalitat Valenciana**.

## Authors
For inquiries regarding collaboration or implementation for specific water quality monitoring projects, please contact the contributors.
* **Gabriel Caballero** - *Lead Developer/Algorithm Design* - [gabriel.caballero@uv.es](mailto:gabriel.caballero@uv.es)
* **Xavier Sòria Perpinyà** - *Scientific Contributor/Field Data & Bio-optical Modeling* 
* **Bárbara Alvado Arranz** - *Scientific Contributor/Field Data & Bio-optical Modeling*
* **Antonio Ruíz Verdú** - *Scientific Contributor/Field Data & Bio-optical Modeling* 

## Keywords
`Remote Sensing` `Hyperspectral` `EnMAP` `PRISMA` `Atmospheric Correction` `6S Model` `Water Quality` `Inland Waters`

## Scientific Communications (2025)

The methodology and validation of the **6ABOS** pipeline have been presented and discussed in the following international scientific forums during 2025:

### 🇩🇪 2nd EnMAP User Workshop
*From Hyperspectral Data to Environmental Understanding* | April 2–4, 2025 | Munich, Germany.
* **Oral/Poster:** *Assessment of EnMAP atmospheric correction in both oligotrophic and hypertrophic inland waters using 6S and in situ spectroscopy data.*
    * **Authors:** **Gabriel Caballero**, X. Sòria-Perpinyà, B. Alvado, A. Ruiz-Verdú, J. Delegido & J. Moreno.
[![View PDF](https://img.shields.io/badge/View_Document-PDF-red?logo=adobe-acrobat-reader&logoColor=white)](docs/GCaballero_Poster_EnMAP_2025.pdf)

### 🇧🇷 XXI Simposio Brasileiro de Sensoramento Remoto
April 13–16, 2025 | Salvador de Bahia, Brazil.
* **Technical Paper:** *Assessment of PRISMA atmospheric correction in hypertrophic inland waters using 6S and in situ spectroscopy data.*
    * **Authors:** **G. Caballero**, X. Sòria-Perpinyà, B. Pérez-González, A. Ruíz-Verdú, J. Delegido & J.M. Moreno.
[![View PDF](https://img.shields.io/badge/View_Document-PDF-red?logo=adobe-acrobat-reader&logoColor=white)](docs/Caballero-proceedings-SBSR-2025-197673.pdf)

### 🇩🇪 International Ocean Colour Science (IOCS) Meeting
December 1–4, 2025 | Darmstadt, Germany.
* **Key Communication:** *Optimising 6S-based atmospheric correction for PRISMA and EnMAP hyperspectral imagery over inland waters.*
    * **Authors:** **Gabriel Rodrigo Caballero**, X. Sòria-Perpinyà, B. Alvado, A. Ruiz-Verdú, J. Delegido & J. Moreno.
[![View PDF](https://img.shields.io/badge/View_Document-PDF-red?logo=adobe-acrobat-reader&logoColor=white)](docs/GCaballero_IOCSM2025_poster.pdf)

## Citation

If you use this software in your research, please [cite](CITATION.cff) it as follows:

**APA Format:**
Caballero Cañas, G. R., Sòria Perpinyà, X., Alvado Arranz, B., & Ruiz-Verdú, A. (2026). 6ABOS: 6S-based Atmospheric Background Offset Subtraction v1.1.0 - Modular Architecture (v1.1.0) [Computer software]. Zenodo. https://doi.org/10.5281/zenodo.18300277

**BibTeX:**
```bibtex
@software{caballero_canas_2026_18300277,
  author       = {Caballero Cañas, Gabriel Rodrigo and 
                  Sòria Perpinyà, Xavier and 
                  Alvado Arranz, Bárbara and 
                  Ruiz-Verdú, Antonio},
  title        = {{6ABOS: 6S-based Atmospheric Background Offset Subtraction v1.1.0 - Modular Architecture}},
  month        = jan,
  year         = 2026,
  publisher    = {Zenodo},
  version      = {v1.1.0},
  doi          = {10.5281/zenodo.18300277},
  url          = {https://doi.org/10.5281/zenodo.18300277}
}
```
## License and Disclaimer
This project is licensed under the **GNU General Purpose License Version 3** - see the [GNU GPL V3](LICENSE) file for details.

This software is provided "as is", without warranty of any kind, express or implied. 6ABOS is a research tool developed for scientific purposes. While every effort has been made to ensure the accuracy of the 6S-based atmospheric correction scheme, the authors assume no liability for:

1. **Data Accuracy:** Any errors or inaccuracies in the output reflectance values resulting from poor quality Level 1 input data, incorrect metadata, or extreme atmospheric conditions.
2. **Decision Making:** The use of 6ABOS outputs for critical decision-making, environmental policy, or commercial applications without independent ground-truth validation.
3. **Software Stability:** Technical issues, bugs, or compatibility errors arising from the integration of the 6S radiative transfer engine or third-party dependencies.

The user assumes all responsibility for the validation of results and the appropriate use of the atmospheric correction framework in their specific study area.
