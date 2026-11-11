from django.shortcuts import render
from django.utils import timezone
from institutions.models import Institution, School, Department
from academics.models import Programme, AcademicYear, Semester
from teaching.models import TeachingSession
from examinations.models import ExaminationSession, ExaminationPeriod
from .models import Announcement


def _institution():
    return Institution.objects.first()


def home(request):
    inst = _institution()
    schools = School.objects.all().prefetch_related('departments', 'programmes')
    announcements = Announcement.objects.filter(is_public=True)[:5]
    context = {
        'institution': inst,
        'schools': schools,
        'announcements': announcements,
        'now': timezone.now(),
    }
    return render(request, 'public/home.html', context)


def about(request):
    return render(request, 'public/about.html', {'institution': _institution()})


def teaching_timetables(request):
    qs = TeachingSession.objects.filter(status='published')
    years = AcademicYear.objects.all()
    semesters = Semester.objects.all()
    programmes = Programme.objects.all()
    schools = School.objects.all()
    departments = Department.objects.all()
    # filters
    if request.GET.get('school'):
        qs = qs.filter(school_id=request.GET['school'])
    if request.GET.get('department'):
        qs = qs.filter(department_id=request.GET['department'])
    if request.GET.get('programme'):
        qs = qs.filter(programme_id=request.GET['programme'])
    if request.GET.get('year'):
        qs = qs.filter(academic_year_id=request.GET['year'])
    if request.GET.get('semester'):
        qs = qs.filter(semester_id=request.GET['semester'])
    if request.GET.get('academic_level'):
        qs = qs.filter(programme__level=request.GET['academic_level'])
    context = {
        'institution': _institution(),
        'sessions': qs.order_by('day', 'start_time')[:500],
        'years': years,
        'semesters': semesters,
        'programmes': programmes,
        'schools': schools,
        'departments': departments,
        'selected': request.GET,
    }
    return render(request, 'public/teaching_timetables.html', context)


def examination_timetables(request):
    qs = ExaminationSession.objects.filter(status='published')
    periods = ExaminationPeriod.objects.all()
    programmes = Programme.objects.all()
    schools = School.objects.all()
    if request.GET.get('school'):
        qs = qs.filter(school_id=request.GET['school'])
    if request.GET.get('programme'):
        qs = qs.filter(programme_id=request.GET['programme'])
    if request.GET.get('period'):
        qs = qs.filter(examination_period_id=request.GET['period'])
    if request.GET.get('academic_level'):
        qs = qs.filter(programme__level=request.GET['academic_level'])
    context = {
        'institution': _institution(),
        'sessions': qs.order_by('examination_date', 'start_time')[:500],
        'periods': periods,
        'programmes': programmes,
        'schools': schools,
        'selected': request.GET,
    }
    return render(request, 'public/examination_timetables.html', context)


def schools_departments(request):
    schools = School.objects.all().prefetch_related('departments', 'programmes')
    return render(request, 'public/schools.html', {'institution': _institution(), 'schools': schools})


def academic_calendar(request):
    years = AcademicYear.objects.all()
    return render(request, 'public/academic_calendar.html', {'institution': _institution(), 'years': years})


def announcements(request):
    anns = Announcement.objects.filter(is_public=True)
    return render(request, 'public/announcements.html', {'institution': _institution(), 'announcements': anns})


def faq(request):
    return render(request, 'public/faq.html', {'institution': _institution()})


def contact(request):
    return render(request, 'public/contact.html', {'institution': _institution()})