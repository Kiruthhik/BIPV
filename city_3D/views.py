from city_3D.utils import *
import joblib
from django_ratelimit .decorators import ratelimit
from datetime import timedelta, datetime
from django.views.decorators.csrf import csrf_exempt

@ratelimit(key='ip', rate='5/m', block=True)
def building_solar_potential(request, id, _date):
    date_obj = datetime.strptime(_date, "%Y-%m-%d")
    month = date_obj.month
     # Fetch the building with related building faces and centroids to minimize the number of queries.
    building = Building.objects.prefetch_related(
        Prefetch(
            'faces',
            queryset=BuildingFace.objects.prefetch_related(
                Prefetch(
                    'centroids',
                    queryset=VirtualGridCentroid.objects.prefetch_related(
                        Prefetch(
                            'shadow_analysis',
                            queryset=ShadowAnalysis.objects.filter(month=date_obj.month),
                            to_attr='monthly_shadow_analysis'
                        )
                    )
                )
            )
        )
    ).get(id=id)
    # Convert geometry to lat/lon
    latlong = building.geometry.centroid.transform(4326, clone=True)
    latitude = latlong.y
    longitude = latlong.x
    
    if date_obj.date() > ((date.today() - timedelta(days=6*30))):
        solar_data = fetch_pvlib_data(latitude,longitude,_date)
    else:
        solar_data = fetch_nasa_power_data(latitude, longitude, _date)

    if solar_data.empty:
        raise ValueError("No solar data returned from NASA POWER API.")

    # Convert solar data to IST
    solar_data['Time (IST)'] = solar_data['Time (UTC)'].dt.tz_convert('Asia/Kolkata')
    solar_data = solar_data.drop(columns=['Time (UTC)'])  # Drop UTC column if not needed
    solar_data = solar_data.rename(columns={'Time (IST)': 'Time'})

    full_day_times = pd.date_range(
    start=f'{_date} 00:00:00',
    end=f'{_date} 23:59:59',
    freq='H',
    tz='Asia/Kolkata'
    )

    # Calculate sunrise and sunset
    sunrise_sunset = sun_rise_set_transit_spa(full_day_times.tz_convert('UTC'), latitude, longitude)
    sunrise = sunrise_sunset['sunrise'].dt.tz_convert('Asia/Kolkata').iloc[0].hour
    sunset = sunrise_sunset['sunset'].dt.tz_convert('Asia/Kolkata').iloc[0].hour
    print("sunrise:",sunrise, "\nsunset:",sunset)

    # Calculate solar angles in IST and merge into solar_data
    solar_angles = calculate_solar_angles(latitude, longitude, solar_data['Time'])
    solar_data = pd.merge(solar_data, solar_angles, on='Time', how='left')
    if solar_data.empty:
        raise ValueError("No solar data returned from NASA POWER API.")

    # Debug: Print solar data
    #print(f"Daily Solar Data ({_date}):")
    #print(solar_data)


    cloud_cover_data = fetch_cloud_cover_data(latitude, longitude, date_obj, date_obj)
    if cloud_cover_data is None:
        print("Using default cloud factor of 1.0")
        cloud_factor = 1.0
    else:
        cloud_cover_data['Time (IST)'] = cloud_cover_data['Time (UTC)'].dt.tz_convert('Asia/Kolkata')
    print(f"Cloud Cover Data ({_date}):")
    print(cloud_cover_data)
    # Initialize total building solar potential
    response_data = {
    'building_id': building.id,
    'height' : building.height,
    'total_solar_potential': '',
    'total_solar_irradiance': "",
    'faces': {}  # Initialize a dictionary to hold face details
}
    def calculate_face_potential(face,sunrise,sunset):
        # Calculate the grid area for the face (divide by 4 since it’s divided into 4 grids)
        grid_area = face.area / 4.0
        face_irradiance = 0.0
        face_potential = 0.0
        surface_azimuth = face.orientation 
        face_orientation = classify_orientation(surface_azimuth)
        #print(f"grid area:{grid_area}\tface tilt:{face.tilt}\n")
        # Loop over all centroids (representing grids)
        grid_data = {}
        for centroid in face.centroids.all():
            # Initialize potential for the grid
            grid_irradiance = 0.0
            grid_potential = 0.0
             # Use prefetched shadow analysis data for the centroid
            shadow_records = {record.hour: record for record in centroid.monthly_shadow_analysis}
            #print(f"centroid{centroid.id}\n")
            #print(f"hour\tDNI\tDHI\tzenith\tazimuth\tcloud\tshadow\tirradiance\n")
            # Get shadow status from ShadowAnalysis table for the centroid
            for hour in range(sunrise, sunset+1):  # 5 AM to 7 PM IST
                # Fetch shadow status for the current month and hour
                try:
                    shadow_record = shadow_records.get(hour)
                    shadow_factor = 0.0 if shadow_record and shadow_record.shadow else 1.0
                except ShadowAnalysis.DoesNotExist:
                    shadow_factor = 1.0  # Default to no shadow if no entry exists

                # Fetch the solar data for the current hour (assuming `solar_data` has hourly data)
                solar_row = solar_data.loc[solar_data['Time'].dt.hour == hour].iloc[0]
                dni = solar_row['DNI']
                dhi = solar_row['DHI']
                zenith = solar_row['Zenith']  # Zenith angle for the current hour
                sun_azimuth = solar_row['Azimuth']  # Sun's azimuth angle for the current hour
                 # Surface azimuth from building face orientation

                # Fetch the cloud cover for the current hour
                if cloud_cover_data is not None:
                    cloud_row = cloud_cover_data.loc[cloud_cover_data['Time (IST)'].dt.hour == hour].iloc[0]
                    cloud_factor = 1.0 - cloud_row['Cloud Cover']  # Apply the cloud cover factor
                else:
                    cloud_factor = 1
                day_of_year = date_obj.timetuple().tm_yday
                irradiance = calculate_irradiance(dni, dhi,latitude,longitude, face.tilt, sun_azimuth, surface_azimuth,day_of_year,hour, 0.2, cloud_factor, shadow_factor)
                # Calculate the solar potential for the grid
                #print(f"{hour:.2f}\t{dni:.2f}\t{dhi:.2f}\t{zenith:.2f}\t{sun_azimuth:.2f}\t{cloud_factor:.2f}\t{shadow_factor}\t{irradiance:.2f}\n")
                grid_irradiance += irradiance/1000
                grid_potential += (irradiance*grid_area)/1000
            grid_data[f'{centroid.label}'] = {
                    'potential': f'{grid_potential:0.2f}kWh',
                    'irradiance' : f'{grid_irradiance:0.2f}kWh/m^2',
                }
                #print(f"grid potential:{grid_potential:.2f}\n")
            face_irradiance += grid_irradiance
            face_potential += grid_potential
            #print(f"face potential:{face_potential:.2f}\n")
        return face.id, face_potential, face_irradiance/4, face_orientation, face.area, grid_data
    total_solar_potential = 0.0
    total_solar_irradiance = 0.0
    face_potentials = {}
    face_irradiations = {}
    face_orientations = {}
    vertical_surface_potential = 0.0
    rooftop_potential = 0.0
    with ThreadPoolExecutor() as executer:
        futures = [executer.submit(calculate_face_potential,face,sunrise,sunset) for face in building.faces.all()]
        for future in futures:
            face_id, face_potential,face_irradiance, face_orientation, area, grid_data = future.result()
            total_solar_potential += face_potential
            total_solar_irradiance += face_irradiance
            face_potentials[f'{face_id}potential'] = face_potential
            face_irradiations[f'{face_id}irradiance'] = face_irradiance
            face_orientations[f'{face_id}orientaton'] = face_orientation
            if face_orientation == 'Roof':
                rooftop_potential += face_potential
            else:
                vertical_surface_potential += face_potential

            response_data['faces'][f'{face_id}'] = {
                'potential' : f'{face_potential:0.2f}kWh',
                'irradiance' : f'{face_irradiance:0.2f} kWh/m^2',
                'orientation' : face_orientation,
                'surface_area' : f'{area:0.2f}m^2'
            }
            response_data['faces'][f'{face_id}'].update(grid_data)

    total_solar_irradiance = total_solar_irradiance/building.faces.count()      
    response_data['total_solar_potential'] =   f"{(total_solar_potential):0.2f} kWh"
    response_data['total_solar_irradiance'] =  f"{(total_solar_irradiance):0.2f} kWh/m^2"
    response_data['vertical_surface_BIPV'] = f'{vertical_surface_potential*0.18:0.2f}kWh'
    response_data['rooftop_potential_BIPV'] = f'{rooftop_potential*0.18:0.2f}kWh'
            
    # response_data={
    #     'building_id': building.id,
    #     'total_solar_potential': f"{(total_solar_potential*0.18)} kWh",
    #     'total_solar_irradiance': f"{(total_solar_irradiance)} kWh/m2"
    # }
    # response_data.update(face_potentials)
    # response_data.update(face_irradiations)
    # response_data.update(face_orientations)
    return JsonResponse(response_data)

def building_solar_potential_hourly(request, id, _date):
    date_obj = datetime.strptime(_date, "%Y-%m-%d")
    month = date_obj.month
     # Fetch the building with related building faces and centroids to minimize the number of queries.
    building = Building.objects.prefetch_related(
        Prefetch(
            'faces',
            queryset=BuildingFace.objects.prefetch_related(
                Prefetch(
                    'centroids',
                    queryset=VirtualGridCentroid.objects.prefetch_related(
                        Prefetch(
                            'shadow_analysis',
                            queryset=ShadowAnalysis.objects.filter(month=date_obj.month),
                            to_attr='monthly_shadow_analysis'
                        )
                    )
                )
            )
        )
    ).get(id=id)
    # Convert geometry to lat/lon
    latlong = building.geometry.centroid.transform(4326, clone=True)
    latitude = latlong.y
    longitude = latlong.x
    
    if date_obj.date() > ((date.today() - timedelta(days=6*30))):
        solar_data = fetch_pvlib_data(latitude,longitude,_date)
    else:
        solar_data = fetch_nasa_power_data(latitude, longitude, _date)

    if solar_data.empty:
        raise ValueError("No solar data returned from NASA POWER API.")

    # Convert solar data to IST
    solar_data['Time (IST)'] = solar_data['Time (UTC)'].dt.tz_convert('Asia/Kolkata')
    solar_data = solar_data.drop(columns=['Time (UTC)'])  # Drop UTC column if not needed
    solar_data = solar_data.rename(columns={'Time (IST)': 'Time'})

    full_day_times = pd.date_range(
    start=f'{_date} 00:00:00',
    end=f'{_date} 23:59:59',
    freq='H',
    tz='Asia/Kolkata'
    )

    # Calculate sunrise and sunset
    sunrise_sunset = sun_rise_set_transit_spa(full_day_times.tz_convert('UTC'), latitude, longitude)
    sunrise = sunrise_sunset['sunrise'].dt.tz_convert('Asia/Kolkata').iloc[0].hour
    sunset = sunrise_sunset['sunset'].dt.tz_convert('Asia/Kolkata').iloc[0].hour
    print("sunrise:",sunrise, "\nsunset:",sunset)

    # Calculate solar angles in IST and merge into solar_data
    solar_angles = calculate_solar_angles(latitude, longitude, solar_data['Time'])
    solar_data = pd.merge(solar_data, solar_angles, on='Time', how='left')
    if solar_data.empty:
        raise ValueError("No solar data returned from NASA POWER API.")

    # Debug: Print solar data
    #print(f"Daily Solar Data ({_date}):")
    #print(solar_data)


    cloud_cover_data = fetch_cloud_cover_data(latitude, longitude, date_obj, date_obj)
    if cloud_cover_data is None:
        print("Using default cloud factor of 1.0")
        cloud_factor = 1.0
    else:
        cloud_cover_data['Time (IST)'] = cloud_cover_data['Time (UTC)'].dt.tz_convert('Asia/Kolkata')
    print(f"Cloud Cover Data ({_date}):")
    print(cloud_cover_data)
    # Initialize total building solar potential
    response_data = {
    'building_id': building.id,
    'height' : building.height
    }
    response_data['faces'] = {}

    def calculate_face_potential(face,sunrise,sunset):
        # Calculate the grid area for the face (divide by 4 since it’s divided into 4 grids)
        grid_area = face.area / 4.0
        #face_irradiance = 0.0
        #face_potential = 0.0
        surface_azimuth = face.orientation 
        face_orientation = classify_orientation(surface_azimuth)
        #print(f"grid area:{grid_area}\tface tilt:{face.tilt}\n")
        # Loop over all centroids (representing grids)
        grid_data = {}
        for centroid in face.centroids.all():
            # Initialize potential for the grid
            grid_data[f'{centroid.label}']={}
            # Use prefetched shadow analysis data for the centroid
            shadow_records = {record.hour: record for record in centroid.monthly_shadow_analysis}
            #print(f"centroid{centroid.id}\n")
            #print(f"hour\tDNI\tDHI\tzenith\tazimuth\tcloud\tshadow\tirradiance\n")
            # Get shadow status from ShadowAnalysis table for the centroid
            for hour in range(sunrise, sunset+1):  # 5 AM to 7 PM IST
                # Fetch shadow status for the current month and hour
                try:
                    shadow_record = shadow_records.get(hour)
                    shadow_factor = 0.0 if shadow_record and shadow_record.shadow else 1.0
                except ShadowAnalysis.DoesNotExist:
                    shadow_factor = 1.0  # Default to no shadow if no entry exists

                # Fetch the solar data for the current hour (assuming `solar_data` has hourly data)
                solar_row = solar_data.loc[solar_data['Time'].dt.hour == hour].iloc[0]
                dni = solar_row['DNI']
                dhi = solar_row['DHI']
                zenith = solar_row['Zenith']  # Zenith angle for the current hour
                sun_azimuth = solar_row['Azimuth']  # Sun's azimuth angle for the current hour
                 # Surface azimuth from building face orientation

                # Fetch the cloud cover for the current hour
                if cloud_cover_data is not None:
                    cloud_row = cloud_cover_data.loc[cloud_cover_data['Time (IST)'].dt.hour == hour].iloc[0]
                    cloud_factor = 1.0 - cloud_row['Cloud Cover']  # Apply the cloud cover factor
                else:
                    cloud_factor = 1
                day_of_year = date_obj.timetuple().tm_yday
                irradiance = calculate_irradiance(dni, dhi,latitude,longitude, face.tilt, sun_azimuth, surface_azimuth,day_of_year,hour, 0.2, cloud_factor, shadow_factor)
                # Calculate the solar potential for the grid
                #print(f"{hour:.2f}\t{dni:.2f}\t{dhi:.2f}\t{zenith:.2f}\t{sun_azimuth:.2f}\t{cloud_factor:.2f}\t{shadow_factor}\t{irradiance:.2f}\n")
                grid_irradiance = irradiance/1000
                grid_potential = (irradiance*grid_area)/1000
                grid_data[f'{centroid.label}'][f'{hour}'] = {
                    'potential': f'{grid_potential:0.2f}kWh',
                    'irradiance' : f'{grid_irradiance:0.2f}kWh/m^2',
                }
                #print(f"grid potential:{grid_potential:.2f}\n")
            #face_irradiance += grid_irradiance
            #face_potential += grid_potential
            #print(f"face potential:{face_potential:.2f}\n")
        return face.id, face_orientation, face.area/4, grid_data
    
    with ThreadPoolExecutor() as executer:
        futures = [executer.submit(calculate_face_potential,face,sunrise,sunset) for face in building.faces.all()]
        for future in futures:
            face_id, face_orientation, area, grid_data = future.result()

            response_data['faces'][f'{face_id}'] = {
                'orientation' : face_orientation,
                'surface_area' : f'{area:0.2f}m^2'
            }
            response_data['faces'][f'{face_id}'].update(grid_data)


            
    # response_data={
    #     'building_id': building.id,
    #     'total_solar_potential': f"{(total_solar_potential*0.18)} kWh",
    #     'total_solar_irradiance': f"{(total_solar_irradiance)} kWh/m2"
    # }
    # response_data.update(face_potentials)
    # response_data.update(face_irradiations)
    # response_data.update(face_orientations)
    return JsonResponse(response_data)

def hourly_shadow_data(request,id,month):
    building = Building.objects.get(id=id)
    response_data = {
        'building_id': building.id,
        'height' : building.height,
        'faces' : {}
    }
    for face in building.faces.all():
        response_data['faces'][f'{face.id}'] ={
            'orientation' : classify_orientation(face.orientation),
            'surface_area' : f'{face.area}',
        }
        grid_data = {}
        for centroid in face.centroids.all():
            grid_data[f'{centroid.label}']={}
            grid_data[f'{centroid.label}']['hourly']={}
            shadow_count = 0
            for hour in range(6,18):
                shadow = 1 if ShadowAnalysis.objects.filter(centroid = centroid,month=month, hour = hour).first().shadow else 0
                grid_data[f'{centroid.label}']['hourly'][hour] = shadow
                if shadow == 1:
                    shadow_count+=1
            grid_data[f'{centroid.label}']['shadow_percentage'] = f'{(shadow_count/(18-6))*100:0.2f}%'
            grid_data[f'{centroid.label}']['shadow_count'] = f'{shadow_count}/{18-6}'
        response_data['faces'][f'{face.id}'].update(grid_data)

    return JsonResponse(response_data)

from django.http import JsonResponse

def hourly_shadow_data_grid(request, code):
    try:
        # Get the building
        building = Building.objects.get(id=5203)

        # Get all faces of the building
        faces = [face for face in building.faces.all()]
        grid_id = code%10
        face_id = code//10
        # Validate face_id
        if face_id < 0 or face_id >= len(faces):
            return JsonResponse({"error": "Invalid face_id"}, status=400)

        # Get the specific face
        face = faces[face_id-1]

        # Get centroids (grids) for the face
        grids = [centroid for centroid in face.centroids.all()]

        # Validate grid_id
        if grid_id < 1 or grid_id > len(grids):
            return JsonResponse({"error": "Invalid grid_id"}, status=400)

        # Get the specific grid (centroid)
        grid = grids[grid_id - 1]

        # Initialize the response_data dictionary
        response_data = {}
        shadow_count = 0
        # Loop over the hours from 6 AM to 5 PM
        for hour in range(6, 18):
            shadow_analysis = ShadowAnalysis.objects.filter(centroid=grid, month=3, hour=hour).first()

            # If no shadow analysis data is found, assume no shadow (0)
            if shadow_analysis is None:
                shadow = 0
            else:
                shadow = 1 if shadow_analysis.shadow else 0  # Check if shadow exists
                if shadow == 1:
                    shadow_count+=1
            # Add the shadow data to the response
            response_data[f'{hour}'] = shadow
        response_data['shadow_percentage'] = f'{(shadow_count/(18-6))*100:0.2f}%'
        response_data['shadow_count'] = f'{shadow_count}/12'
        return JsonResponse(response_data)

    except Exception as e:
        # Catch unexpected errors and return a proper error message
        return JsonResponse({"error": str(e)}, status=500)

    



def building_monthly_solar_potential(request, id, year, month):
     # Fetch the building with related building faces and centroids to minimize the number of queries.
    building = Building.objects.prefetch_related(
        Prefetch(
            'faces',
            queryset=BuildingFace.objects.prefetch_related(
                Prefetch(
                    'centroids',
                    queryset=VirtualGridCentroid.objects.prefetch_related(
                        Prefetch(
                            'shadow_analysis',
                            queryset=ShadowAnalysis.objects.filter(month=month),
                            to_attr='monthly_shadow_analysis'
                        )
                    )
                )
            )
        )
    ).get(id=id)
    # Convert geometry to lat/lon
    latlong = building.geometry.centroid.transform(4326, clone=True)
    latitude = latlong.y
    longitude = latlong.x
    representative_date = f'{year}-{month:02d}-15'
    date_obj = datetime.strptime(representative_date, "%Y-%m-%d")
    # Fetch monthly averaged solar data (GHI, DNI, DHI) for the building's coordinates
    if date_obj.date() > date.today():
        hourly_avg_ghi, hourly_avg_dni, hourly_avg_dhi = fetch_monthly_pvlib_data(latitude, longitude, year, month)
        cloud_factor=1.0
    else:
        hourly_avg_ghi, hourly_avg_dni, hourly_avg_dhi = fetch_monthly_nasa_power_data(latitude, longitude, year, month)
        #print(f"hourly_avg_dni:{hourly_avg_dni}\n hourly_avg_dhi:{hourly_avg_dhi}")
        # Fetch the average cloud cover factor for the month
        average_cloud_cover = fetch_monthly_average_cloud_cover(latitude, longitude, year, month)
        cloud_factor = 1.0 - average_cloud_cover  # Cloud factor to reduce irradiance
    
    # Calculate solar angles for the entire month at different hours
    times = pd.date_range(start=f'{year}-{month:02d}-01 05:00:00', end=f'{year}-{month:02d}-01 19:00:00', freq='H', tz='Asia/Kolkata')
    solar_angles = calculate_solar_angles(latitude, longitude, times)
    # Create a dictionary to access solar angles by hour
    solar_angles['Hour (IST)'] = solar_angles['Time'].dt.tz_convert('Asia/Kolkata').dt.hour
    solar_angles_dict = solar_angles.set_index('Hour (IST)').to_dict(orient='index')

    

# Generate full day date range for the representative day
    full_day_times = pd.date_range(
        start=f'{representative_date} 00:00:00',
        end=f'{representative_date} 23:59:59',
        freq='H',
        tz='Asia/Kolkata'
    )
    sunrise_sunset = sun_rise_set_transit_spa(full_day_times.tz_convert('UTC'), latitude, longitude)
    sunrise = sunrise_sunset['sunrise'].dt.tz_convert('Asia/Kolkata').iloc[0].hour
    sunset = sunrise_sunset['sunset'].dt.tz_convert('Asia/Kolkata').iloc[0].hour
    print("sunrise:",sunrise, "\nsunset:",sunset)


    def calculate_face_potential(face,sunrise,sunset):
            # Calculate the grid area for the face (divide by 4 since it’s divided into 4 grids)
            grid_area = face.area / 4.0
            face_potential = 0.0
            face_irradiance = 0.0
            surface_azimuth = face.orientation
            print(f"grid area:{grid_area}\tface tilt:{face.tilt}\n")
            # Loop over all centroids (representing grids)
            for centroid in face.centroids.all():
                # Initialize potential for the grid
                grid_potential = 0.0
                grid_irradiance = 0.0
                # Use prefetched shadow analysis data for the centroid
                shadow_records = {record.hour: record for record in centroid.monthly_shadow_analysis}
                print(f"centroid{centroid.id}\n")
                print(f"hour\tDNI\tDHI\tzenith\tazimuth\tcloud\tshadow\tirradiance\n")
                # Loop over each hour of the day (5 AM to 7 PM IST)
                for hour in range(sunrise, sunset+1):  # 5 AM to 7 PM
                    # Get shadow status from ShadowAnalysis table for the centroid for the given month and hour
                    try:
                        shadow_record = shadow_records.get(hour)
                        shadow_factor = 0.0 if shadow_record and shadow_record.shadow else 1.0
                    except ShadowAnalysis.DoesNotExist:
                        shadow_factor = 1.0  # Default to no shadow if no entry exists

                    # Calculate solar angles for the given latitude, longitude, and hour
                    ghi = hourly_avg_ghi[hour]
                    dni = hourly_avg_dni[hour]
                    dhi = hourly_avg_dhi[hour]
                    # Retrieve pre-calculated solar angles for the given hour
                    solar_angle = solar_angles_dict.get(hour, {})
                    zenith = solar_angle.get('Zenith', 0.0)
                    sun_azimuth = solar_angle.get('Azimuth', 0.0)

                    # Surface azimuth comes from building face orientation
                    day_of_year = date_obj.timetuple().tm_yday
                    # Calculate the solar potential for the grid using monthly averages
                    irradiance = calculate_irradiance(
                        dni=dni,
                        dhi=dhi,
                        latitude = latitude,
                        longitude = longitude,
                        tilt=face.tilt,
                        sun_azimuth=sun_azimuth,
                        surface_azimuth=surface_azimuth,
                        day_of_year = day_of_year,
                        time_ist = hour, 
                        albedo=0.2,
                        cloud_factor=cloud_factor,
                        shadow_factor=shadow_factor
                    )
                    print(f"{hour:.2f}\t{dni:.2f}\t{dhi:.2f}\t{zenith:.2f}\t{sun_azimuth:.2f}\t{cloud_factor:.2f}\t{shadow_factor}\t{irradiance:.2f}")
                    # Multiply irradiance by grid area and add to grid potential
                    grid_irradiance += irradiance/1000
                    grid_potential += (irradiance * grid_area)/1000
                    print(f"grid potential:{grid_potential:.2f}\n")

                # Add the grid's potential to the total building potential
                face_irradiance += grid_irradiance
                face_potential+= grid_potential
                print(f"face potential:{face_potential:.2f}\n")
            return face.id, face_potential, face_irradiance/4

    total_solar_potential = 0.0
    total_solar_irradiance = 0.0

    # Loop over all building faces
    face_potentials = {}
    face_irradiations = {}

    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(calculate_face_potential, face,sunrise,sunset) for face in building.faces.all()]
        for future in futures:
            face_id, face_potential,face_irradiance = future.result()
            total_solar_potential += face_potential
            total_solar_irradiance += face_irradiance
            face_potentials[f'{face_id}potential'] = face_potential
            face_irradiations[f'{face_id}irradiance'] = face_irradiance

    response_data={
        'building_id': building.id,
        'month': month,
        'year': year,
        'total_solar_potential': f"{(total_solar_potential)*(0.18)}kWh",
        'total_solar_irradiance': f"{total_solar_irradiance}kWh/m2"
    }
    response_data.update(face_potentials) 
    response_data.update(face_irradiations)
    return JsonResponse(response_data)

def grid_solar_potential_hourly(request,code):
    id = 5203
    building = Building.objects.get(id=id)
    _date = "2023-03-23"
    date_obj = datetime.strptime(_date, "%Y-%m-%d")
    faces = [face for face in building.faces.all()]
    grid_id = code%10
    face_id = code//10
        # Validate face_id
    if face_id < 0 or face_id >= len(faces):
        return JsonResponse({"error": "Invalid face_id"}, status=400)

        # Get the specific face
    face = faces[face_id-1]

        # Get centroids (grids) for the face
    grids = [centroid for centroid in face.centroids.all()]

    # Validate grid_id
    if grid_id < 1 or grid_id > len(grids):
        return JsonResponse({"error": "Invalid grid_id"}, status=400)

        # Get the specific grid (centroid)
    grid = grids[grid_id - 1]

    month = date_obj.month


    # Convert geometry to lat/lon
    latlong = building.geometry.centroid.transform(4326, clone=True)
    latitude = latlong.y
    longitude = latlong.x
    
    if date_obj.date() > ((date.today() - timedelta(days=6*30))):
        solar_data = fetch_pvlib_data(latitude,longitude,_date)
    else:
        solar_data = fetch_nasa_power_data(latitude, longitude, _date)

    if solar_data.empty:
        raise ValueError("No solar data returned from NASA POWER API.")

    # Convert solar data to IST
    solar_data['Time (IST)'] = solar_data['Time (UTC)'].dt.tz_convert('Asia/Kolkata')
    solar_data = solar_data.drop(columns=['Time (UTC)'])  # Drop UTC column if not needed
    solar_data = solar_data.rename(columns={'Time (IST)': 'Time'})

    full_day_times = pd.date_range(
    start=f'{_date} 00:00:00',
    end=f'{_date} 23:59:59',
    freq='H',
    tz='Asia/Kolkata'
    )

    # Calculate sunrise and sunset
    sunrise_sunset = sun_rise_set_transit_spa(full_day_times.tz_convert('UTC'), latitude, longitude)
    sunrise = sunrise_sunset['sunrise'].dt.tz_convert('Asia/Kolkata').iloc[0].hour
    sunset = sunrise_sunset['sunset'].dt.tz_convert('Asia/Kolkata').iloc[0].hour
    print("sunrise:",sunrise, "\nsunset:",sunset)

    # Calculate solar angles in IST and merge into solar_data
    solar_angles = calculate_solar_angles(latitude, longitude, solar_data['Time'])
    solar_data = pd.merge(solar_data, solar_angles, on='Time', how='left')
    if solar_data.empty:
        raise ValueError("No solar data returned from NASA POWER API.")

    # Debug: Print solar data
    #print(f"Daily Solar Data ({_date}):")
    #print(solar_data)


    cloud_cover_data = fetch_cloud_cover_data(latitude, longitude, date_obj, date_obj)
    if cloud_cover_data is None:
        print("Using default cloud factor of 1.0")
        cloud_factor = 1.0
    else:
        cloud_cover_data['Time (IST)'] = cloud_cover_data['Time (UTC)'].dt.tz_convert('Asia/Kolkata')
    print(f"Cloud Cover Data ({_date}):")
    print(cloud_cover_data)
    # Initialize total building solar potential
    grid_area = face.area / 4.0
        #face_irradiance = 0.0
        #face_potential = 0.0
    surface_azimuth = face.orientation 
    face_orientation = classify_orientation(surface_azimuth)
    response_data = {}
    for hour in range(sunrise, sunset+1):  # 5 AM to 7 PM IST

                shadow_analysis = ShadowAnalysis.objects.filter(centroid=grid, month=3, hour=hour).first()

            # If no shadow analysis data is found, assume no shadow (0)
                if shadow_analysis is None:
                    shadow_factor = 1
                else:
                    shadow_factor = 0 if shadow_analysis.shadow else 1  # Check if shadow exists
                # Fetch the solar data for the current hour (assuming `solar_data` has hourly data)
                solar_row = solar_data.loc[solar_data['Time'].dt.hour == hour].iloc[0]
                dni = solar_row['DNI']
                dhi = solar_row['DHI']
                zenith = solar_row['Zenith']  # Zenith angle for the current hour
                sun_azimuth = solar_row['Azimuth']  # Sun's azimuth angle for the current hour
                 # Surface azimuth from building face orientation

                # Fetch the cloud cover for the current hour
                if cloud_cover_data is not None:
                    cloud_row = cloud_cover_data.loc[cloud_cover_data['Time (IST)'].dt.hour == hour].iloc[0]
                    cloud_factor = 1.0 - cloud_row['Cloud Cover']  # Apply the cloud cover factor
                else:
                    cloud_factor = 1
                day_of_year = date_obj.timetuple().tm_yday
                irradiance = calculate_irradiance(dni, dhi,latitude,longitude, face.tilt, sun_azimuth, surface_azimuth,day_of_year,hour, 0.2, cloud_factor, shadow_factor)
                # Calculate the solar potential for the grid
                #print(f"{hour:.2f}\t{dni:.2f}\t{dhi:.2f}\t{zenith:.2f}\t{sun_azimuth:.2f}\t{cloud_factor:.2f}\t{shadow_factor}\t{irradiance:.2f}\n")
                grid_irradiance = irradiance/1000
                grid_potential = (irradiance*grid_area)/1000
                response_data[f'{hour}'] = {
                    'potential': f'{grid_potential:0.2f}kWh',
                    'irradiance' : f'{grid_irradiance:0.2f}kWh/m^2',
                }

    return JsonResponse(response_data)

rf_model_high = joblib.load(r'C:\Users\HP\Documents\hackfest\SIH\SIH FINAL\BIPV\city_3D\rf_model_high.sav')
rf_model_medium = joblib.load(r'C:\Users\HP\Documents\hackfest\SIH\SIH FINAL\BIPV\city_3D\rf_model_medium.sav')
rf_model_low = joblib.load(r'C:\Users\HP\Documents\hackfest\SIH\SIH FINAL\BIPV\city_3D\rf_model_low.sav')

def encode_input(data, feature_columns):
    """
    This function performs one-hot encoding of categorical features 
    and ensures the input data matches the model's expected feature set.
    """
    # Debug: Check if 'Building Type' exists in the input
    print("Columns in input_data:", data.columns)

    # Apply one-hot encoding to categorical features
    data["Building Type"] = data["Building Type"].astype('category')
    data["Facade Material"] = data["Facade Material"].astype('category')
    data["Solar Irradiance"] = data["Solar Irradiance"].astype('category')

    # Perform one-hot encoding, drop first category to avoid collinearity
    data_encoded = pd.get_dummies(data, columns=["Building Type", "Facade Material", "Solar Irradiance"], drop_first=True)

    # Debug: Print encoded data columns
    print("Encoded Columns:", data_encoded.columns)

    # Ensure the correct number of columns by reindexing to the expected feature columns
    # Align with the expected feature columns (same order and missing columns will be filled with 0)
    data_encoded = data_encoded.reindex(columns=feature_columns, fill_value=0)

    return data_encoded

from datetime import date


@ratelimit(key='ip', rate='5/m', block=True)
def get_recommendation(request, id, building_type, facade_material):
    # Get the building by ID
    try:
        building = Building.objects.get(id=id)
    except Building.DoesNotExist:
        return JsonResponse({"error": "Building not found"}, status=404)

    # Set date for irradiance calculation
    _date = date(2023, 12, 15)

    # Calculate building irradiance
    building_irradiance = 0.0
    for face in building.faces.all():
        potential_data = face.potential.filter(date=_date).first()
        if potential_data:
            building_irradiance += potential_data.irradiance or 0.0

    # Determine solar irradiance encoding
    Solar_irradiance_low = 1 if building_irradiance < 3.0 else 0
    Solar_irradiance_medium = 1 if 3.0 <= building_irradiance < 6.0 else 0

    # Calculate the surface area of the building
    surface_area = sum(face.area for face in building.faces.all() if face.area is not None)

    # Determine building type encoding
    building_type_industrial = 1 if building_type.lower() == "industrial" else 0
    building_type_residential = 1 if building_type.lower() == "residential" else 0

    # Determine facade material encoding
    facade_material_glass = 1 if facade_material.lower() == "glass" else 0
    facade_material_metal = 1 if facade_material.lower() == "metal" else 0

    # Construct input data dictionary
    input_data = {
        "Surface Area (m²)": surface_area,
        "Building Type_Industrial": building_type_industrial,
        "Building Type_Residential": building_type_residential,
        "Facade Material_Glass": facade_material_glass,
        "Facade Material_Metal": facade_material_metal,
        "Solar Irradiance_Low": Solar_irradiance_low,
        "Solar Irradiance_Medium": Solar_irradiance_medium,
    }

    # Debug: Check the incoming data
    print("Input Data:", input_data)

    # Convert to DataFrame
    input_df = pd.DataFrame([input_data])

    # Debug: Check the DataFrame columns
    print("Columns in input_df:", input_df.columns)

    # List of all expected feature columns based on the model
    feature_columns = [
        "Surface Area (m²)", "Building Type_Industrial", "Building Type_Residential",
        "Facade Material_Glass", "Facade Material_Metal",
        "Solar Irradiance_Low", "Solar Irradiance_Medium"
    ]

    # Ensure the correct number of columns by reindexing
    input_df = input_df.reindex(columns=feature_columns, fill_value=0)

    # Debug: Check the reindexed DataFrame
    print("Reindexed DataFrame:", input_df)

    # Predict using the trained RandomForest model
    try:
        pred_high = rf_model_high.predict(input_df)
        pred_medium = rf_model_medium.predict(input_df)
        pred_low = rf_model_low.predict(input_df)
    except Exception as e:
        return JsonResponse({"error": "Model prediction failed", "details": str(e)}, status=500)

    # Return the predictions as a JSON response
    response = {
        "Predicted Highly Recommended Panel": pred_high[0],
        "Predicted Medium Recommended Panel": pred_medium[0],
        "Predicted Least Recommended Panel": pred_low[0],
    }

    return JsonResponse(response)




 # Import the correct class for dates

def building_solar_potential_seasonal(request, id):
    try:
        building = Building.objects.get(id=id)
        response_data = {}
        dates = [
            date(2023, 3, 21),  # Spring Equinox
            date(2023, 6, 21),  # Summer Solstice
            date(2023, 9, 21),  # Fall Equinox
            date(2023, 12, 15), # Winter Solstice (approx.)
        ]
        for date_obj in dates:
            building_potential = 0.0
            building_irradiance = 0.0
            for face in building.faces.all():
                potential_data = face.potential.filter(date=date_obj).first()
                if potential_data:
                    building_potential += potential_data.potential or 0.0
                    building_irradiance += potential_data.irradiance or 0.0
            response_data[date_obj.strftime("%d-%m")] = {
                'potential': building_potential,
                'irradiance': building_irradiance
            }

        return JsonResponse(response_data, safe=False)
    except Building.DoesNotExist:
        return JsonResponse({'error': 'Building not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
