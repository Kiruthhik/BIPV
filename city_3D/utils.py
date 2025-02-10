import os
import requests
from django.shortcuts import render
from django.http import JsonResponse
from .models import Building, BuildingFace, VirtualGridCentroid, ShadowAnalysis
from datetime import datetime
import pandas as pd
from math import radians, sin, cos, acos, degrees
import pvlib
from pvlib.solarposition import get_solarposition,sun_rise_set_transit_spa
from django.http import JsonResponse
from django.db.models import Prefetch
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, date
os.environ['PROJ_LIB'] = r'C:\Users\HP\AppData\Local\Programs\Python\Python312\Lib\site-packages\pyproj\proj_dir\share\proj'
os.environ['GDAL_DATA'] = r'C:\Users\HP\AppData\Local\Programs\Python\Python312\Lib\site-packages\pyproj\proj_dir\share\proj'


# Fetch GHI, DNI, and DHI from NASA POWER API
def fetch_nasa_power_data(latitude, longitude, date):
    print("Fetching NASA POWER data...")
    start_date = pd.Timestamp(date).strftime('%Y%m%d')
    end_date = (pd.Timestamp(date) + pd.Timedelta(days=1)).strftime('%Y%m%d')
    
    url = "https://power.larc.nasa.gov/api/temporal/hourly/point"
    params = {
        'parameters': 'ALLSKY_SFC_SW_DWN,ALLSKY_SFC_SW_DNI,ALLSKY_SFC_SW_DIFF',
        'community': 'RE',
        'longitude': longitude,
        'latitude': latitude,
        'start': start_date,
        'end': end_date,
        'format': 'JSON',
        'time-standard': 'UTC'
    }

    response = requests.get(url, params=params)
    if response.status_code != 200:
        raise Exception(f"Error fetching data from NASA API: {response.status_code}")
    
    data = response.json()
    parameters = data.get('properties', {}).get('parameter', {})
    ghi = parameters.get('ALLSKY_SFC_SW_DWN', {})
    dni = parameters.get('ALLSKY_SFC_SW_DNI', {})
    dhi = parameters.get('ALLSKY_SFC_SW_DIFF', {})

    #print("GHI Data:", ghi)
    #print("DNI Data:", dni)
    #print("DHI Data:", dhi)
    #print("Fetched Parameters:", parameters)
    times = pd.date_range(start=start_date, end=end_date, freq='1h', tz='UTC')[:-1]
    ghi_values = list(ghi.values())
    dni_values = list(dni.values())
    dhi_values = list(dhi.values())

    min_length = min(len(times), len(ghi_values), len(dni_values), len(dhi_values))
    times = times[:min_length]
    ghi_values = ghi_values[:min_length]
    dni_values = dni_values[:min_length]
    dhi_values = dhi_values[:min_length]

    df = pd.DataFrame({
        'Time (UTC)': times,
        'GHI': ghi_values,
        'DNI': dni_values,
        'DHI': dhi_values
    })
    #print("date:\n")
    #print(f"ghi:{ghi_values}\ndni:{dni_values}\ndhi:{dhi_values}")
    # Convert to IST
    df['Time (IST)'] = df['Time (UTC)'].dt.tz_convert('Asia/Kolkata')
    return df

def fetch_pvlib_data(latitude, longitude, date):
    print("Fetching solar data using pvlib...")
    start_date = pd.Timestamp(date).tz_localize('UTC')
    end_date = (pd.Timestamp(date) + pd.Timedelta(days=1)).tz_localize('UTC')
    
    times = pd.date_range(start=start_date, end=end_date, freq='1h', tz='UTC')[:-1]
    
    # Define location and calculate irradiance
    location = pvlib.location.Location(latitude, longitude)
    clear_sky = location.get_clearsky(times)  # Uses Ineichen model by default
    
    ghi = clear_sky['ghi']  # Global Horizontal Irradiance
    dni = clear_sky['dni']  # Direct Normal Irradiance
    dhi = clear_sky['dhi']  # Diffuse Horizontal Irradiance
    
    # Create DataFrame in the desired format
    df = pd.DataFrame({
        'Time (UTC)': times,
        'GHI': ghi,
        'DNI': dni,
        'DHI': dhi
    })
    
    # Convert to IST
    df['Time (IST)'] = df['Time (UTC)'].dt.tz_convert('Asia/Kolkata')
    return df

def fetch_monthly_nasa_power_data(latitude, longitude, year, month):
    print("Fetching NASA POWER data for the entire month...")
    start_date = pd.Timestamp(f'{year}-{month:02d}-01')
    end_date = (start_date + pd.Timedelta(days=32)).replace(day=1)  # This handles month overflow
    start_date_str = start_date.strftime('%Y%m%d')
    end_date_str = end_date.strftime('%Y%m%d')

    url = "https://power.larc.nasa.gov/api/temporal/hourly/point"
    params = {
        'parameters': 'ALLSKY_SFC_SW_DWN,ALLSKY_SFC_SW_DNI,ALLSKY_SFC_SW_DIFF',
        'community': 'RE',
        'longitude': longitude,
        'latitude': latitude,
        'start': start_date_str,
        'end': end_date_str,
        'format': 'JSON',
        'time-standard': 'UTC'
    }

    response = requests.get(url, params=params)
    if response.status_code != 200:
        raise Exception(f"Error fetching data from NASA API: {response.status_code}")
    
    data = response.json()
    parameters = data.get('properties', {}).get('parameter', {})
    ghi = parameters.get('ALLSKY_SFC_SW_DWN', {})
    dni = parameters.get('ALLSKY_SFC_SW_DNI', {})
    dhi = parameters.get('ALLSKY_SFC_SW_DIFF', {})
    times = pd.date_range(start=start_date, end=end_date, freq='1h', tz='UTC')[:-1]
    ghi_values = list(ghi.values())
    dni_values = list(dni.values())
    dhi_values = list(dhi.values())

    min_length = min(len(times), len(ghi_values), len(dni_values), len(dhi_values))
    times = times[:min_length]
    ghi_values = ghi_values[:min_length]
    dni_values = dni_values[:min_length]
    dhi_values = dhi_values[:min_length]

    df = pd.DataFrame({
        'Time (UTC)': times,
        'GHI': ghi_values,
        'DNI': dni_values,
        'DHI': dhi_values
    })
    df['Time (IST)'] = df['Time (UTC)'].dt.tz_convert('Asia/Kolkata')

    df['Hour'] = df['Time (IST)'].dt.hour
    
    # Calculate average for each hour across all days
    hourly_avg_ghi = df.groupby('Hour')['GHI'].mean()
    hourly_avg_dni = df.groupby('Hour')['DNI'].mean()
    hourly_avg_dhi = df.groupby('Hour')['DHI'].mean()
    #print("month\n")
    #print(f"ghi: {hourly_avg_ghi}\ndni: {hourly_avg_dni}\ndhi: {hourly_avg_dhi}")
    return hourly_avg_ghi, hourly_avg_dni, hourly_avg_dhi


def fetch_monthly_pvlib_data(latitude, longitude, year, month):
    print("Fetching solar data using pvlib for the entire month...")
    
    # Define start and end dates for the month
    start_date = pd.Timestamp(f'{year}-{month:02d}-01', tz='UTC')
    end_date = (start_date + pd.Timedelta(days=32)).replace(day=1)  # Handle month overflow
    
    # Generate hourly timestamps for the entire month
    times = pd.date_range(start=start_date, end=end_date, freq='1h', tz='UTC')[:-1]
        
    # Define location and calculate irradiance
    location = pvlib.location.Location(latitude, longitude)
    clear_sky = location.get_clearsky(times)  # Uses the Ineichen model by default
    
    ghi = clear_sky['ghi']  # Global Horizontal Irradiance
    dni = clear_sky['dni']  # Direct Normal Irradiance
    dhi = clear_sky['dhi']  # Diffuse Horizontal Irradiance
    
    # Create a DataFrame for analysis
    df = pd.DataFrame({
        'Time (UTC)': times,
        'GHI': ghi,
        'DNI': dni,
        'DHI': dhi
    })
    
    # Convert to IST
    df['Time (IST)'] = df['Time (UTC)'].dt.tz_convert('Asia/Kolkata')
    df['Hour'] = df['Time (IST)'].dt.hour
    
    # Calculate average for each hour across all days
    hourly_avg_ghi = df.groupby('Hour')['GHI'].mean()
    hourly_avg_dni = df.groupby('Hour')['DNI'].mean()
    hourly_avg_dhi = df.groupby('Hour')['DHI'].mean()
    
    #print("Monthly Averages (pvlib):")
    #print(f"GHI: {hourly_avg_ghi}\nDNI: {hourly_avg_dni}\nDHI: {hourly_avg_dhi}")
    
    return hourly_avg_ghi, hourly_avg_dni, hourly_avg_dhi


# Function to fetch cloud cover data using Open-Meteo API
def fetch_cloud_cover_data(latitude, longitude, start_date, end_date):
    if start_date > pd.Timestamp.now().normalize():
        print("Future date detected. Skipping cloud cover data fetch.")
        return None

    print("Fetching cloud cover data...")
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        'latitude': latitude,
        'longitude': longitude,
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'hourly': 'cloudcover'
    }

    try:
        response = requests.get(url, params=params)
        if response.status_code != 200:
            raise Exception(f"Error fetching cloud cover data: {response.status_code}")
        
        data = response.json()

        if 'hourly' not in data or 'cloudcover' not in data['hourly']:
            raise Exception("Cloud cover data is not available for the given date and location.")

        times = pd.to_datetime(data['hourly']['time'])
        cloud_cover = data['hourly']['cloudcover']

        cloud_cover_normalized = [cc / 100 for cc in cloud_cover]

        df = pd.DataFrame({
            'Time (UTC)': times,
            'Cloud Cover': cloud_cover_normalized
        })

        df['Time (UTC)'] = df['Time (UTC)'].dt.tz_localize('UTC')
        return df

    except Exception as e:
        print(f"Cloud cover data fetch failed: {e}")
        return None

# Function to fetch monthly average cloud cover using Open-Meteo API
def fetch_monthly_average_cloud_cover(latitude, longitude, year, month):
    print(f"Fetching Monthly Average Cloud Cover for {year}-{month:02d}...")
    start_date = f"{year}-{month:02d}-01"
    end_date = pd.Timestamp(start_date) + pd.offsets.MonthEnd(0)
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        'latitude': latitude,
        'longitude': longitude,
        'start_date': start_date,
        'end_date': end_date.strftime('%Y-%m-%d'),
        'hourly': 'cloudcover',
    }
    response = requests.get(url, params=params)
    if response.status_code != 200:
        raise Exception(f"Error fetching cloud cover data from Open-Meteo API: {response.status_code}")
    data = response.json()
    if 'hourly' not in data or 'cloudcover' not in data['hourly']:
        raise Exception("Cloud cover data is not available for the given date and location.")
    # Extract cloud cover values and convert to a normalized factor (0 to 1)
    cloud_cover = data['hourly']['cloudcover']
    cloud_cover_normalized = [cc / 100 for cc in cloud_cover]

    # Calculate the monthly average cloud cover factor
    avg_cloud_cover = sum(cloud_cover_normalized) / len(cloud_cover_normalized) if cloud_cover_normalized else 0.0
    #print(f"Average Cloud Cover for {year}-{month:02d}: {avg_cloud_cover * 100:.2f}%")

    return avg_cloud_cover

def calculate_solar_angles(latitude, longitude, times):
    print("Calculating solar angles...")
    solar_position = get_solarposition(times, latitude, longitude)
    solar_angles = pd.DataFrame({
        'Time': times,
        'Zenith': solar_position['zenith'].values,
        'Azimuth': solar_position['azimuth'].values
    })
    return solar_angles


def calculate_irradiance(dni, dhi, latitude,longitude, tilt,sun_azimuth ,surface_azimuth, day_of_year, time_ist, albedo, cloud_factor, shadow_factor):
    # Calculate declination angle (delta)
    declination = 23.45 * sin(radians(360 / 365 * (day_of_year - 81)))
     # Convert IST to Solar Time
    # Longitude correction (in hours)
    longitude_correction = (longitude - 82.5) * 4 / 60  # IST based on 82.5°E
    
    # Equation of Time (approximation in minutes)
    equation_of_time = 9.87 * sin(2 * radians(360 / 365 * (day_of_year - 81))) - \
                       7.53 * cos(radians(360 / 365 * (day_of_year - 81))) - \
                       1.5 * sin(radians(360 / 365 * (day_of_year - 81)))
    equation_of_time = equation_of_time / 60  # Convert minutes to hours
    
    # Solar Time (in hours)
    solar_time = time_ist + longitude_correction + equation_of_time
    # Calculate hour angle (h)
    hour_angle = 15 * (solar_time - 12)

    # Convert latitude and tilt to radians
    latitude_rad = radians(latitude)
    declination_rad = radians(declination)
    hour_angle_rad = radians(hour_angle)
    tilt_rad = radians(tilt)
    surface_azimuth_rad = radians(surface_azimuth)

    # Calculate zenith angle (theta_z)
    zenith_cos = (sin(latitude_rad) * sin(declination_rad) * cos(surface_azimuth-sun_azimuth) +
                  cos(latitude_rad) * cos(declination_rad) * cos(hour_angle_rad))
    zenith_angle = degrees(acos(zenith_cos))  # Zenith angle in degrees
    zenith_rad = acos(zenith_cos)            # Zenith angle in radians

    # Beam irradiance
    azimuth_rad = radians(surface_azimuth)
    beam_irradiance = dni * shadow_factor * cloud_factor * max(
        0, cos(zenith_rad) 
    )

    # Diffuse and reflected irradiance
    diffuse_irradiance = dhi* cloud_factor * ((1 + cos(tilt_rad)) / 2)
    reflected_irradiance = albedo * ((dni*shadow_factor*cloud_factor) + (dhi*cloud_factor)) * ((1 - cos(tilt_rad)) / 2)

    # Total irradiance
    total_irradiance = beam_irradiance + diffuse_irradiance + reflected_irradiance

    return total_irradiance

def classify_orientation(azimuth):
    if azimuth == 0:
        return "Roof"
    elif 337.5 <= azimuth <= 360 or 0 <= azimuth < 22.5:
        return "North"
    elif 22.5 <= azimuth < 67.5:
        return "North-East"
    elif 67.5 <= azimuth < 112.5:
        return "East"
    elif 112.5 <= azimuth < 157.5:
        return "South-East"
    elif 157.5 <= azimuth < 202.5:
        return "South"
    elif 202.5 <= azimuth < 247.5:
        return "South-West"
    elif 247.5 <= azimuth < 292.5:
        return "West"
    elif 292.5 <= azimuth < 337.5:
        return "North-West"
    return "Unknown"
