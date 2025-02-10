from django.core.management.base import BaseCommand
from city_3D.models import Building, BuildingFace
from django.contrib.gis.geos import Polygon, LinearRing
from django.db import transaction
import math


def calculate_wall_orientation(coord1, coord2):
    """Calculate azimuth (orientation) of a wall edge based on its coordinates."""
    dx = coord2[0] - coord1[0]
    dy = coord2[1] - coord1[1]
    azimuth = (math.degrees(math.atan2(dy, dx)) + 360) % 360
    return azimuth


class Command(BaseCommand):
    help = "Test building face generation for two specific buildings."

    def handle(self, *args, **options):
        building_ids = [1, 2]  # Replace with the IDs of the two buildings you want to test
        self.generate_faces(building_ids)

    def generate_faces(self, building_ids):
        processed_count = 0
        skipped_count = 0
        skipped_due_to_geometry = []
        skipped_due_to_area = []

        for building_id in building_ids:
            try:
                building = Building.objects.get(id=building_id)
                print(f"Processing Building ID: {building.id}")
                

                footprint = building.geometry
                height = building.height
                print(f"Building ID: {building.id}, Raw Geometry: {footprint.wkt}")
                print(f"Is Geometry Valid: {footprint.valid}")

                if not footprint or not height:
                    print(f"  Skipping Building {building.id}: Missing geometry or height.")
                    skipped_count += 1
                    continue

                # Handle MultiPolygon or Polygon
                if footprint.geom_type == "MultiPolygon":
                    polygons = list(footprint)
                elif footprint.geom_type == "Polygon":
                    polygons = [footprint]
                else:
                    print(f"  Skipping Building {building.id}: Unsupported geometry type ({footprint.geom_type}).")
                    skipped_due_to_geometry.append(building.id)
                    continue

                for idx, polygon in enumerate(polygons, start=1):
                    print(f"  Processing Polygon {idx} for Building {building.id}")

                    if not polygon.valid:
                        print(f"    Polygon {idx} is invalid. Attempting to fix...")
                        polygon = polygon.buffer(0)
                        if not polygon.valid:
                            print(f"    Polygon {idx} could not be fixed. Skipping.")
                            skipped_due_to_geometry.append(building.id)
                            continue

                    if polygon.area < 1e-4:  # Adjust area threshold as needed
                        print(f"    Polygon {idx} has a very small area ({polygon.area}). Skipping.")
                        skipped_due_to_area.append(building.id)
                        continue

                    if not hasattr(polygon, 'exterior') or not polygon.exterior:
                        print(f"    Polygon {idx} has no valid exterior. Skipping.")
                        skipped_due_to_geometry.append(building.id)
                        continue

                    exterior_coords = polygon.exterior.coords
                    for i in range(len(exterior_coords) - 1):
                        coord1 = exterior_coords[i]
                        coord2 = exterior_coords[i + 1]

                        # Define wall coordinates (3D extrusion)
                        wall_coords = [
                            (coord1[0], coord1[1], 0),  # Bottom edge
                            (coord2[0], coord2[1], 0),
                            (coord2[0], coord2[1], height),  # Top edge
                            (coord1[0], coord1[1], height),
                            (coord1[0], coord1[1], 0)  # Close the polygon
                        ]

                        try:
                            wall_geometry = Polygon(LinearRing(wall_coords))
                            if not wall_geometry.valid:
                                raise ValueError("Invalid wall geometry.")
                        except Exception as e:
                            print(f"      Error creating wall geometry: {e}")
                            continue

                        orientation = calculate_wall_orientation(coord1, coord2)

                        try:
                            with transaction.atomic():
                                wall_face = BuildingFace(
                                    building=building,
                                    geometry=wall_geometry,
                                    orientation=orientation,
                                    tilt=90
                                )
                                wall_face.save()
                                processed_count += 1
                                print(f"      Created Wall Face (Orientation: {orientation}).")
                        except Exception as e:
                            print(f"      Error saving wall face: {e}")

                    # Create roof face
                    roof_coords = [(x, y, height) for x, y in polygon.exterior.coords]
                    try:
                        roof_geometry = Polygon(LinearRing(roof_coords))
                        if not roof_geometry.valid:
                            raise ValueError("Invalid roof geometry.")
                        with transaction.atomic():
                            roof_face = BuildingFace(
                                building=building,
                                geometry=roof_geometry,
                                orientation=0,
                                tilt=0
                            )
                            roof_face.save()
                            processed_count += 1
                            print(f"      Created Roof Face.")
                    except Exception as e:
                        print(f"      Error creating roof face: {e}")

            except Building.DoesNotExist:
                print(f"Building ID {building_id} does not exist.")
                skipped_count += 1
                continue

        print("\n==== Summary ====")
        print(f"Total Buildings Processed: {len(building_ids) - skipped_count}")
        print(f"Total Faces Generated: {processed_count}")
        print(f"Skipped Buildings: {skipped_count}")
        print(f"Skipped due to Geometry Issues: {len(skipped_due_to_geometry)}")
        print(f"Skipped due to Small Area: {len(skipped_due_to_area)}")
        print("=================")

