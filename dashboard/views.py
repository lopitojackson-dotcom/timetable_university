from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from institutions.models import School, Department
from academics.models import Programme, AcademicUnit, ClassGroup, AcademicYear, Semester
from resources.models import Lecturer, Venue
from teaching.models import TeachingSession, TeachingGenerationRun
from examinations.models import ExaminationSession, ExaminationPeriod, ExaminationGenerationRun
from conflicts.models import ConflictRecord, ConflictResolutionRun
from notifications.models import Notification

@login_required
def home(request):
    unresolved = ConflictRecord.objects.filter(resolved=False)
    critical = unresolved.filter(severity='error').count()
    resolvable = unresolved.count()  # best-effort
    pending_approvals = TeachingSession.objects.filter(status='under_review').count() + ExaminationSession.objects.filter(status='under_review').count()
    context = {
        'schools': School.objects.count(),
        'departments': Department.objects.count(),
        'programmes': Programme.objects.count(),
        'units': AcademicUnit.objects.count(),
        'lecturers': Lecturer.objects.count(),
        'venues': Venue.objects.count(),
        'classgroups': ClassGroup.objects.count(),
        'teaching_sessions': TeachingSession.objects.count(),
        'exam_sessions': ExaminationSession.objects.count(),
        'conflicts': unresolved.count(),
        'critical_conflicts': critical,
        'resolvable_conflicts': resolvable,
        'unresolved_conflicts': unresolved.count(),
        'published_teaching': TeachingSession.objects.filter(status='published').count(),
        'pending_approvals': pending_approvals,
        'recent_notifications': Notification.objects.filter(user=request.user).order_by('-created_at')[:5],
        'recent_runs': TeachingGenerationRun.objects.order_by('-created_at')[:5],
        'recent_resolution_runs': ConflictResolutionRun.objects.order_by('-started_at')[:5],
    }
    return render(request, 'dashboard/home.html', context)

def public_teaching(request):
    from teaching.models import TeachingSession
    sessions = TeachingSession.objects.filter(status='published')
    year = request.GET.get('year')
    semester = request.GET.get('semester')
    programme = request.GET.get('programme')
    if year:
        sessions = sessions.filter(academic_year_id=year)
    if semester:
        sessions = sessions.filter(semester_id=semester)
    if programme:
        sessions = sessions.filter(programme_id=programme)
    return render(request, 'public/teaching.html', {
        'years': AcademicYear.objects.all(),
        'semesters': Semester.objects.all(),
        'schools': School.objects.all(),
        'programmes': Programme.objects.all(),
        'sessions': sessions.order_by('day','start_time'),
        'selected': {'year':year,'semester':semester,'programme':programme},
    })

def public_exam(request):
    from examinations.models import ExaminationSession
    sessions = ExaminationSession.objects.filter(status='published')
    period = request.GET.get('period')
    programme = request.GET.get('programme')
    if period:
        sessions = sessions.filter(examination_period_id=period)
    if programme:
        sessions = sessions.filter(programme_id=programme)
    return render(request, 'public/exam.html', {
        'periods': ExaminationPeriod.objects.all(),
        'years': AcademicYear.objects.all(),
        'programmes': Programme.objects.all(),
        'sessions': sessions.order_by('examination_date','start_time'),
        'selected': {'period':period,'programme':programme},
    })
