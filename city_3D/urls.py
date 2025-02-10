from django.contrib import admin
from django.urls import  path
from . import views

urlpatterns = [
    path("hourly_shadow_grid/<int:code>",views.hourly_shadow_data_grid),
    path("hourly_potential_grid/<int:code>", views.grid_solar_potential_hourly),
    path("panel_recommendation/<int:id>/<str:building_type>/<str:facade_material>",views.get_recommendation),
    path("potential_analysis_seasonal/<int:id>",views.building_solar_potential_seasonal),
    path("solar_potential_day/<int:id>/<str:_date>",views.building_solar_potential),
    path('shadow_data_hourly/<int:id>/<int:month>', views.hourly_shadow_data),
    path("solar_potential_hourly/<int:id>/<str:_date>",views.building_solar_potential_hourly),
    path("solar_potential_month_avg/<int:id>/<int:year>/<int:month>",views.building_monthly_solar_potential),
]