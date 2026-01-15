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

DEFAULT_CONF = {
    "verbose": True,
    "data_plotting": False,
    "data_storing": True,
    "GEE": False,
    "max_wavelength": 2480,
    "min_wavelength": 379,
    "wavelength_step": 2.5,
    "tgas_threshold": 0.75,
    "input_dir": None,
    "output_dir": None,
    "output_rrs": False
}
