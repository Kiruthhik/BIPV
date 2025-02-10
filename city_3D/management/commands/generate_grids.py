from django.core.management.base import BaseCommand
from django.contrib.gis.geos import Polygon, MultiPolygon
from city_3D.models import Building, BuildingFace, Grid
import math

class Command(BaseCommand):
    help = "Generate 1m² grids for the first 3 buildings."

    def handle(self, *args, **kwargs):
        self.generate_grids()

    def generate_grids(self):
        # Fetch the first 3 buildings
        buildings = Building.objects.all()[:3]
        processed_buildings = 0
        generated_grids = 0

        for building in buildings:
            print(f"\nProcessing Building ID: {building.id}")
            faces = BuildingFace.objects.filter(building=building)

            for face in faces:
                print(f"  Generating grids for Face ID: {face.id}")
                generated = self.create_grids_for_face(face)
                generated_grids += generated

            processed_buildings += 1

        # Summary
        print("\n==== Summary ====")
        print(f"Total Buildings Processed: {processed_buildings}")
        print(f"Total Grids Generated: {generated_grids}")
        print("=================\n")

    def create_grids_for_face(self, face):
        """Generate 1m² grids for a given face."""
        generated_grids = 0
        face_geom = face.geometry

        if not face_geom:
            print("    Face geometry is missing. Skipping.")
            return 0

        # Get bounding box of the face
        min_x, min_y, max_x, max_y = face_geom.extent
        print(f"    Bounding Box: ({min_x}, {min_y}, {max_x}, {max_y})")

        # Generate grid cells within the bounding box
        x = min_x
        while x < max_x:
            y = min_y
            while y < max_y:
                # Create a grid cell as a polygon
                grid_cell_coords = [
                    (x, y),
                    (x + 1, y),
                    (x + 1, y + 1),
                    (x, y + 1),
                    (x, y)
                ]
                grid_cell = Polygon(grid_cell_coords)

                # Check if the grid cell intersects with the face
                if face_geom.intersects(grid_cell):
                    # Clip the grid cell to the face geometry
                    clipped_cell = face_geom.intersection(grid_cell)

                    if clipped_cell and isinstance(clipped_cell, Polygon):
                        # Save the grid cell
                        grid = Grid(
                            face=face,
                            geometry=clipped_cell,
                            x_position=math.floor(x - min_x),
                            y_position=math.floor(y - min_y)
                        )
                        try:
                            grid.save()
                            generated_grids += 1
                        except Exception as e:
                            print(f"      Error saving grid cell: {e}")

                y += 1
            x += 1

        print(f"    Generated {generated_grids} grids for Face ID: {face.id}")
        return generated_grids
