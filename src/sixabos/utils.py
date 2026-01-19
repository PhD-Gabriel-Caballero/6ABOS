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
6ABOS Utility functions.
Software package developed by UV"""


import numpy as np
import pandas as pd
import os, glob, time, matplotlib.pyplot as plt
import xml.etree.ElementTree as ET
from osgeo import gdal

gdal.UseExceptions()

def parse_xml(xml_file, conf=None):
    """Parses EnMAP L1C METADATA.XML to extract global scene parameters."""
    tree = ET.parse(xml_file)
    root = tree.getroot()
    
    # Extract start time and date
    start_time_el = root.find('.//startTime')
    start_time = start_time_el.text if start_time_el is not None else "2024-01-01T00:00:00"
    acquisition_date = start_time[0:10]

    # Find scene center coordinates safely
    longitude = None
    latitude = None
    for point in root.findall(".//spatialCoverage//boundingPolygon//point"):
        frame_element = point.find("frame")
        if frame_element is not None and frame_element.text == "center":
            latitude = float(point.find("latitude").text)
            longitude = float(point.find("longitude").text)

    # Helper function for nested tags like <sunElevationAngle><center>VALUE</center></sunElevationAngle>
    def get_nested_float(xpath, default=0.0):
        try:
            element = root.find(xpath)
            if element is not None and element.text and element.text.strip():
                return float(element.text)
            return default
        except (ValueError, TypeError):
            return default

    scene_parameters = {
        "startTime": start_time,
        "acquisition_date": acquisition_date,
        "scene_center_long": longitude,
        "scene_center_lat": latitude,
        "season": root.find('.//season').text if root.find('.//season') is not None else "N/A",
        "meanGroundElevation": get_nested_float('.//meanGroundElevation'),
        "ozoneValue": get_nested_float('.//ozoneValue') / 1000.0,
        "sceneAOT": get_nested_float('.//sceneAOT') / 1000.0,
        "sceneWV": get_nested_float('.//sceneWV') / 1000.0,
        "sunElevationAngle": get_nested_float('.//sunElevationAngle//center', 45.0),
        "sunAzimuthAngle": get_nested_float('.//sunAzimuthAngle//center', 150.0),
        "viewingAzimuthAngle": get_nested_float('.//viewingAzimuthAngle//center', 0.0),
        "viewingZenithAngle": get_nested_float('.//viewingZenithAngle//center', 0.0)
    }
    if conf.get('verbose', False):
        print("\n" + "="*60)
        print('Metadata of EnMAP-acquired scene')
        print("="*60)
        for key, value in scene_parameters.items():
            print(f"  {key}: {value}")
        print("="*60)
    
    return scene_parameters

def get_enmap_band_parameters(xml_file, conf=None):
    """Extracts Gain, Offset, and FWHM for each EnMAP band using working XPaths."""
    tree = ET.parse(xml_file)
    root = tree.getroot()
    bands_list = []
    
    # Specific path: bandCharacterisation/bandID
    for band in root.findall('.//bandCharacterisation/bandID'):
        try:
            band_data = {
                'band_id': int(band.get('number')),
                'wavelength_center': float(band.find('wavelengthCenterOfBand').text),
                'fwhm': float(band.find('FWHMOfBand').text),
                'gain': float(band.find('GainOfBand').text),
                'offset': float(band.find('OffsetOfBand').text)
            }
            bands_list.append(band_data)
        except (AttributeError, TypeError, ValueError):
            continue
            
    df = pd.DataFrame(bands_list)        
    
    # Security check
    if df.empty:
        raise ValueError("[CRITICAL] No EnMAP bands found in the XML metadata. Check the XPath: './/bandCharacterisation/bandID'")
    
    # Display EnMAP spectral configuration parameters       
    if conf.get('verbose', False):   
        print("\n" + "="*90)
        print(f"  ENMAP BAND PARAMETERS (First 10 of {len(df)} bands)")
        print("="*90)
        print(f"{'INDEX':<6} | {'BAND ID':<8} | {'CWL (nm)':<12} | {'FWHM (nm)':<10} | {'GAIN':<12} | {'OFFSET'}")
        print("-" * 90)
        for i, row in df.head(10).iterrows():
            print(f"{i:<6} | {int(row['band_id']):<8} | {row['wavelength_center']:<12.2f} | "
                  f"{row['fwhm']:<10.2f} | {row['gain']:<12.6f} | {row['offset']:.4f}")
        print("-" * 90)
        print(f"  Total bands parsed: {len(df)}")
        print("="*90 + "\n")
            
    return df

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
    df_srf.index = df_enmap['band_id'].astype(str) # String index for consistency
    return df_srf

def plot_6abos_validation(toa_cube, boa_cube, spectral_conf, conf=None):
    """
    Generates the scientific dual-axis plot (L_TOA vs BOA/Rrs).
    Includes H2O absorption windows and high-fidelity styling.
    """
    if conf is None:
        conf = {}
        
    x_coord, y_coord = 400, 800
    h2o_windows = [
        (710, 735), (810, 840), (890, 990), (1080, 1180), 
        (1300, 1500), (1750, 2000), (2300, 2500)
    ]
    
    if y_coord >= toa_cube.shape[1] or x_coord >= toa_cube.shape[2]:
        y_coord, x_coord = toa_cube.shape[1]//2, toa_cube.shape[2]//2

    wv = spectral_conf['wavelength_center'].values
    pixel_ltoa = toa_cube[:, y_coord, x_coord] * 1000 # Convert to W
    pixel_spectrum = boa_cube[:, y_coord, x_coord]

    fig, ax1 = plt.subplots(figsize=(10, 6))
    
    # Axis 1: BOA Reflectance/Rrs
    label_boa = 'Remote Sensing Reflectance ($sr^{-1}$)' if conf.get('output_rrs') else 'Surface Reflectance'
    line1, = ax1.plot(wv, pixel_spectrum, color='black', lw=2, label=f'EnMAP {label_boa}')
    ax1.set_ylabel(label_boa, fontsize=12, color='black')
    ax1.set_xlabel('Wavelength (nm)', fontsize=12)
    
    # Axis 2: TOA Radiance
    ax2 = ax1.twinx()
    line2, = ax2.plot(wv, pixel_ltoa, color='green', lw=1.5, ls=':', label='EnMAP $L_{TOA}$')
    ax2.set_ylabel('TOA Radiance ($W \cdot m^{-2} \cdot sr^{-1} \cdot nm^{-1}$)', fontsize=12, color='green', labelpad=15)

    # Add H2O absorption bands
    for i, (start, end) in enumerate(h2o_windows):
        ax1.axvspan(start, end, color='skyblue', alpha=0.3, label="Atmospheric $H_{2}O$ Absorption" if i==0 else "")

    plt.title(f'Spectral Integrity Check: Pixel ({x_coord}, {y_coord})', fontsize=14)
    ax1.axhline(0, color='red', lw=1, ls='--', alpha=0.5, label='zero-line')
    
    # Combine legends
    lines = [line1, line2]
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc='upper right', frameon=True)
    
    plt.tight_layout()
    plt.show(block=False) 
    plt.pause(0.1)

def print_6s_inputs(scene_meta, engine, conf=None):
    """
    Prints the 6S input parameters to the console for verification.
    """
    if conf is None:
        conf = {}

    dt = scene_meta['acquisition_date']
    doy = dt.timetuple().tm_yday
    sun_zenith = 90 - scene_meta['sunElevationAngle']
    
    print("\n" + "="*60)
    print(" 6S INPUT PARAMETERS")
    print("="*60)
    print(f"Image acquisition date:  {dt}")
    print(f"Sun-Earth distance (AU): {engine.earth_sun_d:.16f}")
    print(f"Day of the year:         {doy}")
    print(f"Target Altitude:         {scene_meta['meanGroundElevation'] / 1000.0:.5f} km")
    print(f"H2O g/cm²):                     {scene_meta['sceneWV']:.4f}")
    print(f"O3 (cm-atm):                      {scene_meta['ozoneValue']:.4f}")
    print(f"AOT 550 nm:              {scene_meta['sceneAOT']:.4f}")
    print(f"Sun Zenith Angle:        {sun_zenith:.6f} deg")
        
    # Corrected Cosine calculation (degrees to radians)
    cos_sz = np.cos(np.radians(sun_zenith))
    print(f"Cosine of solar zenith:  {cos_sz:.16f}")
    
    # Safe access to threshold
    tgas_limit = conf.get('tgas_threshold', 0.75)
    print(f"Gas trans. threshold:    {tgas_limit}")
    print("="*60 + "\n")
    
def plot_sensor_srf(df_srf, conf):
    """
    Visualizes the Sensor Spectral Response Functions (SRF) and auto-closes the window.
    
    Parameters:
    -----------
    df_srf : pandas.DataFrame
        The SRF matrix where rows are bands and columns are wavelengths.
    conf : dict
        Configuration dictionary containing spectral range parameters.
    """
    print("[*] Displaying sensor SRF profiles (Auto-closing in 2s)...")
    
    # Extract spectral range from configuration
    wv_min = conf.get('min_wavelength') 
    wv_max = conf.get('max_wavelength')  
    wv_step = conf.get('wavelength_step')
    
    # Reconstruct the spectral range for the X-axis
    spectral_range = np.arange(wv_min, wv_max, wv_step)
    
    # Create the plot
    plt.figure(figsize=(15, 5))
    
    # Transpose df_srf to align wavelengths with the X-axis
    plt.plot(spectral_range, df_srf.T, lw=0.8, alpha=0.6)
    
    plt.title('EnMAP Sensor Spectral Response Functions (SRF)', fontsize=14)
    plt.xlabel('Wavelength [nm]', fontsize=12)
    plt.ylabel('Relative Response', fontsize=12)
    plt.grid(True, linestyle=':', alpha=0.5)
    
    # Automated display logic (Non-blocking)
    plt.show(block=False)
    plt.pause(2)  # Maintain window for 2 seconds
    plt.close()   # Automated teardown
    
    print("[*] Continuing with atmospheric simulation...\n")

def save_enmap_tiff(data_cube, output_path, reference_raster_path, metadata_df):
    """Saves output cube as GeoTIFF with spectral metadata."""
    if os.path.exists(output_path):
        try:
            with open(output_path, 'a+b'):
                pass
        except IOError:
            print("\n" + "!"*60)
            print(f" CRITICAL ERROR: File is locked or permission denied.")
            print(f" Path: {output_path}")
            print(" Please close QGIS or any other software using this file.")
            print("!"*60 + "\n")
            return
    try:
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
            out_band.SetMetadataItem("WAVELENGTH_UNIT", "nm")
            out_band.SetMetadataItem("FWHM", str(row['fwhm']))
            out_band.SetMetadataItem("Scale", str(row['gain']))
            out_band.SetMetadataItem("Offset", str(row['offset'])) 
            out_band.SetDescription(f"Band_{row['band_id']}_{row['wavelength_center']}nm")
        
        out_ds.FlushCache()
        out_ds = None
        ref_ds = None
        
    except Exception as e:
        print(f"\n[ERROR] GDAL failed to write: {e}")
