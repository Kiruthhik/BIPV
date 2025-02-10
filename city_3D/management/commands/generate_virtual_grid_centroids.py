import os

# Set the PROJ_LIB path for pyproj or GDAL only in this Python process
os.environ['PROJ_LIB'] = r'C:\Users\HP\AppData\Local\Programs\Python\Python312\Lib\site-packages\pyproj\proj_dir\share\proj'
os.environ['GDAL_DATA'] = r'C:\Users\HP\AppData\Local\Programs\Python\Python312\Lib\site-packages\pyproj\proj_dir\share\proj'

'''initial setup using upfront logic'''
# from django.core.management.base import BaseCommand
# from city_3D.models import BuildingFace, VirtualGridCentroid
# from django.contrib.gis.geos import Point, Polygon


# class Command(BaseCommand):
#     help = "Generate virtual grid centroids for building faces"

#     def handle(self, *args, **kwargs):
#         self.generate_virtual_grid_centroids()

#     def generate_virtual_grid_centroids(self):
#         faces = BuildingFace.objects.filter(building__id__in = [1,2,3])

#         processed_count = 0
#         skipped_faces = []

#         for face in faces:
#             print(f"Processing Face ID: {face.id}")

#             # Get the face geometry
#             geometry = face.geometry

#             # Check for invalid geometry and attempt to fix
#             if not geometry or not geometry.valid:
#                 print(f"  Face {face.id} has invalid geometry. Attempting to fix...")
#                 try:
#                     geometry = geometry.buffer(0)  # Fix common geometry issues
#                     if not geometry.valid:
#                         print(f"  Face {face.id} could not be fixed. Skipping.")
#                         skipped_faces.append(face.id)
#                         continue
#                 except Exception as e:
#                     print(f"  Error fixing geometry for Face {face.id}: {e}")
#                     skipped_faces.append(face.id)
#                     continue

#             # Ensure the geometry has enough points
#             if len(geometry.coords) < 4:  # Minimum 4 points to form a closed polygon
#                 print(f"  Face {face.id} has too few points. Skipping.")
#                 skipped_faces.append(face.id)
#                 continue

#             # Use extent for grid calculations as a fallback
#             min_x, min_y, max_x, max_y = geometry.extent
#             if face.tilt == 90:
#                 # For vertical faces, consider XZ or YZ bounds
#                 min_z, max_z = geometry.extent[2], geometry.extent[3]
#                 x_step = (max_x - min_x) / 2
#                 z_step = (max_z - min_z) / 2
#                 grid_centroids = [
#                     (min_x + x_step / 2, min_y, min_z + z_step / 2, "grid00"),
#                     (min_x + x_step / 2, min_y, min_z + 3 * z_step / 2, "grid01"),
#                     (min_x + 3 * x_step / 2, min_y, min_z + z_step / 2, "grid10"),
#                     (min_x + 3 * x_step / 2, min_y, min_z + 3 * z_step / 2, "grid11"),
#                 ]
#             else:
#                 # For horizontal faces, use XY bounds
#                 x_step = (max_x - min_x) / 2
#                 y_step = (max_y - min_y) / 2
#                 grid_centroids = [
#                     (min_x + x_step / 2, min_y + y_step / 2, 0, "grid00"),
#                     (min_x + x_step / 2, min_y + 3 * y_step / 2, 0, "grid01"),
#                     (min_x + 3 * x_step / 2, min_y + y_step / 2, 0, "grid10"),
#                     (min_x + 3 * x_step / 2, min_y + 3 * y_step / 2, 0, "grid11"),
#                 ]

#             # Save centroids
#             for x, y, z, label in grid_centroids:
#                 try:
#                     centroid_point = Point(x, y, z, srid=geometry.srid)
#                     VirtualGridCentroid.objects.create(
#                         building_face=face,
#                         label=label,
#                         centroid=centroid_point,
#                     )
#                     print(f"    Created centroid {label} for Face ID {face.id}")
#                 except Exception as e:
#                     print(f"    Error creating centroid {label} for Face ID {face.id}: {e}")
#                     continue

#             processed_count += 1

#         # Summary of the operation
#         print("\nSummary:")
#         print(f"  Processed Faces: {processed_count}")
#         print(f"  Skipped Faces: {len(skipped_faces)}")
#         if skipped_faces:
#             print(f"  Skipped Face IDs: {skipped_faces}")

'''takeaways from the grid splitting logic'''
# from django.core.management.base import BaseCommand
# from city_3D.models import BuildingFace, VirtualGridCentroid
# from django.contrib.gis.geos import Point


# class Command(BaseCommand):
#     help = "Generate virtual grid centroids for building faces"

#     def handle(self, *args, **kwargs):
#         self.stdout.write("Starting centroid generation for BuildingFace objects...")

#         processed_count = 0
#         skipped_faces = []

#         for face in BuildingFace.objects.filter(building__id__in = [1,2,3]):  # Adjust filter for specific buildings if needed
#             self.stdout.write(f"Processing Face ID: {face.id}")

#             # Validate geometry
#             face_geom = face.geometry
#             if not face_geom:
#                 self.stderr.write(f"Face {face.id} has no geometry. Skipping.")
#                 skipped_faces.append(face.id)
#                 continue

#             if face_geom.geom_type != "Polygon":
#                 self.stderr.write(f"Face {face.id} geometry is not a Polygon. Skipping.")
#                 skipped_faces.append(face.id)
#                 continue

#             try:
#                 # Get bounding box coordinates
#                 min_x, min_y, max_x, max_y = face_geom.extent

#                 # Calculate midpoints for grid division
#                 mid_x = (min_x + max_x) / 2
#                 mid_y = (min_y + max_y) / 2

#                 # Z-coordinates handling
#                 z_min, z_max = 0, 0
#                 if face_geom.hasz:
#                     coords = list(face_geom.coords[0])
#                     z_min = min(coord[2] for coord in coords)
#                     z_max = max(coord[2] for coord in coords)
#                     mid_z = (z_max+z_min)/2

#                 # Handle vertical faces
#                 if face.tilt == 90:
#                     # Vertical faces
#                     print(f"Vertical face detected (Face ID: {face.id}). Orientation: {face.orientation}")
#                     print(f"Z-coordinate range: z_min={z_min}, z_max={z_max}")

#                     if 0 <= face.orientation < 90 or 270 <= face.orientation <= 360:  # YZ plane
#                         print(f"Vertical face lies in the YZ plane.")
#                         centroids = [
#                             ((min_y + mid_y) / 2, (z_min + mid_z) / 2, mid_x, "grid00"),
#                             ((mid_y + max_y) / 2, (z_min + mid_z) / 2, mid_x, "grid01"),
#                             ((min_y + mid_y) / 2, (mid_z + z_max) / 2, mid_x, "grid10"),
#                             ((mid_y + max_y) / 2, (mid_z + z_max) / 2, mid_x, "grid11"),
#                         ]
#                     else:  # XZ plane
#                         print(f"Vertical face lies in the XZ plane.")
#                         centroids = [
#                             ((min_x + mid_x) / 2, mid_y, (z_min + mid_z) / 2, "grid00"),
#                             ((mid_x + max_x) / 2, mid_y, (z_min + mid_z) / 2, "grid01"),
#                             ((min_x + mid_x) / 2, mid_y, (mid_z + z_max) / 2, "grid10"),
#                             ((mid_x + max_x) / 2, mid_y, (mid_z + z_max) / 2, "grid11"),
#                         ]
#                 else:
#                     # Horizontal faces
#                     print(f"Horizontal face detected (Face ID: {face.id}).")
#                     print(f"Z-coordinate is constant: z_min={z_min}, z_max={z_max}")
#                     centroids = [
#                         ((min_x + mid_x) / 2, (min_y + mid_y) / 2, z_max, "grid00"),
#                         ((mid_x + max_x) / 2, (min_y + mid_y) / 2, z_max, "grid01"),
#                         ((min_x + mid_x) / 2, (mid_y + max_y) / 2, z_max, "grid10"),
#                         ((mid_x + max_x) / 2, (mid_y + max_y) / 2, z_max, "grid11"),
#                     ]

#                 # Save centroids
#                 for x, y, z, label in centroids:
#                     try:
#                         centroid = Point(x, y, z, srid=face_geom.srid)
#                         VirtualGridCentroid.objects.create(
#                             building_face=face,
#                             label=label,
#                             centroid=centroid,
#                         )
#                         self.stdout.write(f"  Created centroid {label} for Face ID {face.id}")
#                     except Exception as e:
#                         self.stderr.write(f"  Error saving centroid {label} for Face {face.id}: {e}")
#                         continue

#                 processed_count += 1

#             except Exception as e:
#                 self.stderr.write(f"Error processing Face {face.id}: {e}")
#                 skipped_faces.append(face.id)

#         # Summary
#         self.stdout.write("\nSummary:")
#         self.stdout.write(f"  Processed Faces: {processed_count}")
#         self.stdout.write(f"  Skipped Faces: {len(skipped_faces)}")
#         if skipped_faces:
#             self.stdout.write(f"  Skipped Face IDs: {skipped_faces}")

'''from the building_faces.geojson file'''
# from django.core.management.base import BaseCommand
# from city_3D.models import BuildingFace, VirtualGridCentroid
# from django.contrib.gis.geos import Point
# import json
# from shapely.geometry import shape

# class Command(BaseCommand):
#     help = "Generate virtual grid centroids for building faces using GeoJSON data"

#     def handle(self, *args, **kwargs):
#         self.stdout.write("Starting centroid generation using GeoJSON data...")

#         # Load GeoJSON data
#         with open('building_facesid.geojson', 'r') as f:
#             geojson_data = json.load(f)

#         processed_count = 0
#         skipped_faces = []

#         for feature in geojson_data['features']:
#             properties = feature.get('properties', {})
#             geometry = feature.get('geometry', {})

#             # Get face_id and tilt from properties
#             face_id = properties.get('face_id')
#             tilt = properties.get('tilt', 0)  # Default tilt to 0
#             orientation = properties.get('orientation', 0)  # Default orientation to 0

#             if not face_id:
#                 self.stderr.write("No face_id found in properties. Skipping.")
#                 continue

#             # Retrieve the BuildingFace object
#             try:
#                 building_face = BuildingFace.objects.get(id=face_id)
#             except BuildingFace.DoesNotExist:
#                 self.stderr.write(f"BuildingFace with ID {face_id} does not exist. Skipping.")
#                 skipped_faces.append(face_id)
#                 continue

#             # Convert GeoJSON geometry to Shapely geometry
#             shapely_geom = shape(geometry)

#             # Generate centroids
#             try:
#                 centroids = self.generate_centroids(shapely_geom, tilt, orientation)
#                 for idx, centroid in enumerate(centroids):
#                     VirtualGridCentroid.objects.create(
#                         building_face=building_face,
#                         label=f'grid{idx:02}',
#                         centroid=Point(centroid.x, centroid.y, centroid.z if hasattr(centroid, 'z') else 0, srid=32643)
#                     )
#                 processed_count += 1
#                 self.stdout.write(f"Processed Face ID: {face_id}")

#             except Exception as e:
#                 self.stderr.write(f"Error processing Face ID {face_id}: {e}")
#                 skipped_faces.append(face_id)

#         # Summary
#         self.stdout.write("\nSummary:")
#         self.stdout.write(f"  Processed Faces: {processed_count}")
#         self.stdout.write(f"  Skipped Faces: {len(skipped_faces)}")
#         if skipped_faces:
#             self.stdout.write(f"  Skipped Face IDs: {skipped_faces}")

#     def generate_centroids(self, geom, tilt, orientation):
#         """
#         Generate virtual grid centroids for a given face geometry.

#         Args:
#             geom (Shapely geometry): The face geometry.
#             tilt (float): The tilt of the face (0.0 for horizontal, 90.0 for vertical).
#             orientation (float): The orientation of the face in degrees.

#         Returns:
#             List[Shapely Point]: A list of centroid points.
#         """
#         minx, miny, maxx, maxy = geom.bounds

#         if tilt == 90.0:
#             # For vertical faces, determine the plane (XZ or YZ)
#             if 0 <= orientation < 90 or 270 <= orientation <= 360:  # YZ plane
#                 minz = min(coord[2] for coord in geom.exterior.coords) if geom.has_z else 0
#                 maxz = max(coord[2] for coord in geom.exterior.coords) if geom.has_z else 1  # Default Z range
#                 z_step = (maxz - minz) / 2
#                 y_step = (maxy - miny) / 2
#                 centroids = [
#                     shape({'type': 'Point', 'coordinates': [(miny + y_step / 2), (minz + z_step / 2), (minx + maxx) / 2]}),  # grid00
#                     shape({'type': 'Point', 'coordinates': [(miny + 3 * y_step / 2), (minz + z_step / 2), (minx + maxx) / 2]}),  # grid01
#                     shape({'type': 'Point', 'coordinates': [(miny + y_step / 2), (minz + 3 * z_step / 2), (minx + maxx) / 2]}),  # grid10
#                     shape({'type': 'Point', 'coordinates': [(miny + 3 * y_step / 2), (minz + 3 * z_step / 2), (minx + maxx) / 2]}),  # grid11
#                 ]
#             else:  # XZ plane
#                 minz = min(coord[2] for coord in geom.exterior.coords) if geom.has_z else 0
#                 maxz = max(coord[2] for coord in geom.exterior.coords) if geom.has_z else 1  # Default Z range
#                 z_step = (maxz - minz) / 2
#                 x_step = (maxx - minx) / 2
#                 centroids = [
#                     shape({'type': 'Point', 'coordinates': [(minx + x_step / 2), (minz + z_step / 2), (miny + maxy) / 2]}),  # grid00
#                     shape({'type': 'Point', 'coordinates': [(minx + 3 * x_step / 2), (minz + z_step / 2), (miny + maxy) / 2]}),  # grid01
#                     shape({'type': 'Point', 'coordinates': [(minx + x_step / 2), (minz + 3 * z_step / 2), (miny + maxy) / 2]}),  # grid10
#                     shape({'type': 'Point', 'coordinates': [(minx + 3 * x_step / 2), (minz + 3 * z_step / 2), (miny + maxy) / 2]}),  # grid11
#                 ]
#         else:
#             # Horizontal faces (XY plane)
#             x_step = (maxx - minx) / 2
#             y_step = (maxy - miny) / 2
#             z_value = min(coord[2] for coord in geom.exterior.coords) if geom.has_z else 0  # Default Z
#             centroids = [
#                 shape({'type': 'Point', 'coordinates': [(minx + x_step / 2), (miny + y_step / 2), z_value]}),  # grid00
#                 shape({'type': 'Point', 'coordinates': [(minx + 3 * x_step / 2), (miny + y_step / 2), z_value]}),  # grid01
#                 shape({'type': 'Point', 'coordinates': [(minx + x_step / 2), (miny + 3 * y_step / 2), z_value]}),  # grid10
#                 shape({'type': 'Point', 'coordinates': [(minx + 3 * x_step / 2), (miny + 3 * y_step / 2), z_value]}),  # grid11
#             ]

#         return centroids

'''centroid without xz,yz pane assumption'''
from django.core.management.base import BaseCommand
from city_3D.models import BuildingFace, VirtualGridCentroid
from django.contrib.gis.geos import Point
import json
from shapely.geometry import shape

class Command(BaseCommand):
    help = "Generate virtual grid centroids for building faces using GeoJSON data"

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting centroid generation using GeoJSON data...")

        # Load GeoJSON data
        with open('building_facesid.geojson', 'r') as f:
            geojson_data = json.load(f)

        processed_count = 0
        skipped_faces = []

        for feature in geojson_data['features']:  # Limit to first 20 BuildingFace instances
            properties = feature.get('properties', {})
            geometry = feature.get('geometry', {})

            # Get face_id and tilt from properties
            face_id = properties.get('face_id')
            tilt = properties.get('tilt', 0)  # Default tilt to 0
            orientation = properties.get('orientation', 0)  # Default orientation to 0

            if not face_id:
                self.stderr.write("No face_id found in properties. Skipping.")
                continue

            # Retrieve the BuildingFace object
            try:
                building_face = BuildingFace.objects.get(id=face_id)
            except BuildingFace.DoesNotExist:
                self.stderr.write(f"BuildingFace with ID {face_id} does not exist. Skipping.")
                skipped_faces.append(face_id)
                continue

            # Convert GeoJSON geometry to Shapely geometry
            shapely_geom = shape(geometry)

            # Generate centroids
            try:
                centroids = self.generate_centroids(shapely_geom, tilt, orientation)
                for idx, centroid in enumerate(centroids):
                    VirtualGridCentroid.objects.create(
                        building_face=building_face,
                        label=f'grid{idx:02}',
                        centroid=Point(centroid[0], centroid[1], centroid[2], srid=32643)
                    )
                processed_count += 1
                self.stdout.write(f"Processed Face ID: {face_id}")

            except Exception as e:
                self.stderr.write(f"Error processing Face ID {face_id}: {e}")
                skipped_faces.append(face_id)

        # Summary
        self.stdout.write("\nSummary:")
        self.stdout.write(f"  Processed Faces: {processed_count}")
        self.stdout.write(f"  Skipped Faces: {len(skipped_faces)}")
        if skipped_faces:
            self.stdout.write(f"  Skipped Face IDs: {skipped_faces}")

    def generate_centroids(self, geom, tilt, orientation):
        """
        Generate virtual grid centroids for a given face geometry using the new midpoint-based approach.

        Args:
            geom (Shapely geometry): The face geometry.
            tilt (float): The tilt of the face (0.0 for horizontal, 90.0 for vertical).
            orientation (float): The orientation of the face in degrees.

        Returns:
            List[Tuple[float, float, float]]: A list of centroid coordinates for 2x2 grids.
        """
        if tilt == 90.0:
            # Get coordinates of the geometry
            coords = list(geom.exterior.coords)

            # Find the centroid of the polygon (cp)
            cp_x = sum(c[0] for c in coords[:-1]) / len(coords[:-1])
            cp_y = sum(c[1] for c in coords[:-1]) / len(coords[:-1])
            cp_z = sum(c[2] for c in coords[:-1]) / len(coords[:-1])
            cp = (cp_x, cp_y, cp_z)

            # Calculate midpoints of edges
            midpoints = []
            for i in range(len(coords) - 1):  # Skip the last duplicate point
                x_mid = (coords[i][0] + coords[i + 1][0]) / 2
                y_mid = (coords[i][1] + coords[i + 1][1]) / 2
                z_mid = (coords[i][2] + coords[i + 1][2]) / 2
                midpoints.append((x_mid, y_mid, z_mid))

            # Generate centroids for 2x2 grids
            centroids = []
            for i in range(len(midpoints)):
                m1 = midpoints[i]
                m2 = midpoints[(i + 1) % len(midpoints)]  # Wrap around to the first midpoint
                centroid_x = (cp[0] + m1[0] + m2[0]) / 3
                centroid_y = (cp[1] + m1[1] + m2[1]) / 3
                centroid_z = (cp[2] + m1[2] + m2[2]) / 3
                centroids.append((centroid_x, centroid_y, centroid_z))

            return centroids
        else:
            # Horizontal faces (XY plane)
            minx, miny, maxx, maxy = geom.bounds
            z_value = geom.exterior.coords[0][2] if geom.has_z else 0  # Default Z

            # Split the face into a 2x2 grid
            x_step = (maxx - minx) / 2
            y_step = (maxy - miny) / 2

            centroids = []

            # Create centroids for the 2x2 grid
            for i in range(2):
                for j in range(2):
                    centroid_x = minx + (i + 0.5) * x_step
                    centroid_y = miny + (j + 0.5) * y_step
                    centroids.append((centroid_x, centroid_y, z_value))

            return centroids
        
