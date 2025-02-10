import os

# Set the PROJ_LIB path for pyproj or GDAL only in this Python process
os.environ['PROJ_LIB'] = r'C:\Users\HP\AppData\Local\Programs\Python\Python312\Lib\site-packages\pyproj\proj_dir\share\proj'
os.environ['GDAL_DATA'] = r'C:\Users\HP\AppData\Local\Programs\Python\Python312\Lib\site-packages\pyproj\proj_dir\share\proj'


from django.core.management.base import BaseCommand
from django.contrib.gis.geos import Polygon
from django.db import transaction
from city_3D.models import BuildingFace, Grid2D

class Command(BaseCommand):
    help = "Generate 2D grids for the first three buildings and save them to the database."

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting 2D grid generation for BuildingFace objects...")

        try:
            with transaction.atomic():
                # Clear existing 2D grids
                Grid2D.objects.all().delete()
                self.stdout.write("Existing 2D grids cleared.")

                # Process BuildingFace objects for the first three buildings
                for face in BuildingFace.objects.filter(building__id__in=[4,5,6]):
                    self.stdout.write(f"Processing Face {face.id} of Building {face.building.id}...")

                    # Generate grids for the face
                    grids = self.generate_2d_grids(face)
                    if not grids:
                        self.stderr.write(f"No grids generated for Face {face.id}. Skipping.")
                        continue

                    # Save generated grids to the database
                    for grid_geom, x_pos, y_pos, height_start, height_end in grids:
                        Grid2D.objects.create(
                            face=face,
                            geometry=grid_geom,
                            x_position=x_pos,
                            y_position=y_pos,
                            height_start=height_start,
                            height_end=height_end
                        )
                    self.stdout.write(f"Generated {len(grids)} 2D grids for Face {face.id}.")
            
            self.stdout.write("2D grid generation completed successfully!")

        except Exception as e:
            self.stderr.write(f"Error during 2D grid generation: {e}")

    def generate_2d_grids(self, face):
        """
        Divides a BuildingFace into 2D grids and handles both horizontal and vertical grids.

        Args:
            face (BuildingFace): The building face to divide into 2D grids.

        Returns:
            List[Tuple[Polygon, int, int, float, float]]: A list of tuples containing:
                - grid geometry (2D Polygon)
                - x_position
                - y_position
                - height_start
                - height_end
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

        # Determine if the face is vertical or horizontal based on tilt
        is_vertical = face.tilt == 90

        # Extract Z-values for height_start and height_end
        z_min = min(coord[2] for coord in face_geom.coords[0])
        z_max = max(coord[2] for coord in face_geom.coords[0])

        grids = []

        if is_vertical:
            # Vertical grids: Divide height (Z-axis)
            height_divisions = 2  # Adjust the number of divisions as needed
            z_step = (z_max - z_min) / height_divisions

            # Divide the X-Y extent into grids for each height layer
            num_x_divisions = 2  # Adjust as needed
            num_y_divisions = 2  # Adjust as needed
            grid_width = (max_x - min_x) / num_x_divisions
            grid_height = (max_y - min_y) / num_y_divisions

            for layer in range(height_divisions):
                height_start = z_min + layer * z_step
                height_end = height_start + z_step

                for x_idx in range(num_x_divisions):
                    for y_idx in range(num_y_divisions):
                        # Calculate the bounds of the grid
                        grid_min_x = min_x + x_idx * grid_width
                        grid_min_y = min_y + y_idx * grid_height
                        grid_max_x = grid_min_x + grid_width
                        grid_max_y = grid_min_y + grid_height

                        # Create the grid as a 2D Polygon
                        grid_geom = Polygon([
                            (grid_min_x, grid_min_y),
                            (grid_max_x, grid_min_y),
                            (grid_max_x, grid_max_y),
                            (grid_min_x, grid_max_y),
                            (grid_min_x, grid_min_y)
                        ])

                        # Append the grid with the current height range
                        grids.append((grid_geom, x_idx, y_idx, height_start, height_end))


        else:
            # Horizontal grids: Divide X-Y plane
            num_x_divisions = 2  # Adjust as needed
            num_y_divisions = 2  # Adjust as needed
            grid_width = (max_x - min_x) / num_x_divisions
            grid_height = (max_y - min_y) / num_y_divisions

            for x_idx in range(num_x_divisions):
                for y_idx in range(num_y_divisions):
                    # Calculate the bounds of the grid
                    grid_min_x = min_x + x_idx * grid_width
                    grid_min_y = min_y + y_idx * grid_height
                    grid_max_x = grid_min_x + grid_width
                    grid_max_y = grid_min_y + grid_height

                    # Create the grid as a 2D Polygon
                    grid_geom = Polygon([
                        (grid_min_x, grid_min_y),
                        (grid_max_x, grid_min_y),
                        (grid_max_x, grid_max_y),
                        (grid_min_x, grid_max_y),
                        (grid_min_x, grid_min_y)
                    ])

                    # Append the grid with z_min and z_max
                    grids.append((grid_geom, x_idx, y_idx, z_min, z_max))

        return grids

