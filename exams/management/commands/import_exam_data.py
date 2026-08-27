from django.core.management.base import BaseCommand
from django.core.management import call_command
from exams.models import Exam


class Command(BaseCommand):
    help = "Import examination data from exam_data.json"

    def handle(self, *args, **options):
        # Do not import again if examination data already exists.
        if Exam.objects.exists():
            self.stdout.write(
                self.style.WARNING(
                    "Examination data already exists. "
                    "Skipping fixture import."
                )
            )
            return

        self.stdout.write("Importing examination data...")

        call_command(
            "loaddata",
            "exam_data.json",
            verbosity=1,
        )

        self.stdout.write(
            self.style.SUCCESS(
                "Examination data imported successfully."
            )
        )