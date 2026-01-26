from setuptools import setup, find_packages
import os

# Get the long description from the README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="sixabos",
    version="1.1.0",
    author="Gabriel Caballero",
    author_email="gabriel.caballero@uv.es",  
    description="6S-based Atmospheric Background Offset Subtraction for EnMAP hyperspectral imagery atmospheric correction",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/PhD-Gabriel-Caballero/6ABOS",
    project_urls={
        "Bug Tracker": "https://github.com/PhD-Gabriel-Caballero/6ABOS/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Atmospheric Science",
    ],
    python_requires=">=3.10",
    
    # Core dependencies
    install_requires=[
        "numpy",
        "scipy",
        "pandas",
        "matplotlib",
        "xmltodict",
        "tqdm",
        "gdal", 
    ],
    
    # Automatically find the S6ABOS_package
    packages=find_packages(),
    
    # If you have data files (like 6S lookup tables or XML templates)
    include_package_data=True,
    
    # This allows users to run your code from the terminal
    entry_points={
        "console_scripts": [
            "sixabos-run=S6ABOS_package.main:main", 
        ],
    },
)
