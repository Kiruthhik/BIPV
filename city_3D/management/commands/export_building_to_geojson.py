import json
from django.core.management.base import BaseCommand
from city_3D.models import Building

import os

# Set the PROJ_LIB path for pyproj or GDAL only in this Python process
os.environ['PROJ_LIB'] = r'C:\Users\HP\AppData\Local\Programs\Python\Python312\Lib\site-packages\pyproj\proj_dir\share\proj'
os.environ['GDAL_DATA'] = r'C:\Users\HP\AppData\Local\Programs\Python\Python312\Lib\site-packages\pyproj\proj_dir\share\proj'



class Command(BaseCommand):
    help = "Export building data to a GeoJSON file."

    def handle(self, *args, **kwargs):
        # GeoJSON structure
        geojson_data = {
            "type": "FeatureCollection",
            "features": []
        }

        # Fetch all buildings
        buildings = Building.objects.all()
        if not buildings.exists():
            self.stdout.write("No buildings found in the database.")
            return

        for building in buildings:
            if not building.geometry:
                self.stdout.write(f"Building ID {building.id} has no geometry. Skipping.")
                continue

            # Add building details to GeoJSON
            geojson_data["features"].append({
                "type": "Feature",
                "properties": {
                    "id": building.id,
                    #"name": building.name,
                    "height": building.height,
                    "other_property": getattr(building, "other_property", None)  # Replace with actual fields
                },
                "geometry": json.loads(building.geometry.geojson)
            })

        # Write to GeoJSON file
        output_file = "building_coordinate.geojson"
        with open(output_file, "w") as geojson_file:
            json.dump(geojson_data, geojson_file, indent=4)
        self.stdout.write(f"Building data successfully exported to {output_file}.")
