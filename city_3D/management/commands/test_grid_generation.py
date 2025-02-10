'''successful grid formation'''
from django.core.management.base import BaseCommand
from django.db import transaction
from city_3D.models import Building, BuildingFace, Grid
from django.contrib.gis.geos import Polygon
import json

import os

# Set the PROJ_LIB path for pyproj or GDAL only in this Python process
os.environ['PROJ_LIB'] = r'C:\Users\HP\AppData\Local\Programs\Python\Python312\Lib\site-packages\pyproj\proj_dir\share\proj'
os.environ['GDAL_DATA'] = r'C:\Users\HP\AppData\Local\Programs\Python\Python312\Lib\site-packages\pyproj\proj_dir\share\proj'

class Command(BaseCommand):
    help = "Generate grids for Building ID: 3 with detailed debugging."

    def handle(self, *args, **kwargs):
        building_id = 3  # Target Building ID
        self.clear_existing_grids()
        self.generate_grids_for_building(building_id)

    def clear_existing_grids(self):
        """Delete all grids in the database to ensure a fresh start."""
        deleted_count = Grid.objects.all().delete()
        print(f"Cleared {deleted_count[0]} existing grids from the database.")

    def generate_grids_for_building(self, building_id):
        """Generate grids for the specified building."""
        try:
            building = Building.objects.get(id=building_id)
        except Building.DoesNotExist:
            print(f"Building with ID {building_id} does not exist.")
            return

        print(f"Generating grids for Building ID: {building_id}")
        faces = BuildingFace.objects.filter(building=building)

        if not faces.exists():
            print(f"No faces found for Building ID: {building_id}")
            return

        # Initialize GeoJSON structure for export
        geojson_data = {
            "type": "FeatureCollection",
            "features": []
        }

        total_grids = 0
        for face in faces:
            print(f"Processing Face ID: {face.id}, Orientation: {face.orientation}, Tilt: {face.tilt}")

            # Get face bounding box dimensions
            bounds = face.geometry.extent
            xmin, ymin, xmax, ymax = bounds
            z_min = 0  # Base height
            z_max = face.geometry.coords[0][0][2] if face.geometry.hasz else 0

            # Calculate grid step
            grid_size = 1.0  # 1-meter square grids
            x_steps = int((xmax - xmin) // grid_size)
            y_steps = int((ymax - ymin) // grid_size)

            grids = []
            for i in range(x_steps):
                for j in range(y_steps):
                    grid_xmin = xmin + (i * grid_size)
                    grid_xmax = grid_xmin + grid_size
                    grid_ymin = ymin + (j * grid_size)
                    grid_ymax = grid_ymin + grid_size

                    # Handle vertical and horizontal face differences
                    if face.tilt == 90.0:  # Vertical surfaces
                        grid_coords = [
                            (grid_xmin, grid_ymin, z_min),
                            (grid_xmax, grid_ymin, z_min),
                            (grid_xmax, grid_ymax, z_max),
                            (grid_xmin, grid_ymax, z_max),
                            (grid_xmin, grid_ymin, z_min)
                        ]
                    else:  # Horizontal surfaces (roof)
                        grid_coords = [
                            (grid_xmin, grid_ymin, z_max),
                            (grid_xmax, grid_ymin, z_max),
                            (grid_xmax, grid_ymax, z_max),
                            (grid_xmin, grid_ymax, z_max),
                            (grid_xmin, grid_ymin, z_max)
                        ]

                    try:
                        grid_geometry = Polygon(grid_coords)
                    except Exception as e:
                        print(f"    Error creating grid polygon for Face ID {face.id}: {e}")
                        continue

                    # Create Grid object
                    grids.append(Grid(
                        face=face,
                        geometry=grid_geometry,
                        x_position=i,
                        y_position=j,
                        solar_potential=0.0,  # Default placeholder
                        is_in_shadow=False
                    ))

            # Save grids for this face
            with transaction.atomic():
                Grid.objects.bulk_create(grids)
            print(f"  Total Grids Created for Face ID {face.id}: {len(grids)}")
            total_grids += len(grids)

            # Add grids to GeoJSON
            for grid in grids:
                geojson_data["features"].append({
                    "type": "Feature",
                    "properties": {
                        "face_id": face.id,
                        "x_position": grid.x_position,
                        "y_position": grid.y_position,
                        "solar_potential": grid.solar_potential,
                        "is_in_shadow": grid.is_in_shadow
                    },
                    "geometry": json.loads(grid.geometry.geojson)
                })

        # Summary
        print("\n==== Grid Generation Summary ====")
        print(f"Total Faces Processed: {faces.count()}")
        print(f"Total Grids Generated: {total_grids}")
        print("=================================\n")

        # Export to GeoJSON
        output_path = f"building_{building_id}_grids.geojson"
        with open(output_path, "w") as geojson_file:
            json.dump(geojson_data, geojson_file, indent=4)
        print(f"GeoJSON saved to {output_path}. Use QGIS or similar tools to visualize the grid alignment.")

'''optimization and debugging'''
# from django.core.management.base import BaseCommand
# from django.db import transaction
# from city_3D.models import Building, BuildingFace, Grid
# from django.contrib.gis.geos import Polygon
# import json
# import os

# # Set the PROJ_LIB path for pyproj or GDAL only in this Python process
# os.environ['PROJ_LIB'] = r'C:\Users\HP\AppData\Local\Programs\Python\Python312\Lib\site-packages\pyproj\proj_dir\share\proj'
# os.environ['GDAL_DATA'] = r'C:\Users\HP\AppData\Local\Programs\Python\Python312\Lib\site-packages\pyproj\proj_dir\share\proj'


# class Command(BaseCommand):
#     help = "Generate grids for a specific building with detailed debugging."

#     def handle(self, *args, **kwargs):
#         building_id = 3  # Target Building ID
#         self.clear_existing_grids()
#         self.generate_grids_for_building(building_id)

#     def clear_existing_grids(self):
#         """Delete all grids in the database to ensure a fresh start."""
#         deleted_count = Grid.objects.all().delete()
#         print(f"Cleared {deleted_count[0]} existing grids from the database.")

#     def generate_grids_for_building(self, building_id):
#         """Generate grids for the specified building."""
#         try:
#             building = Building.objects.get(id=building_id)
#         except Building.DoesNotExist:
#             print(f"Building with ID {building_id} does not exist.")
#             return

#         print(f"Generating grids for Building ID: {building_id}")
#         faces = BuildingFace.objects.filter(building=building)

#         if not faces.exists():
#             print(f"No faces found for Building ID: {building_id}")
#             return

#         # Initialize GeoJSON structure for export
#         geojson_data = {
#             "type": "FeatureCollection",
#             "features": []
#         }

#         total_grids = 0
#         for face in faces:
#             print(f"\nProcessing Face ID: {face.id}, Orientation: {face.orientation}, Tilt: {face.tilt}")

#             face_geometry = face.geometry
#             if not face_geometry.valid:
#                 print(f"  Error: Face {face.id} has invalid geometry. Skipping.")
#                 continue

#             # Calculate grid size and bounds
#             grid_size = 1.0  # 1-meter square grids
#             bounds = face_geometry.extent
#             xmin, ymin, xmax, ymax = bounds
#             z_min = 0  # Base height
#             z_max = face.building.height if face.tilt == 90.0 else face_geometry.coords[0][0][2]

#             x_steps = int((xmax - xmin) // grid_size)
#             y_steps = int((ymax - ymin) // grid_size)

#             grids = []
#             for i in range(x_steps):
#                 for j in range(y_steps):
#                     grid_xmin = xmin + (i * grid_size)
#                     grid_xmax = grid_xmin + grid_size
#                     grid_ymin = ymin + (j * grid_size)
#                     grid_ymax = grid_ymin + grid_size

#                     # Define grid coordinates
#                     if face.tilt == 90.0:  # Vertical surfaces
#                         grid_coords = [
#                             (grid_xmin, grid_ymin, z_min),
#                             (grid_xmax, grid_ymin, z_min),
#                             (grid_xmax, grid_ymax, z_max),
#                             (grid_xmin, grid_ymax, z_max),
#                             (grid_xmin, grid_ymin, z_min)
#                         ]
#                     else:  # Horizontal surfaces (roof)
#                         grid_coords = [
#                             (grid_xmin, grid_ymin, z_max),
#                             (grid_xmax, grid_ymin, z_max),
#                             (grid_xmax, grid_ymax, z_max),
#                             (grid_xmin, grid_ymax, z_max),
#                             (grid_xmin, grid_ymin, z_max)
#                         ]

#                     try:
#                         grid_geometry = Polygon(grid_coords)
#                         if not face_geometry.contains(grid_geometry):
#                             print(f"    Warning: Grid at ({i}, {j}) lies outside the face geometry.")
#                             continue
#                     except Exception as e:
#                         print(f"    Error creating grid polygon for Face ID {face.id}: {e}")
#                         continue

#                     # Add grid to list
#                     grids.append(Grid(
#                         face=face,
#                         geometry=grid_geometry,
#                         x_position=i,
#                         y_position=j,
#                         solar_potential=0.0,  # Default placeholder
#                         is_in_shadow=False
#                     ))

#             # Save grids for this face
#             with transaction.atomic():
#                 Grid.objects.bulk_create(grids)
#             print(f"  Total Grids Created for Face ID {face.id}: {len(grids)}")
#             total_grids += len(grids)

#             # Add grids to GeoJSON
#             for grid in grids:
#                 geojson_data["features"].append({
#                     "type": "Feature",
#                     "properties": {
#                         "face_id": face.id,
#                         "x_position": grid.x_position,
#                         "y_position": grid.y_position,
#                         "solar_potential": grid.solar_potential,
#                         "is_in_shadow": grid.is_in_shadow
#                     },
#                     "geometry": json.loads(grid.geometry.geojson)
#                 })

#         # Summary
#         print("\n==== Grid Generation Summary ====")
#         print(f"Total Faces Processed: {faces.count()}")
#         print(f"Total Grids Generated: {total_grids}")
#         print("=================================\n")

#         # Export to GeoJSON
#         output_path = f"building_{building_id}_grids.geojson"
#         with open(output_path, "w") as geojson_file:
#             json.dump(geojson_data, geojson_file, indent=4)
#         print(f"GeoJSON saved to {output_path}. Use QGIS or similar tools to visualize the grid alignment.")
