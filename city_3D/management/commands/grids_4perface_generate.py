from django.core.management.base import BaseCommand
from django.contrib.gis.geos import Polygon, GEOSGeometry
from city_3D.models import BuildingFace, Grid
from django.db import transaction

import os

# Set the PROJ_LIB path for pyproj or GDAL only in this Python process
os.environ['PROJ_LIB'] = r'C:\Users\HP\AppData\Local\Programs\Python\Python312\Lib\site-packages\pyproj\proj_dir\share\proj'
os.environ['GDAL_DATA'] = r'C:\Users\HP\AppData\Local\Programs\Python\Python312\Lib\site-packages\pyproj\proj_dir\share\proj'


class Command(BaseCommand):
    help = "Generate 4 grids for each BuildingFace and save them to the database"

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting grid generation for BuildingFace objects...")

        try:
            with transaction.atomic():
                # Clear existing grids
                Grid.objects.all().delete()
                self.stdout.write("Existing grids cleared.")

                # Process BuildingFace objects for the first three buildings
                for face in BuildingFace.objects.filter(building__id__in=[1, 2, 3]):
                    self.stdout.write(f"Processing Face {face.id} of Building {face.building.id}...")
                    
                    # Generate grids for the face
                    grids = self.generate_grids(face)
                    if not grids:
                        self.stderr.write(f"No grids generated for Face {face.id}. Skipping.")
                        continue

                    # Save generated grids to the database
                    for grid_geom, x_pos, y_pos in grids:
                        Grid.objects.create(
                            face=face,
                            geometry=grid_geom,
                            x_position=x_pos,
                            y_position=y_pos
                        )
                    self.stdout.write(f"Generated {len(grids)} grids for Face {face.id}.")
            
            self.stdout.write("Grid generation completed successfully!")

        except Exception as e:
            self.stderr.write(f"Error during grid generation: {e}")

    def generate_grids(self, face):
        """
        Divides a BuildingFace into 4 equal grids and returns their geometries.

        Args:
            face (BuildingFace): The building face to divide into grids.

        Returns:
            List[Tuple[Polygon, int, int]]: A list of tuples, each containing the grid geometry and its x/y position.
        """
        face_geom = face.geometry
        if not face_geom:
            self.stderr.write(f"Face {face.id} has no geometry. Skipping.")
            return []

        if face_geom.geom_type != "Polygon":
            self.stderr.write(f"Face {face.id} geometry is not a Polygon. Skipping.")
            return []

        # Get bounding box coordinates
        min_x, min_y, max_x, max_y = face_geom.extent

        # Calculate the midpoint for splitting into 4 grids
        mid_x = (min_x + max_x) / 2
        mid_y = (min_y + max_y) / 2

        # Create grid polygons
        grid_polygons = [
            Polygon([(min_x, min_y), (mid_x, min_y), (mid_x, mid_y), (min_x, mid_y), (min_x, min_y)]),  # Bottom-left
            Polygon([(mid_x, min_y), (max_x, min_y), (max_x, mid_y), (mid_x, mid_y), (mid_x, min_y)]),  # Bottom-right
            Polygon([(min_x, mid_y), (mid_x, mid_y), (mid_x, max_y), (min_x, max_y), (min_x, mid_y)]),  # Top-left
            Polygon([(mid_x, mid_y), (max_x, mid_y), (max_x, max_y), (mid_x, max_y), (mid_x, mid_y)]),  # Top-right
        ]

        # Extract Z-values
        z_min = min(coord[2] for coord in face_geom.coords[0])
        z_max = max(coord[2] for coord in face_geom.coords[0])

        # Assign Z-coordinates and return 3D grid geometries
        grid_geometries = []
        for idx, grid in enumerate(grid_polygons):
            try:
                coords_3d = [(x, y, z_min) for x, y in grid.coords[0]]
                grid_3d = Polygon(coords_3d, srid=face_geom.srid)
                grid_geometries.append((grid_3d, idx % 2, idx // 2))  # x_position, y_position
            except Exception as e:
                self.stderr.write(f"Error creating 3D grid for Face {face.id}: {e}")
        
        return grid_geometries
