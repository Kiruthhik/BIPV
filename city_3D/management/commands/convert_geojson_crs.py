import os

# Set the PROJ_LIB path for pyproj or GDAL only in this Python process
os.environ['PROJ_LIB'] = r'C:\Users\HP\AppData\Local\Programs\Python\Python312\Lib\site-packages\pyproj\proj_dir\share\proj'
os.environ['GDAL_DATA'] = r'C:\Users\HP\AppData\Local\Programs\Python\Python312\Lib\site-packages\pyproj\proj_dir\share\proj'


import json
from django.core.management.base import BaseCommand
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.gdal import CoordTransform, SpatialReference

class Command(BaseCommand):
    help = "Convert a GeoJSON file from EPSG:32643 to EPSG:4326."

    def add_arguments(self, parser):
        parser.add_argument(
            'input_file',
            type=str,
            help="Path to the input GeoJSON file in EPSG:32643.",
        )
        parser.add_argument(
            'output_file',
            type=str,
            help="Path to save the output GeoJSON file in EPSG:4326.",
        )

    def handle(self, *args, **kwargs):
        input_file = kwargs['input_file']
        output_file = kwargs['output_file']

        try:
            self.stdout.write(f"Loading GeoJSON from {input_file}...")
            with open(input_file, 'r', encoding='utf-8') as f:
                geojson_data = json.load(f)

            # Coordinate transformation
            source_srid = 32643  # EPSG:32643 (projected)
            target_srid = 4326   # EPSG:4326 (lat/lon)
            source_srs = SpatialReference(source_srid)
            target_srs = SpatialReference(target_srid)
            transform = CoordTransform(source_srs, target_srs)

            self.stdout.write("Transforming coordinates...")
            for feature in geojson_data['features']:
                geometry = GEOSGeometry(json.dumps(feature['geometry']))

                # Ensure the geometry has the correct SRID before transformation
                if geometry.srid != source_srid:
                    geometry.srid = source_srid

                geometry.transform(transform)  # Perform CRS transformation
                feature['geometry'] = json.loads(geometry.geojson)  # Update geometry with transformed coordinates

            # Save transformed GeoJSON
            self.stdout.write(f"Saving transformed GeoJSON to {output_file}...")
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(geojson_data, f, indent=4)

            self.stdout.write(f"GeoJSON successfully converted and saved to {output_file}.")

        except Exception as e:
            self.stderr.write(f"An error occurred: {e}")
