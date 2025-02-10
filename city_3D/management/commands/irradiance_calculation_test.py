import openpyxl
import pandas as pd
from django.core.management.base import BaseCommand
from datetime import datetime
from city_3D.models import Building
from city_3D.views import building_solar_potential, building_monthly_solar_potential

class Command(BaseCommand):
    help = 'Calculate and store solar potential data for a given date and building ID in Excel'

    def handle(self, *args, **options):
        # Manually input the date and building id
        input_date = '2022-11-06'  # Example date
        building_id = 1  # Example building id
        
        # Parse the input date
        date = datetime.strptime(input_date, "%Y-%m-%d")
        year, month, day = date.year, date.month, date.day
        
        # Initialize the Excel workbook and sheet
        wb = openpyxl.Workbook()
        ws_daily = wb.active
        ws_daily.title = "Daily Results"
        ws_monthly = wb.create_sheet(title="Monthly Results")

        # Define headers for both sheets
        headers = ['Hour', 'DNI', 'DHI', 'Zenith', 'Tilt', 'Sun Azimuth', 'Surface Azimuth', 'Albedo', 'Cloud Factor', 'Shadow Factor']
        ws_daily.append(headers)
        ws_monthly.append(headers)

        # Function to store results in the sheet
        def store_results(ws, results, prefix=''):
            for hour, params in results.items():
                row = [f"{prefix}{hour}"]
                row.extend([
                    params.get('dni'),
                    params.get('dhi'),
                    params.get('zenith'),
                    params.get('tilt'),
                    params.get('sun_azimuth'),
                    params.get('surface_azimuth'),
                    params.get('albedo'),
                    params.get('cloud_factor'),
                    params.get('shadow_factor')
                ])
                ws.append(row)

        # Run the daily solar potential function
        daily_results = building_solar_potential(None, building_id, input_date)
        # For each hour, get the first centroid's parameters (simplified)
        daily_comparison = {}
        for hour, data in daily_results.items():
            daily_comparison[hour] = data[0]  # Use the first centroid result

        # Run the monthly solar potential function
        monthly_results = building_monthly_solar_potential(None, building_id, year, month)
        monthly_comparison = {}
        for hour, data in monthly_results.items():
            monthly_comparison[hour] = data[0]  # Use the first centroid result

        # Store results in Excel sheets
        store_results(ws_daily, daily_comparison)
        store_results(ws_monthly, monthly_comparison, prefix="Month ")

        # Save the workbook
        wb.save(f"solar_potential_results_{building_id}_{input_date}.xlsx")

        self.stdout.write(self.style.SUCCESS(f'Successfully saved results for building {building_id} on {input_date}'))
