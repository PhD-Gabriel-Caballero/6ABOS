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
Main processing orchestration module.
Software package developed by UV"""

import os, glob, time, numpy as np, matplotlib.pyplot as plt
from datetime import datetime
from osgeo import gdal
from .config import DEFAULT_CONF
from .utils import parse_xml, get_enmap_band_parameters, save_enmap_tiff, calculate_gaussian_srf, print_6s_inputs, plot_6abos_validation, plot_sensor_srf
from .core import SixABOSEngine, run_single_6s_band
from .atmospheric import Atmospheric
from concurrent.futures import ProcessPoolExecutor, as_completed

gdal.UseExceptions()

def run_6abos(user_config=None):
    """Executes the complete 6ABOS atmospheric correction pipeline."""
    conf = DEFAULT_CONF.copy()
    if user_config: conf.update(user_config)
    
    start_wall_time = time.time()
    
    # Metadata extraction & Date fix
    xml_path = glob.glob(os.path.join(conf['input_dir'], "*METADATA.XML"))[0]
    toa_path = glob.glob(os.path.join(conf['input_dir'], "*SPECTRAL_IMAGE.TIF"))[0]
    
    if conf.get('verbose'):
        print(f"[*] Path to TOA radiance: {toa_path}\n")

    scene_meta = parse_xml(xml_path, conf)
    
    if isinstance(scene_meta['acquisition_date'], str):
        raw_date = scene_meta['acquisition_date'][:10]
        scene_meta['acquisition_date'] = datetime.strptime(raw_date, '%Y-%m-%d')
    
    spectral_conf = get_enmap_band_parameters(xml_path, conf)
    
    # GEE Integration (Water, Ozone, Aerosol)
    if conf.get('GEE', False):
        pid = conf.get('GEE_project_id') 
        if Atmospheric.initialize_gee(pid):
            try:
                import ee
                geom = ee.Geometry.Point([scene_meta['scene_center_long'], scene_meta['scene_center_lat']])
                date = ee.Date(scene_meta['startTime'])
                
                print("[GEE] Fetching atmospheric data (NCEP/TOMS/MODIS)...")
                scene_meta['sceneWV'] = Atmospheric.water(geom, date).getInfo()
                scene_meta['ozoneValue'] = Atmospheric.ozone(geom, date).getInfo()
                scene_meta['sceneAOT'] = Atmospheric.aerosol(geom, date).getInfo()
            except Exception as e:
                print(f"[GEE WARNING] Cloud fetch failed: {e}. Using XML defaults.")

    # Engine Setup
    engine = SixABOSEngine(conf)
    engine.compute_earth_sun_distance(scene_meta['acquisition_date'])
    
    if conf.get('verbose'):
        print_6s_inputs(scene_meta, engine, conf)

    # Spectral Response Functions
    df_srf = calculate_gaussian_srf(spectral_conf, np.arange(conf['min_wavelength'], conf['max_wavelength'], conf['wavelength_step']))
    
    # SRF visualization 
    if conf.get('data_plotting'):
        plot_sensor_srf(df_srf, conf)
    
    tasks = engine.prepare_rtm_tasks(scene_meta, df_srf, conf)
    
    # Parallel 6S Radiative Transfer Modelling 
    total_rtm = len(tasks)
    start_time_rtm = time.time()
    print(f"[RTM] Simulating {total_rtm} bands in parallel...")
    
    with ProcessPoolExecutor() as executor:
        futures = {executor.submit(run_single_6s_band, t): t[0] for t in tasks}
        for i, future in enumerate(as_completed(futures), 1):
            elapsed = time.time() - start_time_rtm
            avg_time = elapsed / i
            remaining = avg_time * (total_rtm - i)
            pct = (i / total_rtm) * 100
            bar = '=' * int(pct/2) + '>' + '-' * (50 - int(pct/2))
            print(f'\r    Progress: [{bar:51}] {pct:.1f}% | ETA: {remaining:.0f}s ', end='', flush=True)
            bid, res = future.result()
            engine.results_6s[bid] = res

    # Atmospheric Correction  
    print(f"\n\n[*] Applying atmospheric correction to image cube...")
    ds = gdal.Open(toa_path)
    num_bands = ds.RasterCount
    output_cube = np.empty((num_bands, ds.RasterYSize, ds.RasterXSize), dtype=np.float32)
    toa_cube = np.empty((num_bands, ds.RasterYSize, ds.RasterXSize), dtype=np.float32)

    for i in range(1, num_bands + 1):
        # Counter every 20 bands
        if i % 20 == 0 or i == num_bands:
            print(f"    -> Processing Band {i}/{num_bands}")
            
        band_meta = spectral_conf.iloc[i-1]
        rad = ds.GetRasterBand(i).ReadAsArray() * band_meta['gain'] + band_meta['offset']
        toa_cube[i-1] = rad
        output_cube[i-1] = engine.apply_atmospheric_correction(rad, i)

    # Export
    if conf.get('data_storing'):
        folder_name = os.path.basename(os.path.normpath(conf['input_dir'])) # Get input folder name
        
        # Determine suffix based on rrs parameter
        suffix = "-rrs-6abos.tif" if conf.get('output_rrs') else "-pboa-6abos.tif"
        file_name = f"{folder_name}{suffix}"
        
        out_path = os.path.join(conf['output_dir'] or conf['input_dir'], file_name)
        
        print(f"\n[*] GDAL is processing and writing the output Geotiff...")
        save_enmap_tiff(output_cube, out_path, toa_path, spectral_conf)
        print(f"\n[OK] Processing complete. Output: {out_path}")
        
    # Plotting spectra for validation
    if conf.get('data_plotting'):
        print("[*] Generating validation spectral plot...")
        plot_6abos_validation(toa_cube, output_cube, spectral_conf, conf)
        
        print("\n" + "="*60)
        print(" PROCESS FINISHED SUCCESSFULLY")
        print(" The plot window is now active.")
        print(" PLEASE PRESS 'ENTER' IN THIS CONSOLE TO CLOSE THE PROGRAM.")
        print("="*60)
        
        input()