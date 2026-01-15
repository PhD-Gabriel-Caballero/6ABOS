# -*- coding: utf-8 -*-
# 6ABOS: 6S-based Atmospheric Background Offset Subtraction for Atmospheric Correction
# Copyright (C) 2026 Gabriel Caballero (University of Valencia)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along
# with this program. If not, see <https://www.gnu.org/licenses/>.

"""6ABOS Atmospheric processing framework. Software package developed by UV."""

import os
import numpy as np
import pandas as pd
import xml.etree.ElementTree as ET
from osgeo import gdal

def parse_xml(xml_file):
    """Parses EnMAP L1C METADATA.XML to extract global scene parameters."""
    tree = ET.parse(xml_file)
    root = tree.getroot()
    start_time = root.find('.//startTime').text
    acquisition_date = start_time[0:10]

    longitude = None
    latitude = None
    for point in root.findall(".//spatialCoverage//boundingPolygon//point"):
        frame_element = point.find("frame")
        if frame_element is not None and frame_element.text == "center":
            latitude = float(point.find("latitude").text)
            longitude = float(point.find("longitude").text)

    scene_parameters = {
        "startTime": start_time,
        "acquisition_date": acquisition_date,
        "scene_center_long": longitude,
        "scene_center_lat": latitude,
        "season": root.find('.//season').text,
        "meanGroundElevation": float(root.find('.//meanGroundElevation').text),
        "ozoneValue": int(root.find('.//ozoneValue').text) / 1000.0,
        "sceneAOT": int(root.find('.//sceneAOT').text) / 1000.0,
        "sceneWV": int(root.find('.//sceneWV').text) / 1000.0,
        "sunElevationAngle": float(root.find('.//sunElevationAngle//center').text),
        "sunAzimuthAngle": float(root.find('.//sunAzimuthAngle//center').text),
        "viewingAzimuthAngle": float(root.find('.//viewingAzimuthAngle//center').text),
        "viewingZenithAngle": float(root.find('.//viewingZenithAngle//center').text)
    }
    return scene_parameters

def get_enmap_band_parameters(xml_file):
    """Extracts Gain, Offset, and FWHM for each EnMAP band."""
    tree = ET.parse(xml_file)
    root = tree.getroot()
    bands_list = []
    for band in root.findall('.//bandCharacterisation/bandID'):
        band_data = {
            'band_id': int(band.get('number')),
            'wavelength_center': float(band.find('wavelengthCenterOfBand').text),
            'fwhm': float(band.find('FWHMOfBand').text),
            'gain': float(band.find('GainOfBand').text),
            'offset': float(band.find('OffsetOfBand').text)
        }
        bands_list.append(band_data)
    return pd.DataFrame(bands_list)

def calculate_gaussian_srf(df_enmap, spectral_range):
    """Generates Gaussian Spectral Response Functions (SRF)."""
    srf_results = []
    for _, row in df_enmap.iterrows():
        center = row['wavelength_center']
        fwhm = row['fwhm']
        sigma = fwhm / (2 * np.sqrt(2 * np.log(2)))
        gaussian_curve = np.exp(-((spectral_range - center)**2) / (2 * sigma**2))
        srf_results.append(gaussian_curve)
    df_srf = pd.DataFrame(srf_results, columns=spectral_range)
    df_srf.index = df_enmap['band_id']
    return df_srf

def save_enmap_tiff(data_cube, output_path, reference_raster_path, metadata_df):
    """Saves output cube as GeoTIFF with spectral metadata."""
    bands_count, rows, cols = data_cube.shape
    ref_ds = gdal.Open(reference_raster_path)
    if ref_ds is None:
        raise FileNotFoundError(f"Reference raster {reference_raster_path} not found.")

    driver = gdal.GetDriverByName("GTiff")
    out_ds = driver.Create(output_path, cols, rows, bands_count, gdal.GDT_Float32)
    out_ds.SetGeoTransform(ref_ds.GetGeoTransform())
    out_ds.SetProjection(ref_ds.GetProjection())

    for i in range(bands_count):
        out_band = out_ds.GetRasterBand(i + 1)
        out_band.WriteArray(data_cube[i, :, :])
        out_band.SetNoDataValue(np.nan)
        row = metadata_df.iloc[i]
        out_band.SetMetadataItem("WAVELENGTH", str(row['wavelength_center']))
        out_band.SetDescription(f"Band_{row['band_id']}_{row['wavelength_center']}nm")
    
    out_ds.FlushCache()
    out_ds = None
    ref_ds = None
