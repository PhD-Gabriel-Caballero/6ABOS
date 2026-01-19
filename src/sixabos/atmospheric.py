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

import ee

class Atmospheric:
    @staticmethod
    def initialize_gee(project_id=None):
        """Initializes Earth Engine with optional project ID."""
        try:
            if project_id: ee.Initialize(project=project_id)
            else: ee.Initialize()
            print(f"[GEE] Successfully connected. Project: {project_id}")
            return True
        except Exception as e:
            print(f"[GEE ERROR] {e}")
            return False

    @staticmethod
    def round_date(date, xhour):
        y, m, d = date.get('year'), date.get('month'), date.get('day')
        h = date.get('hour')
        hh = h.divide(xhour).round().multiply(xhour)
        return ee.Date.fromYMD(y, m, d).advance(hh, 'hour')

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
        aot_ic = ee.ImageCollection('MODIS/061/MCD19A2_GRANULES').filterDate(date.advance(-7, 'day'), date.advance(7, 'day')).filterBounds(centroid)
        aot_img = aot_ic.median()
        aot = aot_img.reduceRegion(reducer=ee.Reducer.mean(), geometry=centroid, scale=1000).get('Optical_Depth_047')
        return ee.Number(ee.Algorithms.If(aot, aot, 0.15)).divide(1000)