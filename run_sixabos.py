# -*- coding: utf-8 -*-
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
input_folder = r"C:\Users\gcaba\OneDrive\Documents\UV\Prometeo\EnMAP_6S_AC\ENMAP_L1C_Barbara\ENMAP01-____L1C-DT0000087385_20240731T112117Z_002_V010501_20241122T180323Z"
output_folder = r"D:\6ABOS_Results\Aerosol"

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
        "aerosol_profile": 'Urban', # Options: 'Continental', 'Maritime', 'Urban', 'Desert'
        'GEE': False,
        'GEE_project_id': "abos-482615", 
        'verbose': True,
        'output_rrs': True,
        "data_storing": False,
        'data_plotting': True  # Enable the SRF and validation plots
    }

    try:
        print("\n" + "="*60)
        print("MAIN EXECUTION PHASE")
        print("="*60)

        # Launch Main Process (now includes progress bar and plots)
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