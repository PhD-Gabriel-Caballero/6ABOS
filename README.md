[![Py6S](https://img.shields.io/badge/Powered%20by-Py6S-blue.svg)](https://py6s.readthedocs.io/en/master/)

# 6ABOS: 6S-based Atmospheric Background Offset Subtraction
<p align="center">
  <img src="assets/6ABOS.png" alt="6ABOS Header" width="100%">
</p>

**6ABOS** is a novel, efficient, and generic atmospheric correction (AC) framework designed specifically for **aquatic remote sensing**. It leverages a radiative transfer modeling (RTM) approach based on the **6S (Second Simulation of the Satellite Signal in the Solar Spectrum)** model to retrieve accurate water surface reflectance from hyperspectral sensors.

## The Challenge
In aquatic remote sensing, accurately retrieving water quality parameters (e.g., chlorophyll-a, turbidity, CDOM) is a significant challenge. Light interaction with both the atmosphere and the water column is complex, and for inland water bodies, the water-leaving signal is often extremely weak compared to the atmospheric contribution. Standard land-based AC methods frequently fail to capture the subtle spectral signatures required for aquatic analysis.

## Objectives
The objective of 6ABOS is to bridge the gap between complex RTMs and practical application by providing a method that is:
* **Efficient:** Reducing the computational burden of traditional pixel-by-pixel inversions.
* **Generic:** Applicable to various hyperspectral platforms, specifically validated for **Level 1 PRISMA and EnMAP** imagery.
* **Simple:** Utilizing a streamlined RTM scheme that remains accessible while maintaining scientific rigor.

## Key Features
* **6S Engine Integration:** Built upon the robust 6S radiative transfer model version 1.1.
* **Multi-Sensor Support:** Optimized for the high spectral resolution of **PRISMA** and **EnMAP** missions.
* **Atmospheric Physics:** The atmospheric correction engine is powered by Py6S, employing a Homogeneous Lambertian + Water Lake ground reflectance model.
  
## Methodology
6ABOS implements a atmospheric background offset subtraction framework. By modeling the atmospheric path radiance and solar irradiance through 6S, the system leverages simulated atmospheric parameters to solve the radiative transfer equation, enabling the conversion of Top-of-Atmosphere (TOA) radiance into Bottom-of-Atmosphere (BOA) reflectance.

## Repository Structure
* `/src`: Core 6ABOS Python/R scripts.
* `/data`: Example metadata and spectral response functions (SRF) for PRISMA/EnMAP.
* `/docs`: Technical documentation and 6S compilation guides.
* `/notebooks`: Tutorials on how to process a sample EnMAP tile.

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/PhD-Gabriel-Caballero/6ABOS/blob/main/notebooks/EnMAP/6ABOS_EnMAP_AC_v1.2_Dic_2025.ipynb)

## Affiliation & Support
This project is developed at the **Laboratory for Earth Observation**, Universitat de València, within the framework of the **RESSBIO** project. 

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


## License
This project is licensed under the **MIT** License - see the LICENSE file for details.

## Disclaimer
This software is provided "as is", without warranty of any kind, express or implied. 6ABOS is a research tool developed for scientific purposes. While every effort has been made to ensure the accuracy of the 6S-based atmospheric correction scheme, the authors assume no liability for:

1. **Data Accuracy:** Any errors or inaccuracies in the output reflectance values resulting from poor quality Level 1 input data, incorrect metadata, or extreme atmospheric conditions.
2. **Decision Making:** The use of 6ABOS outputs for critical decision-making, environmental policy, or commercial applications without independent ground-truth validation.
3. **Software Stability:** Technical issues, bugs, or compatibility errors arising from the integration of the 6S radiative transfer engine or third-party dependencies.

The user assumes all responsibility for the validation of results and the appropriate use of the atmospheric correction framework in their specific study area.

