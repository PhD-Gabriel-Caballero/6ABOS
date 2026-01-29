# -*- coding: utf-8 -*-
# 6ABOS: 6S-based Atmospheric Background Offset Subtraction for Atmospheric Correction
# Copyright (C) 2026 Gabriel Caballero (University of Valencia)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along
# with this program. If not, see <https://www.gnu.org/licenses/>.

from setuptools import setup, find_packages
import os

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="sixabos",
    version="1.1.4",
    author="Gabriel Caballero",
    author_email="gabriel.caballero@uv.es",
    description="6S-based Atmospheric Background Offset Subtraction",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/PhD-Gabriel-Caballero/6ABOS",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: GNU GENERAL PUBLIC LICENSE",
        "Operating System :: OS Independent",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Atmospheric Science",
    ],
    python_requires=">=3.10",
    
    install_requires=[
        "numpy",
        "pandas",
        "scipy",
        "matplotlib",
        "xmltodict",
        "py6s",
        "earthengine-api",
        "gdal", 
    ],
    include_package_data=True,
)
