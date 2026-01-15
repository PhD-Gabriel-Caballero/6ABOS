#!/usr/bin/env python
# coding: utf-8

# ## 6ABOS EnMAP Atmospheric Correction Code

# In[1]:


# Library:
from Py6S import *
import pandas as pd
import geopandas as gpd
import pandas_geojson as pdg
from IPython.display import display
import numpy as np
import csv
from osgeo import gdal
import numpy as np
import pandas as pd
import json
import os
import glob
from PIL import Image
import csv
import matplotlib.pyplot as plt
import rasterio
import math
import ee
import datetime
import re
import os
import glob

import xml.etree.ElementTree as ET
import xmltodict

from scipy.interpolate import interp1d
from scipy.signal import savgol_filter


# In[27]:


# Configuration dictionary
conf = {"verbose":True, 
        "data exporting":False, 
        "data plotting":True, 
        "data storing": True, 
        "testing":True,
        "VNIR":False, 
        "GEE": False, 
        "max_wavelength": 2480,
        "min_wavelength": 379,
        "wavelength_step": 2.5,
        # Total transmissivity threshold of gases
        "tgas_threshold":0.75,
        # Replace with the actual path to the EnMAP L1 folder
        "input_dir": r'D:\EnMAP_L1\Lake_Constance\ENMAP01-____L1C-DT0000122760_20250403T105753Z_031_V010502_20250414T203123Z',
        # Replace with the actual path to the EnMAP L2 folder (6ABOS)
        "output_dir":'d:/6ABOS/',
        # Output: 1) Surface reflectance (output_rrs = False), 2) Remote sensing reflectance (output_rrs = True)
        "output_rrs":False}


# In[3]:


# Google Earth Engine (GEE) Authentication & Initialization

# NOTE: Users must have a valid GEE account. 
# Replace the project ID below with your own Google Cloud Project ID.

if conf['GEE']:
    try:
        # Initial attempt using a specific User Project. 
        ee.Authenticate()
        ee.Initialize(project='abos-482615') #complete whit your personal/institutional project ID.
    except Exception as e:
        # Fallback mechanism: 
        # If the specific project initialization fails, it tries a default setup.
        # Check your GEE console if you encounter persistent permission errors.
        print(f"Warning: Project-specific GEE initialization failed: {e}")
        print("Attempting default GEE initialization...")
        ee.Authenticate()
        ee.Initialize()


# ### Functions definition

# In[4]:


"""
atmospheric.py, Sam Murphy (2016-10-26)

Atmospheric water vapour, ozone and AOT from GEE

Usage
H2O = Atmospheric.water(geom,date)
O3 = Atmospheric.ozone(geom,date)
AOT = Atmospheric.aerosol(geom,date)

"""
import ee

class Atmospheric():

  def round_date(date,xhour):
    """
    rounds a date of to the closest 'x' hours
    """
    y = date.get('year')
    m = date.get('month')
    d = date.get('day')
    H = date.get('hour')
    HH = H.divide(xhour).round().multiply(xhour)
    return date.fromYMD(y,m,d).advance(HH,'hour')

  def round_month(date):
    """
    round date to closest month
    """
    # start of THIS month
    m1 = date.fromYMD(date.get('year'),date.get('month'),ee.Number(1))

    # start of NEXT month
    m2 = m1.advance(1,'month')

    # difference from date
    d1 = ee.Number(date.difference(m1,'day')).abs()
    d2 = ee.Number(date.difference(m2,'day')).abs()

    # return closest start of month
    return ee.Date(ee.Algorithms.If(d2.gt(d1),m1,m2))



  def water(geom,date):
    """
    Water vapour column above target at time of image aquisition.

    (Kalnay et al., 1996, The NCEP/NCAR 40-Year Reanalysis Project. Bull. 
    Amer. Meteor. Soc., 77, 437-471)
    """

    # Point geometry required
    centroid = geom.centroid()

    # H2O datetime is in 6 hour intervals
    H2O_date = Atmospheric.round_date(date,6)

    # filtered water collection
    water_ic = ee.ImageCollection('NCEP_RE/surface_wv').filterDate(H2O_date, H2O_date.advance(1,'month'))

    # water image
    water_img = ee.Image(water_ic.first())

    # water_vapour at target
    water = water_img.reduceRegion(reducer=ee.Reducer.mean(), geometry=centroid).get('pr_wtr')

    # convert to Py6S units (Google = kg/m^2, Py6S = g/cm^2)
    water_Py6S_units = ee.Number(water).divide(10)                                   

    return water_Py6S_units



  def ozone(geom,date):
    """
    returns ozone measurement from merged TOMS/OMI dataset

    OR

    uses our fill value (which is mean value for that latlon and day-of-year)

    """

    # Point geometry required
    centroid = geom.centroid()

    def ozone_measurement(centroid,O3_date):

      # filtered ozone collection
      ozone_ic = ee.ImageCollection('TOMS/MERGED').filterDate(O3_date, O3_date.advance(1,'month'))

      # ozone image
      ozone_img = ee.Image(ozone_ic.first())

      # ozone value IF TOMS/OMI image exists ELSE use fill value
      ozone = ee.Algorithms.If(ozone_img,\
      ozone_img.reduceRegion(reducer=ee.Reducer.mean(), geometry=centroid).get('ozone'),\
      ozone_fill(centroid,O3_date))

      return ozone

    def ozone_fill(centroid,O3_date):
      """
      Gets our ozone fill value (i.e. mean value for that doy and latlon)

      you can see it
      1) compared to LEDAPS: https://code.earthengine.google.com/8e62a5a66e4920e701813e43c0ecb83e
      2) as a video: https://www.youtube.com/watch?v=rgqwvMRVguI&feature=youtu.be

      """

      # ozone fills (i.e. one band per doy)
      ozone_fills = ee.ImageCollection('users/samsammurphy/public/ozone_fill').toList(366)

      # day of year index
      jan01 = ee.Date.fromYMD(O3_date.get('year'),1,1)
      doy_index = date.difference(jan01,'day').toInt()# (NB. index is one less than doy, so no need to +1)

      # day of year image
      fill_image = ee.Image(ozone_fills.get(doy_index))

      # return scalar fill value
      return fill_image.reduceRegion(reducer=ee.Reducer.mean(), geometry=centroid).get('ozone')

    # O3 datetime in 24 hour intervals
    O3_date = Atmospheric.round_date(date,24)

    # TOMS temporal gap
    TOMS_gap = ee.DateRange('1994-11-01','1996-08-01')  

    # avoid TOMS gap entirely
    ozone = ee.Algorithms.If(TOMS_gap.contains(O3_date),ozone_fill(centroid,O3_date),ozone_measurement(centroid,O3_date))

    # fix other data gaps (e.g. spatial, missing images, etc..)
    ozone = ee.Algorithms.If(ozone,ozone,ozone_fill(centroid,O3_date))

    #convert to Py6S units 
    ozone_Py6S_units = ee.Number(ozone).divide(1000)# (i.e. Dobson units are milli-atm-cm )                             

    return ozone_Py6S_units


  def aerosol(geom,date):
    """
    Aerosol Optical Thickness.

    try:
      MODIS Aerosol Product (monthly)
    except:
      fill value
    """

    def aerosol_fill(date):
      """
      MODIS AOT fill value for this month (i.e. no data gaps)
      """
      return ee.Image('users/samsammurphy/public/AOT_stack')\
               .select([ee.String('AOT_').cat(date.format('M'))])\
               .rename(['AOT_550'])


    def aerosol_this_month(date):
      """
      MODIS AOT original data product for this month (i.e. some data gaps)
      """
      # image for this month
      img =  ee.Image(\
                      ee.ImageCollection('MODIS/006/MOD08_M3')\
                        .filterDate(Atmospheric.round_month(date))\
                        .first()\
                     )

      # fill missing month (?)
      img = ee.Algorithms.If(img,\
                               # all good
                               img\
                               .select(['Aerosol_Optical_Depth_Land_Mean_Mean_550'])\
                               .divide(1000)\
                               .rename(['AOT_550']),\
                              # missing month
                                aerosol_fill(date))

      return img    


    def get_AOT(AOT_band,geom):
      """
      AOT scalar value for target
      """  
      return ee.Image(AOT_band).reduceRegion(reducer=ee.Reducer.mean(),\
                                 geometry=geom.centroid())\
                                .get('AOT_550')


    after_modis_start = date.difference(ee.Date('2000-03-01'),'month').gt(0)

    AOT_band = ee.Algorithms.If(after_modis_start, aerosol_this_month(date), aerosol_fill(date))

    AOT = get_AOT(AOT_band,geom)

    AOT = ee.Algorithms.If(AOT,AOT,get_AOT(aerosol_fill(date),geom))
    # i.e. check reduce region worked (else force fill value)

    return AOT


# In[5]:


#
def parse_xml(xml_file):
  """Parses an XML file and prints its contents.

  Args:
    xml_file: Path to the XML file.
  """

  tree = ET.parse(xml_file)
  root = tree.getroot()
  startTime = root.find('.//startTime').text
  acquisition_date = startTime[0:10]

  for point in root.findall(".//spatialCoverage//boundingPolygon//point"):
            frame_element = point.find("frame")
            if frame_element is not None and frame_element.text == "center":
                latitude_element = float(point.find("latitude").text)
                longitude_element = float(point.find("longitude").text)

  scene_center_long = longitude_element
  scene_center_lat = latitude_element

  season = root.find('.//season').text
  ozoneValue = int(root.find('.//ozoneValue').text)
  sceneAOT = int(root.find('.//sceneAOT').text)
  sceneWV = int(root.find('.//sceneWV').text)
  sunElevationAngle = float(root.find('.//sunElevationAngle//center').text)
  sunAzimuthAngle = float(root.find('.//sunAzimuthAngle//center').text)
  viewingAzimuthAngle = float(root.find('.//viewingAzimuthAngle//center').text)
  viewingZenithAngle = float(root.find('.//viewingZenithAngle//center').text)
  meanGroundElevation  = float(root.find('.//meanGroundElevation').text)
  meanGroundElevation  = float(root.find('.//meanGroundElevation').text)

  # Dictionary with EnMAP scene parameters
  scene_parameters = {
        "startTime":  startTime,
        "acquisition_date" : acquisition_date,
        "scene_center_long" : scene_center_long ,
        "scene_center_lat" : scene_center_lat,
        "season" : season, 
        "meanGroundElevation" : meanGroundElevation,
        "ozoneValue": ozoneValue/1000,
        "sceneAOT": sceneAOT/1000,
        "sceneWV": sceneWV/1000, 
        "sunElevationAngle": sunElevationAngle, 
        "sunAzimuthAngle": sunAzimuthAngle,
        "viewingAzimuthAngle": viewingAzimuthAngle,
        "viewingZenithAngle": viewingZenithAngle
        }

  return scene_parameters


# In[6]:


#
def get_enmap_band_parameters(xml_file):
    """
    Parses EnMAP L1C metadata to extract spectral characterization parameters.
    Returns a pandas DataFrame with band ID, center wavelength, FWHM, gain, and offset.
    """
    # Load and parse the XML file
    tree = ET.parse(xml_file)
    root = tree.getroot()

    bands_list = []

    # Locate the bandCharacterisation section which contains all bandID elements
    # Using findall with the specific path to ensure correct data retrieval
    for band in root.findall('.//bandCharacterisation/bandID'):
        # Extract the band number from the 'number' attribute
        band_id = int(band.get('number'))

        # Extract parameters using find().text and convert to float
        # These parameters are essential for Radiance conversion and 6S input
        band_data = {
            'band_id': band_id,
            'wavelength_center': float(band.find('wavelengthCenterOfBand').text),
            'fwhm': float(band.find('FWHMOfBand').text),
            'gain': float(band.find('GainOfBand').text),
            'offset': float(band.find('OffsetOfBand').text)
        }
        bands_list.append(band_data)

    # Convert the list of dictionaries into a structured DataFrame
    df = pd.DataFrame(bands_list)
    return df


# In[7]:


def calculate_gaussian_srf(df_enmap, spectral_range):
    """
    Calculates the Gaussian Spectral Response Function for each band.
    Amplitude is normalized to 1 at the peak.
    """
    srf_results = []

    for index, row in df_enmap.iterrows():
        center = row['wavelength_center']
        fwhm = row['fwhm']

        # Calculate Sigma from FWHM
        sigma = fwhm / (2 * np.sqrt(2 * np.log(2)))

        # Apply Gaussian Formula: f(x) = a * exp(-(x-b)^2 / (2*sigma^2))
        # Amplitude (a) is set to 1
        gaussian_curve = np.exp(-((spectral_range - center)**2) / (2 * sigma**2))

        srf_results.append(gaussian_curve)

    # Create a DataFrame where columns are wavelengths and rows are bands
    df_srf = pd.DataFrame(srf_results, columns=spectral_range)
    df_srf.index = df_enmap['band_id']

    return df_srf


# In[8]:


def atmospheric_correction(toa_radiance,ac_params,earth_sun_d,tgas_threshold):
    """
    Performs atmospheric correction to retrieve Bottom of Atmosphere (BOA) 
    reflectance and Remote Sensing Reflectance (Rrs).
    """
    # RTM Parameters

    # Solar irradiance: Direct and diffuse
    solar_diffuse_irrad = ac_params['diffuse_solar_irradiance']
    solar_direct_irrad = ac_params['direct_solar_irradiance']

    #Lpath is the radiance scattered by the atmosphere into the sensor’s field of view 
    L_path = ac_params['atmospheric_intrinsic_radiance']    

    # Total_gaseous_transmittance -> T_gT
    T_gT = float(ac_params['total_gaseous_transmittance'])

    # Total transmission of the Ozone -> Tg_O3:
    Tg_O3 = float(ac_params['ozone_transmittance_total'])

    # Total transmittance upward (Rayleigh + Aerosol) -> T_upward:
    T_upward = float(ac_params['total_scattering_transmittance_upward'])

    # Atmosphere spherical albedo -> s_atm:
    s_atm = float(ac_params['spherical_albedo'])

    #The solar constant integrated upon the filter response in [w/m2/sr/nm]
    Es = (solar_diffuse_irrad + solar_direct_irrad)

    # Top of Atmosphere radiance 
    l_toa_corrected = (toa_radiance * 1000.0) * (earth_sun_d**2)

    # Bottom of Atmosphere reflectance (Physical approach)
    if T_gT  > tgas_threshold:

        if conf['verbose']:
            print('Band with tgas > '+str(tgas_threshold)+' included from surface level reflectance ρs calculation')

        p_boa = (l_toa_corrected/Tg_O3 - L_path)/(Es*T_upward/np.pi + s_atm*(l_toa_corrected/Tg_O3 - L_path))

    else:
        if conf['verbose']:
            print('Band with tgas < '+str(tgas_threshold)+' excluded from surface level reflectance ρs calculation')
        p_boa = np.full(toa_radiance.shape, np.nan)

    # Rrs Calcutaions
    rrs = np.divide(p_boa, np.pi) # Calculate Rrs

    # Clean up edge cases (masking zeros or artifacts)
    #rrs[np.isnan(rrs)] = 0  

    # Convert variables to float 32 data format
    rrs = rrs.astype(np.float32)
    p_boa = p_boa.astype(np.float32)
    l_toa_corrected = l_toa_corrected.astype(np.float32)

    return rrs,p_boa, l_toa_corrected


# In[9]:


def save_enmap_cube_to_tiff(data_cube, output_path, reference_raster_path, metadata_df=None):
    """
    Saves a 3D NumPy EnMAP cube to a GeoTIFF, copying spatial metadata 
    from a reference file and injecting spectral metadata.

    Args:
        data_cube: NumPy array of shape [Bands, Rows, Cols]
        output_path: Path where the .tif will be saved.
        reference_raster_path: Path to one of the original EnMAP .tif files 
                               to copy the Geotransform and Projection.
        wavelengths: Optional list/array of wavelength centers for band metadata.
    """
    try:
        # Get dimensions from the data cube
        bands_count, rows, cols = data_cube.shape

        # Open reference raster to get spatial information
        ref_ds = gdal.Open(reference_raster_path)

        if ref_ds is None:
            raise Exception(f"Could not open reference raster: {reference_raster_path}")

        geotransform = ref_ds.GetGeoTransform()
        projection = ref_ds.GetProjection()
        ref_ds = None 

        # Create the output GeoTIFF
        # We use Float32 because Rrs data contains decimals and NaNs
        driver = gdal.GetDriverByName("GTiff")
        out_ds = driver.Create(output_path, cols, rows, bands_count, gdal.GDT_Float32)

        out_ds.SetGeoTransform(geotransform)
        out_ds.SetProjection(projection)

        # Get metada from metada dataframe
        wavelengths = metadata_df['wavelength_center'].values
        fwhms =  metadata_df['fwhm'].values
        gains =  metadata_df['gain'].values
        offsets =  metadata_df['offset'].values
        band_ids =  metadata_df['band_id'].values

        # Write data cube bands and metadata
        for i in range(bands_count):
            out_band = out_ds.GetRasterBand(i + 1)

            # Write the 2D array for the current band
            out_band.WriteArray(data_cube[i, :, :])

            # Set NoData Value as NaN
            out_band.SetNoDataValue(np.nan)

            # Inject Wavelength Metadata if provided
            if wavelengths is not None:
                wv = str(wavelengths[i])
                fw = str(fwhms[i])
                sc = str(gains[i])
                of = str(offsets[i])

                out_band.SetMetadataItem("WAVELENGTH", wv)
                out_band.SetMetadataItem("WAVELENGTH UNIT", "nm")
                out_band.SetMetadataItem("Offset", of)
                out_band.SetMetadataItem("Scale", sc)
                out_band.SetDescription(f"Band_{i+1}_{wv}nm")
            else:
                out_band.SetDescription(f"Band_{i+1}")

        # Finalize file
        out_ds.FlushCache()
        out_ds = None

        print(f"Successfully saved EnMAP cube to: {output_path}")

    except Exception as e:
        print(f"Failed to save raster: {e}")


# ### Metadata and atmospheric constituent preprocessing

# In[10]:


# Path to TOA data definition
directory = conf['input_dir']

# Construct the search pattern

# L1 TOA data
path_to_toa_radiance = str(glob.glob(os.path.join(directory, f"*{'SPECTRAL_IMAGE.TIF'}"))[0])

# L1 metadata
path_to_xml_metadata =   str(glob.glob(os.path.join(directory,f"*{'METADATA.XML'}"))[0])

if conf['verbose']:
    print('Path_to_toa_radiance: ',path_to_toa_radiance)
    print('Metadata file: ',path_to_xml_metadata)


# In[11]:


# EnMAP metadata file reading
scene_pam_dict = parse_xml(path_to_xml_metadata)

# 6S atmospheric constituents configuration
enmap_aod550 = scene_pam_dict['sceneAOT']
enmap_h2o = scene_pam_dict['sceneWV']
enmap_o3 = scene_pam_dict['ozoneValue']
alt  = scene_pam_dict['meanGroundElevation']

if conf['verbose']:
    print("The following metadata file is being read :",path_to_xml_metadata)
    print()
    print('\033[1m' + 'Metada of EnMAP-acquired scene'+ '\033[0m')
    print(scene_pam_dict)

if conf['GEE']:
    acquisition_date = ee.Date(scene_pam_dict['acquisition_date'])
    scene_center = ee.Geometry.Point(scene_pam_dict['scene_center_long'],scene_pam_dict['scene_center_lat'])

    enmap_h2o = Atmospheric.water(scene_center,acquisition_date).getInfo()
    enmap_o3 = Atmospheric.ozone(scene_center,acquisition_date).getInfo()
    enmap_aod550 = Atmospheric.aerosol(scene_center,acquisition_date).getInfo()

    SRTM = ee.Image('CGIAR/SRTM90_V4')# Shuttle Radar Topography mission covers *most* of the Earth
    alt = SRTM.reduceRegion(reducer = ee.Reducer.mean(),geometry = scene_center.centroid()).get('elevation').getInfo()

    print('\033[1m' + 'Atmospheric constituents retrieved from GEE catalogue' + '\033[0m')
    print('Target Altitude: '+ str(alt)+' km')
    print('H20: ', enmap_h2o)
    print('O3: ', enmap_o3) # cm-atm
    print('AOT 550 nm: ', enmap_aod550)

# Ground elevation compensation (Py6S requires altitude in kilometers)
if alt == None:
    target_alt = 0.0
else:
    if alt >= 0:
        target_alt = alt/1000.0
    else:
        target_alt = 0.0


# In[12]:


#Ozone Column: {200-500, AUT}: ozone value in Dobson units, AUT: Automatic

# Get the day and month as integers
date_obj = datetime.datetime.strptime(scene_pam_dict['acquisition_date'], '%Y-%m-%d')

acquisition_day = date_obj.day
acquisition_month = date_obj.month 

# Adquisition date
doy = date_obj.timetuple().tm_yday

# Earth-Sun distance (from day of year)
# http://physics.stackexchange.com/questions/177949/earth-sun-distance-on-a-given-day-of-the-year
earth_sun_d = 1 - 0.01672 * math.cos(0.9856 * (doy-4)) 

solar_Az =  scene_pam_dict['sunAzimuthAngle'] #Sun_Azimuth_angle 
solar_Zn =  90 - scene_pam_dict['sunElevationAngle'] #Sun_Zenith_angle = 90 - Sun_elevation_angle
view_Zn =   scene_pam_dict['viewingZenithAngle'] #View Zenith Angle 
view_Az =   scene_pam_dict['viewingAzimuthAngle'] #View Azimuth Angle

# Cosine of the solar azimuthal angle
cos_azs = math.cos(math.radians(solar_Zn))

if conf['verbose']:
    print('\033[1m' + '6S input parameters'+ '\033[0m')
    print('image acquisition date: ', date_obj)
    print('Sun-Earth distance in astronomic units: ',earth_sun_d**2)
    print('Day of the year', doy)
    print('EnMAP acquisition day ',acquisition_day)
    print('EnMAP acquisition month ',acquisition_month)
    print('Target Altitude: '+ str(target_alt)+' km')
    print('H20: ',enmap_h2o)
    print('O3: ',enmap_o3) # cm-atm
    print('AOT 550 nm: ',enmap_aod550)
    print('Sun_azimuth_angle: '+ str(solar_Az)+'°')
    print('Sun_zenith_angle: '+ str(solar_Zn)+'°')
    print('View Zenith Angle: ' + str(view_Zn)+'°')
    print('View Azimuth Angle: ' + str(view_Az)+'°')
    print('Cosine of the solar zenithal angle: ', cos_azs)
    print('Total transmissivity threshold of gases: ',conf['tgas_threshold'])


# ### 6S Radiative Transfer Model Execution

# In[13]:


# ENMAP
# Instantiate
s = SixS()

###############################################################################################################
# Atmospheric constituents
s.atmos_profile = AtmosProfile.PredefinedType(AtmosProfile.MidlatitudeSummer)
s.aero_profile = AeroProfile.Continental
s.atmos_profile = AtmosProfile.UserWaterAndOzone(enmap_h2o,enmap_o3)
s.aot550 = enmap_aod550  

# Ground Reflectance-------------------------------------------------------------------------------------------:
s.ground_reflectance = GroundReflectance.HomogeneousLambertian(GroundReflectance.LakeWater)

# Earth-Sun-satellite geometry

# Geometries of view and illumination--------------------------------------------------------------------------:
s.geometry = Geometry.User()
s.geometry.day = acquisition_day
s.geometry.month = acquisition_month
s.geometry.solar_z = float(solar_Zn) # Solar zenith angle
s.geometry.solar_a = float(solar_Az) # Solar azimuth angle
s.geometry.view_z = float(view_Zn)   # View zenith angle
s.geometry.view_a = float(view_Az)   # View azimuth angle

# Altitudes---------------------------------------------------------------------------------------------------:
s.altitudes = Altitudes()
s.altitudes.set_sensor_satellite_level()  # Set the sensor altitude to be satellite level.
s.altitudes.set_target_custom_altitude(target_alt)  # The altitude of the target (in km).
###############################################################################################################


# In[14]:


# Getting EnMAP's spectral configuration
enmap_spectral_conf_df = get_enmap_band_parameters(path_to_xml_metadata)

if conf['verbose']:
    display(enmap_spectral_conf_df)

# Definning the spectral range (379 to 1049 nm with 1nm step)

wv_min = conf['min_wavelength'] 
wv_max = conf['max_wavelength']  
wv_step = conf['wavelength_step']

spectral_range = np.arange(wv_min, wv_max, wv_step)

# Assuming df_enmap is the DataFrame from the previous step
df_srf_final = calculate_gaussian_srf(enmap_spectral_conf_df, spectral_range)

if conf['verbose']:
    print("SRF Matrix Shape (Bands x Wavelengths):", df_srf_final.shape)
    display(df_srf_final)

if conf['data plotting']:
    # Transpose the DataFrame so wavelengths are on the X-axis
    df_srf_final.T.plot(figsize=(20, 6), legend=None)

    plt.title('EnMAP sensor SRF [nm]', fontsize=18)
    plt.ylabel('Spectral response functions', fontsize=14)
    plt.xlabel('Wavelength [nm]', fontsize=14)
    plt.grid(True, alpha=0.3) # Added for better visualization of band overlaps


# In[15]:


# Running 6S for EnMAP Hyperspectral Bands 

# Initialize results container
dictionary_enmap_6s = {}

for band_id in df_srf_final.index:

    # Get the SRF values for the current band (all wavelengths in the range)
    srf_values = df_srf_final.loc[band_id].values.tolist()

    # Define the wavelength range for 6S (Converting nm to micrometers)
    start_wv = wv_min / 1000.0
    end_wv = wv_max / 1000.0

    # Configure the 6S object with the custom Spectral Response Function
    s.wavelength = Wavelength(start_wv, end_wv, srf_values)

    # Run the atmospheric simulation
    s.run()

    # Extract and store the atmospheric parameters
    # We include all terms required by the 6ABOS physical inversion formula
    outputs = {
        # 1. Geometry & Albedo
        'spherical_albedo': s.outputs.spherical_albedo.total,

        # 2. Transmittances (Individual gases)
        'ozone_transmittance_total': s.outputs.transmittance_ozone.total,
        'water_transmittance_total': s.outputs.transmittance_water.total,

        # 3. Total Gaseous Transmittance (T_gT) - Product of all gas absorption
        'total_gaseous_transmittance': s.outputs.transmittance_global_gas.total,

        # 4. Scattering Transmittances
        'total_scattering_transmittance_upward': s.outputs.transmittance_total_scattering.upward,
        'total_scattering_transmittance_downward': s.outputs.transmittance_total_scattering.downward,

        # 5. Radiance & Irradiance (Crucial for the TOA to BOA equation)
        # We extract 'atmospheric_intrinsic_radiance' (L_path) 
        'atmospheric_intrinsic_radiance': s.outputs.atmospheric_intrinsic_radiance,
        'direct_solar_irradiance': s.outputs.direct_solar_irradiance,
        'diffuse_solar_irradiance': s.outputs.diffuse_solar_irradiance
    }

    # Save in the dictionary using the Band ID as key
    dictionary_enmap_6s[str(band_id)] = outputs

    if conf['verbose'] and int(band_id) % 20 == 0:
        print(f"6S simulation completed for Band {band_id}")

print(f"Total bands processed: {len(dictionary_enmap_6s)}")


# In[16]:


if conf['verbose']:
    display(dictionary_enmap_6s)


# ### ATMOSPHERIC CORRECTION: TOA RADIANCE TO SURFACE REFLECTANCE

# In[28]:


# Initializing containers for atmospheric components and output products
# Open the multi-band TIFF
dataset = gdal.Open(path_to_toa_radiance, gdal.GA_ReadOnly)

if not dataset:
    print("Failed to open the file.")
else:
    # Get the total number of bands
    total_bands = dataset.RasterCount
    rows = dataset.RasterYSize
    cols = dataset.RasterXSize

    # Pre-allocate the 3D array to save memory 
    sixabos_3d_cube = np.empty((total_bands, rows, cols), dtype=np.float32)

    if conf['verbose']:
        print(f"Total bands found: {total_bands}")

    # Iterate through each band individually
    for i in range(1, total_bands+1):
        if conf['verbose']:
            print('Processing band #',i)
        band = dataset.GetRasterBand(i)

        # Read band data as a NumPy array (TOA Radiance)
        band_data = band.ReadAsArray().astype(np.float32)

        # Read gain and offset from the EnMAP spectral configuration dataframe
        band_scale = enmap_spectral_conf_df.iloc[i-1]['gain']
        band_offset = enmap_spectral_conf_df.iloc[i-1]['offset']
        band_id = enmap_spectral_conf_df.iloc[i-1]['band_id']
        band_wv = enmap_spectral_conf_df.iloc[i-1]['wavelength_center']

        if conf['verbose']:
            print('Band ID ',band_id)
            print('Band wavelength center', band_wv)
            print('Band Gain ',band_scale)
            print('Band Offset ',band_offset)

        # Radiance = (DN * Gain) + Offset
        array_enmap_aux = band_data*band_scale + band_offset

        # Access the corresponding 6S parameters from 6S dictionary
        params_6s = dictionary_enmap_6s[str(i)]
        if conf['verbose']:
            print(f"6S params for band {i}: {params_6s}")

        if params_6s:
            #############################################################
            # 6ABOS Atmospheric Correction
            #
            if conf['verbose']:
                print(f"\033[1mPerforming 6ABOS atmospheric correction on EnMAP band: {band_wv} nm\033[0m")

            # Atmospherically corrected Remote Sensing Reflectance (Rrs) 
            tgas_threshold = conf['tgas_threshold']
            rrs,p_boa,l_toa_corrected = atmospheric_correction(array_enmap_aux,params_6s,earth_sun_d,tgas_threshold)
            #
            #############################################################
            pass

        if conf['data plotting']: 
            # Check if the array is full of NaNs (excluded band)
            if np.isnan(rrs).all():
                print(f"Skipping plot for band {band_wv} nm: Data is all NaN (Gaseous absorption too high).")
            else:
            # Proceed with plotting only if we have valid data
                fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(10, 10), gridspec_kw={'height_ratios': [1, 0.8]})

                # Plot 1: EnMAP Top of Atmosphere (TOA) Reflectance
                vmin1, vmax1 = np.mean(l_toa_corrected)-3*np.std(l_toa_corrected), np.mean(l_toa_corrected)+3*np.std(l_toa_corrected)
                im1 = ax1.imshow(l_toa_corrected, cmap='gray', vmin=vmin1, vmax=vmax1)
                ax1.set_title(f'EnMAP L_TOA: {band_wv} nm', fontsize=12, fontweight='bold')
                ax1.set_xlabel('x_pixels#', fontsize=12)
                ax1.set_ylabel('y_pixels#', fontsize=12)
                fig.colorbar(im1, ax=ax1, shrink=0.5, pad=0.05, label='$W/m^2/sr/\mu m$')

                # Plot 2: Atmospherically Corrected Remote Sensing Reflectance (Rrs)
                vmin2, vmax2 = np.mean(rrs)-3*np.std(rrs), np.mean(rrs)+3*np.std(rrs)
                im2 = ax2.imshow(rrs, cmap='viridis', vmin=vmin2, vmax=vmax2)
                ax2.set_title(f'Corrected Rrs: {band_wv} nm', fontsize=12, fontweight='bold')
                ax2.set_xlabel('x_pixels#', fontsize=12)
                ax2.set_ylabel('y_pixels#', fontsize=12)
                fig.colorbar(im2, ax=ax2, shrink=0.5, pad=0.05, label='$sr^{-1}$')

                # Histogram 1: TOA Reflectance Distribution
                ax3.hist(l_toa_corrected.ravel(), bins=100, color='gray', alpha=0.6, density=True)
                ax3.set_xlabel('TOA Radiance ($W/m^2/sr/\mu m$)')
                ax3.set_ylabel('Probability Density')
                ax3.grid(True, alpha=0.3, linestyle='--')
                ax3.axvline(np.mean(l_toa_corrected), color='red', linestyle='dashed', linewidth=1, label='Mean')
                ax3.legend()

                # Histogram 2: Rrs Distribution
                ax4.hist(rrs.ravel(), bins=100, color='teal', alpha=0.6, density=True)
                ax4.set_xlabel('Remote Sensing Reflectance ($sr^{-1}$)')
                ax4.set_ylabel('Probability Density')
                ax4.grid(True, alpha=0.3, linestyle='--')
                ax4.axvline(np.mean(rrs), color='red', linestyle='dashed', linewidth=1, label='Mean')
                ax4.legend()

                # Final layout adjustments
                plt.tight_layout()
                plt.show()

        if conf['output_rrs']:
            # Storing band-wise Rrs into the pre-allocated 3D cube
            sixabos_3d_cube[i-1, :, :] = rrs.astype(np.float32)
        else:
            # Storing band-wise surface reflectance into the pre-allocated 3D cube
            sixabos_3d_cube[i-1, :, :] = p_boa.astype(np.float32)

    # Clean up
    dataset = None
    band = None

print('End of data processing')

print(f"Final Data Cube Shape: {sixabos_3d_cube.shape}")


# In[29]:


if conf['data plotting']:
    # RE-OPEN the LTOA dataset
    temp_ds = gdal.Open(path_to_toa_radiance, gdal.GA_ReadOnly)

    if not temp_ds:
        print("Error: Could not re-open dataset for plotting.")
    else:
        # Define the spectral windows for Water Vapor (H2O) absorption (nm)
        h2o_windows = [
            (710, 735), (810, 840), (890, 990), (1080, 1180), 
            (1300, 1500), (1750, 2000), (2300, 2500)
        ]

        # Extract spectrum and wavelengths
        x_coord, y_coord = 400, 800
        pixel_spectrum = sixabos_3d_cube[:, y_coord, x_coord]

        # Extracting TOA Radiance directly from the temporary dataset
        pixel_ltoa = []
        for b in range(1, total_bands + 1):
            band_obj = temp_ds.GetRasterBand(b)
            # Read only a 1x1 window at the specific coordinate
            # band_obj.ReadAsArray(x_offset, y_offset, x_size, y_size)
            val = band_obj.ReadAsArray(x_coord, y_coord, 1, 1)[0, 0]

            gain = enmap_spectral_conf_df.iloc[b-1]['gain']
            offset = enmap_spectral_conf_df.iloc[b-1]['offset']
            pixel_ltoa.append(val * gain + offset)

        pixel_ltoa = np.array(pixel_ltoa)*1000
        wavelengths = enmap_spectral_conf_df['wavelength_center'].values

    # Plotting EnMAP Rrs
    plt.figure(figsize=(10, 6))

    # Plot the valid spectrum (filtering out NaNs for a continuous line where possible)
    plt.plot(wavelengths, pixel_spectrum, color='black', lw=2, label='EnMAP $R_{rs}$')

    # Highlight Water Absorption Windows
    for i, (start, end) in enumerate(h2o_windows):
        # Only label the first one to keep the legend clean
        lbl = "Atmospheric $H_{2}O$ Absorption" if i == 0 else ""
        plt.axvspan(start, end, color='skyblue', alpha=0.3, label=lbl)

    # Scientific Styling
    plt.title(f'Spectral Integrity Check: Pixel ({x_coord}, {y_coord})', fontsize=18, fontweight='bold')
    plt.xlabel('Wavelength (nm)', fontsize=14)
    if conf['output_rrs']:
        plt.ylabel('Remote Sensing Reflectance ($sr^{-1}$)', fontsize=14)
    else: 
        plt.ylabel('Surface Reflectance', fontsize=14)
    plt.xlim(wv_min, wv_max)
    #plt.ylim(-0.0005, np.nanmax(pixel_spectrum) * 1.2) # Dynamic height
    plt.grid(True, which='both', alpha=0.2, linestyle='--')

    # Adding a zero line to detect over-correction
    plt.axhline(0, color='red', lw=2, ls='--', alpha=0.5,label='zero line')

    plt.legend(loc='upper right', frameon=True, fontsize=12)
    plt.tight_layout()
    plt.show()

    # Plotting EnMAP Rrs against L_TOA
    fig, ax1 = plt.subplots(figsize=(10, 6))

    # --- Primary Y-Axis: Rrs ---
    # Plot the valid spectrum (filtering out NaNs for a continuous line where possible)
    line1, = ax1.plot(wavelengths, pixel_spectrum, color='black', lw=2, label='EnMAP $R_{rs}$')
    if conf['output_rrs']:
        ax1.set_ylabel('Remote Sensing Reflectance ($sr^{-1}$)', fontsize=14, color='black')
    else: 
        ax1.set_ylabel('Surface Reflectance', fontsize=14, color='black')

    ax1.tick_params(axis='y', labelcolor='black')

    # --- Secondary Y-Axis: L_TOA ---
    ax2 = ax1.twinx()  # Instantiate a second axes that shares the same x-axis
    line2, = ax2.plot(wavelengths, pixel_ltoa, color='green', lw=1.5, ls=':', label='EnMAP $L_{TOA}$')
    ax2.set_ylabel('TOA Radiance ($W \cdot m^{-2} \cdot sr^{-1} \cdot nm^{-1}$)', fontsize=14, color='green', labelpad=15)
    ax2.tick_params(axis='y', labelcolor='green')

    # Highlight Water Absorption Windows
    h2o_patch = None
    for i, (start, end) in enumerate(h2o_windows):
        # Only label the first one to keep the legend clean
        #lbl = "Atmospheric $H_{2}O$ Absorption" if i == 0 else ""
        h2o_patch = ax1.axvspan(start, end, color='skyblue', alpha=0.3, label=lbl)

    # Scientific Styling
    plt.title(f'Spectral Integrity Check: Pixel ({x_coord}, {y_coord})', fontsize=18)
    ax1.set_xlabel('Wavelength (nm)', fontsize=14)
    ax1.set_xlim(wv_min, wv_max)
    ax1.grid(True, which='both', alpha=0.2, linestyle='--')

    # Adding a zero line to detect over-correction
    zero_line = ax1.axhline(0, color='red', lw=2, ls='--', alpha=0.5, label='zero line')

    # --- Unified Legend Logic ---
    # Collect all handles (lines and the shaded area patch)
    handles = [line1, line2, zero_line, h2o_patch]
    labels = ['EnMAP $R_{rs}$', 'EnMAP $L_{TOA}$', 'Zero Line', 'Atmospheric $H_{2}O$ Absorption']
    #labels = [h.get_label() for h in handles]

    # Draw the combined legend on ax1
    ax1.legend(handles, labels, loc='upper right', frameon=True, fontsize=12)

    plt.tight_layout()
    plt.show()

    temp_ds = None


# ### Raster file generation

# In[30]:


# Saving EnMAP datacube as TIF 
output_directory = conf['output_dir']

# Split the path into the directory and the filename
folder_path, full_filename = os.path.split(path_to_toa_radiance)

# Split the filename into the name and the extension (.TIF)
file_name, extension = os.path.splitext(full_filename)

# Define suffix based on the output type
suffix = "-rrs_6abos" if conf['output_rrs'] else "-pboa_6abos"

# Create the new filename and full output path
new_filename = f"{file_name}{suffix}{extension}"
path_to_rrs_output = os.path.join(output_directory, new_filename)

if conf['verbose']:
    print(f"Input:  {path_to_toa_radiance}")
    print(f"Output: {path_to_rrs_output}")

# Data storing logic
if conf['data storing']:
    if conf['output_rrs']:
        # Saving Remote Sensing Reflectance (Rrs)
        save_enmap_cube_to_tiff(sixabos_3d_cube, path_to_rrs_output, path_to_toa_radiance, enmap_spectral_conf_df)
    else:
        # Saving Planar BOA Reflectance (PBOA)
        save_enmap_cube_to_tiff(sixabos_3d_cube, path_to_rrs_output, path_to_toa_radiance, enmap_spectral_conf_df)


# In[ ]:




