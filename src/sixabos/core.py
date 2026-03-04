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

"""
6ABOS: 6S-based Atmospheric Background Offset Subtraction Atmospheric Correction Framework
Radiative Transfer Modeling (RTM) & Physics Engine for 6ABOS.
Software package developed by UV
"""

import math
from datetime import datetime
import numpy as np
from Py6S import SixS, AtmosProfile, AeroProfile, Geometry, Altitudes, Wavelength, GroundReflectance

def run_single_6s_band(task_tuple):
    """Core function for 6S simulation per spectral band."""
    band_id, srf_values, scene_meta, conf = task_tuple
    try:
        s = SixS()

        # 1. Atmospheric profile
        s.atmos_profile = AtmosProfile.UserWaterAndOzone(
            scene_meta['sceneWV'], 
            scene_meta['ozoneValue']
        )
        
        # 2. Aerosol profile mapping
        aero_map = {
            'Continental': AeroProfile.Continental,
            'Maritime': AeroProfile.Maritime,
            'Urban': AeroProfile.Urban,
            'Desert': AeroProfile.Desert,
            'BiomassBurning': AeroProfile.BiomassBurning
        }
        
        chosen_profile = conf.get('aerosol_profile', 'Continental')
        s.aero_profile = AeroProfile.PredefinedType(
            aero_map.get(chosen_profile, AeroProfile.Continental)
        )
        s.aot550 = scene_meta['sceneAOT']
        
        # 3. Geometry (with date string protection)
        s.geometry = Geometry.User()
        dt = scene_meta['acquisition_date']
        if isinstance(dt, str):
            try:
                dt = datetime.strptime(dt.strip(), '%Y-%m-%d')
            except ValueError:
                dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))

        s.geometry.day, s.geometry.month = dt.day, dt.month
        s.geometry.solar_z = 90 - scene_meta['sunElevationAngle']
        s.geometry.solar_a = scene_meta['sunAzimuthAngle']
        s.geometry.view_z = scene_meta['viewingZenithAngle']
        s.geometry.view_a = scene_meta['viewingAzimuthAngle']
        
        # 4. Altitudes
        s.altitudes = Altitudes()
        s.altitudes.set_sensor_satellite_level()
        s.altitudes.set_target_custom_altitude(
            max(0, scene_meta['meanGroundElevation'] / 1000.0)
        )
        
        # 5. Ground Reflectance (Specific models for Water/Vegetation)
        if conf.get('use_lake_water', False):
            s.ground_reflectance = GroundReflectance.HomogeneousLambertian(
                GroundReflectance.LakeWater
            )
        else:
            s.ground_reflectance = GroundReflectance.HomogeneousLambertian(
                GroundReflectance.GreenVegetation
            )
            
        # 6. Wavelength (Spectral Response Function)
        s.wavelength = Wavelength(
            conf['min_wavelength']/1000.0, 
            conf['max_wavelength']/1000.0, 
            srf_values
        )
        
        # 7. Execute 6S
        s.run()

        if not s.outputs:
            return str(band_id), "Error: 6S execution returned no outputs"

        return str(band_id), {
            'spherical_albedo': s.outputs.spherical_albedo.total,
            'trans_ozone': s.outputs.transmittance_ozone.total,
            'trans_gas': s.outputs.transmittance_global_gas.total,
            'trans_scat_up': s.outputs.transmittance_total_scattering.upward,
            'path_rad': s.outputs.atmospheric_intrinsic_radiance,
            'solar_irr': s.outputs.direct_solar_irradiance + s.outputs.diffuse_solar_irradiance
        }
    except Exception as e:
        return str(band_id), f"Error: {e}"

class SixABOSEngine:
    """Atmospheric Correction Engine implementing physical inversion."""
    
    def __init__(self, config):
        self.conf = config
        self.results_6s = {}
        self.earth_sun_d = 1.0

    def compute_earth_sun_distance(self, dt):
        """Calculates Earth-Sun distance based on Julian Day."""
        if isinstance(dt, str):
            try:
                dt = datetime.strptime(dt.strip(), '%Y-%m-%d')
            except ValueError:
                dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
        
        doy = dt.timetuple().tm_yday
        self.earth_sun_d = 1 - 0.01672 * math.cos(math.radians(0.9856 * (doy - 4)))

    def prepare_rtm_tasks(self, scene_meta, df_srf, conf):
        """Generates list of tuples for parallel processing."""
        return [(bid, df_srf.loc[bid].values.tolist(), scene_meta, conf) for bid in df_srf.index]

    def apply_atmospheric_correction(self, toa_radiance, band_id):
        """Applies physical inversion: L_toa -> BOA Reflectance."""
        p = self.results_6s.get(str(band_id))
        
        # Check for valid results and gas transmittance thresholds
        if p is None or isinstance(p, str) or p['trans_gas'] <= self.conf['tgas_threshold']:
            return np.full(toa_radiance.shape, np.nan, dtype=np.float32)
        
        # 1. Earth-Sun distance correction and scale factor (1000.0)
        l_toa_corr = (toa_radiance * 1000.0) * (self.earth_sun_d**2)
        
        # 2. Complete Physical Inversion (Ozone and Spherical Albedo coupling)
        term = (l_toa_corr / p['trans_ozone']) - p['path_rad']
        denom = (p['solar_irr'] * p['trans_scat_up'] / np.pi) + (p['spherical_albedo'] * term)
        
        p_boa = term / denom
        
        # 3. Physical Clipping (Reflectance must be between 0 and 1.1)
        p_boa = np.clip(p_boa, 0, 1.1)
        
        # 4. Output format (Remote Sensing Reflectance vs Surface Reflectance)
        if self.conf.get('output_rrs', False):
            return (p_boa / np.pi).astype(np.float32)
            
        return p_boa.astype(np.float32)