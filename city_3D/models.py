from django.contrib.gis.db import models


class Building(models.Model):
    height = models.FloatField(null=True, blank=True)  # Height from the shapefile
    geometry = models.MultiPolygonField(srid=32643)  # Allow for both Polygon and MultiPolygon
    total_solar_potential = models.FloatField(null=True, blank=True) 

    

    def __str__(self):
        return f"Building {self.id} (Height: {self.height})"
    
class BuildingFace(models.Model):
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name='faces')
    geometry = models.PolygonField(srid=32643, dim=3)  # 3D individual face geometry
    orientation = models.FloatField()  # Azimuth (0° = North, 90° = East, etc.)
    tilt = models.FloatField(default=90)  # Tilt in degrees (90° for vertical walls)
    solar_potential = models.FloatField(null=True, blank=True)  # Total solar potential (kWh) for the face
    area = models.FloatField(null=True, blank=True)
    def __str__(self):
        return f"Face {self.id} of Building {self.building.id} (Orientation: {self.orientation}°)"



class VirtualGridCentroid(models.Model):
    building_face = models.ForeignKey(BuildingFace, on_delete=models.CASCADE, related_name='centroids')
    label = models.CharField(max_length=10)  # e.g., "grid00"
    centroid = models.PointField(srid=32643, dim=3)  # 3D centroid location
    def __str__(self):
        return f"Centroid {self.label} of Face {self.building_face.id}"
    

class ShadowAnalysis(models.Model):
    centroid = models.ForeignKey(VirtualGridCentroid, on_delete=models.CASCADE, related_name='shadow_analysis')
    month = models.IntegerField()  # Store month as an integer (1 for January, 12 for December)
    hour = models.IntegerField()  # Store the hour in 24-hour format (5 for 5 AM, 19 for 7 PM)
    shadow = models.BooleanField()  # True if shadow is present, False otherwise

    class Meta:
        unique_together = ('centroid', 'month', 'hour')  # Ensure no duplicate entries for centroid, month, and hour

    def __str__(self):
        return f"Shadow for Centroid {self.centroid.label} - Month: {self.month}, Hour: {self.hour}"

class ShadowAnalysis_new(models.Model):
    centroid = models.ForeignKey(VirtualGridCentroid, on_delete=models.CASCADE, related_name='shadow_analysiss')
    month = models.IntegerField()  # Store month as an integer (1 for January, 12 for December)
    hour = models.IntegerField()  # Store the hour in 24-hour format (5 for 5 AM, 19 for 7 PM)
    shadow = models.BooleanField()  # True if shadow is present, False otherwise

    class Meta:
        unique_together = ('centroid', 'month', 'hour')  # Ensure no duplicate entries for centroid, month, and hour

    def __str__(self):
        return f"Shadow for Centroid {self.centroid.label} - Month: {self.month}, Hour: {self.hour}"

class Potential_Estimate(models.Model):
    face = models.ForeignKey(BuildingFace, on_delete=models.CASCADE, related_name='potential')
    month = models.IntegerField()
    date = models.DateField()
    potential = models.FloatField(null=True, blank=True) 
    irradiance = models.FloatField(null=True, blank=True) 





class Grid(models.Model):
    face = models.ForeignKey(BuildingFace, on_delete=models.CASCADE, related_name='grids')
    geometry = models.PolygonField(srid=32643, dim=3)  # 3D grid cell geometry (derived from face geometry)
    x_position = models.IntegerField()  # X-coordinate (local to the face grid)
    y_position = models.IntegerField()  # Y-coordinate (local to the face grid)
    solar_potential = models.FloatField(default=0.0)  # Solar potential (kWh) for the grid
    is_in_shadow = models.BooleanField(default=False)  # Whether the grid is in shadow
    area = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"Grid ({self.x_position}, {self.y_position}) on Face {self.face.id}"
    


class Grid2D(models.Model):
    """
    Represents 2D grid cells derived from BuildingFace for easier manipulation and storage.
    These grids can later be assembled back into 3D grids for visualization.
    """
    face = models.ForeignKey(BuildingFace, on_delete=models.CASCADE, related_name='grids_2d')
    geometry = models.PolygonField(srid=32643, dim=2)  # 2D grid geometry
    x_position = models.IntegerField()  # X-coordinate in the face's local grid system
    y_position = models.IntegerField()  # Y-coordinate in the face's local grid system
    height_start = models.FloatField(null=True, blank=True)  # Starting height of the grid in 3D
    height_end = models.FloatField(null=True, blank=True)  # Ending height of the grid in 3D
    solar_potential = models.FloatField(default=0.0)  # Solar potential (kWh) for the grid
    is_in_shadow = models.BooleanField(default=False)  # Whether the grid is in shadow
    area = models.FloatField(null=True, blank=True)
    def __str__(self):
        return f"2D Grid ({self.x_position}, {self.y_position}) on Face {self.face.id}"

    def to_3d_grid(self):
        """
        Converts this 2D grid to a 3D Polygon using height_start and height_end.
        """
        if not self.geometry:
            raise ValueError("Geometry is not defined for this 2D grid.")

        coords = list(self.geometry.coords[0])
        coords_3d = [(x, y, self.height_start) for x, y in coords] + \
                    [(x, y, self.height_end) for x, y in coords[::-1]]
        return models.Polygon(coords_3d, srid=self.geometry.srid)
    
class Grid3D(models.Model):
    face = models.ForeignKey(BuildingFace, on_delete=models.CASCADE, related_name='grids_3d')
    geometry = models.PolygonField(srid=32643, dim=3)  # 3D grid geometry
    x_position = models.IntegerField()  # X-coordinate (local grid index)
    y_position = models.IntegerField()  # Y-coordinate (local grid index)
    z_position = models.IntegerField()  # Z-coordinate (local grid index for stacking)
    solar_potential = models.FloatField(default=0.0)  # Solar potential (kWh)
    is_in_shadow = models.BooleanField(default=False)  # Shadow status
    area = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"Grid ({self.x_position}, {self.y_position}, {self.z_position}) on Face {self.face.id}"
