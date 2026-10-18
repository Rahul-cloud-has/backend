import datetime
from io import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from .models import (
    Category, Course, CourseCategory, Franchise, User, WebsiteCourse, next_franchise_code,
)

YEAR = datetime.datetime.now().year


class NextFranchiseCodeTests(TestCase):
    def test_first_code(self):
        self.assertEqual(next_franchise_code(), f"FR-{YEAR}-0001")

    def test_uses_highest_suffix_not_row_count(self):
        # Rows 1 and 2 were deleted, only 0003 remains: count()+1 would give 0002.
        User.objects.create_user(username="u3", password="x", role="franchise", franchise_code=f"FR-{YEAR}-0003")
        self.assertEqual(next_franchise_code(), f"FR-{YEAR}-0004")

    def test_orphan_franchise_row_is_respected(self):
        Franchise.objects.create(name="Orphan", code=f"FR-{YEAR}-0009", phone="1")
        self.assertEqual(next_franchise_code(), f"FR-{YEAR}-0010")

    def test_ignores_other_years_and_non_numeric(self):
        User.objects.create_user(username="old", password="x", role="franchise", franchise_code="FR-1999-0050")
        User.objects.create_user(username="odd", password="x", role="franchise", franchise_code=f"FR-{YEAR}-ABCD")
        self.assertEqual(next_franchise_code(), f"FR-{YEAR}-0001")


class MergeCategoryCommandTests(TestCase):
    def setUp(self):
        self.good = CourseCategory.objects.create(label="CAKE MAKING & BAKING COURSE")
        self.bad = CourseCategory.objects.create(label="CAKE MAKING & BAKING COURCE")
        self.course = WebsiteCourse.objects.create(
            name="Cake", slug="cake-1", category=self.bad, fee=1, total_payment=1,
            duration=self._duration(),
        )
        self.good_legacy = Category.objects.create(name="CAKE MAKING & BAKING COURSE")
        self.bad_legacy = Category.objects.create(name="CAKE MAKING & BAKING COURCE")

    def _duration(self):
        from .models import CourseDuration
        return CourseDuration.objects.create(value="3 Month")

    def _run(self, *extra):
        out = StringIO()
        call_command(
            "merge_category", "--from", "CAKE MAKING & BAKING COURCE",
            "--into", "CAKE MAKING & BAKING COURSE", *extra, stdout=out,
        )
        return out.getvalue()

    def test_dry_run_writes_nothing(self):
        output = self._run()
        self.assertIn("DRY RUN", output)
        self.assertTrue(CourseCategory.objects.filter(pk=self.bad.pk).exists())
        self.assertTrue(Category.objects.filter(pk=self.bad_legacy.pk).exists())

    def test_apply_moves_courses_then_deletes_source(self):
        self._run("--apply")
        self.course.refresh_from_db()
        self.assertEqual(self.course.category_id, self.good.pk)
        self.assertFalse(CourseCategory.objects.filter(pk=self.bad.pk).exists())
        self.assertFalse(Category.objects.filter(pk=self.bad_legacy.pk).exists())

    def test_refuses_when_target_missing(self):
        with self.assertRaises(CommandError):
            call_command("merge_category", "--from", "CAKE MAKING & BAKING COURCE", "--into", "NOPE", "--apply")
        self.assertTrue(CourseCategory.objects.filter(pk=self.bad.pk).exists())
