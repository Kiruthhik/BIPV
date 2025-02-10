# import os

# # Set the PROJ_LIB path for pyproj or GDAL only in this Python process
# os.environ['PROJ_LIB'] = r'C:\Users\HP\AppData\Local\Programs\Python\Python312\Lib\site-packages\pyproj\proj_dir\share\proj'
# os.environ['GDAL_DATA'] = r'C:\Users\HP\AppData\Local\Programs\Python\Python312\Lib\site-packages\pyproj\proj_dir\share\proj'

# from django.core.management.base import BaseCommand
# from city_3D.models import Building, BuildingFace, VirtualGridCentroid
# from django.contrib.gis.geos import GEOSGeometry
# import json

# class Command(BaseCommand):
#     help = "Export Building data to a GeoJSON file with face centroids in latitude and longitude (EPSG:4326)"

#     def handle(self, *args, **kwargs):
#         output_file = "buildings_with_centroids.geojson"
#         print(f"Exporting data to {output_file}...")

#         # Prepare the GeoJSON structure
#         geojson = {
#             "type": "FeatureCollection",
#             "features": []
#         }

#         # Iterate through all Building objects
#         for building in Building.objects.all():
#             try:
#                 # Transform building geometry to EPSG:4326
#                 geom = building.geometry.transform(4326, clone=True)
#                 building_feature = {
#                     "type": "Feature",
#                     "geometry": json.loads(geom.geojson),  # Geometry of the building in EPSG:4326
#                     "properties": {
#                         "building_id": building.id,
#                         "height": building.height,
#                         "total_solar_potential": building.total_solar_potential,
#                         "faces": []  # This will contain details of all faces and centroids
#                     }
#                 }

#                 # Iterate through all faces of the building
#                 for face in building.faces.all():
#                     face_data = {
#                         "face_id": face.id,
#                         "orientation": face.orientation,
#                         "tilt": face.tilt,
#                         "solar_potential": face.solar_potential,
#                         "centroids": []
#                     }

#                     # Add centroids of the face transformed to EPSG:4326
#                     for centroid in face.centroids.all():
#                         transformed_centroid = centroid.centroid.transform(4326, clone=True)
#                         centroid_point = json.loads(transformed_centroid.geojson)
#                         face_data["centroids"].append({
#                             "label": centroid.label,
#                             "coordinates": centroid_point["coordinates"]
#                         })

#                     # Append face data to the building properties
#                     building_feature["properties"]["faces"].append(face_data)

#                 # Append the building feature to the GeoJSON
#                 geojson["features"].append(building_feature)
#                 print(f"Added Building ID {building.id} with its faces and centroids.")

#             except Exception as e:
#                 print(f"Error processing Building ID {building.id}: {e}")

#         # Write the GeoJSON data to a file
#         try:
#             with open(output_file, "w", encoding="utf-8") as f:
#                 json.dump(geojson, f, indent=2)
#             print(f"Successfully exported to {output_file}")
#         except Exception as e:
#             print(f"Error writing to file: {e}")
'''reduce size of geojson'''
import os

# Set the PROJ_LIB path for pyproj or GDAL only in this Python process
os.environ['PROJ_LIB'] = r'C:\Users\HP\AppData\Local\Programs\Python\Python312\Lib\site-packages\pyproj\proj_dir\share\proj'
os.environ['GDAL_DATA'] = r'C:\Users\HP\AppData\Local\Programs\Python\Python312\Lib\site-packages\pyproj\proj_dir\share\proj'

from django.core.management.base import BaseCommand
from city_3D.models import Building, BuildingFace
import json

class Command(BaseCommand):
    help = "Export Building data with centroids in simplified GeoJSON format (EPSG:4326)"

    def handle(self, *args, **kwargs):
        output_file = "buildingsid_with_centroids_id_jk.geojson"
        print(f"Exporting data to {output_file}...")

        # Prepare the GeoJSON structure
        geojson = {
            "type": "FeatureCollection",
            "features": []
        }
        building_ids = [5203,5028,5165,5232]
        # Iterate through all Building objects
        for building in Building.objects.filter(id__in = building_ids):
            try:
                # Transform building geometry to EPSG:4326
                building_geom = building.geometry.transform(4326, clone=True)
                building_feature = {
                    "type": "Feature",
                    "geometry": json.loads(building_geom.geojson),  # Geometry of the building in EPSG:4326
                    "properties": {
                        "building_id": building.id,
                        "height": building.height,
                        "centroids": []
                    }
                }

                # Collect centroids from all faces of the building
                for face in building.faces.all():
                    for centroid in face.centroids.all():
                        transformed_centroid = centroid.centroid.transform(4326, clone=True)
                        centroid_point = json.loads(transformed_centroid.geojson)
                        building_feature["properties"]["centroids"].append({
                            "id": centroid.id,
                            "coordinates": centroid_point["coordinates"]
                        })

                geojson["features"].append(building_feature)
                print(f"Added Building ID {building.id} with centroids.")

            except Exception as e:
                print(f"Error processing Building ID {building.id}: {e}")

        # Write to file
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(geojson, f, indent=2)
            print(f"Successfully exported to {output_file}")
        except Exception as e:
            print(f"Error writing to file: {e}")
