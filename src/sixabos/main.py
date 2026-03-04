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

import os
import glob
import time
import argparse
import sys
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, as_completed

import numpy as np
from osgeo import gdal

from .config import DEFAULT_CONF
from .utils import (
    parse_xml, get_enmap_band_parameters, save_enmap_tiff, 
    calculate_gaussian_srf, print_6s_inputs, plot_6abos_validation, 
    plot_sensor_srf
)
from .core import SixABOSEngine, run_single_6s_band

def run_6abos(user_conf=None):
    """Main execution workflow for 6ABOS processing."""
    conf = DEFAULT_CONF.copy()
    if user_conf:
        conf.update(user_conf)

    # CLI Argument Configuration
    parser = argparse.ArgumentParser(description='6ABOS: 6S-based Atmospheric Background Offset Subtraction')
    parser.add_argument('--input', type=str, help='Path to EnMAP L1C folder')
    parser.add_argument('--output', type=str, help='Destination folder')
    parser.add_argument('--tgas', type=float, help='Gas transmittance threshold', default=conf['tgas_threshold'])
    parser.add_argument('--aerosol', type=str, choices=['Continental', 'Maritime', 'Urban', 'Desert', 'BiomassBurning'], 
                        help='Aerosol profile', default=conf['aerosol_profile'])
    parser.add_argument('--lakewater', action='store_true', help='Use LakeWater reflectance model in 6S')
    
    args = parser.parse_args()

    # Update configuration from CLI
    if args.input: conf['input_dir'] = args.input
    if args.output: conf['output_dir'] = args.output
    conf['tgas_threshold'] = args.tgas
    conf['aerosol_profile'] = args.aerosol
    conf['use_lake_water'] = args.lakewater 
    
    print(f"\n{'='*60}\n 6ABOS Atmospheric Correction Framework \n{'='*60}")
    
    # 1. Path Discovery for TIF and Metadata
    try:
        toa_path = glob.glob(os.path.join(conf['input_dir'], '*SPECTRAL_IMAGE.TIF'))[0]
        xml_path = glob.glob(os.path.join(conf['input_dir'], '*METADATA.XML'))[0]
    except (IndexError, TypeError):
        print(f"[ERROR] EnMAP L1C files not found at: {conf.get('input_dir')}")
        print("Please use the --input flag with the correct path.")
        return

    # 2. Parsing Metadata and Band Parameters
    scene_meta = parse_xml(xml_path, conf)
    spectral_conf = get_enmap_band_parameters(xml_path, conf)
    
    # 3. Atmospheric Correction Engine Initialization
    engine = SixABOSEngine(conf)
    engine.compute_earth_sun_distance(scene_meta['acquisition_date'])

    # 4. Sensor Spectral Response Function (SRF) Calculation
    print("[*] Calculating Sensor Spectral Response Functions (SRF)...")
    wavelength_range = np.arange(conf['min_wavelength'], conf['max_wavelength'], conf['wavelength_step'])
    df_srf = calculate_gaussian_srf(spectral_conf, wavelength_range)

    # 5. Parallel 6S RTM Execution
    print(f"[*] Launching 6S RTM simulations (Parallel Engine)...")
    tasks = engine.prepare_rtm_tasks(scene_meta, df_srf, conf)
    total_rtm = len(tasks)
    start_time_rtm = time.time()
    
    # CPU Management: reserving one core for system stability
    max_workers = max(1, os.cpu_count() - 1)
    print(f"    -> Using {max_workers} workers for {total_rtm} bands.")

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        # Submit all RTM tasks
        futures = {executor.submit(run_single_6s_band, t): t[0] for t in tasks}
        
        # Process results as they complete to update progress feedback
        for i, future in enumerate(as_completed(futures), 1):
            bid, res = future.result()
            engine.results_6s[bid] = res
            
            # Progress bar and ETA calculation
            elapsed = time.time() - start_time_rtm
            avg_time = elapsed / i
            remaining = avg_time * (total_rtm - i)
            pct = (i / total_rtm) * 100
            
            bar_len = 40
            filled = int(bar_len * i // total_rtm)
            bar = '=' * filled + '>' + '-' * (bar_len - filled)
            
            print(f'\r    Progress: [{bar}] {pct:.1f}% | Band {bid} done | ETA: {remaining:.0f}s ', end='', flush=True)

    print(f"\n[*] 6S simulations finished in {time.time() - start_time_rtm:.1f} seconds.")

    # 6. Surface Reflectance Inversion (Spatial Processing)
    ds = gdal.Open(toa_path)
    rows, cols = ds.RasterYSize, ds.RasterXSize
    num_bands = ds.RasterCount
    
    output_cube = np.zeros((num_bands, rows, cols), dtype=np.float32)

    print(f"[*] Applying physical inversion to {num_bands} bands...")
    for i in range(1, num_bands + 1):
        if i % 50 == 0 or i == num_bands:
            print(f"    -> Processing Band {i}/{num_bands}")
            
        band_meta = spectral_conf.iloc[i-1]
        # Radiometric calibration (Applying gain/offset to raw data)
        rad = ds.GetRasterBand(i).ReadAsArray() * band_meta['gain'] + band_meta['offset']
        output_cube[i-1] = engine.apply_atmospheric_correction(rad, i)

    # 7. Final Export to Geotiff
    if conf.get('data_storing'):
        folder_name = os.path.basename(os.path.normpath(conf['input_dir']))
        suffix = "-6abos-corrected.tif"
        file_name = f"{folder_name}{suffix}"
        out_path = os.path.join(conf['output_dir'] or conf['input_dir'], file_name)
        
        save_enmap_tiff(output_cube, out_path, toa_path, spectral_conf)
        print(f"\n[OK] Processing complete. Output file: {out_path}")

if __name__ == "__main__":
    run_6abos()