# from django.core.management.base import BaseCommand
# from city_3D.models import BuildingFace
# from django.contrib.gis.geos import GEOSGeometry
# import json

# class Command(BaseCommand):
#     help = "Export BuildingFace data to a GeoJSON file"

#     def handle(self, *args, **kwargs):
#         output_file = "building3_faces.geojson"
#         print(f"Exporting data to {output_file}...")

#         # Prepare the GeoJSON structure
#         geojson = {
#             "type": "FeatureCollection",
#             "features": []
#         }

#         # Iterate through all BuildingFace objects
#         for face in BuildingFace.objects.filter(building_id=3):
#             try:
#                 # Convert geometry to GeoJSON format
#                 geom = GEOSGeometry(face.geometry.wkt)
#                 geojson_feature = {
#                     "type": "Feature",
#                     "geometry": json.loads(geom.geojson),
#                     "properties": {
#                         "building_id": face.building.id,
#                         "orientation": face.orientation,
#                         "tilt": face.tilt,
#                         "solar_potential": face.solar_potential
#                     }
#                 }
#                 geojson["features"].append(geojson_feature)
#                 print(f"Added face {face.id} of building {face.building.id}")
#             except Exception as e:
#                 print(f"Error processing face {face.id}: {e}")

#         # Write to file
#         try:
#             with open(output_file, "w", encoding="utf-8") as f:
#                 json.dump(geojson, f, indent=2)
#             print(f"Successfully exported to {output_file}")
#         except Exception as e:
#             print(f"Error writing to file: {e}")

'''to include face id'''
from django.core.management.base import BaseCommand
from city_3D.models import BuildingFace
from django.contrib.gis.geos import GEOSGeometry
import json

class Command(BaseCommand):
    help = "Export BuildingFace data to a GeoJSON file"

    def handle(self, *args, **kwargs):
        output_file = "building_facesid.geojson"
        print(f"Exporting data to {output_file}...")

        # Prepare the GeoJSON structure
        geojson = {
            "type": "FeatureCollection",
            "features": []
        }

        # Iterate through all BuildingFace objects for building_id=3
        for face in BuildingFace.objects.all():
            try:
                # Convert geometry to GeoJSON format
                geom = GEOSGeometry(face.geometry.wkt)
                geojson_feature = {
                    "type": "Feature",
                    "geometry": json.loads(geom.geojson),
                    "properties": {
                        "face_id": face.id,  # Include face_id in properties
                        "building_id": face.building.id,
                        "orientation": face.orientation,
                        "tilt": face.tilt,
                        "solar_potential": face.solar_potential
                    }
                }
                geojson["features"].append(geojson_feature)
                print(f"Added face {face.id} of building {face.building.id}")
            except Exception as e:
                print(f"Error processing face {face.id}: {e}")

        # Write to file
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(geojson, f, indent=2)
            print(f"Successfully exported to {output_file}")
        except Exception as e:
            print(f"Error writing to file: {e}")
