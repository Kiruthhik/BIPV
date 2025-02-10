import os

# Set the PROJ_LIB path for pyproj or GDAL only in this Python process
os.environ['PROJ_LIB'] = r'C:\Users\HP\AppData\Local\Programs\Python\Python312\Lib\site-packages\pyproj\proj_dir\share\proj'
os.environ['GDAL_DATA'] = r'C:\Users\HP\AppData\Local\Programs\Python\Python312\Lib\site-packages\pyproj\proj_dir\share\proj'


from django.core.management.base import BaseCommand
from city_3D.models import BuildingFace, VirtualGridCentroid, Building
from django.contrib.gis.geos import GEOSGeometry
import json

class Command(BaseCommand):
    help = "Export BuildingFace data to a GeoJSON file with centroids in latitude and longitude (EPSG:4326)"

    def handle(self, *args, **kwargs):
        output_file = "faces_with_centroids_latlongjk.geojson"
        print(f"Exporting data to {output_file}...")

        # Prepare the GeoJSON structure
        geojson = {
            "type": "FeatureCollection",
            "features": []
        }

        # Iterate through all BuildingFace objects
        for building in Building.objects.filter(id__in= [5203,5028,5165,5232]):
            for face in building.faces.all():
                try:
                    # Transform geometry to EPSG:4326
                    geom = face.geometry.transform(4326, clone=True)
                    face_feature = {
                        "type": "Feature",
                        "geometry": json.loads(geom.geojson),  # Geometry of the face in EPSG:4326
                        "properties": {
                            "face_id": face.id,
                            "building_id": face.building.id,
                            "orientation": face.orientation,
                            "tilt": face.tilt,
                            "solar_potential": face.solar_potential,
                            "centroids": []
                        }
                    }

                    # Add centroids transformed to EPSG:4326
                    for centroid in face.centroids.all():  # Access related VirtualGridCentroid objects
                        transformed_centroid = centroid.centroid.transform(4326, clone=True)
                        centroid_point = json.loads(transformed_centroid.geojson)
                        face_feature["properties"]["centroids"].append({
                            "label": centroid.label,
                            "coordinates": centroid_point["coordinates"]
                        })

                    geojson["features"].append(face_feature)
                    print(f"Added Face ID {face.id} with centroids.")

                except Exception as e:
                    print(f"Error processing Face ID {face.id}: {e}")

        try:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(geojson, f, indent=2)
            print(f"Successfully exported to {output_file}")
        except Exception as e:
            print(f"Error writing to file: {e}")
