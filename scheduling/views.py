from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from academics.models import AcademicYear, Semester, Programme
from institutions.models import School
from examinations.models import ExaminationPeriod
from .services import generate_teaching_timetable, generate_exam_timetable, generate_teaching_alternatives, generate_exam_alternatives

@login_required
def generate_teaching_view(request):
    if not (request.user.is_superuser or request.user.is_timetable_admin() or request.user.is_school_admin()):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied
    if request.method == 'POST':
        ay = AcademicYear.objects.get(pk=request.POST['academic_year'])
        sem = Semester.objects.get(pk=request.POST['semester'])
        school = School.objects.get(pk=request.POST['school']) if request.POST.get('school') else None
        programme = Programme.objects.get(pk=request.POST['programme']) if request.POST.get('programme') else None
        academic_level = request.POST.get('academic_level') or None
        from teaching.models import TeachingGenerationRun
        run = TeachingGenerationRun.objects.create(academic_level=academic_level, academic_year=ay, semester=sem, school=school, programme=programme, created_by=request.user, status='processing', progress=10)
        level_label = 'Diploma' if academic_level == 'diploma' else ('Degree' if academic_level == 'degree' else 'Teaching')
        try:
            created, unsched = generate_teaching_timetable(ay, sem, school=school, programme=programme, created_by=request.user, academic_level=academic_level)
        except Exception as e:
            run.status = 'failed'
            run.error = str(e)
            run.completed_at = timezone.now()
            run.save()
            from notifications.models import Notification
            Notification.objects.create(user=request.user, title='Timetable Generation Requires Attention',
                message=f'The system could not generate a fully valid timetable: {e}',
                link='/scheduling/teaching/', notification_type='generation_failed',
                metadata={'run_id': run.id, 'academic_level': academic_level})
            messages.error(request, f'Generation failed: {e}')
            return redirect('generate_teaching')
        run.status = 'completed' if not unsched else 'completed_with_warnings'
        run.progress = 100
        run.message = f'Created {len(created)} sessions. Unscheduled: {len(unsched)}.'
        run.completed_at = timezone.now()
        run.save()
        from notifications.models import Notification
        from conflicts.services import detect_teaching_conflicts
        tc = detect_teaching_conflicts(academic_year=ay, semester=sem, school=school, programme=programme, academic_level=academic_level)
        if not created:
            Notification.objects.create(user=request.user, title='Timetable Generation Requires Attention',
                message=f'The system could not generate a fully valid timetable because of insufficient resources.',
                link='/scheduling/teaching/', notification_type='generation_failed',
                metadata={'run_id': run.id, 'academic_level': academic_level})
        else:
            Notification.objects.create(user=request.user, title=f'New {level_label} Teaching Timetable Generated',
                message=f'The {level_label} Teaching Timetable for {ay} {sem} has been generated successfully. {len(created)} sessions created. {len(unsched)} unscheduled. {tc} conflicts detected.',
                link='/teaching/sessions/', notification_type='teaching_generated',
                metadata={'run_id': run.id, 'academic_level': academic_level, 'alternatives': 0, 'validation': 'completed'})
        if tc > 0:
            Notification.objects.create(user=request.user, title='Conflict Detected',
                message=f'{tc} teaching conflicts detected after generation.',
                link='/conflicts/', notification_type='conflict_detected', metadata={'count': tc})
        messages.success(request, f'Created {len(created)} teaching sessions. Unscheduled: {len(unsched)}')
        return redirect('teaching_session_list')
    return render(request, 'scheduling/generate_teaching.html', {
        'years': AcademicYear.objects.all(),
        'semesters': Semester.objects.all(),
        'schools': School.objects.all(),
        'programmes': Programme.objects.all(),
    })

@login_required
@login_required
def generate_teaching_alternatives_view(request):
    if not (request.user.is_superuser or request.user.is_timetable_admin() or request.user.is_school_admin()):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied
    if request.method == 'POST':
        ay = AcademicYear.objects.get(pk=request.POST['academic_year'])
        sem = Semester.objects.get(pk=request.POST['semester'])
        school = School.objects.get(pk=request.POST['school']) if request.POST.get('school') else None
        programme = Programme.objects.get(pk=request.POST['programme']) if request.POST.get('programme') else None
        academic_level = request.POST.get('academic_level') or None
        run, alts = generate_teaching_alternatives(ay, sem, school=school, programme=programme, created_by=request.user, count=10, academic_level=academic_level)
        from notifications.models import Notification
        level_label = 'Diploma' if academic_level == 'diploma' else ('Degree' if academic_level == 'degree' else 'Teaching')
        Notification.objects.create(user=request.user, title=f'New {level_label} Teaching Timetable Generated',
            message=f'The {level_label} Teaching Timetable for {ay} {sem} has been generated. {len(alts)} alternatives are available for review.',
            link=f'/scheduling/teaching/alternatives/{run.id}/', notification_type='alternatives_ready',
            metadata={'run_id': run.id, 'alternatives': len(alts), 'academic_level': academic_level})
        messages.success(request, f'Generated {len(alts)} teaching alternatives.')
        return redirect('teaching_alternatives', run_id=run.id)
    return render(request, 'scheduling/generate_teaching.html', {
        'years': AcademicYear.objects.all(),
        'semesters': Semester.objects.all(),
        'schools': School.objects.all(),
        'programmes': Programme.objects.all(),
        'mode': 'alternatives',
    })

@login_required
def teaching_alternatives_view(request, run_id):
    from teaching.models import TeachingGenerationRun, TeachingAlternative
    run = TeachingGenerationRun.objects.get(pk=run_id)
    alts = run.alternatives.all()
    return render(request, 'scheduling/teaching_alternatives.html', {'run': run, 'alternatives': alts})

@login_required
def select_teaching_alternative(request, alt_id):
    from teaching.models import TeachingAlternative
    alt = TeachingAlternative.objects.get(pk=alt_id)
    alt.run.alternatives.update(selected=False)
    alt.selected = True
    alt.save()
    messages.success(request, f'Selected Alternative {alt.number}.')
    return redirect('teaching_alternatives', run_id=alt.run.id)

@login_required
def generate_exam_alternatives_view(request):
    if not (request.user.is_superuser or request.user.is_timetable_admin() or request.user.is_school_admin()):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied
    if request.method == 'POST':
        period = ExaminationPeriod.objects.get(pk=request.POST['period'])
        ay = AcademicYear.objects.get(pk=request.POST['academic_year'])
        sem = Semester.objects.get(pk=request.POST['semester']) if request.POST.get('semester') else None
        school = School.objects.get(pk=request.POST['school']) if request.POST.get('school') else None
        programme = Programme.objects.get(pk=request.POST['programme']) if request.POST.get('programme') else None
        academic_level = request.POST.get('academic_level') or None
        run, alts = generate_exam_alternatives(period, ay, semester=sem, school=school, programme=programme, created_by=request.user, count=10, academic_level=academic_level)
        from notifications.models import Notification
        level_label = 'Diploma' if academic_level == 'diploma' else ('Degree' if academic_level == 'degree' else 'Examination')
        Notification.objects.create(user=request.user, title=f'New {level_label} Examination Timetable Generated',
            message=f'The {level_label} Examination Timetable for {ay} has been generated. {len(alts)} alternatives are available for review.',
            link=f'/scheduling/exams/alternatives/{run.id}/', notification_type='alternatives_ready',
            metadata={'run_id': run.id, 'alternatives': len(alts), 'academic_level': academic_level})
        messages.success(request, f'Generated {len(alts)} exam alternatives.')
        return redirect('exam_alternatives', run_id=run.id)
    return render(request, 'scheduling/generate_exam.html', {
        'periods': ExaminationPeriod.objects.all(),
        'years': AcademicYear.objects.all(),
        'semesters': Semester.objects.all(),
        'schools': School.objects.all(),
        'programmes': Programme.objects.all(),
        'mode': 'alternatives',
    })

@login_required
def exam_alternatives_view(request, run_id):
    from examinations.models import ExaminationGenerationRun, ExaminationAlternative
    run = ExaminationGenerationRun.objects.get(pk=run_id)
    alts = run.alternatives.all()
    return render(request, 'scheduling/exam_alternatives.html', {'run': run, 'alternatives': alts})

@login_required
def select_exam_alternative(request, alt_id):
    from examinations.models import ExaminationAlternative
    alt = ExaminationAlternative.objects.get(pk=alt_id)
    alt.run.alternatives.update(selected=False)
    alt.selected = True
    alt.save()
    messages.success(request, f'Selected Exam Alternative {alt.number}.')
    return redirect('exam_alternatives', run_id=alt.run.id)

def generate_exam_view(request):
    if not (request.user.is_superuser or request.user.is_timetable_admin() or request.user.is_school_admin()):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied
    if request.method == 'POST':
        period = ExaminationPeriod.objects.get(pk=request.POST['period'])
        ay = AcademicYear.objects.get(pk=request.POST['academic_year'])
        sem = Semester.objects.get(pk=request.POST['semester']) if request.POST.get('semester') else None
        school = School.objects.get(pk=request.POST['school']) if request.POST.get('school') else None
        programme = Programme.objects.get(pk=request.POST['programme']) if request.POST.get('programme') else None
        academic_level = request.POST.get('academic_level') or None
        from examinations.models import ExaminationGenerationRun
        run = ExaminationGenerationRun.objects.create(academic_level=academic_level, examination_period=period, academic_year=ay, semester=sem, school=school, programme=programme, created_by=request.user, status='processing', progress=10)
        level_label = 'Diploma' if academic_level == 'diploma' else ('Degree' if academic_level == 'degree' else 'Examination')
        try:
            created, unsched = generate_exam_timetable(period, ay, semester=sem, school=school, programme=programme, created_by=request.user, academic_level=academic_level)
        except Exception as e:
            run.status = 'failed'
            run.error = str(e)
            run.completed_at = timezone.now()
            run.save()
            from notifications.models import Notification
            Notification.objects.create(user=request.user, title='Timetable Generation Requires Attention',
                message=f'The system could not generate a fully valid timetable: {e}',
                link='/scheduling/exams/', notification_type='generation_failed',
                metadata={'run_id': run.id, 'academic_level': academic_level})
            messages.error(request, f'Generation failed: {e}')
            return redirect('generate_exam')
        run.status = 'completed' if not unsched else 'completed_with_warnings'
        run.progress = 100
        run.message = f'Created {len(created)} sessions. Unscheduled: {len(unsched)}.'
        run.completed_at = timezone.now()
        run.save()
        from notifications.models import Notification
        from conflicts.services import detect_exam_conflicts
        ec = detect_exam_conflicts(academic_year=ay, semester=sem, school=school, programme=programme, academic_level=academic_level, examination_period=period)
        if not created:
            Notification.objects.create(user=request.user, title='Timetable Generation Requires Attention',
                message=f'The system could not generate a fully valid timetable because of insufficient resources.',
                link='/scheduling/exams/', notification_type='generation_failed',
                metadata={'run_id': run.id, 'academic_level': academic_level})
        else:
            Notification.objects.create(user=request.user, title=f'New {level_label} Examination Timetable Generated',
                message=f'The {level_label} Examination Timetable for {ay} has been generated successfully. {len(created)} sessions created. Unscheduled: {len(unsched)}. {ec} conflicts detected.',
                link='/examinations/sessions/', notification_type='exam_generated',
                metadata={'run_id': run.id, 'academic_level': academic_level, 'alternatives': 0, 'validation': 'completed'})
        if ec > 0:
            Notification.objects.create(user=request.user, title='Conflict Detected',
                message=f'{ec} examination conflicts detected after generation.',
                link='/conflicts/', notification_type='conflict_detected', metadata={'count': ec})
        messages.success(request, f'Created {len(created)} exam sessions. Unscheduled: {len(unsched)}')
        return redirect('exam_session_list')
    return render(request, 'scheduling/generate_exam.html', {
        'periods': ExaminationPeriod.objects.all(),
        'years': AcademicYear.objects.all(),
        'semesters': Semester.objects.all(),
        'schools': School.objects.all(),
        'programmes': Programme.objects.all(),
    })
