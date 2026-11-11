try:
    from celery import shared_task
except Exception:
    def shared_task(*a, **k):
        def decorator(f):
            f.delay = lambda *a, **k: f(*a, **k)
            return f
        return decorator

from scheduling.services import generate_teaching_alternatives, generate_exam_alternatives

@shared_task
def generate_teaching_task(academic_year_id, semester_id, school_id=None, programme_id=None, created_by_id=None, count=10, academic_level=None):
    from academics.models import AcademicYear, Semester
    from institutions.models import School
    from academics.models import Programme
    ay = AcademicYear.objects.get(pk=academic_year_id)
    sem = Semester.objects.get(pk=semester_id)
    school = School.objects.get(pk=school_id) if school_id else None
    programme = Programme.objects.get(pk=programme_id) if programme_id else None
    from django.contrib.auth import get_user_model
    user = get_user_model().objects.filter(pk=created_by_id).first() if created_by_id else None
    return generate_teaching_alternatives(ay, sem, school=school, programme=programme, created_by=user, count=count, academic_level=academic_level)

@shared_task
def generate_exam_task(period_id, academic_year_id, semester_id=None, school_id=None, programme_id=None, created_by_id=None, count=10, academic_level=None):
    from examinations.models import ExaminationPeriod
    from academics.models import AcademicYear, Semester
    from institutions.models import School
    from academics.models import Programme
    period = ExaminationPeriod.objects.get(pk=period_id)
    ay = AcademicYear.objects.get(pk=academic_year_id)
    sem = Semester.objects.get(pk=semester_id) if semester_id else None
    school = School.objects.get(pk=school_id) if school_id else None
    programme = Programme.objects.get(pk=programme_id) if programme_id else None
    from django.contrib.auth import get_user_model
    user = get_user_model().objects.filter(pk=created_by_id).first() if created_by_id else None
    from scheduling.services import generate_exam_alternatives
    return generate_exam_alternatives(period, ay, semester=sem, school=school, programme=programme, created_by=user, count=count, academic_level=academic_level)