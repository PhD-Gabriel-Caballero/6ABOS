# 6ABOS: 6S-based Atmospheric Background Offset Subtraction

**6ABOS** is an atmospheric correction (AC) tool specifically developed for **EnMAP** (Environmental Mapping and Analysis Program) hyperspectral data. It leverages the **6S radiative transfer model** to perform precise offset subtraction, accounting for atmospheric background effects that often contaminate surface reflectance products.

## ⚠️ Purpose
Standard atmospheric corrections may leave residual offsets due to complex aerosol-surface interactions. 6ABOS implements a robust subtraction method to improve the signal-to-noise ratio and the spectral integrity of EnMAP data, crucial for downstream bio-geochemical analysis.

## 🚀 Key Features
* **6S Integration:** Full coupling with the Second Simulation of the Satellite Signal in the Solar Spectrum (6S).
* **Hyperspectral Support:** Optimized for the high spectral resolution of EnMAP.
* **Background Mitigation:** Advanced subtraction of atmospheric background radiance.
* **Open Science:** Developed within the framework of **Arfik** and **SysBio** (Universitat de València).
