import os

# Set the PROJ_LIB path for pyproj or GDAL only in this Python process
os.environ['PROJ_LIB'] = r'C:\Users\HP\AppData\Local\Programs\Python\Python312\Lib\site-packages\pyproj\proj_dir\share\proj'
os.environ['GDAL_DATA'] = r'C:\Users\HP\AppData\Local\Programs\Python\Python312\Lib\site-packages\pyproj\proj_dir\share\proj'

import json
from django.core.management.base import BaseCommand
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.gdal import CoordTransform, SpatialReference
from city_3D.models import Grid3D


class Command(BaseCommand):
    help = "Export Grid3D objects to a GeoJSON file grouped by building with CRS converted to EPSG:4326."

    def add_arguments(self, parser):
        parser.add_argument(
            '--output', type=str, default="grids_3d_new_latlong.geojson",
            help="Path to save the output GeoJSON file."
        )

    def handle(self, *args, **kwargs):
        output_path = kwargs['output']
        self.stdout.write(f"Exporting Grid3D objects to {output_path}...")

        try:
            # Define coordinate transformation to EPSG:4326
            target_srid = 4326
            source_srid = 32643  # Update this to match your grid's original CRS
            source_srs = SpatialReference(source_srid)
            target_srs = SpatialReference(target_srid)
            transform = CoordTransform(source_srs, target_srs)

            # Collect all grid features
            all_features = []

            for grid in Grid3D.objects.all():
                # Transform the grid geometry to EPSG:4326
                transformed_geometry = grid.geometry.transform(target_srid, clone=True)

                grid_feature = {
                    "type": "Feature",
                    "geometry": json.loads(transformed_geometry.geojson),
                    "properties": {
                        "face_id": grid.face.id,
                        "building_id": grid.face.building.id,
                        "x_position": grid.x_position,
                        "y_position": grid.y_position,
                        "z_position": grid.z_position,
                        "area": grid.area,
                        "solar_potential": grid.solar_potential,
                        "is_in_shadow": grid.is_in_shadow
                    }
                }

                all_features.append(grid_feature)

            # Save combined GeoJSON
            geojson_data = {
                "type": "FeatureCollection",
                "features": all_features
            }

            with open(output_path, "w") as geojson_file:
                json.dump(geojson_data, geojson_file, indent=4)

            self.stdout.write(f"GeoJSON export completed: {output_path}")

        except Exception as e:
            self.stderr.write(f"Error during export: {e}")
