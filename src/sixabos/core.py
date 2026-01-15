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

import numpy as np
import math
from Py6S import SixS, AtmosProfile, AeroProfile, Geometry, Altitudes, Wavelength
from .utils import calculate_gaussian_srf

class SixABOSEngine:
    def __init__(self, config):
        self.conf = config
        self.results_6s = {}
        self.earth_sun_d = None

    def compute_earth_sun_distance(self, acquisition_date):
        from datetime import datetime
        date_obj = datetime.strptime(acquisition_date, '%Y-%m-%d')
        doy = date_obj.timetuple().tm_yday
        self.earth_sun_d = 1 - 0.01672 * math.cos(math.radians(0.9856 * (doy - 4)))
        return doy

    def run_rtm_loop(self, scene_meta, spectral_conf):
        s = SixS()
        s.atmos_profile = AtmosProfile.UserWaterAndOzone(scene_meta['sceneWV'], scene_meta['ozoneValue'])
        s.aero_profile = AeroProfile.Continental
        s.aot550 = scene_meta['sceneAOT']
        s.geometry = Geometry.User()
        s.geometry.day = int(scene_meta['acquisition_date'].split('-')[2])
        s.geometry.month = int(scene_meta['acquisition_date'].split('-')[1])
        s.geometry.solar_z = 90 - scene_meta['sunElevationAngle']
        s.geometry.solar_a = scene_meta['sunAzimuthAngle']
        s.geometry.view_z = scene_meta['viewingZenithAngle']
        s.geometry.view_a = scene_meta['viewingAzimuthAngle']
        s.altitudes = Altitudes()
        s.altitudes.set_sensor_satellite_level()
        s.altitudes.set_target_custom_altitude(max(0, scene_meta['meanGroundElevation'] / 1000.0))

        spectral_range = np.arange(self.conf['min_wavelength'], self.conf['max_wavelength'], self.conf['wavelength_step'])
        df_srf = calculate_gaussian_srf(spectral_conf, spectral_range)

        for band_id in df_srf.index:
            srf_values = df_srf.loc[band_id].values.tolist()
            s.wavelength = Wavelength(self.conf['min_wavelength']/1000.0, self.conf['max_wavelength']/1000.0, srf_values)
            s.run()
            self.results_6s[str(band_id)] = {
                'spherical_albedo': s.outputs.spherical_albedo.total,
                'ozone_transmittance_total': s.outputs.transmittance_ozone.total,
                'total_gaseous_transmittance': s.outputs.transmittance_global_gas.total,
                'total_scattering_transmittance_upward': s.outputs.transmittance_total_scattering.upward,
                'atmospheric_intrinsic_radiance': s.outputs.atmospheric_intrinsic_radiance,
                'solar_irradiance': s.outputs.direct_solar_irradiance + s.outputs.diffuse_solar_irradiance
            }

    def apply_atmospheric_correction(self, toa_radiance, band_id):
        params = self.results_6s[str(band_id)]
        if params['total_gaseous_transmittance'] <= self.conf['tgas_threshold']:
            return np.full(toa_radiance.shape, np.nan)
        l_toa_corr = (toa_radiance * 1000.0) * (self.earth_sun_d**2)
        term = (l_toa_corr / params['ozone_transmittance_total']) - params['atmospheric_intrinsic_radiance']
        denom = (params['solar_irradiance'] * params['total_scattering_transmittance_upward'] / np.pi) + (params['spherical_albedo'] * term)
        p_boa = term / denom
        return (p_boa / np.pi).astype(np.float32) if self.conf['output_rrs'] else p_boa.astype(np.float32)
