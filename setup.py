from setuptools import setup, find_packages
import os

# Leer la descripción larga desde el README
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="sixabos",
    version="1.1.1",
    author="Gabriel Caballero",
    author_email="gabriel.caballero@uv.es",
    description="6S-based Atmospheric Background Offset Subtraction",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/PhD-Gabriel-Caballero/6ABOS",
    packages=find_packages(),
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
        #"gdal", 
    ],
    include_package_data=True,
)
