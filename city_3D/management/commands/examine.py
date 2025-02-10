from django.core.management.base import BaseCommand
from django.contrib.gis.geos import MultiPolygon, Polygon, LinearRing
from city_3D.models import Building, BuildingFace

import os

# Set the PROJ_LIB path for pyproj or GDAL only in this Python process
os.environ['PROJ_LIB'] = r'C:\Users\HP\AppData\Local\Programs\Python\Python312\Lib\site-packages\pyproj\proj_dir\share\proj'
os.environ['GDAL_DATA'] = r'C:\Users\HP\AppData\Local\Programs\Python\Python312\Lib\site-packages\pyproj\proj_dir\share\proj'


class Command(BaseCommand):
    help = "Examine buildings and generate faces, even without exterior."

    def handle(self, *args, **kwargs):
        print("Starting geometry examination and face generation...\n")
        self.examine_and_generate_faces()

    def examine_and_generate_faces(self):
        buildings = Building.objects.filter(id__in =[1,2])
        total_buildings = buildings.count()
        valid_geometries = 0
        invalid_geometries = 0
        total_faces_generated = 0

        for building in buildings:
            print(f"Examining Building ID: {building.id}")
            geometry = building.geometry
            if not geometry:
                print(f"  No geometry found for Building ID: {building.id}. Skipping.")
                invalid_geometries += 1
                continue

            print(f"  Geometry Type: {geometry.geom_type}")
            print(f"  SRID: {geometry.srid}")
            print(f"  Area: {geometry.area}")

            if geometry.geom_type not in ["Polygon", "MultiPolygon"]:
                print(f"  Unsupported geometry type for Building ID: {building.id}. Skipping.")
                invalid_geometries += 1
                continue

            valid_geometries += 1
            polygons = [geometry] if geometry.geom_type == "Polygon" else list(geometry)

            for idx, polygon in enumerate(polygons, start=1):
                print(f"    Processing Polygon {idx} for Building {building.id}")
                if not polygon.valid:
                    print(f"      Invalid Polygon. Attempting to fix...")
                    polygon = polygon.buffer(0)
                    if not polygon.valid:
                        print(f"      Polygon could not be fixed. Skipping.")
                        continue

                # Generate roof and wall faces
                total_faces_generated += self.generate_faces(building, polygon)

        print("\n==== Summary ====")
        print(f"  Total Buildings: {total_buildings}")
        print(f"  Valid Geometries: {valid_geometries}")
        print(f"  Invalid Geometries: {invalid_geometries}")
        print(f"  Total Faces Generated: {total_faces_generated}")
        print("=================\n")

    def generate_faces(self, building, polygon):
        """Generate roof and wall faces using polygon coordinates."""
        faces_generated = 0
        height = building.height or 0
        if height == 0:
            print(f"      Building height is 0. Skipping face generation.")
            return faces_generated

        coords = list(polygon.coords) if polygon.geom_type == "Polygon" else [poly.coords for poly in polygon]
        for ring_idx, ring_coords in enumerate(coords, start=1):
            if ring_idx > 1:
                print(f"      Skipping interior ring {ring_idx}. Only exterior coordinates are used.")
                continue

            # Generate roof face
            roof_coords = [(x, y, height) for x, y in ring_coords]
            try:
                roof_face = BuildingFace(
                    building=building,
                    geometry=Polygon(roof_coords),
                    orientation=0,
                    tilt=0,
                )
                roof_face.save()
                print(f"        Created Roof Face for Building {building.id}.")
                faces_generated += 1
            except Exception as e:
                print(f"        Error creating roof face for Building {building.id}: {e}")

            # Generate wall faces
            for i in range(len(ring_coords) - 1):
                coord1 = ring_coords[i]
                coord2 = ring_coords[i + 1]
                wall_coords = [
                    (coord1[0], coord1[1], 0),  # Bottom-left
                    (coord2[0], coord2[1], 0),  # Bottom-right
                    (coord2[0], coord2[1], height),  # Top-right
                    (coord1[0], coord1[1], height),  # Top-left
                    (coord1[0], coord1[1], 0),  # Close loop
                ]
                try:
                    wall_face = BuildingFace(
                        building=building,
                        geometry=Polygon(LinearRing(wall_coords)),
                        orientation=self.calculate_orientation(coord1, coord2),
                        tilt=90,
                    )
                    wall_face.save()
                    print(f"        Created Wall Face for Building {building.id}.")
                    faces_generated += 1
                except Exception as e:
                    print(f"        Error creating wall face for Building {building.id}: {e}")
        return faces_generated

    def calculate_orientation(self, coord1, coord2):
        """Calculate azimuth (orientation) of a wall edge."""
        import math
        dx = coord2[0] - coord1[0]
        dy = coord2[1] - coord1[1]
        azimuth = (math.degrees(math.atan2(dy, dx)) + 360) % 360
        return azimuth
