"""Management command to seed default document categories."""
from django.core.management.base import BaseCommand
from documents.models import DocumentCategory


class Command(BaseCommand):
    help = "Seed default document categories for the AI College Assistant"

    CATEGORIES = [
        ("Placement Guidelines", "Placement-related policies and procedures"),
        ("Internship Guidelines", "Internship rules and procedures"),
        ("Academic Regulations", "Academic policies and regulations"),
        ("Syllabus", "Course and semester syllabus"),
        ("Exam Rules", "Examination policies and guidelines"),
        ("Company Eligibility", "Company-specific eligibility criteria and requirements"),
        ("Notices", "Important university notices and announcements"),
    ]

    def handle(self, *args, **options):
        created_count = 0
        for name, description in self.CATEGORIES:
            obj, created = DocumentCategory.objects.get_or_create(
                name=name,
                defaults={"description": description, "is_active": True},
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"  Created: {name}"))
            else:
                self.stdout.write(f"  Already exists: {name}")

        self.stdout.write(
            self.style.SUCCESS(
                f"\nDone. {created_count} new categories created."
            )
        )
