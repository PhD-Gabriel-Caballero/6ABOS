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

import ee

class Atmospheric:
    """Handles retrieval of H2O, O3, AOT from Google Earth Engine."""
    
    @staticmethod
    def initialize_gee(project_id=None):
        try:
            if project_id:
                ee.Initialize(project=project_id)
            else:
                ee.Initialize()
            return True
        except Exception as e:
            print(f"GEE initialization failed: {e}")
            return False

    @staticmethod
    def round_date(date, xhour):
        y, m, d, h = date.get('year'), date.get('month'), date.get('day'), date.get('hour')
        hh = h.divide(xhour).round().multiply(xhour)
        return date.fromYMD(y, m, d).advance(hh, 'hour')

    @staticmethod
    def water(geom, date):
        centroid = geom.centroid()
        h2o_date = Atmospheric.round_date(date, 6)
        water_ic = ee.ImageCollection('NCEP_RE/surface_wv').filterDate(h2o_date, h2o_date.advance(1, 'month'))
        water_img = ee.Image(water_ic.first())
        water = water_img.reduceRegion(reducer=ee.Reducer.mean(), geometry=centroid).get('pr_wtr')
        return ee.Number(water).divide(10)

    @staticmethod
    def ozone(geom, date):
        centroid = geom.centroid()
        o3_date = Atmospheric.round_date(date, 24)
        ozone_ic = ee.ImageCollection('TOMS/MERGED').filterDate(o3_date, o3_date.advance(1, 'month'))
        ozone_img = ee.Image(ozone_ic.first())
        ozone = ee.Algorithms.If(ozone_img, ozone_img.reduceRegion(reducer=ee.Reducer.mean(), geometry=centroid).get('ozone'), 300)
        return ee.Number(ozone).divide(1000)

    @staticmethod
    def aerosol(geom, date):
        centroid = geom.centroid()
        modis_ic = ee.ImageCollection('MODIS/006/MOD08_M3').filterDate(date.advance(-1, 'month'), date.advance(1, 'month'))
        img = ee.Image(modis_ic.first())
        aot = ee.Algorithms.If(img, img.select(['Aerosol_Optical_Depth_Land_Mean_Mean_550']).divide(1000), 0.2)
        return ee.Image(aot).reduceRegion(reducer=ee.Reducer.mean(), geometry=centroid).get('AOT_550')
