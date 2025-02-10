import os
# Set the PROJ_LIB path for pyproj or GDAL only in this Python process
os.environ['PROJ_LIB'] = r'C:\Users\HP\AppData\Local\Programs\Python\Python312\Lib\site-packages\pyproj\proj_dir\share\proj'
os.environ['GDAL_DATA'] = r'C:\Users\HP\AppData\Local\Programs\Python\Python312\Lib\site-packages\pyproj\proj_dir\share\proj'

from django.core.management.base import BaseCommand
from city_3D.models import BuildingFace
from django.contrib.gis.geos import Polygon, MultiPolygon

class Command(BaseCommand):
    help = "Fix invalid geometries for Building ID: 3 and ensure Z-dimension integrity."

    def handle(self, *args, **kwargs):
        faces = BuildingFace.objects.filter(building_id=3)
        fixed_count = 0
        skipped_count = 0

        for face in faces:
            print(f"Processing Face ID: {face.id}")
            if not face.geometry.valid:
                try:
                    print("  Invalid geometry detected. Attempting to fix...")

                    # Attempt to fix the geometry
                    fixed_geometry = face.geometry.buffer(0)

                    if fixed_geometry.is_empty or not fixed_geometry.coords:
                        print(f"  Irreparable geometry for Face ID: {face.id}. Geometry collapsed during fixing.")
                        skipped_count += 1
                        continue

                    # Handle mismatch in vertices
                    if fixed_geometry.geom_type == "Polygon":
                        if len(fixed_geometry.exterior.coords) != len(face.geometry.coords[0]):
                            print(f"  Mismatch in vertices: Original ({len(face.geometry.coords[0])}) vs Fixed ({len(fixed_geometry.exterior.coords)}). Reusing original Z-values.")

                            # Reuse original Z-dimension values
                            original_coords = face.geometry.coords[0]
                            fixed_coords = fixed_geometry.exterior.coords
                            if len(fixed_coords) == len(original_coords):
                                new_coords = [
                                    (fixed[0], fixed[1], orig[2])  # Reuse Z-value from original
                                    for fixed, orig in zip(fixed_coords, original_coords)
                                ]
                                fixed_geometry = Polygon(new_coords, srid=face.geometry.srid)
                            else:
                                print(f"  Unable to align vertices for Face ID: {face.id}. Skipping.")
                                skipped_count += 1
                                continue

                    elif fixed_geometry.geom_type == "MultiPolygon":
                        print(f"  Handling MultiPolygon geometry for Face ID: {face.id}")
                        new_polygons = []
                        for original_poly, fixed_poly in zip(face.geometry, fixed_geometry):
                            if len(original_poly.coords[0]) != len(fixed_poly.exterior.coords):
                                new_coords = [
                                    (fixed[0], fixed[1], orig[2])
                                    for fixed, orig in zip(fixed_poly.exterior.coords, original_poly.coords[0])
                                ]
                                new_polygons.append(Polygon(new_coords))
                            else:
                                new_polygons.append(fixed_poly)

                        fixed_geometry = MultiPolygon(new_polygons, srid=face.geometry.srid)

                    # Save the fixed geometry
                    face.geometry = fixed_geometry
                    face.save()
                    fixed_count += 1
                    print(f"  Fixed geometry for Face ID: {face.id}")
                except Exception as e:
                    skipped_count += 1
                    print(f"  Error fixing geometry for Face ID: {face.id} - {e}")
            else:
                print(f"  Face ID: {face.id} is already valid. Skipping.")

        # Summary
        print("\n==== Geometry Fix Summary ====")
        print(f"Total Faces Processed: {faces.count()}")
        print(f"Total Geometries Fixed: {fixed_count}")
        print(f"Total Geometries Skipped: {skipped_count}")
        print("=================================")
