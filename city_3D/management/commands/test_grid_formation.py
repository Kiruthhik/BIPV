# from django.core.management.base import BaseCommand
# from city_3D.models import Building, BuildingFace, Grid
# import json

import os

# Set the PROJ_LIB path for pyproj or GDAL only in this Python process
os.environ['PROJ_LIB'] = r'C:\Users\HP\AppData\Local\Programs\Python\Python312\Lib\site-packages\pyproj\proj_dir\share\proj'
os.environ['GDAL_DATA'] = r'C:\Users\HP\AppData\Local\Programs\Python\Python312\Lib\site-packages\pyproj\proj_dir\share\proj'

# Proceed with your script



# class Command(BaseCommand):
#     help = "Test grid formation for Building ID: 1 and save results to GeoJSON."

#     def handle(self, *args, **kwargs):
#         self.test_grid_formation(building_id=1)

#     def test_grid_formation(self, building_id):
#         # Fetch the building
#         try:
#             building = Building.objects.get(id=building_id)
#         except Building.DoesNotExist:
#             print(f"Building with ID {building_id} does not exist.")
#             return

#         print(f"Testing grid formation for Building ID: {building_id}")
#         faces = BuildingFace.objects.filter(building=building)

#         if not faces.exists():
#             print(f"No faces found for Building ID: {building_id}")
#             return

#         # Initialize GeoJSON structure
#         geojson_data = {
#             "type": "FeatureCollection",
#             "features": []
#         }

#         total_grids = 0

#         for face in faces:
#             print(f"  Face ID: {face.id}, Orientation: {face.orientation}, Tilt: {face.tilt}")
#             grids = Grid.objects.filter(face=face)
#             grid_count = grids.count()

#             if grid_count == 0:
#                 print(f"    No grids found for Face ID: {face.id}")
#                 continue

#             print(f"    Total Grids: {grid_count}")
#             total_grids += grid_count

#             # Add grids to GeoJSON
#             for grid in grids:
#                 try:
#                     feature = {
#                         "type": "Feature",
#                         "properties": {
#                             "face_id": face.id,
#                             "x_position": grid.x_position,
#                             "y_position": grid.y_position,
#                             "solar_potential": grid.solar_potential,
#                             "is_in_shadow": grid.is_in_shadow
#                         },
#                         "geometry": json.loads(grid.geometry.geojson)
#                     }
#                     geojson_data["features"].append(feature)
#                 except Exception as e:
#                     print(f"    Error processing grid ID {grid.id}: {e}")

#         # Summary
#         print("\n==== Summary ====")
#         print(f"Total Faces Processed: {faces.count()}")
#         print(f"Total Grids Processed: {total_grids}")
#         print("=================")

#         # Export to GeoJSON
#         output_path = f"building_{building_id}_grids.geojson"
#         try:
#             with open(output_path, "w") as geojson_file:
#                 json.dump(geojson_data, geojson_file, indent=4)
#             print(f"GeoJSON saved to {output_path}. Use QGIS or similar tools to visualize the grid alignment.")
#         except Exception as e:
#             print(f"Error saving GeoJSON file: {e}")

# 
'''testing building 3 grids mathematically'''
from django.core.management.base import BaseCommand
from city_3D.models import Building, BuildingFace, Grid
from django.contrib.gis.geos import Polygon
from django.contrib.gis.geos.error import GEOSException
import math

class Command(BaseCommand):
    help = "Test and validate grid formation for vertical and roof faces."

    def handle(self, *args, **kwargs):
        self.validate_grids(building_id=3)  # Run validation for Building ID 3

    def validate_grids(self, building_id):
        building_faces = BuildingFace.objects.filter(building_id=building_id)
        if not building_faces.exists():
            print(f"No faces found for Building ID: {building_id}")
            return

        print(f"Validating grids for Building ID: {building_id}")
        total_errors = 0

        for face in building_faces:
            print(f"\nProcessing Face ID: {face.id}, Orientation: {face.orientation}, Tilt: {face.tilt}")
            grids = Grid.objects.filter(face=face)

            if not grids.exists():
                print(f"  No grids found for Face ID: {face.id}")
                continue

            face_geometry = face.geometry
            face_bbox = face_geometry.envelope

            grid_errors = 0
            for grid in grids:
                grid_geometry = grid.geometry

                # 1. Validate grid fits within the face bounding box
                if not face_bbox.contains(grid_geometry):
                    print(f"    Error: Grid {grid.id} lies outside the bounding box of Face {face.id}.")
                    grid_errors += 1

                # 2. Validate grid fits within the face geometry
                if not face_geometry.contains(grid_geometry):
                    print(f"    Error: Grid {grid.id} lies outside the geometry of Face {face.id}.")
                    grid_errors += 1

                # 3. Validate grid dimensions (1m x 1m)
                if not self.validate_grid_dimensions(grid_geometry):
                    print(f"    Error: Grid {grid.id} does not have proper dimensions.")
                    grid_errors += 1

                # 4. Validate Z-coordinates for vertical walls
                if face.tilt == 90:
                    if not self.validate_vertical_grid_z(grid_geometry, face.building.height):
                        print(f"    Error: Grid {grid.id} has incorrect Z-coordinates for a vertical face.")
                        grid_errors += 1

            print(f"  Total Errors for Face {face.id}: {grid_errors}")
            total_errors += grid_errors

        print("\n==== Validation Summary ====")
        print(f"Total Faces Processed: {building_faces.count()}")
        print(f"Total Errors Found: {total_errors}")
        print("=============================")

    def validate_grid_dimensions(self, grid_geometry):
        """Check if a grid cell is approximately 1m x 1m."""
        try:
            coords = grid_geometry.coords[0]
            side_lengths = [
                math.dist(coords[i], coords[i + 1]) for i in range(len(coords) - 1)
            ]
            # A grid should ideally be square (1m x 1m)
            return all(abs(side - 1.0) < 0.1 for side in side_lengths)
        except (IndexError, GEOSException) as e:
            print(f"    Error validating grid dimensions: {e}")
            return False

    def validate_vertical_grid_z(self, grid_geometry, height):
        """Validate Z-coordinates of vertical grids."""
        try:
            coords = grid_geometry.coords[0]
            z_values = [coord[2] for coord in coords]
            return min(z_values) == 0 and max(z_values) == height
        except (IndexError, GEOSException) as e:
            print(f"    Error validating Z-coordinates: {e}")
            return False
