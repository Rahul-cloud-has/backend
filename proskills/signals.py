from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from .models import Course
from .sync import sync_course_to_website_course, deactivate_website_course_for


@receiver(post_save, sender=Course)
def handle_course_saved(sender, instance, **kwargs):
    sync_course_to_website_course(instance)


@receiver(pre_delete, sender=Course)
def handle_course_deleted(sender, instance, **kwargs):
    # Must run before deletion: Course's on_delete=SET_NULL on the reverse
    # WebsiteCourse.source_course FK clears source_course_id as part of the
    # same delete operation, so a post_delete handler would find no rows left
    # to match by that id.
    deactivate_website_course_for(instance)
