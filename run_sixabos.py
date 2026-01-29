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
import argparse
import traceback

# Setup paths to include src directory if running from source
# This is a fallback in case the package is not yet installed in the environment
try:
    from sixabos import main, utils
    print("--- [SYSTEM] 6ABOS Modules successfully hooked ---")
except ImportError:
    # If import fails, try to look into the 'src' folder relative to this script
    sys.path.append(os.path.join(os.path.dirname(__file__), "src"))
    try:
        from sixabos import main, utils
    except ImportError as e:
        print(f"--- [ERROR] Module Hook Failed: {e} ---")
        sys.exit(1)

def run_sixabos():
    """
    Runs the full 6ABOS pipeline using command-line arguments
    """
    # CLI Argument Parser setup
    parser = argparse.ArgumentParser(description="6ABOS: Full-stack tool for CLMS vegetation monitoring")
    
    parser.add_argument("-i", "--input", help="Path to EnMAP L1C scene directory", required=False)
    parser.add_argument("-o", "--output", help="Path to destination folder for results", required=False)
    parser.add_argument("-p", "--project", help="Google Earth Engine Project ID", default="user-project-id")
    parser.add_argument("--aerosol", help="Aerosol profile (Urban, Continental, etc.)", default="Urban")
    
    args = parser.parse_args()

    # Path logic: Use arguments if provided, otherwise fallback to local default folders.
    # This prevents hardcoded path errors on different operating systems (Linux/Mac/Windows).
    input_folder = args.input if args.input else os.path.join(os.getcwd(), "input_sample")
    output_folder = args.output if args.output else os.path.join(os.getcwd(), "6ABOS_Results")

    # Ensure output directory exists (cross-platform compatible)
    if not os.path.exists(output_folder):
        os.makedirs(output_folder, exist_ok=True)

    # Configuration dictionary for the main pipeline
    user_config = {
        'input_dir': input_folder,
        'output_dir': output_folder,
        'aerosol_profile': args.aerosol, 
        'GEE': False,
        'GEE_project_id': args.project, 
        'verbose': True,
        'output_rrs': True,
        'data_storing': False,
        'data_plotting': True  
    }

    try:
        print("\n" + "="*60)
        print(f"MAIN EXECUTION PHASE")
        print(f"Input: {input_folder}")
        print(f"Output: {output_folder}")
        print("="*60)

        # Launch the core processing engine
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
        sys.exit(1)

if __name__ == "__main__":
    run_sixabos()
