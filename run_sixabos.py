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
Atmospheric data retrieval module (GEE integration)..
Software package developed by UV"""

import os
import sys
import glob
import traceback

# Setup paths to include src directory
current_dir = os.getcwd()
sys.path.append(os.path.join(current_dir, "src"))

try:
    from sixabos import main, utils
    print("--- [SYSTEM] 6ABOS Modules successfully hooked ---")
except ImportError as e:
    print(f"--- [ERROR] Module Hook Failed: {e} ---")
    sys.exit()

# Target paths

# input_folder: Root directory containing the EnMAP L1C scene (XML and TIFF files)
input_folder = r"C:\EnMAP_6S_AC\ENMAP_L1C_Barbara\ENMAP01-____L1C-DT0000087385_20240731T112117Z_002_V010501_20241122T180323Z" # example 

# output_folder: Destination for the corrected BOA (Bottom of Atmosphere) GeoTIFFs
output_folder = r"C:\6ABOS_Results"

# Ensure output directory exists
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

def run_sixabos():
    """
    Runs the full 6ABOS pipeline
    """
    user_config = {
        'input_dir': input_folder,
        'output_dir': output_folder,
        "aerosol_profile": 'Urban', # Options: 'Continental', 'Maritime', 'Urban', 'Desert', 'BiomassBurning'
        'GEE': False,
        'GEE_project_id': "user-project-id", 
        'verbose': True,
        'output_rrs': True,
        "data_storing": False,
        'data_plotting': True  # Enable the SRF and validation plots
    }

    try:
        print("\n" + "="*60)
        print("MAIN EXECUTION PHASE")
        print("="*60)

        # Launch main process 
        main.run_6abos(user_config)

        print("\n" + "="*60)
        print(" SUCCESS: Process finished successfully.")
        print("="*60)

    except Exception as e:
        print("\n" + "!"*60)
        print(f" CRITICAL ERROR: {type(e).__name__}")
        print(f" Message: {e}")
        print("!"*60)
        traceback.print_exc()

if __name__ == "__main__":
    run_sixabos()