try:
    from celery import shared_task
except Exception:
    def shared_task(*a, **k):
        def decorator(f):
            f.delay = lambda *a, **k: f(*a, **k)
            return f
        return decorator

@shared_task
def resolve_conflicts_task(academic_level=None, school_id=None, department_id=None, programme_id=None,
                           academic_year_id=None, semester_id=None, examination_period_id=None,
                           user_id=None, apply=False, preview=False):
    from institutions.models import School, Department
    from academics.models import Programme, AcademicYear, Semester
    from examinations.models import ExaminationPeriod
    from django.contrib.auth import get_user_model
    from conflicts.services import resolve_all_conflicts
    school = School.objects.get(pk=school_id) if school_id else None
    department = Department.objects.get(pk=department_id) if department_id else None
    programme = Programme.objects.get(pk=programme_id) if programme_id else None
    academic_year = AcademicYear.objects.get(pk=academic_year_id) if academic_year_id else None
    semester = Semester.objects.get(pk=semester_id) if semester_id else None
    examination_period = ExaminationPeriod.objects.get(pk=examination_period_id) if examination_period_id else None
    user = get_user_model().objects.filter(pk=user_id).first() if user_id else None
    return resolve_all_conflicts(academic_level=academic_level, school=school, department=department,
                                 programme=programme, academic_year=academic_year, semester=semester,
                                 examination_period=examination_period, user=user, apply=apply, preview=preview)

@shared_task
def detect_conflicts_task(**scope):
    from conflicts.services import detect_all_conflicts
    return detect_all_conflicts(**scope)