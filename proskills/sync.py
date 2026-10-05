from .models import Course, WebsiteCourse, CourseCategory, CourseDuration


def sync_course_to_website_course(course: Course) -> WebsiteCourse:
    category = CourseCategory.objects.filter(label__iexact=course.category.name).first() \
        or CourseCategory.objects.create(label=course.category.name)
    duration = CourseDuration.objects.filter(value__iexact=course.sessions.name).first() \
        or CourseDuration.objects.create(value=course.sessions.name)

    wc, created = WebsiteCourse.objects.get_or_create(
        source_course=course,
        defaults=dict(
            name=course.course_name, category=category, duration=duration,
            fee=course.fee, total_payment=course.fee,
            description=course.description or '', is_active=course.is_active,
        ),
    )
    if not created:
        wc.name, wc.category, wc.duration = course.course_name, category, duration
        wc.fee = wc.total_payment = course.fee
        wc.description, wc.is_active = course.description or '', course.is_active
        wc.save()
    return wc


def deactivate_website_course_for(course: Course) -> None:
    WebsiteCourse.objects.filter(source_course_id=course.pk).update(is_active=False)
