'''initial logic'''
import os

# Set the PROJ_LIB path for pyproj or GDAL only in this Python process
os.environ['PROJ_LIB'] = r'C:\Users\HP\AppData\Local\Programs\Python\Python312\Lib\site-packages\pyproj\proj_dir\share\proj'
os.environ['GDAL_DATA'] = r'C:\Users\HP\AppData\Local\Programs\Python\Python312\Lib\site-packages\pyproj\proj_dir\share\proj'


# from django.core.management.base import BaseCommand
# from django.contrib.gis.geos import Polygon
# from django.db import transaction
# from city_3D.models import BuildingFace, Grid3D

# class Command(BaseCommand):
#     help = "Generate 3D grids for the faces of the first three buildings."

#     def handle(self, *args, **kwargs):
#         self.stdout.write("Starting 3D grid generation for BuildingFace objects...")

#         try:
#             with transaction.atomic():
#                 # Clear existing grids
#                 Grid3D.objects.all().delete()
#                 self.stdout.write("Existing 3D grids cleared.")

#                 # Process BuildingFace objects for the first three buildings
#                 for face in BuildingFace.objects.filter(building__id__in=[1, 2, 3]):
#                     self.stdout.write(f"Processing Face {face.id} of Building {face.building.id}...")

#                     # Generate grids for the face
#                     grids = self.split_face_into_grids(face)
#                     if not grids:
#                         self.stderr.write(f"No grids generated for Face {face.id}. Skipping.")
#                         continue

#                     # Save generated grids to the database
#                     for grid_geom, x_pos, y_pos, z_pos in grids:
#                         Grid3D.objects.create(
#                             face=face,
#                             geometry=grid_geom,
#                             x_position=x_pos,
#                             y_position=y_pos,
#                             z_position=z_pos
#                         )
#                     self.stdout.write(f"Generated {len(grids)} 3D grids for Face {face.id}.")

#             self.stdout.write("3D grid generation completed successfully!")

#         except Exception as e:
#             self.stderr.write(f"Error during 3D grid generation: {e}")

#     def split_face_into_grids(face):
#         """
#         Splits a 3D face into 2D grids based on the face's orientation and geometry.

#         Args:
#             face (BuildingFace): The face to split.

#         Returns:
#             List[Tuple[Polygon, int, int, int]]: Grids with geometry and indices.
#         """
#         face_geom = face.geometry

#         # Validate face geometry
#         if not face_geom or face_geom.geom_type != "Polygon":
#             print(f"Invalid geometry for face {face.id}. Skipping.")
#             return []

#         # Determine grid division counts
#         num_x_divisions = 2  # Horizontal splitting
#         num_y_divisions = 2  # Vertical splitting
#         grids = []

#         # Get bounding box coordinates
#         min_x, min_y, min_z = face_geom.coords[0][0]
#         max_x, max_y, max_z = face_geom.coords[0][-1]

#         if face.tilt == 90:  # Vertical face
#             # Split based on orientation
#             if face.orientation in [0, 180]:  # YZ plane (North-South)
#                 step_y = (max_y - min_y) / num_y_divisions
#                 step_z = (max_z - min_z) / num_x_divisions  # Height divided along Z-axis

#                 for i in range(num_x_divisions):
#                     for j in range(num_y_divisions):
#                         # Define grid bounds
#                         grid_min_y = min_y + j * step_y
#                         grid_min_z = min_z + i * step_z
#                         grid_max_y = grid_min_y + step_y
#                         grid_max_z = grid_min_z + step_z

#                         # Create grid geometry (in YZ plane)
#                         grid_geom = Polygon([
#                             (min_x, grid_min_y, grid_min_z),
#                             (min_x, grid_max_y, grid_min_z),
#                             (min_x, grid_max_y, grid_max_z),
#                             (min_x, grid_min_y, grid_max_z),
#                             (min_x, grid_min_y, grid_min_z),
#                         ])
#                         grids.append((grid_geom, 0, j, i))  # X-index is always 0 for YZ plane

#             elif face.orientation in [90, 270]:  # XZ plane (East-West)
#                 step_x = (max_x - min_x) / num_x_divisions
#                 step_z = (max_z - min_z) / num_y_divisions  # Height divided along Z-axis

#                 for i in range(num_x_divisions):
#                     for j in range(num_y_divisions):
#                         # Define grid bounds
#                         grid_min_x = min_x + i * step_x
#                         grid_min_z = min_z + j * step_z
#                         grid_max_x = grid_min_x + step_x
#                         grid_max_z = grid_min_z + step_z

#                         # Create grid geometry (in XZ plane)
#                         grid_geom = Polygon([
#                             (grid_min_x, min_y, grid_min_z),
#                             (grid_max_x, min_y, grid_min_z),
#                             (grid_max_x, min_y, grid_max_z),
#                             (grid_min_x, min_y, grid_max_z),
#                             (grid_min_x, min_y, grid_min_z),
#                         ])
#                         grids.append((grid_geom, i, 0, j))  # Y-index is always 0 for XZ plane

#         else:  # Horizontal face
#             step_x = (max_x - min_x) / num_x_divisions
#             step_y = (max_y - min_y) / num_y_divisions

#             for i in range(num_x_divisions):
#                 for j in range(num_y_divisions):
#                     # Define grid bounds
#                     grid_min_x = min_x + i * step_x
#                     grid_min_y = min_y + j * step_y
#                     grid_max_x = grid_min_x + step_x
#                     grid_max_y = grid_min_y + step_y

#                     # Create grid geometry (in XY plane)
#                     grid_geom = Polygon([
#                         (grid_min_x, grid_min_y, min_z),
#                         (grid_max_x, grid_min_y, min_z),
#                         (grid_max_x, grid_max_y, min_z),
#                         (grid_min_x, grid_max_y, min_z),
#                         (grid_min_x, grid_min_y, min_z),
#                     ])
#                     grids.append((grid_geom, i, j, 0))  # Z-index is always 0 for horizontal plane

#         return grids

'''specific logic for vertical and horizontal face'''

# import os
# import numpy as np
# from django.core.management.base import BaseCommand
# from django.contrib.gis.geos import Polygon
# from django.db import transaction
# from city_3D.models import BuildingFace, Grid3D


# class Command(BaseCommand):
#     help = "Generate 3D grids for building faces based on orientation and tilt."

#     def handle(self, *args, **kwargs):
#         self.stdout.write("Starting grid generation for BuildingFace objects...")

#         try:
#             with transaction.atomic():
#                 # Clear existing grids
#                 Grid3D.objects.all().delete()
#                 self.stdout.write("Existing grids cleared.")

#                 # Process all faces
#                 for face in BuildingFace.objects.filter(building__id__in = [1,2,3]):
#                     self.stdout.write(f"Processing Face {face.id} of Building {face.building.id}...")

#                     # Generate grids for the face
#                     grids = self.generate_grids(face)
#                     if not grids:
#                         self.stderr.write(f"No grids generated for Face {face.id}. Skipping.")
#                         continue

#                     # Save generated grids to the database
#                     for grid_geom, x_pos, y_pos, z_pos, area in grids:
#                         Grid3D.objects.create(
#                             face=face,
#                             geometry=grid_geom,
#                             x_position=x_pos,
#                             y_position=y_pos,
#                             z_position=z_pos,
#                             area=area
#                         )
#                     self.stdout.write(f"Generated {len(grids)} grids for Face {face.id}.")
            
#             self.stdout.write("Grid generation completed successfully!")

#         except Exception as e:
#             self.stderr.write(f"Error during grid generation: {e}")

#     def generate_grids(self, face):
#         """
#         Generates grids for a building face, considering orientation and tilt.

#         Args:
#             face (BuildingFace): The face to split into grids.

#         Returns:
#             List[Tuple[Polygon, int, int, int, float]]: Grids with geometry, indices, and area.
#         """
#         face_geom = face.geometry
#         if not face_geom or face_geom.geom_type != "Polygon":
#             self.stderr.write(f"Face {face.id} has invalid geometry. Skipping.")
#             return []

#         # Check if the face is horizontal or vertical
#         is_horizontal = face.tilt == 0
#         is_vertical = face.tilt == 90

#         # Orientation-based grid generation
#         if is_horizontal:
#             return self.split_horizontal_face(face_geom)
#         elif is_vertical:
#             return self.split_vertical_face(face_geom, face.orientation, face.id)
#         else:
#             self.stderr.write(f"Face {face.id} has an unsupported tilt angle: {face.tilt}. Skipping.")
#             return []

#     def split_horizontal_face(self, face_geom):
#         """
#         Splits a horizontal face into grids with Z-coordinates.

#         Args:
#             face_geom (Polygon): Geometry of the face.

#         Returns:
#             List[Tuple[Polygon, int, int, int, float]]: Grids with geometry, indices, and area.
#         """
#         min_x, min_y, max_x, max_y = face_geom.extent

#         num_x_divisions = 2
#         num_y_divisions = 2
#         grid_width = (max_x - min_x) / num_x_divisions
#         grid_height = (max_y - min_y) / num_y_divisions

#         grids = []

#         for x_idx in range(num_x_divisions):
#             for y_idx in range(num_y_divisions):
#                 grid_min_x = min_x + x_idx * grid_width
#                 grid_min_y = min_y + y_idx * grid_height
#                 grid_max_x = grid_min_x + grid_width
#                 grid_max_y = grid_min_y + grid_height

#                 # Add Z-dimension to grid geometry (assume z = 0 for horizontal grids)
#                 grid_polygon = Polygon([
#                     (grid_min_x, grid_min_y, 0),
#                     (grid_max_x, grid_min_y, 0),
#                     (grid_max_x, grid_max_y, 0),
#                     (grid_min_x, grid_max_y, 0),
#                     (grid_min_x, grid_min_y, 0)
#                 ])

#                 # Calculate area
#                 grid_area = grid_width * grid_height

#                 # Append grid (z_position is 0 for horizontal)
#                 grids.append((grid_polygon, x_idx, y_idx, 0, grid_area))

#         return grids

#     def split_vertical_face(self, face_geom, orientation, face_id):
#         """
#         Splits a vertical face into grids with Z-coordinates.

#         Args:
#             face_geom (Polygon): Geometry of the face.
#             orientation (float): Azimuth angle of the face (degrees).
#             face_id (int): ID of the face for debugging.

#         Returns:
#             List[Tuple[Polygon, int, int, int, float]]: Grids with geometry, indices, and area.
#         """
#         is_zx_plane = 0 <= orientation < 90 or 270 <= orientation <= 360
#         is_zy_plane = 90 <= orientation < 270

#         min_x, min_y, max_x, max_y = face_geom.extent

#         grids = []

#         if is_zx_plane:
#             num_z_divisions = 2
#             num_x_divisions = 2
#             grid_width = (max_x - min_x) / num_x_divisions
#             grid_height = (max_y - min_y) / num_z_divisions

#             for z_idx in range(num_z_divisions):
#                 for x_idx in range(num_x_divisions):
#                     grid_min_x = min_x + x_idx * grid_width
#                     grid_min_y = min_y + z_idx * grid_height
#                     grid_max_x = grid_min_x + grid_width
#                     grid_max_y = grid_min_y + grid_height

#                     # Add Z-dimension to grid geometry
#                     grid_polygon = Polygon([
#                         (grid_min_x, grid_min_y, z_idx * grid_height),
#                         (grid_max_x, grid_min_y, z_idx * grid_height),
#                         (grid_max_x, grid_max_y, z_idx * grid_height),
#                         (grid_min_x, grid_max_y, z_idx * grid_height),
#                         (grid_min_x, grid_min_y, z_idx * grid_height)
#                     ])

#                     # Calculate area
#                     grid_area = grid_width * grid_height

#                     # Append grid
#                     grids.append((grid_polygon, x_idx, 0, z_idx, grid_area))

#         elif is_zy_plane:
#             num_z_divisions = 2
#             num_y_divisions = 2
#             grid_width = (max_x - min_x) / num_y_divisions
#             grid_height = (max_y - min_y) / num_z_divisions

#             for z_idx in range(num_z_divisions):
#                 for y_idx in range(num_y_divisions):
#                     grid_min_x = min_x + z_idx * grid_height
#                     grid_min_y = min_y + y_idx * grid_width
#                     grid_max_x = grid_min_x + grid_height
#                     grid_max_y = grid_min_y + grid_width

#                     # Add Z-dimension to grid geometry
#                     grid_polygon = Polygon([
#                         (grid_min_x, grid_min_y, z_idx * grid_height),
#                         (grid_max_x, grid_min_y, z_idx * grid_height),
#                         (grid_max_x, grid_max_y, z_idx * grid_height),
#                         (grid_min_x, grid_max_y, z_idx * grid_height),
#                         (grid_min_x, grid_min_y, z_idx * grid_height)
#                     ])

#                     # Calculate area
#                     grid_area = grid_width * grid_height

#                     # Append grid
#                     grids.append((grid_polygon, 0, y_idx, z_idx, grid_area))

#         else:
#             self.stderr.write(f"Face orientation {orientation} does not fall into ZX or ZY plane.")

#         return grids
'''without xz or yz plane'''
import os
import numpy as np
from django.core.management.base import BaseCommand
from django.contrib.gis.geos import Polygon
from django.db import transaction
from city_3D.models import BuildingFace, Grid3D


class Command(BaseCommand):
    help = "Generate 3D grids for building faces based on orientation and tilt."

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting grid generation for BuildingFace objects...")

        try:
            with transaction.atomic():
                # Clear existing grids
                Grid3D.objects.all().delete()
                self.stdout.write("Existing grids cleared.")

                # Process all faces
                for face in BuildingFace.objects.filter(building__id__in=[5203, 5165, 5232, 5208]):
                    self.stdout.write(f"Processing Face {face.id} of Building {face.building.id}...")

                    # Generate grids for the face
                    grids = self.generate_grids(face)
                    if not grids:
                        self.stderr.write(f"No grids generated for Face {face.id}. Skipping.")
                        continue

                    # Save generated grids to the database
                    for grid_geom, x_pos, y_pos, z_pos, area in grids:
                        Grid3D.objects.create(
                            face=face,
                            geometry=grid_geom,
                            x_position=x_pos,
                            y_position=y_pos,
                            z_position=z_pos,
                            area=area
                        )
                    self.stdout.write(f"Generated {len(grids)} grids for Face {face.id}.")

            self.stdout.write("Grid generation completed successfully!")

        except Exception as e:
            self.stderr.write(f"Error during grid generation: {e}")

    def generate_grids(self, face):
        """
        Generates grids for a building face, considering orientation and tilt.

        Args:
            face (BuildingFace): The face to split into grids.

        Returns:
            List[Tuple[Polygon, int, int, int, float]]: Grids with geometry, indices, and area.
        """
        face_geom = face.geometry
        if not face_geom or face_geom.geom_type != "Polygon":
            self.stderr.write(f"Face {face.id} has invalid geometry. Skipping.")
            return []

        # Check if the face is horizontal or vertical
        is_horizontal = face.tilt == 0
        is_vertical = face.tilt == 90

        # Orientation-based grid generation
        if is_horizontal:
            return self.split_horizontal_face(face_geom)
        elif is_vertical:
            return self.split_vertical_face(face_geom)
        else:
            self.stderr.write(f"Face {face.id} has an unsupported tilt angle: {face.tilt}. Skipping.")
            return []

    def split_horizontal_face(self, face_geom):
        """
        Splits a horizontal face into grids with Z-coordinates.

        Args:
            face_geom (Polygon): Geometry of the face.

        Returns:
            List[Tuple[Polygon, int, int, int, float]]: Grids with geometry, indices, and area.
        """
        min_x, min_y, max_x, max_y = face_geom.extent

        num_x_divisions = 2
        num_y_divisions = 2
        grid_width = (max_x - min_x) / num_x_divisions
        grid_height = (max_y - min_y) / num_y_divisions

        grids = []

        for x_idx in range(num_x_divisions):
            for y_idx in range(num_y_divisions):
                grid_min_x = min_x + x_idx * grid_width
                grid_min_y = min_y + y_idx * grid_height
                grid_max_x = grid_min_x + grid_width
                grid_max_y = grid_min_y + grid_height

                # Add Z-dimension to grid geometry (assume z = 0 for horizontal grids)
                grid_polygon = Polygon([
                    (grid_min_x, grid_min_y, 0),
                    (grid_max_x, grid_min_y, 0),
                    (grid_max_x, grid_max_y, 0),
                    (grid_min_x, grid_max_y, 0),
                    (grid_min_x, grid_min_y, 0)
                ])

                # Calculate area
                grid_area = grid_width * grid_height

                # Append grid (z_position is 0 for horizontal)
                grids.append((grid_polygon, x_idx, y_idx, 0, grid_area))

        return grids

    def split_vertical_face(self, face_geom):
        """
        Splits a vertical face into grids based on its geometry, orientation, and tilt.

        Args:
            face_geom (Polygon): Geometry of the face.

        Returns:
            List[Tuple[Polygon, int, int, int, float]]: Grids with geometry, indices, and area.
        """
        min_x, min_y, max_x, max_y = face_geom.extent

        # Calculate number of divisions based on face dimensions
        num_x_divisions = 2
        num_y_divisions = 2
        grid_width = (max_x - min_x) / num_x_divisions
        grid_height = (max_y - min_y) / num_y_divisions

        grids = []

        # Split the face into grid cells without making assumptions about the plane orientation
        for x_idx in range(num_x_divisions):
            for y_idx in range(num_y_divisions):
                grid_min_x = min_x + x_idx * grid_width
                grid_min_y = min_y + y_idx * grid_height
                grid_max_x = grid_min_x + grid_width
                grid_max_y = grid_min_y + grid_height

                # Create the grid polygon
                grid_polygon = Polygon([
                    (grid_min_x, grid_min_y, 0),  # Z=0 initially, will adjust later if necessary
                    (grid_max_x, grid_min_y, 0),
                    (grid_max_x, grid_max_y, 0),
                    (grid_min_x, grid_max_y, 0),
                    (grid_min_x, grid_min_y, 0)
                ])

                # Calculate grid area
                grid_area = grid_width * grid_height

                # Append grid
                grids.append((grid_polygon, x_idx, y_idx, 0, grid_area))

        return grids
