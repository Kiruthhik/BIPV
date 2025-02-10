'''successful'''
# from django.core.management.base import BaseCommand
# from django.contrib.gis.geos import GEOSGeometry
# from city_3D.models import Grid
# import json

# class Command(BaseCommand):
#     help = "Export Grid data to a GeoJSON file for visualization"

#     def handle(self, *args, **kwargs):
#         output_file = "building123_grids.geojson"
#         print(f"Exporting grid data to {output_file}...")

#         # Prepare the GeoJSON structure
#         geojson = {
#             "type": "FeatureCollection",
#             "features": []
#         }

#         # Query grids for the first three buildings
#         grids = Grid.objects.filter(face__building__id__in=[1, 2, 3])
#         if not grids.exists():
#             print("No grid data found for the first three buildings.")
#             return

#         for grid in grids:
#             try:
#                 # Get 3D geometry of the grid
#                 geom = GEOSGeometry(grid.geometry.wkt)
#                 geojson_feature = {
#                     "type": "Feature",
#                     "geometry": json.loads(geom.geojson),
#                     "properties": {
#                         "building_id": grid.face.building.id,
#                         "face_id": grid.face.id,
#                         "x_position": grid.x_position,
#                         "y_position": grid.y_position,
#                         "solar_potential": grid.solar_potential,
#                         "is_in_shadow": grid.is_in_shadow,
#                     }
#                 }
#                 geojson["features"].append(geojson_feature)
#                 print(f"Added Grid ({grid.x_position}, {grid.y_position}) of Face {grid.face.id}.")
#             except Exception as e:
#                 print(f"Error processing Grid {grid.id}: {e}")

#         # Write to file
#         try:
#             with open(output_file, "w", encoding="utf-8") as f:
#                 json.dump(geojson, f, indent=2)
#             print(f"Successfully exported to {output_file}")
#         except Exception as e:
#             print(f"Error writing to file: {e}")

'''including faces details in grid'''
from django.core.management.base import BaseCommand
from django.contrib.gis.geos import GEOSGeometry
from city_3D.models import Grid
import json


class Command(BaseCommand):
    help = "Export Grid data to a GeoJSON file for visualization with additional details"

    def handle(self, *args, **kwargs):
        output_file = "building123_grids_detailed.geojson"
        print(f"Exporting grid data to {output_file}...")

        # Prepare the GeoJSON structure
        geojson = {
            "type": "FeatureCollection",
            "features": []
        }

        # Query grids for the first three buildings
        grids = Grid.objects.filter(face__building__id__in=[1, 2, 3])
        if not grids.exists():
            print("No grid data found for the first three buildings.")
            return

        for grid in grids:
            try:
                # Get 3D geometry of the grid
                geom = GEOSGeometry(grid.geometry.wkt)
                face = grid.face

                # Determine grid type and orientation
                if face.tilt == 90:  # Vertical grids
                    grid_type = "vertical"
                    orientation = face.orientation
                elif face.tilt == 0:  # Horizontal grids (e.g., roofs)
                    grid_type = "horizontal"
                    orientation = None
                else:
                    grid_type = "sloped"
                    orientation = face.orientation

                geojson_feature = {
                    "type": "Feature",
                    "geometry": json.loads(geom.geojson),
                    "properties": {
                        "building_id": face.building.id,
                        "face_id": face.id,
                        "x_position": grid.x_position,
                        "y_position": grid.y_position,
                        "solar_potential": grid.solar_potential,
                        "is_in_shadow": grid.is_in_shadow,
                        "grid_type": grid_type,
                        "orientation": orientation,
                        "tilt": face.tilt,
                    }
                }
                geojson["features"].append(geojson_feature)
                print(f"Added Grid ({grid.x_position}, {grid.y_position}) of Face {face.id}.")
            except Exception as e:
                print(f"Error processing Grid {grid.id}: {e}")

        # Write to file
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(geojson, f, indent=2)
            print(f"Successfully exported to {output_file}")
        except Exception as e:
            print(f"Error writing to file: {e}")
