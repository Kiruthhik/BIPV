import os

# Set the PROJ_LIB path for pyproj or GDAL only in this Python process
os.environ['PROJ_LIB'] = r'C:\Users\HP\AppData\Local\Programs\Python\Python312\Lib\site-packages\pyproj\proj_dir\share\proj'
os.environ['GDAL_DATA'] = r'C:\Users\HP\AppData\Local\Programs\Python\Python312\Lib\site-packages\pyproj\proj_dir\share\proj'

import json
from django.core.management.base import BaseCommand
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.gdal import CoordTransform, SpatialReference
from city_3D.models import Grid2D


class Command(BaseCommand):
    help = "Export Grid2D objects to a GeoJSON file with height, orientation, and grid type"

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting export of Grid2D to GeoJSON with 3D properties...")

        try:
            # Define output file
            output_file = "grid2d_build123.geojson"

            # Initialize GeoJSON structure
            geojson_data = {
                "type": "FeatureCollection",
                "features": []
            }

            # Set up coordinate transformation (EPSG:32643 to EPSG:4326)
            source_srid = 32643  # Assuming UTM Zone 43N
            target_srid = 4326  # WGS84 (lat/lon)
            source_srs = SpatialReference(source_srid)
            target_srs = SpatialReference(target_srid)
            transform = CoordTransform(source_srs, target_srs)

            # Query all Grid2D objects
            grids = Grid2D.objects.all()
            self.stdout.write(f"Found {grids.count()} grids to export.")

            # Process each grid
            for grid in grids:
                # Transform geometry to lat/lon
                geom_utm = grid.geometry
                geom_latlon = geom_utm.transform(transform, clone=True)

                # Determine grid type (horizontal or vertical)
                grid_type = "horizontal" if grid.height_start == grid.height_end else "vertical"

                # Create GeoJSON feature
                feature = {
                    "type": "Feature",
                    "geometry": json.loads(geom_latlon.json),
                    "properties": {
                        "x_position": grid.x_position,
                        "y_position": grid.y_position,
                        "height_start": grid.height_start,
                        "height_end": grid.height_end,
                        "orientation": grid.face.orientation if grid_type == "vertical" else None,
                        "grid_type": grid_type,
                        "solar_potential": grid.solar_potential,
                        "is_in_shadow": grid.is_in_shadow,
                    }
                }

                # Add to features list
                geojson_data["features"].append(feature)

            # Save GeoJSON to file
            with open(output_file, "w") as f:
                json.dump(geojson_data, f, indent=2)

            self.stdout.write(self.style.SUCCESS(f"Exported grids to {output_file} successfully!"))

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error exporting grids: {e}"))
