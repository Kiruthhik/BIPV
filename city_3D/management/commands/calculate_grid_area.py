import os
from django.core.management.base import BaseCommand
from django.contrib.gis.geos import Polygon
from django.db import transaction
from city_3D.models import Grid

# Set the PROJ_LIB path for pyproj or GDAL only in this Python process
os.environ['PROJ_LIB'] = r'C:\Users\HP\AppData\Local\Programs\Python\Python312\Lib\site-packages\pyproj\proj_dir\share\proj'
os.environ['GDAL_DATA'] = r'C:\Users\HP\AppData\Local\Programs\Python\Python312\Lib\site-packages\pyproj\proj_dir\share\proj'


class Command(BaseCommand):
    help = "Calculate and store the surface area of each Grid3D."

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting area calculation for Grid3D objects...")

        try:
            with transaction.atomic():
                grids = Grid.objects.all()
                self.stdout.write(f"Found {grids.count()} grids to process.")

                for grid in grids:
                    if not grid.geometry:
                        self.stderr.write(f"Grid {grid.id} has no geometry. Skipping.")
                        continue

                    try:
                        # Calculate the surface area of the grid
                        area = grid.geometry.area
                        grid.area = area
                        grid.save()
                        self.stdout.write(f"Updated Grid {grid.id} with area: {area:.2f} square meters.")
                    except Exception as e:
                        self.stderr.write(f"Error calculating area for Grid {grid.id}: {e}")

            self.stdout.write("Area calculation completed successfully!")

        except Exception as e:
            self.stderr.write(f"Error during area calculation: {e}")
