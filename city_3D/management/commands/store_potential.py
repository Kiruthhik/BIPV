import datetime
from django.core.management.base import BaseCommand
from django.db import transaction
from city_3D.models import Building, BuildingFace, Potential_Estimate
from city_3D.views import building_solar_potential  # Import the function
import json

class Command(BaseCommand):
    help = "Calculate and store potential estimates for buildings on specific dates"

    def handle(self, *args, **kwargs):
        # Define the specific dates for analysis
        dates = [
            datetime.date(2023, 3, 21),
            datetime.date(2023, 6, 21),
            datetime.date(2023, 9, 21),
            datetime.date(2023, 12, 15),
        ]

        # Get all buildings
        buildings = Building.objects.all()[:2]

        for building in buildings:
            self.stdout.write(f"Processing Building ID: {building.id}")
            for _date in dates:
                self.stdout.write(f"  - Fetching data for date: {_date}")

                # Call the building_solar_potential function
                try:
                    __date = f"{_date.year}-{_date.month}-{_date.day}"
                    response = building_solar_potential(None, building.id, __date)

                    # Check if response is a JsonResponse or similar object
                    if hasattr(response, 'content'):
                        # Parse the JSON content from the response
                        output = json.loads(response.content)
                    else:
                        raise ValueError("Invalid response format, expected JsonResponse with content.")
                except Exception as e:
                    self.stderr.write(f"Error processing Building {building.id} on {_date}: {str(e)}")
                    continue

                # Debug output of the building_solar_potential function
                self.stdout.write(f"Output for Building ID {building.id} on {_date}: {output}")

                # Parse the output JSON and store in Potential_Estimate
                with transaction.atomic():
                    for key, value in output.items():
                        # Process keys ending with "potential"
                        if key.endswith("potential") and key[:-len("potential")].isdigit():
                            try:
                                # Extract face_id from the key
                                face_id = int(key.replace("potential", ""))
                                potential = value

                                # Find corresponding irradiance value
                                irradiance_key = f"{face_id}irradiance"
                                irradiance = output.get(irradiance_key, None)

                                # Get the building face
                                face = BuildingFace.objects.filter(id=face_id, building=building).first()
                                if not face:
                                    self.stderr.write(
                                        f"  - Face ID {face_id} not found for Building {building.id}. Skipping."
                                    )
                                    continue
                                
                                # Debug logging
                                self.stdout.write(
                                    f"    - Preparing to save PotentialEstimate: "
                                    f"Face ID {face.id}, Date {_date}, Potential {potential}, Irradiance {irradiance}"
                                )

                                # Save or update the Potential_Estimate
                                potential_estimate, created = Potential_Estimate.objects.update_or_create(
                                    face=face,
                                    date=_date,
                                    defaults={
                                        "month": _date.month,
                                        "potential": potential,
                                        "irradiance": irradiance,
                                    }
                                )
                                potential_estimate.save()

                                # Log action
                                action = "Created" if created else "Updated"
                                self.stdout.write(f"    - {action} PotentialEstimate for Face {face.id} on {_date}")

                            except Exception as e:
                                self.stderr.write(
                                    f"Error saving PotentialEstimate for Face ID {face_id} on {_date}: {str(e)}"
                                )

        self.stdout.write("Process complete!")
