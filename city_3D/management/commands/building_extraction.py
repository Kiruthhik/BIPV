from django.contrib.gis.gdal import DataSource
from city_3D.models import Building
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = "Generate BuildingFace data for a single building"
    def handle(self, *args, **options):
        building = Building.objects.get(id=10457)
        with open("debug_building.geojson", "w") as f:
            f.write(building.geometry.geojson)
        
        #return super().handle(*args, **options)

