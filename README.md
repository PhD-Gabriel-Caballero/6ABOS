# 6ABOS: 6S-based Atmospheric Background Offset Subtraction

**6ABOS** is a novel, efficient, and generic atmospheric correction (AC) framework designed specifically for **aquatic remote sensing**. It leverages a radiative transfer modeling (RTM) approach based on the **6S (Second Simulation of the Satellite Signal in the Solar Spectrum)** model to retrieve accurate water surface reflectance from hyperspectral sensors.

## 🌊 The Challenge
In aquatic remote sensing, accurately retrieving water quality parameters (e.g., chlorophyll-a, turbidity, CDOM) is a significant challenge. Light interaction with both the atmosphere and the water column is complex, and for inland water bodies, the water-leaving signal is often extremely weak compared to the atmospheric contribution. Standard land-based AC methods frequently fail to capture the subtle spectral signatures required for aquatic analysis.

## 🎯 Objectives
The objective of 6ABOS is to bridge the gap between complex RTMs and practical application by providing a method that is:
* **Efficient:** Reducing the computational burden of traditional pixel-by-pixel inversions.
* **Generic:** Applicable to various hyperspectral platforms, specifically validated for **Level 1 PRISMA and EnMAP** imagery.
* **Simple:** Utilizing a streamlined RTM scheme that remains accessible while maintaining scientific rigor.

## 🚀 Key Features
* **6S Engine Integration:** Built upon the robust and gold-standard 6S radiative transfer model version 1.1.
* **Multi-Sensor Support:** Optimized for the high spectral resolution of **PRISMA** and **EnMAP** missions.
* **Aquatic-Centric Design:** Specifically tuned for inland water bodies where atmospheric background noise is a dominant factor.
* **Background Mitigation:** Implements a specialized offset subtraction to isolate the water-leaving radiance from atmospheric interference.

## 🛠 Methodology
6ABOS implements a background offset subtraction framework. By modeling the atmospheric path radiance and solar irradiance through 6S, the system calculates a refined offset that is subtracted from the Top-of-Atmosphere (TOA) signal to retrieve the Bottom-of-Atmosphere (BOA) reflectance.

## 📁 Repository Structure
* `/src`: Core 6ABOS Python/R scripts.
* `/data`: Example metadata and spectral response functions (SRF) for PRISMA/EnMAP.
* `/docs`: Technical documentation and 6S compilation guides.
* `/notebooks`: Tutorials on how to process a sample EnMAP tile.

## 🤝 Affiliation & Support
This project is developed at the **Laboratory for Earth Observation**, Universitat de València, within the framework of the **RESSBIO** project. 

## Authors
For inquiries regarding collaboration or implementation for specific water quality monitoring projects, please contact the contributors.
**Gabriel Caballero** - *Lead Developer* - [gabriel.caballero@uv.es](mailto:gabriel.caballero@uv.es)

## 📄 License
This project is licensed under the **MIT** License - see the LICENSE file for details.

## ⚠️ Disclaimer
This software is provided "as is", without warranty of any kind, express or implied. 6ABOS is a research tool developed for scientific purposes. While every effort has been made to ensure the accuracy of the 6S-based atmospheric correction scheme, the authors assume no liability for:

1. **Data Accuracy:** Any errors or inaccuracies in the output reflectance values resulting from poor quality Level 1 input data, incorrect metadata, or extreme atmospheric conditions.
2. **Decision Making:** The use of 6ABOS outputs for critical decision-making, environmental policy, or commercial applications without independent ground-truth validation.
3. **Software Stability:** Technical issues, bugs, or compatibility errors arising from the integration of the 6S radiative transfer engine or third-party dependencies.

The user assumes all responsibility for the validation of results and the appropriate use of the atmospheric correction framework in their specific study area.

## 🏷️ Keywords
`Remote Sensing` `Hyperspectral` `EnMAP` `PRISMA` `Atmospheric Correction` `6S Model` `Water Quality` `Inland Waters`
