# import math
# import json
# from datetime import datetime, timedelta
# import suncalc
# import geopy.distance
# from django.core.management.base import BaseCommand
# from city_3D.models import VirtualGridCentroid, ShadowAnalysis, Building

# class Command(BaseCommand):
#     help = "Perform shadow analysis for all centroids and store results in the database"

#     def handle(self, *args, **kwargs):
#         print("Starting shadow analysis...")

#         # Load GeoJSON data
#         geojson_file = 'buildings_with_centroids_id.geojson'  # Update the path if necessary
#         print(f"Loading GeoJSON file: {geojson_file}")
#         geojson_data = self.load_geojson(geojson_file)

#         # Specify the date and time interval
#         date_time = datetime(2023, 8, 15)  # Specific date for shadow analysis
#         print("Month:",date_time.month)
#         interval_minutes = 60  # 1-hour interval
#         print(f"Analyzing shadows for date: {date_time.strftime('%Y-%m-%d')} at {interval_minutes}-minute intervals.")

#         # Perform shadow analysis
#         print("Performing shadow analysis for the entire day...")
#         results = self.perform_shadow_analysis_for_day(geojson_data, date_time, interval_minutes)

#         # Save results to the database
#         print("Saving shadow analysis results to the database...")
#         self.save_results_to_db(results)
#         print("Shadow analysis completed.")

#     def load_geojson(self, file_path):
#         with open(file_path, 'r') as file:
#             return json.load(file)

#     def get_sun_position(self, lat, lon, time):
#         sun = suncalc.get_position(time, lat, lon)
#         return sun['altitude'], sun['azimuth']

#     def calculate_distance(self, coord1, coord2):
#         return geopy.distance.geodesic(coord1, coord2).meters

#     def is_in_shadow(self, building_face, centroid_coords, sun_altitude, sun_azimuth):
#         face_coords = building_face['geometry']['coordinates'][0][0]  # MultiPolygon -> Polygon -> Coordinates

#         # Calculate the center of the face (approximate)
#         face_center = [sum(coord[0] for coord in face_coords) / len(face_coords),
#                        sum(coord[1] for coord in face_coords)]

#         # Vector pointing from centroid to face center
#         vector_to_face_center = [face_center[0] - centroid_coords[0], face_center[1] - centroid_coords[1]]

#         # Calculate sun vector
#         sun_vector = [math.cos(sun_azimuth) * math.sin(sun_altitude), math.sin(sun_azimuth) * math.sin(sun_altitude)]

#         # Avoid calculation errors if sun_vector magnitude is zero
#         magnitude_sun = math.sqrt(sun_vector[0]**2 + sun_vector[1]**2)
#         if magnitude_sun == 0:
#             return 1  # Not shadowed, sun directly overhead

#         # Calculate angle between the vectors
#         dot_product = vector_to_face_center[0] * sun_vector[0] + vector_to_face_center[1] * sun_vector[1]
#         magnitude_face = math.sqrt(vector_to_face_center[0]**2 + vector_to_face_center[1]**2)

#         if magnitude_face == 0:
#             return 1  # Not shadowed

#         cos_angle = dot_product / (magnitude_face * magnitude_sun)

#         # If the angle between the vectors is greater than a threshold, the grid is in shadow
#         return 0 if cos_angle < 0 else 1

#     def perform_shadow_analysis_for_day(self, geojson_data, date, interval_minutes):
#         results = []
#         total_centroids = sum(len(feature['properties'].get('centroids', [])) for feature in geojson_data['features'])
#         processed_centroids = 0

#         for feature in geojson_data['features']:
#             building_id = feature['properties']['building_id']
#             print(f"Processing building ID: {building_id}")

#             for centroid in feature['properties'].get('centroids', []):
#                 centroid_id = centroid['id']
#                 print(f"  Processing centroid ID: {centroid_id}")
#                 centroid_coords = centroid['coordinates'][:2]  # Use only lat/lon (ignore height)

#                 current_time = datetime(date.year, date.month, date.day, 6, 0)
#                 while current_time.hour < 18:
#                     sun_altitude, sun_azimuth = self.get_sun_position(centroid_coords[1], centroid_coords[0], current_time)

#                     if sun_altitude is None or sun_azimuth is None:
#                         shadow_status = 1  # Not shadowed if sun position is invalid
#                     else:
#                         shadow_status = self.is_in_shadow(feature, centroid_coords, sun_altitude, sun_azimuth)

#                     results.append({
#                         'building_id': building_id,
#                         'centroid_id': centroid_id,
#                         'month': current_time.month,
#                         'hour': current_time.hour,
#                         'shadow_status': shadow_status
#                     })

#                     current_time += timedelta(minutes=interval_minutes)

#                 processed_centroids += 1
#                 print(f"  Completed centroid ID: {centroid_id} ({processed_centroids}/{total_centroids})")

#         return results

#     def save_results_to_db(self, results):
#         rows_processed = 0
#         errors = 0

#         for result in results:
#             try:
#                 # Find the centroid
#                 centroid = VirtualGridCentroid.objects.get(id=result['centroid_id'])

#                 # Create or update the shadow analysis entry
#                 ShadowAnalysis.objects.update_or_create(
#                     centroid=centroid,
#                     month=result['month'],
#                     hour=result['hour'],
#                     defaults={'shadow':not bool(result['shadow_status'])}
#                 )
#                 rows_processed += 1
#                 print(f"Saved shadow analysis for centroid ID {result['centroid_id']} at hour {result['hour']}.")
#             except Exception as e:
#                 self.stderr.write(f"Error processing result: {result}. Error: {e}")
#                 errors += 1

#         print(f"\nSummary:")
#         print(f"  Rows processed: {rows_processed}")
#         print(f"  Errors: {errors}")


# from datetime import datetime, timedelta
# from django.core.management.base import BaseCommand
# from pybdshadow import ShadowCalculator, Building3D
# from city_3D.models import Building, BuildingFace, VirtualGridCentroid, ShadowAnalysis


# class Command(BaseCommand):
#     help = "Perform shadow analysis for all centroids and store results in the database"

#     def handle(self, *args, **kwargs):
#         print("Starting shadow analysis...")

#         # Specify the date and time interval
#         date_time = datetime(2023, 8, 15)  # Specific date for shadow analysis
#         interval_minutes = 60  # 1-hour interval
#         print(f"Analyzing shadows for date: {date_time.strftime('%Y-%m-%d')} at {interval_minutes}-minute intervals.")

#         # Fetch buildings and prepare for shadow analysis
#         print("Fetching building data from the database...")
#         buildings = self.prepare_buildings()

#         # Perform shadow analysis
#         print("Performing shadow analysis for the entire day...")
#         results = self.perform_shadow_analysis(buildings, date_time, interval_minutes)

#         # Save results to the database
#         print("Saving shadow analysis results to the database...")
#         self.save_results_to_db(results)
#         print("Shadow analysis completed.")

#     def prepare_buildings(self):
#         """
#         Fetch building and face details from the database and prepare Building3D objects for pybdshadow.
#         """
#         buildings = []
#         for building in Building.objects.prefetch_related('faces__centroids'):
#             faces = []
#             for face in building.faces.all():
#                 face_centroids = [
#                     {"id": centroid.id, "coordinates": (centroid.centroid.x, centroid.centroid.y, centroid.centroid.z)}
#                     for centroid in face.centroids.all()
#                 ]
#                 faces.append({
#                     "id": face.id,
#                     "geometry": face.geometry.coords[0],  # Extracting Polygon coordinates
#                     "orientation": face.orientation,
#                     "tilt": face.tilt,
#                     "centroids": face_centroids
#                 })
#             buildings.append(Building3D(building_id=building.id, faces=faces))
#         return buildings

#     def perform_shadow_analysis(self, buildings, date_time, interval_minutes):
#         """
#         Perform shadow analysis using pybdshadow.
#         """
#         shadow_calculator = ShadowCalculator(buildings)
#         results = []

#         # Iterate through each time interval in the day
#         current_time = datetime(date_time.year, date_time.month, date_time.day, 6, 0)
#         while current_time.hour < 18:
#             print(f"Analyzing shadows at {current_time.strftime('%H:%M')}...")
#             shadow_data = shadow_calculator.compute_shadows(current_time)

#             # Process shadow data for saving
#             for building_id, face_data in shadow_data.items():
#                 for face_id, centroids in face_data.items():
#                     for centroid_id, is_shadowed in centroids.items():
#                         results.append({
#                             'centroid_id': centroid_id,
#                             'month': current_time.month,
#                             'hour': current_time.hour,
#                             'shadow_status': is_shadowed
#                         })

#             current_time += timedelta(minutes=interval_minutes)

#         return results

#     def save_results_to_db(self, results):
#         rows_processed = 0
#         errors = 0

#         for result in results:
#             try:
#                 # Find the centroid
#                 centroid = VirtualGridCentroid.objects.get(id=result['centroid_id'])

#                 # Create or update the shadow analysis entry
#                 ShadowAnalysis.objects.update_or_create(
#                     centroid=centroid,
#                     month=result['month'],
#                     hour=result['hour'],
#                     defaults={'shadow': bool(result['shadow_status'])}
#                 )
#                 rows_processed += 1
#                 print(f"Saved shadow analysis for centroid ID {result['centroid_id']} at hour {result['hour']}.")
#             except Exception as e:
#                 self.stderr.write(f"Error processing result: {result}. Error: {e}")
#                 errors += 1

#         print(f"\nSummary:")
#         print(f"  Rows processed: {rows_processed}")
#         print(f"  Errors: {errors}")

'''shadow analysis using pybdshadow for all building'''
# from datetime import datetime, timedelta
# from multiprocessing import Pool
# from django.core.management.base import BaseCommand
# from pybdshadow import ShadowCalculator, Building3D
# from city_3D.models import Building, BuildingFace, VirtualGridCentroid, ShadowAnalysis


# class Command(BaseCommand):
#     help = "Perform shadow analysis for all centroids and store results in the database"

#     def handle(self, *args, **kwargs):
#         print("Starting shadow analysis...")

#         # Specify the date and time interval
#         date_time = datetime(2023, 8, 15)  # Specific date for shadow analysis
#         interval_minutes = 60  # 1-hour interval
#         batch_size = 500  # Number of buildings to process in each batch
#         num_workers = 4  # Number of parallel workers

#         print(f"Analyzing shadows for date: {date_time.strftime('%Y-%m-%d')} at {interval_minutes}-minute intervals.")
#         total_buildings = Building.objects.count()
#         print(f"Total buildings to process: {total_buildings}")

#         # Divide buildings into batches
#         building_batches = self.get_building_batches(batch_size)

#         # Perform shadow analysis in parallel
#         print(f"Processing in parallel with {num_workers} workers...")
#         with Pool(processes=num_workers) as pool:
#             all_results = pool.map(
#                 self.process_batch,
#                 [(batch, date_time, interval_minutes) for batch in building_batches]
#             )

#         # Flatten results and save to database
#         results = [result for batch_results in all_results for result in batch_results]
#         print(f"Saving {len(results)} shadow analysis results to the database...")
#         self.save_results_to_db(results)
#         print("Shadow analysis completed.")

#     def get_building_batches(self, batch_size):
#         """
#         Divide buildings into batches for processing.
#         """
#         total_buildings = Building.objects.count()
#         batches = []
#         for batch_start in range(0, total_buildings, batch_size):
#             batch = Building.objects.prefetch_related('faces__centroids')[
#                 batch_start:batch_start + batch_size
#             ]
#             batches.append(batch)
#         return batches

#     def process_batch(self, args):
#         """
#         Process a single batch of buildings.
#         """
#         batch, date_time, interval_minutes = args
#         buildings = self.prepare_buildings(batch)
#         return self.perform_shadow_analysis(buildings, date_time, interval_minutes)

#     def prepare_buildings(self, batch):
#         """
#         Prepare Building3D objects for pybdshadow from the database batch.
#         """
#         buildings = []
#         for building in batch:
#             faces = []
#             for face in building.faces.all():
#                 face_centroids = [
#                     {"id": centroid.id, "coordinates": (centroid.centroid.x, centroid.centroid.y, centroid.centroid.z)}
#                     for centroid in face.centroids.all()
#                 ]
#                 faces.append({
#                     "id": face.id,
#                     "geometry": face.geometry.coords[0],  # Extracting Polygon coordinates
#                     "orientation": face.orientation,
#                     "tilt": face.tilt,
#                     "centroids": face_centroids
#                 })
#             buildings.append(Building3D(building_id=building.id, faces=faces))
#         return buildings

#     def perform_shadow_analysis(self, buildings, date_time, interval_minutes):
#         """
#         Perform shadow analysis using pybdshadow.
#         """
#         shadow_calculator = ShadowCalculator(buildings)
#         results = []

#         # Iterate through each time interval in the day
#         current_time = datetime(date_time.year, date_time.month, date_time.day, 6, 0)
#         while current_time.hour < 18:
#             shadow_data = shadow_calculator.compute_shadows(current_time)

#             # Process shadow data for saving
#             for building_id, face_data in shadow_data.items():
#                 for face_id, centroids in face_data.items():
#                     for centroid_id, is_shadowed in centroids.items():
#                         results.append({
#                             'centroid_id': centroid_id,
#                             'month': current_time.month,
#                             'hour': current_time.hour,
#                             'shadow_status': is_shadowed
#                         })

#             current_time += timedelta(minutes=interval_minutes)

#         return results

#     def save_results_to_db(self, results):
#         """
#         Save shadow analysis results to the database using bulk_create.
#         """
#         shadow_entries = [
#             ShadowAnalysis(
#                 centroid_id=result['centroid_id'],
#                 month=result['month'],
#                 hour=result['hour'],
#                 shadow=bool(result['shadow_status'])
#             )
#             for result in results
#         ]

#         # Perform bulk create for efficiency
#         ShadowAnalysis.objects.bulk_create(shadow_entries, batch_size=1000)

'''shadow analysis using pybdshadow for first 10 buildings'''

# from datetime import datetime, timedelta
# from django.core.management.base import BaseCommand
# from pybdshadow.analysis import cal_sunshadows
# from pybdshadow.preprocess import bd_preprocess
# from shapely.geometry import Polygon
# import geopandas as gpd
# import pandas as pd
# from city_3D.models import Building, BuildingFace, VirtualGridCentroid, ShadowAnalysis


# class Command(BaseCommand):
#     help = "Perform shadow analysis for all buildings but store results only for centroids of the first 10 buildings."

#     def handle(self, *args, **kwargs):
#         print("Starting shadow analysis...")

#         # Specify the date and time interval
#         date_time = datetime(2023, 12, 15)  # Specific date for shadow analysis
#         interval_minutes = 3600  # 1-hour interval in seconds
#         cityname = "Ahmedabad"  # Replace with your city name

#         print(f"Analyzing shadows for date: {date_time.strftime('%Y-%m-%d')} at {interval_minutes // 60}-minute intervals.")

#         # Fetch and preprocess building data
#         print("Fetching and preprocessing building data...")
#         buildings_gdf = self.fetch_and_preprocess_building_data()

#         # Get centroids for the first 10 buildings
#         first_10_centroids = self.get_first_10_centroids()

#         # Perform shadow analysis
#         results = self.perform_shadow_analysis(
#             buildings_gdf, date_time, interval_minutes, first_10_centroids, cityname
#         )

#         # Save results to the database
#         print("Saving shadow analysis results to the database...")
#         self.save_results_to_db(results)
#         print("Shadow analysis completed.")

#     def fetch_and_preprocess_building_data(self):
#         """
#         Fetch building and face data from the database, convert it to GeoDataFrame,
#         and preprocess it using bd_preprocess. Ensure valid WGS84 CRS.
#         """
#         building_data = []

#         # Fetch building and face data
#         for building in Building.objects.prefetch_related('faces'):
#             for face in building.faces.all():
#                 building_data.append({
#                     "geometry": Polygon(face.geometry.coords[0]),  # Convert face geometry to Polygon
#                     "height": building.height,
#                 })

#         # Create GeoDataFrame with original CRS
#         buildings_gdf = gpd.GeoDataFrame(building_data, crs="EPSG:32643")  # Replace EPSG:32643 with your CRS
#         print("Original CRS:", buildings_gdf.crs)

#         # Transform to WGS84
#         buildings_gdf = buildings_gdf.to_crs(epsg=4326)
#         print("Transformed CRS:", buildings_gdf.crs)

#         # Validate and fix geometries
#         buildings_gdf = buildings_gdf[buildings_gdf.is_valid]  # Filter invalid geometries
#         buildings_gdf['geometry'] = buildings_gdf['geometry'].buffer(0)  # Fix invalid geometries

#         # Reduce dataset for debugging
#         buildings_gdf = buildings_gdf.head(10)  # Limit to first 10 buildings

#         # Preprocess buildings using bd_preprocess
#         return bd_preprocess(buildings_gdf, height='height')



#     def get_first_10_centroids(self):
#         """
#         Fetch centroids for the first 10 buildings.
#         """
#         centroids = []
#         first_10_buildings = Building.objects.prefetch_related('faces__centroids')[:10]
#         for building in first_10_buildings:
#             for face in building.faces.all():
#                 for centroid in face.centroids.all():
#                     centroids.append({"id": centroid.id, "coordinates": centroid.centroid})
#         return centroids

#     def perform_shadow_analysis(self, buildings_gdf, date_time, precision, centroids_to_store, cityname):
#         """
#         Perform shadow analysis using pybdshadow's cal_sunshadows.
#         """
#         results = []

#         print(f"Calculating shadows for {cityname} on {date_time.strftime('%Y-%m-%d')}...")

#         shadow_data = cal_sunshadows(
#             buildings=buildings_gdf,
#             cityname=cityname,
#             dates=[date_time.strftime('%Y-%m-%d')],
#             precision=precision,
#             save_shadows=False  # Skip saving files to disk
#         )

#         # Process shadow data
#         for _, shadow in shadow_data.iterrows():
#             for centroid in centroids_to_store:
#                 if shadow["geometry"].contains(centroid["coordinates"]):  # Adjust based on shadow data structure
#                     results.append({
#                         "centroid_id": centroid["id"],
#                         "month": date_time.month,
#                         "hour": shadow["datetime"].hour,
#                         "shadow_status": True,  # Assuming the presence of shadow
#                     })

#         return results

#     def save_results_to_db(self, results):
#         """
#         Save shadow analysis results to the database using bulk_create.
#         """
#         shadow_entries = [
#             ShadowAnalysis(
#                 centroid_id=result['centroid_id'],
#                 month=result['month'],
#                 hour=result['hour'],
#                 shadow=bool(result['shadow_status'])
#             )
#             for result in results
#         ]

#         # Perform bulk create for efficiency
#         ShadowAnalysis.objects.bulk_create(shadow_entries, batch_size=1000)
'''skipping'''
# from datetime import datetime, timedelta
# from django.core.management.base import BaseCommand
# from pybdshadow.analysis import cal_sunshadows
# from pybdshadow.preprocess import bd_preprocess
# from shapely.geometry import Polygon, shape, Point
# import geopandas as gpd
# import pandas as pd
# from city_3D.models import Building, BuildingFace, VirtualGridCentroid, ShadowAnalysis


# class Command(BaseCommand):
#     help = "Perform shadow analysis for all buildings but store results only for centroids of the first 10 buildings."

#     def handle(self, *args, **kwargs):
#         print("Starting shadow analysis...")

#         # Specify the date and time interval
#         date_time = datetime(2023, 12, 15)  # Specific date for shadow analysis
#         interval_minutes = 3600  # 1-hour interval in seconds
#         cityname = "Ahmedabad"  # Replace with your city name

#         print(f"Analyzing shadows for date: {date_time.strftime('%Y-%m-%d')} at {interval_minutes // 60}-minute intervals.")

#         # Fetch and preprocess building data
#         print("Fetching and preprocessing building data...")
#         buildings_gdf = self.fetch_and_preprocess_building_data()

#         # Get centroids for the first 10 buildings
#         first_10_centroids = self.get_first_10_centroids()

#         # Perform shadow analysis
#         results = self.perform_shadow_analysis(
#             buildings_gdf, date_time, interval_minutes, first_10_centroids, cityname
#         )

#         # Save results to the database
#         print("Saving shadow analysis results to the database...")
#         self.save_results_to_db(results)
#         print("Shadow analysis completed.")

#     def fetch_and_preprocess_building_data(self):
#         """
#         Fetch building and face data from the database, convert it to GeoDataFrame,
#         and preprocess it using bd_preprocess. Ensure valid WGS84 CRS.
#         """
#         building_data = []

#         # Fetch building and face data
#         for building in Building.objects.prefetch_related('faces'):
#             for face in building.faces.all():
#                 building_data.append({
#                     "geometry": Polygon(face.geometry.coords[0]),  # Convert face geometry to Polygon
#                     "height": building.height,
#                 })

#         # Create GeoDataFrame with original CRS
#         buildings_gdf = gpd.GeoDataFrame(building_data, crs="EPSG:32643")  # Replace EPSG:32643 with your CRS
#         print("Original CRS:", buildings_gdf.crs)

#         # Transform to WGS84
#         buildings_gdf = buildings_gdf.to_crs(epsg=4326)
#         print("Transformed CRS:", buildings_gdf.crs)

#         # Validate and fix geometries
#         buildings_gdf = buildings_gdf[buildings_gdf.is_valid]  # Filter invalid geometries
#         buildings_gdf['geometry'] = buildings_gdf['geometry'].buffer(0)  # Fix invalid geometries

#         # Reduce dataset for debugging
#         buildings_gdf = buildings_gdf.head(10)  # Limit to first 10 buildings for testing

#         # Preprocess buildings using bd_preprocess
#         return bd_preprocess(buildings_gdf, height='height')

#     def get_first_10_centroids(self):
#         """
#         Fetch centroids for the first 10 buildings.
#         """
#         centroids = []
#         first_10_buildings = Building.objects.prefetch_related('faces__centroids')[:10]
#         for building in first_10_buildings:
#             for face in building.faces.all():
#                 for centroid in face.centroids.all():
#                     centroids.append({"id": centroid.id, "coordinates": centroid.centroid})
#         return centroids

#     def perform_shadow_analysis(self, buildings_gdf, date_time, precision, centroids_to_store, cityname):
#         """
#         Perform shadow analysis using pybdshadow's cal_sunshadows.
#         """
#         results = []

#         print(f"Calculating shadows for {cityname} on {date_time.strftime('%Y-%m-%d')}...")

#         shadow_data = cal_sunshadows(
#             buildings=buildings_gdf,
#             cityname=cityname,
#             dates=[date_time.strftime('%Y-%m-%d')],
#             precision=precision,
#             save_shadows=False  # Skip saving files to disk
#         )

#         # Process shadow data
#         for _, shadow in shadow_data.iterrows():
#             shadow_geometry = shadow["geometry"]
#             if not isinstance(shadow_geometry, Polygon):
#                 try:
#                     shadow_geometry = shape(shadow_geometry)  # Convert to Shapely geometry
#                 except Exception as e:
#                     print(f"Invalid shadow geometry: {shadow_geometry}, error: {e}")
#                     continue

#             for centroid in centroids_to_store:
#                 centroid_point = centroid["coordinates"]
#                 if not isinstance(centroid_point, Point):
#                     centroid_point = Point(centroid_point)  # Convert to Point

#                 # Check if centroid is within the shadow
#                 if shadow_geometry.contains(centroid_point):
#                     results.append({
#                         "centroid_id": centroid["id"],
#                         "month": date_time.month,
#                         "hour": shadow["datetime"].hour,
#                         "shadow_status": True,  # Assuming the presence of shadow
#                     })

#         return results

#     def save_results_to_db(self, results):
#         """
#         Save shadow analysis results to the database using bulk_create.
#         """
#         shadow_entries = [
#             ShadowAnalysis(
#                 centroid_id=result['centroid_id'],
#                 month=result['month'],
#                 hour=result['hour'],
#                 shadow=bool(result['shadow_status'])
#             )
#             for result in results
#         ]

#         # Perform bulk create for efficiency
#         ShadowAnalysis.objects.bulk_create(shadow_entries, batch_size=1000)

'''using data from geojson file'''
from datetime import datetime
from django.core.management.base import BaseCommand
from pybdshadow.analysis import cal_sunshadows
from pybdshadow.preprocess import bd_preprocess
from shapely.geometry import shape, Point
import geopandas as gpd
import json
from city_3D.models import ShadowAnalysis


class Command(BaseCommand):
    help = "Perform shadow analysis for all buildings using GeoJSON data but store results only for centroids of the first 10 buildings."

    def handle(self, *args, **kwargs):
        print("Starting shadow analysis...")

        # Specify the date and time interval
        date_time = datetime(2023, 12, 15)  # Specific date for shadow analysis
        interval_minutes = 3600  # 1-hour interval in seconds
        cityname = "Ahmedabad"  # Replace with your city name
        geojson_file = "buildings_with_centroids_id.geojson"  # Path to your GeoJSON file

        print(f"Analyzing shadows for date: {date_time.strftime('%Y-%m-%d')} at {interval_minutes // 60}-minute intervals.")
        print(f"Loading GeoJSON file: {geojson_file}")

        # Load GeoJSON data
        geojson_data = self.load_geojson(geojson_file)

        # Fetch and preprocess building data
        print("Fetching and preprocessing building data from GeoJSON...")
        buildings_gdf = self.preprocess_geojson_buildings(geojson_data)

        # Get centroids for the first 10 buildings
        first_10_centroids = self.get_first_10_centroids(geojson_data)

        # Perform shadow analysis
        results = self.perform_shadow_analysis(
            buildings_gdf, date_time, interval_minutes, first_10_centroids, cityname
        )

        # Save results to the database
        print("Saving shadow analysis results to the database...")
        self.save_results_to_db(results)
        print("Shadow analysis completed.")

    def load_geojson(self, file_path):
        """
        Load GeoJSON file.
        """
        with open(file_path, 'r') as file:
            return json.load(file)

    def preprocess_geojson_buildings(self, geojson_data):
        """
        Convert GeoJSON data to GeoDataFrame and preprocess it.
        """
        # Extract buildings and their geometries
        building_features = geojson_data['features']
        building_data = [
            {"geometry": shape(feature['geometry']), "height": feature['properties'].get('height', 0)}
            for feature in building_features
        ]

        # Create GeoDataFrame
        buildings_gdf = gpd.GeoDataFrame(building_data, crs="EPSG:4326")  # GeoJSON is assumed to be in WGS84 CRS

        # Validate and fix geometries
        buildings_gdf = buildings_gdf[buildings_gdf.is_valid]  # Remove invalid geometries
        buildings_gdf['geometry'] = buildings_gdf['geometry'].buffer(0)  # Fix minor geometry issues

        # Preprocess buildings using bd_preprocess
        buildings_gdf = bd_preprocess(buildings_gdf, height='height')

        # Ensure CRS is explicitly set
        buildings_gdf.crs = "EPSG:4326"

        return buildings_gdf

    def get_first_10_centroids(self, geojson_data):
        """
        Extract centroids for the first 10 buildings.
        """
        centroids = []
        for feature in geojson_data['features'][:10]:  # Limit to first 10 buildings
            building_id = feature['properties'].get('building_id')
            for centroid in feature['properties'].get('centroids', []):
                centroids.append({
                    "id": centroid['id'],
                    "coordinates": Point(centroid['coordinates'][:2]),  # Use only lat/lon (ignore height)
                    "building_id": building_id,
                })
        return centroids

    def perform_shadow_analysis(self, buildings_gdf, date_time, precision, centroids_to_store, cityname):
        """
        Perform shadow analysis using pybdshadow's cal_sunshadows.
        """
        results = []

        print(f"Calculating shadows for {cityname} on {date_time.strftime('%Y-%m-%d')}...")

        try:
            shadow_data = cal_sunshadows(
                buildings=buildings_gdf,
                cityname=cityname,
                dates=[date_time.strftime('%Y-%m-%d')],
                precision=precision,
                save_shadows=False  # Skip saving files to disk
            )
        except Exception as e:
            print(f"Error during shadow analysis: {e}")
            return results

        # Process shadow data
        for _, shadow in shadow_data.iterrows():
            for centroid in centroids_to_store:
                shadow_geometry = shadow.get("geometry")
                centroid_point = centroid["coordinates"]

                if shadow_geometry and shadow_geometry.contains(centroid_point):
                    results.append({
                        "centroid_id": centroid["id"],
                        "month": date_time.month,
                        "hour": shadow["datetime"].hour,
                        "shadow_status": True,  # Assuming the presence of shadow
                    })

        return results

    def save_results_to_db(self, results):
        """
        Save shadow analysis results to the database using bulk_create.
        """
        shadow_entries = [
            ShadowAnalysis(
                centroid_id=result['centroid_id'],
                month=result['month'],
                hour=result['hour'],
                shadow=bool(result['shadow_status'])
            )
            for result in results
        ]

        # Perform bulk create for efficiency
        ShadowAnalysis.objects.bulk_create(shadow_entries, batch_size=1000)
