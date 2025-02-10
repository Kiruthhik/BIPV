import os

# Set the PROJ_LIB path for pyproj or GDAL only in this Python process
os.environ['PROJ_LIB'] = r'C:\Users\HP\AppData\Local\Programs\Python\Python312\Lib\site-packages\pyproj\proj_dir\share\proj'
os.environ['GDAL_DATA'] = r'C:\Users\HP\AppData\Local\Programs\Python\Python312\Lib\site-packages\pyproj\proj_dir\share\proj'


# from django.core.management.base import BaseCommand
# from django.db import transaction
# from city_3D.models import BuildingFace

# class Command(BaseCommand):
#     help = "Calculate and store the area for each BuildingFace."

#     def handle(self, *args, **kwargs):
#         self.stdout.write("Starting area calculation for BuildingFace objects...")

#         try:
#             with transaction.atomic():
#                 faces = BuildingFace.objects.filter(building__id__in = [1,2,3])
#                 self.stdout.write(f"Found {faces.count()} faces to process.")

#                 for face in faces:
#                     if not face.geometry or face.geometry.empty:
#                         self.stderr.write(f"Face {face.id} has empty geometry. Skipping.")
#                         continue

#                     try:
#                         if not face.geometry.valid:
#                             self.stderr.write(f"Face {face.id} has invalid geometry. Attempting to fix...")
#                             face.geometry = face.geometry.buffer(0)
#                             if not face.geometry.valid:
#                                 self.stderr.write(f"Face {face.id} could not be fixed. Skipping.")
#                                 continue

#                         # Handle horizontal faces (tilt == 0)
#                         if face.tilt == 0:
#                             face_area = self.calculate_horizontal_face_area(face.geometry)

#                         # Handle vertical faces (tilt == 90)
#                         elif face.tilt == 90:
#                             face_area = self.calculate_vertical_face_area(face.geometry)

#                         # Handle unsupported tilt values
#                         else:
#                             self.stderr.write(f"Face {face.id} has an unsupported tilt angle ({face.tilt}). Skipping.")
#                             continue

#                         # Save the calculated area to the database
#                         face.area = face_area
#                         face.save()

#                         self.stdout.write(f"Updated Face {face.id} with area: {face_area:.2f} square meters.")

#                     except Exception as e:
#                         self.stderr.write(f"Error calculating area for Face {face.id}: {e}")

#             self.stdout.write("Area calculation completed successfully!")

#         except Exception as e:
#             self.stderr.write(f"Error during area calculation: {e}")

#     def calculate_horizontal_face_area(self, geometry):
#         """
#         Calculate the area of a horizontal face.

#         Args:
#             geometry (Polygon): 2D geometry of the horizontal face.

#         Returns:
#             float: The area of the horizontal face.
#         """
#         try:
#             if geometry.geom_type == "Polygon":
#                 return geometry.area
#             elif geometry.geom_type == "MultiPolygon":
#                 return sum(polygon.area for polygon in geometry)
#             else:
#                 raise ValueError(f"Unsupported geometry type: {geometry.geom_type}")
#         except Exception as e:
#             raise ValueError(f"Error calculating horizontal face area: {e}")

#     def calculate_vertical_face_area(self, geometry):
#         """
#         Calculate the area of a vertical face based on its 3D geometry.

#         Args:
#             geometry (Polygon): 3D geometry of the vertical face.

#         Returns:
#             float: The area of the vertical face.
#         """
#         try:
#             coords = geometry.coords if geometry.geom_type == "Polygon" else geometry.exterior.coords
#             if len(coords) < 2:
#                 raise ValueError("Not enough coordinates for a valid vertical face.")

#             area = 0.0
#             for i in range(len(coords) - 1):
#                 x1, y1, z1 = coords[i]
#                 x2, y2, z2 = coords[i + 1]
#                 base_length = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
#                 height = abs(z2 - z1)
#                 area += base_length * height

#             return abs(area)
#         except Exception as e:
#             raise ValueError(f"Error calculating vertical face area: {e}")

'''base lenght X height for vertical faces'''
from django.core.management.base import BaseCommand
from city_3D.models import BuildingFace
import math


class Command(BaseCommand):
    help = "Calculate and store the surface area of each BuildingFace."

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting area calculation for BuildingFace objects...")

        try:
            faces = BuildingFace.objects.all()
            self.stdout.write(f"Found {faces.count()} faces to process.")

            for face in faces:
                try:
                    self.stdout.write(f"Processing Face {face.id}:")
                    self.stdout.write(f"  Geometry Type: {face.geometry.geom_type}")
                    self.stdout.write(f"  Geometry Coordinates: {list(face.geometry.coords[0])[:5]} (first 5 coordinates)")

                    # Check if it's a horizontal or vertical face
                    if self.is_horizontal_face(face.geometry):
                        area = self.calculate_horizontal_area(face.geometry)
                        self.stdout.write(f"  Using horizontal face area: {area:.2f}")
                    else:
                        building_height = face.building.height or 0.0  # Default to 0 if height is not provided
                        if building_height <= 0.0:
                            raise ValueError("Building height is not valid for vertical face area calculation.")
                        area = self.calculate_vertical_area(face.geometry, building_height)
                        self.stdout.write(f"  Using vertical face area: {area:.2f}")

                    # Update the face area in the database
                    face.area = area
                    face.save()
                    self.stdout.write(f"Updated Face {face.id} with area: {area:.2f} square meters.")
                except Exception as e:
                    self.stderr.write(f"Error calculating area for Face {face.id}: {e}")

            self.stdout.write("Area calculation completed successfully!")
        except Exception as e:
            self.stderr.write(f"Error during area calculation: {e}")

    def is_horizontal_face(self, geometry):
        """
        Determine if a face is horizontal based on the Z-coordinates.
        """
        coords = list(geometry.coords[0])
        z_values = {coord[2] for coord in coords}  # Extract unique Z-values
        return len(z_values) == 1  # Horizontal if all Z-values are the same

    def calculate_horizontal_area(self, geometry):
        """
        Calculate the area of a horizontal face.
        """
        return geometry.area

    def calculate_vertical_area(self, geometry, building_height):
        """
        Calculate the area of a vertical face using X-Y base length and building height.

        Args:
            geometry (Polygon): 3D geometry of the vertical face.
            building_height (float): The height of the building to which the face belongs.

        Returns:
            float: The area of the vertical face.
        """
        coords = list(geometry.coords[0])  # Extract the exterior coordinates
        if len(coords) < 4:  # A valid polygon should have at least 4 points to form a closed shape
            raise ValueError("Not enough coordinates for a valid vertical face.")

        total_area = 0.0
        self.stdout.write(f"  Vertical face has {len(coords)} coordinates.")

        for i in range(len(coords) - 1):  # Iterate over edges
            x1, y1, z1 = coords[i]
            x2, y2, z2 = coords[i + 1]

            # Calculate base length (X-Y distance)
            base_length = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

            # Calculate orientation (azimuth)
            #orientation = math.degrees(math.atan2(y2 - y1, x2 - x1)) % 360

            # Calculate segment area using the building height
            segment_area = base_length * building_height
            total_area += segment_area

            # Debug: Log intermediate calculations with orientation
            self.stdout.write(f"    Segment {i}:")
            self.stdout.write(f"      Start Point: ({x1}, {y1}, {z1})")
            self.stdout.write(f"      End Point: ({x2}, {y2}, {z2})")
            self.stdout.write(f"      Base Length: {base_length:.2f}")
            #self.stdout.write(f"      Orientation: {orientation:.2f}°")
            self.stdout.write(f"      Building Height: {building_height:.2f}")
            self.stdout.write(f"      Segment Area: {segment_area:.2f}")

        self.stdout.write(f"  Total Vertical Face Area: {total_area:.2f}")
        return total_area
