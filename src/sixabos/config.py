# -*- coding: utf-8 -*-
# 6ABOS: 6S-based Atmospheric Background Offset Subtraction for Atmospheric Correction
# Copyright (C) 2026 Gabriel Caballero (University of Valencia)
# email: gabriel.caballero@uv.es
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along
# with this program. If not, see <https://www.gnu.org/licenses/>.

""" 6ABOS: 6S-based Atmospheric Background Offset Subtraction Atmospheric Correction Framework
6ABOS Configuration settings.
Software package developed by UV"""

DEFAULT_CONF = {
    "verbose": True,
    "data_plotting": False,      # Enable spectral validation plots
    "data_storing": False,       # Save the output GeoTIFF
    "GEE": False,               # Use Google Earth Engine for atmospheric parameters
    "GEE_project_id": "project-id", 
    "max_wavelength": 2480,
    "min_wavelength": 379,
    "wavelength_step": 2.5,
    "aerosol_profile": 'Continental', # Options: 'Continental', 'Maritime', 'Urban', 'Desert', 'BiomassBurning'
    "tgas_threshold": 0.75,     # Mask pixels with low gas transmittance
    "input_dir": None,          # Path to EnMAP L1C folder
    "output_dir": None,         # Destination folder
    "output_rrs": True         # True for Rrs, False for pBOA
}