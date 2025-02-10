# your_app/management/commands/shadow_data.py
from django.core.management.base import BaseCommand
from city_3D.models import Building
from city_3D.utils import classify_orientation


class Command(BaseCommand):
    help = "Fetch and print shadow data for a particular building"

    # def add_arguments(self, parser):
    #     # Add an argument to specify the building ID
    #     parser.add_argument(
    #         "building_id", type=int, help="ID of the building to fetch shadow data for"
    #     )

    def handle(self, *args, **options):
        #building_id = options["building_id"]

        try:
            # Fetch the building
            building = Building.objects.get(id=5203)
            self.stdout.write(f"Building ID: {building.id}")

            # Iterate over each face of the building
            for face in building.faces.all():
                self.stdout.write(f"Face ID: {face.id} facing {classify_orientation(face.orientation)}")
                self.stdout.write("Hour-wise shadow data:\n\t\t\t5\t6\t7\t8\t9\t10\t11\t12\t13\t14\t15\t16\t17\t18\t19\n")
                
                # Iterate over each centroid of the face
                for centroid in face.centroids.all():
                    shadow_row = []  # Collect shadow data for the row
                    for hour in range(5, 20):  # Iterate over hours from 5 AM to 7 PM
                        shadow_analysis = centroid.shadow_analysis.filter(month=11, hour=hour).first()
                        if shadow_analysis:
                            shadow_row.append("1" if shadow_analysis.shadow else "0")  # "1" for shadow, "0" otherwise
                        else:
                            shadow_row.append("-")  # "-" indicates no data available
                    
                    # Print the centroid label and its hour-wise shadow data
                    self.stdout.write(f"Centroid {centroid.label}:\t" + "\t".join(shadow_row))
        
        except Building.DoesNotExist:
            self.stderr.write(f"Building with ID 5203 does not exist.")
        except Exception as e:
            self.stderr.write(f"An error occurred: {str(e)}")
