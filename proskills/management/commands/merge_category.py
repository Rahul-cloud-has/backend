from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from proskills.models import Category, Course, CourseCategory, WebsiteCourse


class Command(BaseCommand):
    help = (
        "Move all courses from a misspelled category into the correct one, then delete the "
        "empty misspelled category (both proskills_category and course_categories). "
        "Dry-run by default; pass --apply to write."
    )

    def add_arguments(self, parser):
        parser.add_argument("--from", dest="source", required=True, help="Misspelled category name/label (exact)")
        parser.add_argument("--into", dest="target", required=True, help="Correct category name/label (exact)")
        parser.add_argument("--apply", action="store_true", help="Actually write changes")

    def handle(self, *args, **opts):
        source, target, apply = opts["source"], opts["target"], opts["apply"]
        if source.strip().lower() == target.strip().lower():
            raise CommandError("--from and --into must be different categories.")

        plans = []
        for model, field, course_model in (
            (Category, "name", Course),
            (CourseCategory, "label", WebsiteCourse),
        ):
            src = model.objects.filter(**{f"{field}__iexact": source}).first()
            dst = model.objects.filter(**{f"{field}__iexact": target}).first()
            if not src and not dst:
                self.stdout.write(f"[{model.__name__}] neither category exists - skipping")
                continue
            if src and not dst:
                raise CommandError(f"[{model.__name__}] target '{target}' not found; refusing to delete '{source}'.")
            if not src:
                self.stdout.write(f"[{model.__name__}] source '{source}' not found - nothing to do")
                continue
            count = course_model.objects.filter(category=src).count()
            self.stdout.write(
                f"[{model.__name__}] '{getattr(src, field)}' (id={src.id}) -> '{getattr(dst, field)}' (id={dst.id}); "
                f"{count} {course_model.__name__} row(s) would move, then the source category is deleted."
            )
            plans.append((src, dst, course_model))

        if not apply:
            self.stdout.write(self.style.WARNING("DRY RUN - no changes written. Re-run with --apply to execute."))
            return

        with transaction.atomic():
            for src, dst, course_model in plans:
                moved = course_model.objects.filter(category=src).update(category=dst)
                remaining = course_model.objects.filter(category=src).count()
                if remaining:
                    raise CommandError("Courses still reference the source category; aborting (rolled back).")
                src.delete()
                self.stdout.write(self.style.SUCCESS(f"Moved {moved} row(s) and deleted '{src}'."))
