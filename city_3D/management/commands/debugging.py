from django.contrib.gis.geos import MultiPolygon
from shapely.geometry import shape, Polygon as ShapelyPolygon, MultiPolygon as ShapelyMultiPolygon
from shapely.validation import explain_validity
from django.core.management.base import BaseCommand
import shapely.wkb

class Command(BaseCommand):
    help = "Generate BuildingFace data for a single building"

    def handle(self, *args, **kwargs):
        # Manually specify building details
        building_geometry_wkt = "MULTIPOLYGON(((72.52821838969341 23.05439083820052,72.52815595341147 23.05428144910028,72.52805541142327 23.05433408194941,72.52811804563602 23.05443263303459,72.52821838969341 23.05439083820052)))"
        building_height = 6

        # Convert WKT to GEOSGeometry
        building_geometry = MultiPolygon.from_ewkt(f"SRID=4326;{building_geometry_wkt}")

        # Debug: Validate geometry
        print(f"Building Geometry Type: {building_geometry.geom_type}")
        print(f"Valid Geometry: {building_geometry.valid}")
        print(f"Geometry Area: {building_geometry.area}")

        # Convert GEOSGeometry to Shapely geometry using WKB
        try:
            shapely_geometry = shapely.wkb.loads(bytes(building_geometry.wkb))
        except Exception as e:
            print(f"Error converting to Shapely geometry: {e}")
            return

        # Process MultiPolygon or Polygon
        if isinstance(shapely_geometry, ShapelyMultiPolygon):
            polygons = shapely_geometry.geoms  # Use .geoms to access individual polygons
        elif isinstance(shapely_geometry, ShapelyPolygon):
            polygons = [shapely_geometry]
        else:
            print("Invalid geometry type for processing. Exiting.")
            return

        for index, polygon in enumerate(polygons):
            print(f"Processing Polygon {index + 1}")
            print(f"Raw WKT: {polygon.wkt}")
            print(f"Polygon Area: {polygon.area}")

            if polygon.exterior:
                print(f"Exterior Coordinates: {list(polygon.exterior.coords)}")
            else:
                print("No valid exterior. Investigating further...")

                # Check validity issues using Shapely
                print(f"Shapely Validity Issue: {explain_validity(polygon)}")

                # Attempt to fix the geometry
                if not polygon.is_valid:
                    print("Attempting to fix invalid polygon...")
                    fixed_polygon = polygon.buffer(0)
                    if fixed_polygon.is_valid:
                        print("Polygon fixed successfully.")
                        polygon = fixed_polygon
                    else:
                        print("Failed to fix polygon.")
                        continue

            # If the geometry is valid and large enough, proceed with processing
            if polygon.area >= 1e-6:
                print("Processing valid polygon...")
                # Continue with face generation logic
            else:
                print(f"Polygon Area is too small ({polygon.area}). Skipping.")
