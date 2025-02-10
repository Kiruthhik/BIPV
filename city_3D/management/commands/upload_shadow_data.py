import os
import pandas as pd
from django.core.management.base import BaseCommand
from city_3D.models import VirtualGridCentroid, ShadowAnalysis


class Command(BaseCommand):
    help = "Upload shadow analysis data from a CSV file to the database"

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            required=True,
            help=r"C:\Users\HP\Documents\hackfest\SIH\SIH FINAL\shadow data poova\shadow_analysis_results 1.csv"
        )

    def handle(self, *args, **options):
        file_path = options['file']
        hardcoded_month = 1  # Hardcoded month value, you can change this as needed

        # Check if file exists
        if not os.path.exists(file_path):
            self.stderr.write(f"File not found: {file_path}")
            return

        # Read CSV file
        try:
            self.stdout.write(f"Reading CSV file: {file_path}")
            data = pd.read_csv(file_path)
        except Exception as e:
            self.stderr.write(f"Error reading CSV file: {e}")
            return

        # Validate required columns
        required_columns = {'building_id', 'centroid_id', 'time', 'shadow_status'}
        if not required_columns.issubset(data.columns):
            self.stderr.write(f"CSV file must contain the following columns: {', '.join(required_columns)}")
            return

        # Process each row and insert data into the database
        rows_processed = 0
        errors = 0

        for _, row in data.iterrows():
            try:
                centroid_id = int(row['centroid_id'])
                hour = int(row['time'].split(':')[0])  # Extract hour from time (e.g., '06:00' -> 6)
                shadow_status = not bool(row['shadow_status'])

                # Find the centroid
                try:
                    centroid = VirtualGridCentroid.objects.get(id=centroid_id)
                except VirtualGridCentroid.DoesNotExist:
                    self.stderr.write(f"Centroid with ID {centroid_id} does not exist. Skipping.")
                    errors += 1
                    continue

                # Create or update the shadow analysis entry
                shadow_entry, created = ShadowAnalysis.objects.update_or_create(
                    centroid=centroid,
                    month=hardcoded_month,
                    hour=hour,
                    defaults={'shadow': shadow_status}
                )
                print(f"buidling processed {row['building_id']}")
                rows_processed += 1
            except Exception as e:
                self.stderr.write(f"Error processing row: {row.to_dict()}. Error: {e}")
                errors += 1

        self.stdout.write(f"\nSummary:")
        self.stdout.write(f"  Rows processed: {rows_processed}")
        self.stdout.write(f"  Errors: {errors}")
        self.stdout.write("Upload completed.")