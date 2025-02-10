# from django.contrib.gis import admin
# from .models import Building, BuildingFace, Grid

# @admin.register(Building)
# class BuildingAdmin(admin.OSMGeoAdmin):
#     list_display = ('id', 'height', 'total_solar_potential')

# @admin.register(BuildingFace)
# class BuildingFaceAdmin(admin.OSMGeoAdmin):
#     list_display = ('id', 'building', 'orientation', 'solar_potential')

# @admin.register(Grid)
# class GridAdmin(admin.OSMGeoAdmin):
#     list_display = ('id', 'face', 'x_position', 'y_position', 'solar_potential')

from django.contrib import admin
from .models import Building, BuildingFace, Grid3D, VirtualGridCentroid, ShadowAnalysis, Potential_Estimate
from django.utils.safestring import mark_safe
from django.db.models import Count, F, Sum, Case, When
# Register Building
import logging
logger = logging.getLogger(__name__)

class BuildingAdmin(admin.ModelAdmin):  # Use ModelAdmin if OSMGeoAdmin is unavailable
    list_display = ('id', 'height', 'total_solar_potential')
    change_form_template = 'admin/building_change_form.html'

    def change_view(self, request, object_id, form_url='', extra_context=None):
        # Fetch building and its related data
        building = self.get_queryset(request).get(pk=object_id)
        faces = building.faces.all()
        shadow_data = []

        for face in faces:
            face_data = {
                "face_id": face.id,
                "shadow_percentages": []
            }
            for hour in range(5, 20):  # From 5 AM to 7 PM
                centroids = face.centroids.all()
                total_centroids = centroids.count()
                shadowed_centroids = centroids.filter(
                    shadow_analysis__hour=hour,
                    shadow_analysis__month=request.GET.get('month', 3)  # Default to January
                ).aggregate(shadow_count=Count('shadow_analysis', filter=F('shadow_analysis__shadow')))
                shadow_percentage = (
                    (shadowed_centroids['shadow_count'] or 0) / total_centroids * 100
                    if total_centroids > 0 else 0
                )
                face_data["shadow_percentages"].append(shadow_percentage)
            shadow_data.append(face_data)
        
        logger.debug(f"Shadow Data: {shadow_data}")
        logger.debug(f"Hours: {list(range(5, 20))}")
        logger.debug(f"Faces: {[{'id': face.id} for face in faces]}")

        serialized_faces = [{"id": face.id} for face in faces]

        # Pass shadow data to the template
        extra_context = extra_context or {}
        extra_context['shadow_data'] = shadow_data  # Already serialized as list of dictionaries
        extra_context['hours'] = list(range(5, 20))  # Static list of hours
        extra_context['faces'] = serialized_faces  # Serialized faces
        return super().change_view(request, object_id, form_url, extra_context=extra_context)

    
admin.site.register(Building, BuildingAdmin)


# Register BuildingFace
@admin.register(BuildingFace)
class BuildingFaceAdmin(admin.ModelAdmin):  # Use ModelAdmin if OSMGeoAdmin is unavailable
    list_display = ('id', 'building', 'orientation','tilt' ,'area')

# Register Grid
@admin.register(Grid3D)
class Grid3DAdmin(admin.ModelAdmin):  # Use ModelAdmin if OSMGeoAdmin is unavailable
    list_display = ('id', 'face', 'x_position', 'y_position', 'solar_potential')

@admin.register(VirtualGridCentroid)
class VirtualGridCentroidAdmin(admin.ModelAdmin):  # Use ModelAdmin if OSMGeoAdmin is unavailable
    list_display = ('id',  'label')

# Register ShadowAnalysis
class ShadowAnalysisAdmin(admin.ModelAdmin):
    list_display = ('centroid', 'month', 'hour', 'shadow')
    list_filter = ('month', 'hour', 'shadow')  # Optional: add filters for easier admin navigation
    search_fields = ('centroid__label',)  # Optional: allow searching by centroid label
    change_form_template = 'admin/shadow_analysis_change_form.html'  # Custom template

    def get_queryset(self, request):
        """Optimize the queryset for shadow data analysis."""
        return super().get_queryset(request).select_related('centroid', 'centroid__building_face', 'centroid__building_face__building')
admin.site.register(ShadowAnalysis, ShadowAnalysisAdmin)

@admin.register(Potential_Estimate)
class PotentialEstimateAdmin(admin.ModelAdmin):
    list_display = ('id', 'face', 'month', 'date', 'potential', 'irradiance')
    list_filter = ('month', 'date')  # Optional: add filters for month and date
    search_fields = ('face__id',)  # Optional: allow searching by BuildingFace ID