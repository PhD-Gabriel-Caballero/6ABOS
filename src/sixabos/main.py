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
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along
# with this program. If not, see <https://www.gnu.org/licenses/>.

"""6ABOS Atmospheric processing framework. Software package developed by UV."""

import os
import sys
import glob
import numpy as np
from osgeo import gdal
from .config import DEFAULT_CONF
from .utils import parse_xml, get_enmap_band_parameters, save_enmap_tiff
from .core import SixABOSEngine
from .atmospheric import Atmospheric

def run_6abos(user_config=None):
    conf = DEFAULT_CONF.copy()
    if user_config: conf.update(user_config)
    if not conf['input_dir'] or not os.path.exists(conf['input_dir']):
        print(f"Error: {conf['input_dir']} not found."); return

    xml_path = glob.glob(os.path.join(conf['input_dir'], "*METADATA.XML"))[0]
    toa_path = glob.glob(os.path.join(conf['input_dir'], "*SPECTRAL_IMAGE.TIF"))[0]
    scene_meta = parse_xml(xml_path)
    spectral_conf = get_enmap_band_parameters(xml_path)

    if conf['GEE']:
        if Atmospheric.initialize_gee():
            import ee
            date_ee = ee.Date(scene_meta['acquisition_date'])
            geom_ee = ee.Geometry.Point(scene_meta['scene_center_long'], scene_meta['scene_center_lat'])
            scene_meta['sceneWV'] = Atmospheric.water(geom_ee, date_ee).getInfo()
            scene_meta['ozoneValue'] = Atmospheric.ozone(geom_ee, date_ee).getInfo()
            scene_meta['sceneAOT'] = Atmospheric.aerosol(geom_ee, date_ee).getInfo()

    engine = SixABOSEngine(conf)
    engine.run_rtm_loop(scene_meta, spectral_conf)
    ds = gdal.Open(toa_path)
    output_cube = np.empty((ds.RasterCount, ds.RasterYSize, ds.RasterXSize), dtype=np.float32)

    for i in range(1, ds.RasterCount + 1):
        toa_rad = ds.GetRasterBand(i).ReadAsArray() * spectral_conf.iloc[i-1]['gain'] + spectral_conf.iloc[i-1]['offset']
        output_cube[i-1, :, :] = engine.apply_atmospheric_correction(toa_rad, i)

    if conf['data_storing']:
        save_enmap_tiff(output_cube, os.path.join(conf['output_dir'] or conf['input_dir'], "6ABOS_EnMAP_L2.tif"), toa_path, spectral_conf)

def main():
    config_update = {}
    if len(sys.argv) > 1: config_update['input_dir'] = sys.argv[1]
    run_6abos(config_update)

if __name__ == "__main__": main()
