from django.core.management.base import BaseCommand
from django.db import transaction

from proskills.models import Course, WebsiteCourse
from proskills.sync import sync_course_to_website_course


class Command(BaseCommand):
    help = "Ensure every existing Course has a linked WebsiteCourse."

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        created = linked = 0
        for course in Course.objects.all():
            if WebsiteCourse.objects.filter(source_course=course).exists():
                continue
            candidate = WebsiteCourse.objects.filter(
                source_course__isnull=True, name__iexact=course.course_name,
            ).first()
            if candidate:
                self.stdout.write(f"Link WebsiteCourse #{candidate.pk} -> Course #{course.pk}")
                if not dry_run:
                    candidate.source_course = course
                    candidate.save(update_fields=['source_course'])
                linked += 1
            else:
                self.stdout.write(f"Create WebsiteCourse for Course #{course.pk}")
                if not dry_run:
                    with transaction.atomic():
                        sync_course_to_website_course(course)
                created += 1
        self.stdout.write(self.style.SUCCESS(f"created={created} linked={linked} dry_run={dry_run}"))
