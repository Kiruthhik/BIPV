# import os
# import geopandas as gpd
# from shapely.geometry import MultiPolygon, Polygon
# from django.contrib.gis.geos import GEOSGeometry
# from django.core.management.base import BaseCommand
# from city_3D.models import Building

# class Command(BaseCommand):
#     help = "Load building data from a shapefile into the Building model"

#     def add_arguments(self, parser):
#         parser.add_argument(
#             '--shapefile',
#             type=str,
#             required=True,
#             help="Path to the shapefile to be loaded"
#         )

#     def handle(self, *args, **options):
#         shapefile_path = options['shapefile']

#         # Step 1: Load the shapefile
#         print(f"Loading shapefile from: {shapefile_path}")
#         try:
#             gdf = gpd.read_file(shapefile_path)
#         except Exception as e:
#             print(f"Error reading shapefile: {e}")
#             return

#         # Step 2: Clean invalid geometries
#         print("Cleaning invalid geometries...")
#         gdf = gdf[gdf.is_valid]  # Remove invalid geometries
#         gdf = gdf[gdf.geometry.notnull()]  # Remove rows with empty geometry

#         # Reproject to WGS84 (EPSG:4326), if needed
#         if gdf.crs != "EPSG:4326":
#             print(f"Reprojecting from {gdf.crs} to EPSG:4326...")
#             try:
#                 gdf = gdf.to_crs("EPSG:4326")
#             except Exception as e:
#                 print(f"Error reprojecting shapefile: {e}")
#                 return

#         # Step 3: Convert Polygons to MultiPolygons and fix invalid geometries
#         def convert_to_geosgeometry(geometry):
#             """
#             Converts Shapely geometry to Django-compatible GEOSGeometry.
#             Handles both Polygon and MultiPolygon types.
#             """
#             try:
#                 # Fix invalid geometries with buffer(0)
#                 if not geometry.is_valid:
#                     print(f"Fixing invalid geometry: {geometry}")
#                     geometry = geometry.buffer(0)  # Fix common issues

#                 # Convert Polygon to MultiPolygon, if needed
#                 if geometry.geom_type == "Polygon":
#                     geometry = MultiPolygon([geometry])

#                 # Convert Shapely geometry to GEOSGeometry using WKB
#                 geos_geometry = GEOSGeometry(memoryview(geometry.wkb))  # Use WKB directly

#                 # Validate the converted geometry
#                 if not geos_geometry.valid:
#                     print("Converted GEOSGeometry is still invalid.")
#                     return None

#                 return geos_geometry
#             except Exception as e:
#                 print(f"Error during geometry conversion: {e}")
#                 return None

#         print("Converting Polygons and MultiPolygons to GEOSGeometry...")
#         gdf['geometry'] = gdf['geometry'].apply(convert_to_geosgeometry)

#         # Drop rows with invalid geometries after conversion
#         gdf = gdf[gdf.geometry.notnull()]

#         # Counters for logging
#         total_count = len(gdf)
#         saved_count = 0
#         skipped_count = 0
#         skipped_due_to_invalid_geometry = 0
#         skipped_due_to_missing_height = 0

#         # Step 4: Load data into the database
#         print("Loading data into the database...")
#         for index, row in gdf.iterrows():
#             try:
#                 # Debug geometry type and validity
#                 print(f"Index: {index}, Geometry Type: {type(row.geometry)}")

#                 # Ensure the geometry is a GEOSGeometry object
#                 if not isinstance(row.geometry, GEOSGeometry):
#                     print(f"Skipping invalid geometry at index {index}: Not a GEOSGeometry object")
#                     skipped_due_to_invalid_geometry += 1
#                     skipped_count += 1
#                     continue

#                 # Validate geometry before saving
#                 if not row.geometry.valid or row.geometry.empty:
#                     print(f"Skipping invalid or empty geometry at index {index}")
#                     skipped_due_to_invalid_geometry += 1
#                     skipped_count += 1
#                     continue

#                 # Check for missing height
#                 if 'height' not in row or row['height'] is None:
#                     print(f"Skipping building at index {index}: Missing height")
#                     skipped_due_to_missing_height += 1
#                     skipped_count += 1
#                     continue

#                 # Save each building to the database
#                 building = Building(
#                     height=row['height'],  # Replace with the correct field name in your shapefile
#                     geometry=row.geometry
#                 )
#                 building.save()
#                 saved_count += 1
#                 print(f"Saved building at index {index}")
#             except Exception as e:
#                 print(f"Error saving building at index {index}: {e}")
#                 skipped_count += 1

#         # Summary
#         print("\n==== Summary ====")
#         print(f"Total Buildings in Shapefile: {total_count}")
#         print(f"Successfully Saved Buildings: {saved_count}")
#         print(f"Total Skipped Buildings: {skipped_count}")
#         print(f"Skipped Due to Invalid Geometry: {skipped_due_to_invalid_geometry}")
#         print(f"Skipped Due to Missing Height: {skipped_due_to_missing_height}")
#         print("=================\n")



'''data from geojson file'''

# import os
# import django
# import geopandas as gpd
# from shapely.geometry import MultiPolygon, Polygon
# from shapely.validation import explain_validity
# from django.contrib.gis.geos import GEOSGeometry
# from city_3D.models import Building
# from django.core.management.base import BaseCommand


# class Command(BaseCommand):
#     help = "Load GeoJSON data into the Building model"

#     def handle(self, *args, **kwargs):
#         # Load GeoJSON file
#         try:
#             geojson_path = r"C:\Users\HP\Documents\hackfest\SIH\SIH FINAL\build_kir2.geojson"
#             gdf = gpd.read_file(geojson_path)
#         except Exception as e:
#             print(f"Error loading GeoJSON file: {e}")
#             return

#         # Reproject to EPSG:32643 if needed
#         if gdf.crs != "EPSG:32643":
#             gdf = gdf.to_crs("EPSG:32643")

#         # Validate and fix geometries
#         def fix_geometry(geom):
#             try:
#                 if not geom.is_valid:
#                     print(f"Fixing invalid geometry: {explain_validity(geom)}")
#                     geom = geom.buffer(0)
#                 return geom
#             except Exception as e:
#                 print(f"Error fixing geometry: {e}")
#                 return None

#         gdf['geometry'] = gdf['geometry'].apply(lambda geom: fix_geometry(geom))
#         gdf = gdf[gdf.geometry.notnull()]  # Drop rows with invalid geometries

#         # Load data into the database
#         for index, row in gdf.iterrows():
#             try:
#                 geometry = GEOSGeometry(row.geometry.wkb, srid=32643)
#                 height = row.get('height', None)
#                 if height is None or not isinstance(height, (int, float)):
#                     continue

#                 building = Building(height=height, geometry=geometry)
#                 building.save()
#             except Exception as e:
#                 print(f"Error saving building at index {index}: {e}")

'''debug 5 building'''
import os
import geopandas as gpd
from django.contrib.gis.geos import GEOSGeometry
from city_3D.models import Building
from shapely.validation import explain_validity
from django.core.management.base import BaseCommand
import traceback


class Command(BaseCommand):
    help = "Load GeoJSON data into the Building model for debugging purposes (loads only the first 5 buildings)."

    def handle(self, *args, **kwargs):
        # Step 1: Define the GeoJSON file path
        geojson_path = r"C:\Users\HP\Documents\hackfest\SIH\SIH FINAL\build_kir2.geojson"

        # Step 2: Load and clean the GeoJSON file
        print("Loading GeoJSON file...")
        try:
            gdf = gpd.read_file(geojson_path)
        except Exception as e:
            print(f"Error loading GeoJSON file: {e}")
            traceback.print_exc()
            return

        print("GeoJSON file loaded successfully.")
        print(f"CRS of GeoJSON file: {gdf.crs}")

        # Ensure the CRS is EPSG:32643
        if gdf.crs != "EPSG:32643":
            print(f"Reprojecting from {gdf.crs} to EPSG:32643...")
            try:
                gdf = gdf.to_crs("EPSG:32643")
            except Exception as e:
                print(f"Error reprojecting CRS: {e}")
                traceback.print_exc()
                return

        print("Reprojection successful. CRS is now:", gdf.crs)

        # Step 3: Debug and clean invalid geometries
        print("Cleaning and validating geometries...")
        gdf['validity'] = gdf['geometry'].apply(lambda geom: explain_validity(geom) if not geom.is_valid else "Valid")
        invalid_geometries = gdf[gdf['validity'] != "Valid"]

        if not invalid_geometries.empty:
            print("Found invalid geometries:")
            print(invalid_geometries[['geometry', 'validity']].head())
            print("Fixing invalid geometries using buffer(0)...")
            gdf['geometry'] = gdf['geometry'].apply(lambda geom: geom.buffer(0) if not geom.is_valid else geom)

        # Remove remaining invalid geometries
        gdf = gdf[gdf.geometry.notnull() & gdf.is_valid]

        # Step 4: Limit to the first 5 buildings for debugging
        # print("Limiting to the first 5 buildings for testing...")
        # gdf = gdf.head(5)

        print(f"Number of buildings to process: {len(gdf)}")

        # Step 5: Load data into the database
        print("Loading data into the database...")
        for index, row in gdf.iterrows():
            try:
                print(f"Processing building at index {index}...")
                geometry = GEOSGeometry(row.geometry.wkt, srid=32643)

                # Validate the converted geometry
                if not geometry.valid:
                    print(f"Geometry at index {index} is invalid after conversion.")
                    continue

                # Debugging geometry details
                print(f"Building geometry details (index {index}):")
                print(f"  Type: {geometry.geom_type}")
                print(f"  SRID: {geometry.srid}")
                print(f"  Valid: {geometry.valid}")

                # Save the building to the database
                building = Building(
                    height=row.get('height', None),
                    geometry=geometry
                )
                building.save()
                print(f"Saved building at index {index}.")
            except Exception as e:
                print(f"Error saving building at index {index}: {e}")
                traceback.print_exc()

        print("Debugging complete. Check the database for results.")
