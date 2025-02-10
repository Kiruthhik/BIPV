

from django.core.management.base import BaseCommand

# Define the Command class, inheriting from BaseCommand



from city_3D.models import Building, BuildingFace
from django.contrib.gis.geos import Polygon, LinearRing, MultiPolygon
def generate_building_faces():
    from django.db import transaction
    buildings = Building.objects.all()

    # Lists to track processing statistics
    processed_count = 0
    skipped_count = 0
    skipped_due_to_area = []
    skipped_due_to_geometry = []

    # Set thresholds for main and minor polygons
    MIN_AREA_MAIN_THRESHOLD = 1e-4  # For valid, main buildings
    MIN_AREA_MINOR_THRESHOLD = 1e-6  # For smaller auxiliary structures

    for building in buildings:
        print(f"Processing Building ID: {building.id}")
        
        # Get building footprint (geometry) and height
        footprint = building.geometry
        height = building.height

        # Check if geometry exists
        if not footprint or not height:
            print(f"Skipping Building {building.id} due to missing geometry or height")
            skipped_count += 1
            continue

        # Ensure we're working with individual Polygons
        if footprint.geom_type == "MultiPolygon":
            print(f"Building {building.id} has a MultiPolygon geometry with {len(footprint)} polygons.")
            polygons = list(footprint)  # Decompose MultiPolygon into individual Polygons
        elif footprint.geom_type == "Polygon":
            print(f"Building {building.id} has a Polygon geometry.")
            polygons = [footprint]  # Treat it as a single Polygon
        else:
            print(f"Unsupported geometry type for Building {building.id}: {footprint.geom_type}")
            skipped_due_to_geometry.append(building.id)
            continue

        # Process each Polygon in the MultiPolygon
        for idx, polygon in enumerate(polygons, start=1):
            print(f"  Processing Polygon {idx} for Building {building.id}")

            # Validate the polygon
            if polygon.empty:
                print(f"  Polygon {idx} for Building {building.id} is empty. Skipping.")
                skipped_due_to_geometry.append(building.id)
                continue

            # Check for realistic area
            if polygon.area < MIN_AREA_MINOR_THRESHOLD:
                print(f"  Polygon {idx} for Building {building.id} has a very small area ({polygon.area}). Skipping.")
                skipped_due_to_area.append(building.id)
                continue

            # Attempt to fix invalid geometries
            if not polygon.valid:
                print(f"  Polygon {idx} for Building {building.id} is invalid. Attempting to fix...")
                polygon = polygon.buffer(0)  # Fix common issues
                if not polygon.valid:
                    print(f"  Polygon {idx} for Building {building.id} could not be fixed. Skipping.")
                    skipped_due_to_geometry.append(building.id)
                    continue

            # Ensure the polygon has a valid exterior
            if not hasattr(polygon, 'exterior') or not polygon.exterior:
                print(f"  Polygon {idx} for Building {building.id} has no valid exterior. Skipping.")
                skipped_due_to_geometry.append(building.id)
                continue

            # Debug exterior details
            print(f"  Polygon {idx} Exterior Details:")
            print(f"    Exterior Coordinates: {polygon.exterior.coords[:5]}")  # Show the first 5 coordinates

            # Create wall faces from the exterior boundary
            exterior_coords = polygon.exterior.coords  # Outer boundary coordinates
            for i in range(len(exterior_coords) - 1):  # Iterate through each edge
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
                    # Create a wall geometry
                    wall_geometry = Polygon(LinearRing(wall_coords))
                except Exception as e:
                    print(f"    Error creating wall geometry for Building {building.id}: {e}")
                    continue

                # Calculate the orientation (azimuth) of the wall
                orientation = calculate_wall_orientation(coord1, coord2)

                # Save the wall face
                try:
                    with transaction.atomic():
                        wall_face = BuildingFace(
                            building=building,
                            geometry=wall_geometry,
                            orientation=orientation,
                            tilt=90  # Vertical walls
                        )
                        wall_face.save()
                        print(f"    Created Wall Face (Orientation: {orientation}) for Building {building.id}")
                        processed_count += 1
                except Exception as e:
                    print(f"    Error saving wall face for Building {building.id}: {e}")

    # Summary of the operation
    print("\nSummary:")
    print(f"  Processed Buildings: {processed_count}")
    print(f"  Skipped Buildings: {skipped_count}")
    print(f"  Skipped due to small area: {len(skipped_due_to_area)}")
    print(f"  Skipped due to geometry issues: {len(skipped_due_to_geometry)}")





def calculate_wall_orientation(coord1, coord2):
    """Calculate azimuth (orientation) of a wall edge based on its coordinates."""
    import math
    dx = coord2[0] - coord1[0]
    dy = coord2[1] - coord1[1]
    azimuth = (math.degrees(math.atan2(dy, dx)) + 360) % 360
    return azimuth

class Command(BaseCommand):
    def handle(self, *args, **options):
        generate_building_faces()

'''claude '''
# from django.core.management.base import BaseCommand
# from django.contrib.gis.geos import MultiPolygon, Polygon, LinearRing
# from city_3D.models import Building, BuildingFace

# class Command(BaseCommand):
#     help = "Generate BuildingFace data for all buildings"

#     def handle(self, *args, **kwargs):
#         # Process all buildings
#         for building in Building.objects.all():
#             print(f"Processing Building ID: {building.id}")
#             try:
#                 process_building_faces(building)
#                 print(f"Successfully processed Building ID: {building.id}")
#             except Exception as e:
#                 print(f"Error processing Building ID: {building.id} - {e}")

# def process_building_faces(building):
#     """Process a single building into its constituent faces."""
#     height = building.height

#     # Get the footprint polygon(s)
#     multi_polygon = building.geometry

#     if multi_polygon.geom_type == "Polygon":
#         polygons = [multi_polygon]
#     elif multi_polygon.geom_type == "MultiPolygon":
#         polygons = list(multi_polygon)
#     else:
#         print(f"Unsupported geometry type: {multi_polygon.geom_type}. Skipping.")
#         return

#     faces = []
#     for polygon in polygons:
#         if not hasattr(polygon, "exterior") or not polygon.exterior:
#             print(f"Polygon for Building ID {building.id} has no valid exterior. Skipping.")
#             continue

#         exterior_ring = polygon.exterior.coords  # Get exterior ring coordinates

#         # Process rooftop (same as footprint but at height)
#         roof_coords = [(x, y, height) for x, y in exterior_ring]
#         roof = BuildingFace(
#             building=building,
#             face_type="ROOF",
#             geometry=Polygon(roof_coords),
#             area=polygon.area
#         )
#         faces.append(roof)

#         # Process walls
#         prev_point = None
#         for point in exterior_ring:
#             if prev_point is not None:
#                 # Create wall face (rectangle) from two ground points and their elevated versions
#                 wall_coords = [
#                     (prev_point[0], prev_point[1], 0),  # Bottom left
#                     (point[0], point[1], 0),           # Bottom right
#                     (point[0], point[1], height),      # Top right
#                     (prev_point[0], prev_point[1], height),  # Top left
#                     (prev_point[0], prev_point[1], 0),  # Close the polygon
#                 ]

#                 wall = BuildingFace(
#                     building=building,
#                     face_type="WALL",
#                     geometry=Polygon(wall_coords),
#                     area=calculate_wall_area(wall_coords)
#                 )
#                 faces.append(wall)

#             prev_point = point

#     # Bulk create all faces
#     BuildingFace.objects.bulk_create(faces)

# def calculate_wall_area(coords):
#     """Calculate the area of a vertical wall face."""
#     # Simple calculation of rectangle area (height * width)
#     width = ((coords[0][0] - coords[1][0])**2 +
#              (coords[0][1] - coords[1][1])**2)**0.5
#     height = coords[2][2]  # Vertical height
#     return width * height



'''foot print and height utilization approach'''
# from django.core.management.base import BaseCommand

# from django.contrib.gis.geos import Polygon, MultiPolygon, LinearRing
# from city_3D.models import Building, BuildingFace


# def generate_building_faces():
#     buildings = Building.objects.all()
#     skipped_buildings = 0
#     processed_buildings = 0
#     generated_faces = 0

#     for building in buildings:
#         print(f"Processing Building ID: {building.id}")

#         footprint = building.geometry  # Base geometry
#         height = building.height  # Building height

#         if not footprint or not height:
#             print(f"Skipping Building {building.id} due to missing geometry or height")
#             skipped_buildings += 1
#             continue

#         if footprint.geom_type == "Polygon":
#             polygons = [footprint]  # Treat it as a single polygon
#         elif footprint.geom_type == "MultiPolygon":
#             polygons = list(footprint)  # Decompose MultiPolygon into individual polygons
#         else:
#             print(f"Skipping Building {building.id} as it is not a Polygon or MultiPolygon")
#             skipped_buildings += 1
#             continue

#         for index, polygon in enumerate(polygons):
#             # Debug: Print details of each polygon
#             print(f"  Processing Polygon {index + 1} for Building {building.id}")
#             print(f"    Polygon Valid: {polygon.valid}")  # Use .valid instead of .is_valid
#             print(f"    Polygon Area: {polygon.area}")

#             # Check if the polygon has a valid exterior
#             if not hasattr(polygon, 'exterior') or polygon.exterior is None:
#                 print(f"  Skipping Polygon {index + 1} for Building {building.id}: No valid exterior")
#                 continue

#             # Create the roof face
#             try:
#                 roof = Polygon(
#                     [(x, y, height) for x, y in polygon.exterior.coords]
#                 )
#                 roof_face = BuildingFace(
#                     building=building,
#                     geometry=roof,
#                     orientation=0,  # Orientation is irrelevant for roof
#                     tilt=0  # Flat roof
#                 )
#                 roof_face.save()
#                 generated_faces += 1
#                 print(f"    Created Roof Face for Building {building.id}")
#             except Exception as e:
#                 print(f"    Error creating roof face for Building {building.id}: {e}")
#                 continue

#             # Create wall faces from the exterior boundary
#             exterior_coords = polygon.exterior.coords
#             for i in range(len(exterior_coords) - 1):
#                 coord1 = exterior_coords[i]
#                 coord2 = exterior_coords[i + 1]

#                 # Create wall polygon (quadrilateral)
#                 try:
#                     wall_coords = [
#                         (coord1[0], coord1[1], 0),  # Bottom-left
#                         (coord2[0], coord2[1], 0),  # Bottom-right
#                         (coord2[0], coord2[1], height),  # Top-right
#                         (coord1[0], coord1[1], height),  # Top-left
#                         (coord1[0], coord1[1], 0)  # Close the loop
#                     ]
#                     wall_geometry = Polygon(LinearRing(wall_coords))

#                     # Calculate orientation (azimuth)
#                     orientation = calculate_wall_orientation(coord1, coord2)

#                     # Save wall face
#                     wall_face = BuildingFace(
#                         building=building,
#                         geometry=wall_geometry,
#                         orientation=orientation,
#                         tilt=90  # Vertical wall
#                     )
#                     wall_face.save()
#                     generated_faces += 1
#                     print(f"    Created Wall Face (Orientation: {orientation}) for Building {building.id}")
#                 except Exception as e:
#                     print(f"    Error creating wall face for Building {building.id}: {e}")

#         processed_buildings += 1

#     # Summary
#     print("\n==== Summary ====")
#     print(f"Total Buildings Processed: {processed_buildings}")
#     print(f"Total Buildings Skipped: {skipped_buildings}")
#     print(f"Total Faces Generated: {generated_faces}")
#     print("=================\n")


# def calculate_wall_orientation(coord1, coord2):
#     """Calculate the azimuth (orientation) of a wall edge."""
#     import math
#     dx = coord2[0] - coord1[0]
#     dy = coord2[1] - coord1[1]
#     azimuth = (math.degrees(math.atan2(dy, dx)) + 360) % 360
#     return azimuth


# class Command(BaseCommand):
#     help = "Generate BuildingFace data for each building"

#     def handle(self, *args, **kwargs):
#         generate_building_faces()


# from django.core.management.base import BaseCommand
# from django.contrib.gis.geos import MultiPolygon, Polygon, LinearRing
# from city_3D.models import Building, BuildingFace
# from django.db import transaction


# class Command(BaseCommand):
#     help = "Generate BuildingFace data for all buildings"

#     def handle(self, *args, **kwargs):
#         self.generate_building_faces()

#     def generate_building_faces(self):
#         # Fetch all buildings from the database
#         buildings = Building.objects.all()

#         # Statistics for processing
#         processed_count = 0
#         skipped_count = 0
#         generated_faces = 0
#         skipped_due_to_geometry = []
#         skipped_due_to_area = []

#         # Area thresholds
#         MIN_AREA_MAIN_THRESHOLD = 1  # Minimum valid area (in square meters)
#         MIN_AREA_MINOR_THRESHOLD = 0.1  # For very small auxiliary polygons

#         for building in buildings:
#             print(f"Processing Building ID: {building.id}")
#             try:
#                 # Get building footprint and height
#                 footprint = building.geometry
#                 height = building.height

#                 if not footprint or not height:
#                     print(f"Skipping Building {building.id} due to missing geometry or height")
#                     skipped_count += 1
#                     continue

#                 # Handle MultiPolygon or Polygon geometries
#                 if footprint.geom_type == "MultiPolygon":
#                     polygons = list(footprint)
#                 elif footprint.geom_type == "Polygon":
#                     polygons = [footprint]
#                 else:
#                     print(f"Unsupported geometry type for Building ID {building.id}: {footprint.geom_type}")
#                     skipped_due_to_geometry.append(building.id)
#                     continue

#                 for idx, polygon in enumerate(polygons, start=1):
#                     print(f"  Processing Polygon {idx} for Building {building.id}")

#                     # Check polygon validity
#                     if not polygon.valid:
#                         print(f"    Polygon {idx} is invalid. Attempting to fix...")
#                         polygon = polygon.buffer(0)
#                         if not polygon.valid:
#                             print(f"    Polygon {idx} could not be fixed. Skipping.")
#                             skipped_due_to_geometry.append(building.id)
#                             continue

#                     # Check for area thresholds
#                     if polygon.area < MIN_AREA_MINOR_THRESHOLD:
#                         print(f"    Polygon {idx} has a very small area ({polygon.area}). Skipping.")
#                         skipped_due_to_area.append(building.id)
#                         continue

#                     # Ensure polygon has a valid exterior
#                     if not hasattr(polygon, "exterior") or not polygon.exterior:
#                         print(f"    Polygon {idx} has no valid exterior. Skipping.")
#                         skipped_due_to_geometry.append(building.id)
#                         continue

#                     # Process the rooftop
#                     exterior_coords = polygon.exterior.coords
#                     roof_coords = [(x, y, height) for x, y in exterior_coords]

#                     try:
#                         roof_face = BuildingFace(
#                             building=building,
#                             face_type="ROOF",
#                             geometry=Polygon(roof_coords),
#                             area=polygon.area,
#                         )
#                         roof_face.save()
#                         print(f"    Created Roof Face for Building {building.id}")
#                         generated_faces += 1
#                     except Exception as e:
#                         print(f"    Error creating roof face for Building {building.id}: {e}")
#                         continue

#                     # Process the walls
#                     prev_point = None
#                     for point in exterior_coords:
#                         if prev_point is not None:
#                             wall_coords = [
#                                 (prev_point[0], prev_point[1], 0),
#                                 (point[0], point[1], 0),
#                                 (point[0], point[1], height),
#                                 (prev_point[0], prev_point[1], height),
#                                 (prev_point[0], prev_point[1], 0),
#                             ]

#                             try:
#                                 wall_face = BuildingFace(
#                                     building=building,
#                                     face_type="WALL",
#                                     geometry=Polygon(LinearRing(wall_coords)),
#                                     area=self.calculate_wall_area(wall_coords),
#                                 )
#                                 wall_face.save()
#                                 print(f"    Created Wall Face for Building {building.id}")
#                                 generated_faces += 1
#                             except Exception as e:
#                                 print(f"    Error creating wall face for Building {building.id}: {e}")

#                         prev_point = point

#                 processed_count += 1

#             except Exception as e:
#                 print(f"Error processing Building ID {building.id}: {e}")
#                 skipped_count += 1

#         # Print summary
#         print("\n==== Summary ====")
#         print(f"Total Buildings Processed: {processed_count}")
#         print(f"Total Buildings Skipped: {skipped_count}")
#         print(f"Total Faces Generated: {generated_faces}")
#         print(f"Skipped due to geometry issues: {len(skipped_due_to_geometry)}")
#         print(f"Skipped due to small area: {len(skipped_due_to_area)}")
#         print("=================\n")

#     def calculate_wall_area(self, coords):
#         """Calculate the area of a vertical wall face."""
#         # Simple calculation of rectangle area (height * width)
#         width = ((coords[0][0] - coords[1][0]) ** 2 + (coords[0][1] - coords[1][1]) ** 2) ** 0.5
#         height = coords[2][2]  # Vertical height
#         return width * height

'''latest'''
# from django.core.management.base import BaseCommand
# from django.contrib.gis.geos import Polygon, MultiPolygon, LinearRing
# from city_3D.models import Building, BuildingFace
# from django.db import transaction

# class Command(BaseCommand):
#     help = "Generate BuildingFace data for all buildings"

#     def handle(self, *args, **kwargs):
#         print("Starting BuildingFace generation...")
#         self.generate_building_faces()

#     def generate_building_faces(self):
#         # Fetch all buildings from the database
#         buildings = Building.objects.all()

#         # Statistics for processing
#         processed_count = 0
#         skipped_count = 0
#         generated_faces = 0
#         skipped_due_to_geometry = []
#         skipped_due_to_area = []

#         # Area thresholds
#         MIN_AREA_MAIN_THRESHOLD = 1.0  # Minimum valid area (in square meters)
#         MIN_AREA_MINOR_THRESHOLD = 0.1  # For very small auxiliary polygons

#         for building in buildings:
#             print(f"\nProcessing Building ID: {building.id}")
#             try:
#                 # Get building footprint and height
#                 footprint = building.geometry
#                 height = building.height

#                 if not footprint or not height:
#                     print(f"Skipping Building {building.id} due to missing geometry or height")
#                     skipped_count += 1
#                     continue

#                 print(f"  Footprint Type: {footprint.geom_type}, Height: {height}")

#                 # Handle MultiPolygon or Polygon geometries
#                 if footprint.geom_type == "MultiPolygon":
#                     polygons = list(footprint)
#                     print(f"  MultiPolygon contains {len(polygons)} polygons.")
#                 elif footprint.geom_type == "Polygon":
#                     polygons = [footprint]
#                 else:
#                     print(f"  Unsupported geometry type for Building ID {building.id}: {footprint.geom_type}")
#                     skipped_due_to_geometry.append(building.id)
#                     continue

#                 for idx, polygon in enumerate(polygons, start=1):
#                     print(f"    Processing Polygon {idx} for Building {building.id}")

#                     # Check polygon validity
#                     if not polygon.valid:
#                         print(f"      Polygon {idx} is invalid. Attempting to fix...")
#                         polygon = polygon.buffer(0)
#                         if not polygon.valid:
#                             print(f"      Polygon {idx} could not be fixed. Skipping.")
#                             skipped_due_to_geometry.append(building.id)
#                             continue

#                     # Check for area thresholds
#                     print(f"      Polygon Area: {polygon.area}")
#                     if polygon.area < MIN_AREA_MINOR_THRESHOLD:
#                         print(f"      Polygon {idx} has a very small area ({polygon.area}). Skipping.")
#                         skipped_due_to_area.append(building.id)
#                         continue

#                     # Ensure polygon has a valid exterior
#                     if not hasattr(polygon, "exterior") or not polygon.exterior:
#                         print(f"      Polygon {idx} has no valid exterior. Skipping.")
#                         skipped_due_to_geometry.append(building.id)
#                         continue

#                     # Process the rooftop
#                     exterior_coords = polygon.exterior.coords
#                     roof_coords = [(x, y, height) for x, y in exterior_coords]

#                     try:
#                         roof_face = BuildingFace(
#                             building=building,
#                             face_type="ROOF",
#                             geometry=Polygon(roof_coords),
#                             area=polygon.area,
#                         )
#                         roof_face.save()
#                         print(f"      Created Roof Face for Building ID {building.id}")
#                         generated_faces += 1
#                     except Exception as e:
#                         print(f"      Error creating roof face for Building ID {building.id}: {e}")
#                         continue

#                     # Process the walls
#                     prev_point = None
#                     for point in exterior_coords:
#                         if prev_point is not None:
#                             wall_coords = [
#                                 (prev_point[0], prev_point[1], 0),
#                                 (point[0], point[1], 0),
#                                 (point[0], point[1], height),
#                                 (prev_point[0], prev_point[1], height),
#                                 (prev_point[0], prev_point[1], 0),
#                             ]

#                             try:
#                                 wall_face = BuildingFace(
#                                     building=building,
#                                     face_type="WALL",
#                                     geometry=Polygon(LinearRing(wall_coords)),
#                                     area=self.calculate_wall_area(wall_coords),
#                                 )
#                                 wall_face.save()
#                                 print(f"      Created Wall Face for Building ID {building.id}")
#                                 generated_faces += 1
#                             except Exception as e:
#                                 print(f"      Error creating wall face for Building ID {building.id}: {e}")

#                         prev_point = point

#                 processed_count += 1

#             except Exception as e:
#                 print(f"Error processing Building ID {building.id}: {e}")
#                 skipped_count += 1

#         # Print summary
#         print("\n==== Summary ====")
#         print(f"Total Buildings Processed: {processed_count}")
#         print(f"Total Buildings Skipped: {skipped_count}")
#         print(f"Total Faces Generated: {generated_faces}")
#         print(f"Skipped due to geometry issues: {len(skipped_due_to_geometry)}")
#         print(f"Skipped due to small area: {len(skipped_due_to_area)}")
#         print("=================\n")

#     def calculate_wall_area(self, coords):
#         """Calculate the area of a vertical wall face."""
#         try:
#             width = ((coords[0][0] - coords[1][0]) ** 2 + (coords[0][1] - coords[1][1]) ** 2) ** 0.5
#             height = coords[2][2]  # Vertical height
#             return width * height
#         except Exception as e:
#             print(f"Error calculating wall area: {e}")
#             return 0
