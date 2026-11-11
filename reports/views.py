from django.shortcuts import render
from django.http import HttpResponse
import io, zipfile
from teaching.models import TeachingSession
from examinations.models import ExaminationSession, ExaminationPeriod
from academics.models import AcademicYear, Semester, Programme, ClassGroup
from institutions.models import School, Department
from reports.layout import (classgroup_column_label, period_string_for_teaching,
                           period_string_for_exam, chunks)
from reports.pdf import build_teaching_pdf, build_exam_pdf
from reports.excel import build_teaching_excel, build_exam_excel


def index(request):
    return render(request, 'reports/index.html', {
        'years': AcademicYear.objects.all(),
        'semesters': Semester.objects.all(),
        'schools': School.objects.all(),
        'departments': Department.objects.all(),
        'programmes': Programme.objects.all(),
        'periods': ExaminationPeriod.objects.all(),
    })


def _teaching_filters(request):
    qs = TeachingSession.objects.all()
    if request.GET.get('academic_level'):
        qs = qs.filter(programme__level=request.GET['academic_level'])
    if request.GET.get('academic_year'):
        qs = qs.filter(academic_year_id=request.GET['academic_year'])
    if request.GET.get('semester'):
        qs = qs.filter(semester_id=request.GET['semester'])
    if request.GET.get('school'):
        qs = qs.filter(school_id=request.GET['school'])
    if request.GET.get('department'):
        qs = qs.filter(department_id=request.GET['department'])
    if request.GET.get('programme'):
        qs = qs.filter(programme_id=request.GET['programme'])
    if request.GET.get('study_year'):
        qs = qs.filter(study_year=request.GET['study_year'])
    if request.GET.get('class_group'):
        qs = qs.filter(class_group_id=request.GET['class_group'])
    if request.GET.get('lecturer'):
        qs = qs.filter(lecturer_id=request.GET['lecturer'])
    if request.GET.get('study_level'):
        qs = qs.filter(programme__level=request.GET['study_level'])
    return qs


def _exam_filters(request):
    qs = ExaminationSession.objects.all()
    if request.GET.get('academic_level'):
        qs = qs.filter(programme__level=request.GET['academic_level'])
    if request.GET.get('period'):
        qs = qs.filter(examination_period_id=request.GET['period'])
    if request.GET.get('academic_year'):
        qs = qs.filter(academic_year_id=request.GET['academic_year'])
    if request.GET.get('semester'):
        qs = qs.filter(semester_id=request.GET['semester'])
    if request.GET.get('school'):
        qs = qs.filter(school_id=request.GET['school'])
    if request.GET.get('department'):
        qs = qs.filter(department_id=request.GET['department'])
    if request.GET.get('programme'):
        qs = qs.filter(programme_id=request.GET['programme'])
    if request.GET.get('study_year'):
        qs = qs.filter(study_year=request.GET['study_year'])
    if request.GET.get('class_group'):
        qs = qs.filter(class_group_id=request.GET['class_group'])
    if request.GET.get('lecturer'):
        qs = qs.filter(unit_lecturer_id=request.GET['lecturer'])
    if request.GET.get('study_level'):
        qs = qs.filter(programme__level=request.GET['study_level'])
    return qs


def _teaching_columns(qs):
    cg_ids = list(qs.values_list('class_group', flat=True).distinct())
    cgs = list(ClassGroup.objects.filter(id__in=cg_ids).select_related('programme'))
    # determine multiple groups per programme/year/sem
    from collections import Counter
    counts = Counter((cg.programme_id, cg.study_year, cg.study_semester) for cg in cgs)
    cols = []
    for cg in sorted(cgs, key=lambda x: (x.programme.code, x.study_year, x.study_semester, x.group_name)):
        multiple = counts[(cg.programme_id, cg.study_year, cg.study_semester)] > 1
        cols.append({'id': cg.id, 'label': classgroup_column_label(cg, multiple=multiple), 'cg': cg})
    return cols


def _exam_columns(qs):
    return _teaching_columns(qs)


def _teaching_period(request, qs):
    sem = None
    ay = None
    if request.GET.get('semester'):
        try:
            sem = Semester.objects.get(pk=request.GET['semester'])
        except Semester.DoesNotExist:
            sem = None
    if request.GET.get('academic_year'):
        try:
            ay = AcademicYear.objects.get(pk=request.GET['academic_year'])
        except AcademicYear.DoesNotExist:
            ay = None
    if sem is None and qs.exists():
        sem = qs.first().semester
    if ay is None and qs.exists():
        ay = qs.first().academic_year
    return period_string_for_teaching(ay, sem)


def _exam_period(request, qs):
    period = None
    sem = None
    ay = None
    if request.GET.get('period'):
        try:
            period = ExaminationPeriod.objects.get(pk=request.GET['period'])
        except ExaminationPeriod.DoesNotExist:
            period = None
    if request.GET.get('semester'):
        try:
            sem = Semester.objects.get(pk=request.GET['semester'])
        except Semester.DoesNotExist:
            sem = None
    if request.GET.get('academic_year'):
        try:
            ay = AcademicYear.objects.get(pk=request.GET['academic_year'])
        except AcademicYear.DoesNotExist:
            ay = None
    if period is None and qs.exists():
        period = qs.first().examination_period if hasattr(qs.first(), 'examination_period') else None
    if sem is None and qs.exists():
        sem = qs.first().semester
    if ay is None and qs.exists():
        ay = qs.first().academic_year
    return period_string_for_exam(ay, sem, period)


def _teaching_title(request):
    level = (request.GET.get('academic_level') or '').lower()
    if level == 'diploma':
        return 'Diploma Undergraduate Teaching Timetable'
    if level == 'degree':
        return 'Degree Undergraduate Teaching Timetable'
    return 'Undergraduate Teaching Timetable'


def teaching_layout_pdf(request):
    qs = _teaching_filters(request).order_by('day', 'start_time')
    columns = _teaching_columns(qs)
    version = request.GET.get('version', 'DRAFT 1')
    period = _teaching_period(request, qs)
    response = HttpResponse(content_type='application/pdf')
    disp = 'inline' if request.GET.get('preview') else 'attachment'
    response['Content-Disposition'] = f'{disp}; filename="teaching_layout.pdf"'
    cpp = int(request.GET.get('columns_per_page', 20) or 20)
    paper = request.GET.get('paper_size')
    from reports.pdf import build_teaching_pdf
    build_teaching_pdf(response, qs, columns, title=_teaching_title(request),
                       period=period, version=version, columns_per_page=cpp,
                       paper_size=paper)
    return response


def _exam_title(request):
    level = (request.GET.get('academic_level') or '').lower()
    if level == 'diploma':
        return 'Diploma Undergraduate Examination Timetable'
    if level == 'degree':
        return 'Degree Undergraduate Examination Timetable'
    return 'Undergraduate Examination Timetable'


def exam_layout_pdf(request):
    qs = _exam_filters(request).order_by('examination_date', 'start_time')
    columns = _exam_columns(qs)
    version = request.GET.get('version', 'DRAFT 1')
    period = _exam_period(request, qs)
    response = HttpResponse(content_type='application/pdf')
    disp = 'inline' if request.GET.get('preview') else 'attachment'
    response['Content-Disposition'] = f'{disp}; filename="exam_layout.pdf"'
    cpp = int(request.GET.get('columns_per_page', 20) or 20)
    paper = request.GET.get('paper_size')
    from reports.pdf import build_exam_pdf
    build_exam_pdf(response, qs, columns, title=_exam_title(request),
                   period=period, version=version, columns_per_page=cpp,
                   paper_size=paper)
    return response


# Backwards-compatible simple endpoints redirect to layout
def teaching_pdf(request):
    return teaching_layout_pdf(request)


def exam_pdf(request):
    return exam_layout_pdf(request)


def teaching_excel(request):
    qs = _teaching_filters(request).order_by('day', 'start_time')
    columns = _teaching_columns(qs)
    version = request.GET.get('version', 'DRAFT 1')
    period = _teaching_period(request, qs)
    cpp = int(request.GET.get('columns_per_page', 20) or 20)
    buf = build_teaching_excel(qs, columns, title=_teaching_title(request),
                               period=period, version=version, columns_per_page=cpp)
    response = HttpResponse(buf.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="teaching_timetable.xlsx"'
    return response


def exam_excel(request):
    qs = _exam_filters(request).order_by('examination_date', 'start_time')
    columns = _exam_columns(qs)
    version = request.GET.get('version', 'DRAFT 1')
    period = _exam_period(request, qs)
    cpp = int(request.GET.get('columns_per_page', 20) or 20)
    buf = build_exam_excel(qs, columns, title=_exam_title(request),
                           period=period, version=version, columns_per_page=cpp)
    response = HttpResponse(buf.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="exam_timetable.xlsx"'
    return response


def _available_year_semesters(request):
    from academics.models import ClassGroup
    qs = ClassGroup.objects.all()
    if request.GET.get('academic_level'):
        qs = qs.filter(programme__level=request.GET['academic_level'])
    if request.GET.get('school'):
        qs = qs.filter(programme__school_id=request.GET['school'])
    if request.GET.get('department'):
        qs = qs.filter(programme__department_id=request.GET['department'])
    if request.GET.get('programme'):
        qs = qs.filter(programme_id=request.GET['programme'])
    pairs = sorted(set((cg.study_year, cg.study_semester) for cg in qs))
    return pairs


def download_center(request):
    from institutions.models import School, Department
    from academics.models import Programme, AcademicYear, Semester
    pairs = _available_year_semesters(request)
    is_exam = request.GET.get('timetable_type') == 'examination'
    rows = []
    for y, s in pairs:
        q = request.GET.copy()
        q['study_year'] = y
        q['study_semester'] = s
        if is_exam:
            view_url = '/reports/exam/layout/?' + q.urlencode()
            pdf_url = '/reports/exam/layout/?' + q.urlencode()
            excel_url = '/reports/exam/excel/?' + q.urlencode()
        else:
            view_url = '/reports/teaching/layout/?' + q.urlencode()
            pdf_url = '/reports/teaching/layout/?' + q.urlencode()
            excel_url = '/reports/teaching/excel/?' + q.urlencode()
        rows.append({'year': y, 'semester': s, 'view_url': view_url,
                     'pdf_url': pdf_url, 'excel_url': excel_url})
    return render(request, 'reports/download_center.html', {
        'rows': rows,
        'years': AcademicYear.objects.all(),
        'semesters': Semester.objects.all(),
        'schools': School.objects.all(),
        'departments': Department.objects.all(),
        'programmes': Programme.objects.all(),
        'is_exam': is_exam,
    })


def download_all_years(request):
    is_exam = request.GET.get('timetable_type') == 'examination'
    pairs = _available_year_semesters(request)
    if not pairs:
        from django.http import HttpResponse
        return HttpResponse('No timetables available for the selected filters.', status=404)
    buf = io.BytesIO()
    zf = zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED)
    level = (request.GET.get('academic_level') or 'all').title()
    kind = 'Examinations' if is_exam else 'Teaching'
    ay_name = request.GET.get('academic_year')
    suffix = f"_{ay_name}" if ay_name else ''
    for y, s in pairs:
        from django.test import RequestFactory
        rf = RequestFactory()
        q = request.GET.copy()
        q['study_year'] = y
        q['study_semester'] = s
        req = rf.get('/x/', q.dict())
        from reports.views import _teaching_filters, _exam_filters, _teaching_columns, _exam_columns, _teaching_period, _exam_period
        if is_exam:
            qs = _exam_filters(req).order_by('examination_date', 'start_time')
            columns = _exam_columns(qs)
            period = _exam_period(req, qs)
            from reports.pdf import build_exam_pdf
            pdf_buf = io.BytesIO()
            title = 'Diploma Undergraduate Examination Timetable' if request.GET.get('academic_level') == 'diploma' else ('Degree Undergraduate Examination Timetable' if request.GET.get('academic_level') == 'degree' else 'Undergraduate Examination Timetable')
            build_exam_pdf(pdf_buf, qs, columns, title=title, period=period, version=request.GET.get('version', 'DRAFT 1'))
            fname = f"{level}_{kind}_Y{y}_S{s}{suffix}.pdf"
        else:
            qs = _teaching_filters(req).order_by('day', 'start_time')
            columns = _teaching_columns(qs)
            period = _teaching_period(req, qs)
            from reports.pdf import build_teaching_pdf
            pdf_buf = io.BytesIO()
            title = 'Diploma Undergraduate Teaching Timetable' if request.GET.get('academic_level') == 'diploma' else ('Degree Undergraduate Teaching Timetable' if request.GET.get('academic_level') == 'degree' else 'Undergraduate Teaching Timetable')
            build_teaching_pdf(pdf_buf, qs, columns, title=title, period=period, version=request.GET.get('version', 'DRAFT 1'))
            fname = f"{level}_{kind}_Y{y}_S{s}{suffix}.pdf"
        if pdf_buf.tell() == 0 and pdf_buf.getvalue() == b'':
            continue
        zf.writestr(fname, pdf_buf.getvalue())
    zf.close()
    buf.seek(0)
    from django.http import HttpResponse
    response = HttpResponse(buf.getvalue(), content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="{level}_{kind}_All_Years{suffix}.zip"'
    return response


def _lecturer_sessions(lecturer_id, request):
    from teaching.models import TeachingSession
    qs = TeachingSession.objects.filter(lecturer_id=lecturer_id).select_related('unit', 'programme', 'class_group', 'venue', 'academic_year', 'semester')
    if request.GET.get('academic_year'):
        qs = qs.filter(academic_year_id=request.GET['academic_year'])
    if request.GET.get('semester'):
        qs = qs.filter(semester_id=request.GET['semester'])
    if request.GET.get('academic_level'):
        qs = qs.filter(programme__level=request.GET['academic_level'])
    return qs


def _lecturer_matrix(sessions):
    from reports.layout import teaching_slots
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    slots = teaching_slots()  # (start,end)
    # map slot index
    def slot_index(s):
        for i, (st, en) in enumerate(slots):
            if s.start_time == st and s.end_time == en:
                return i
        return None
    grid = {}
    for d in days:
        for i in range(len(slots)):
            grid[(d, i)] = []
    for s in sessions:
        if s.day not in days:
            continue
        i = slot_index(s)
        if i is None:
            # append to a pseudo slot? skip for grid but keep in sessions
            continue
        grid[(s.day, i)].append(s)
    return days, slots, grid


def _lecturer_workload(sessions):
    from datetime import datetime, timedelta
    total_sessions = len(sessions)
    total_hours = 0.0
    for s in sessions:
        dt1 = datetime.combine(datetime.today(), s.start_time)
        dt2 = datetime.combine(datetime.today(), s.end_time)
        total_hours += (dt2 - dt1).total_seconds() / 3600.0
    units = len(set(s.unit_id for s in sessions))
    programmes = len(set(s.programme_id for s in sessions if s.programme_id))
    departments = len(set(s.department_id for s in sessions if s.department_id))
    groups = len(set(s.class_group_id for s in sessions if s.class_group_id))
    # free sessions
    days, slots, grid = _lecturer_matrix(sessions)
    occupied = sum(1 for d in days for i in range(len(slots)) if grid[(d, i)])
    free = len(days) * len(slots) - occupied
    # conflicts
    conflicts = 0
    for i, a in enumerate(sessions):
        for b in sessions[i+1:]:
            if a.day == b.day and a.start_time < b.end_time and b.start_time < a.end_time:
                conflicts += 1
    return {
        'total_sessions': total_sessions,
        'total_hours': round(total_hours, 2),
        'units': units,
        'programmes': programmes,
        'departments': departments,
        'groups': groups,
        'free_sessions': free,
        'conflicts': conflicts,
    }


def _lecturer_period(request, sessions):
    from academics.models import AcademicYear, Semester
    from reports.layout import period_string_for_teaching
    sem = None
    ay = None
    if request.GET.get('semester'):
        try:
            sem = Semester.objects.get(pk=request.GET['semester'])
        except Semester.DoesNotExist:
            sem = None
    if request.GET.get('academic_year'):
        try:
            ay = AcademicYear.objects.get(pk=request.GET['academic_year'])
        except AcademicYear.DoesNotExist:
            ay = None
    if sem is None and sessions:
        sem = sessions[0].semester
    if ay is None and sessions:
        ay = sessions[0].academic_year
    return period_string_for_teaching(ay, sem)


def lecturer_timetables(request):
    from resources.models import Lecturer
    from institutions.models import School, Department
    from academics.models import AcademicYear, Semester
    qs = Lecturer.objects.all()
    if request.GET.get('search'):
        q = request.GET['search']
        qs = qs.filter(full_name__icontains=q) | qs.filter(staff_number__icontains=q)
    if request.GET.get('school'):
        qs = qs.filter(school_id=request.GET['school'])
    if request.GET.get('department'):
        qs = qs.filter(department_id=request.GET['department'])
    selected = None
    sessions = []
    workload = None
    preview = False
    if request.GET.get('lecturer'):
        try:
            selected = Lecturer.objects.get(pk=request.GET['lecturer'])
            sessions = list(_lecturer_sessions(selected.id, request))
            workload = _lecturer_workload(sessions)
            preview = True
        except Lecturer.DoesNotExist:
            selected = None
    return render(request, 'reports/lecturer_timetables.html', {
        'lecturers': qs.order_by('full_name'),
        'schools': School.objects.all(),
        'departments': Department.objects.all(),
        'years': AcademicYear.objects.all(),
        'semesters': Semester.objects.all(),
        'selected': selected,
        'sessions': sessions,
        'workload': workload,
        'preview': preview,
    })


def lecturer_timetable_pdf(request):
    from resources.models import Lecturer
    lid = request.GET.get('lecturer')
    if not lid:
        return HttpResponse('lecturer parameter required', status=400)
    try:
        lecturer = Lecturer.objects.get(pk=lid)
    except Lecturer.DoesNotExist:
        return HttpResponse('Lecturer not found', status=404)
    sessions = list(_lecturer_sessions(lecturer.id, request))
    period = _lecturer_period(request, sessions)
    version = request.GET.get('version', 'DRAFT 1')
    from reports.pdf import build_lecturer_pdf
    response = HttpResponse(content_type='application/pdf')
    disp = 'inline' if request.GET.get('preview') else 'attachment'
    safe = lecturer.full_name.replace(' ', '_')
    response['Content-Disposition'] = f'{disp}; filename="MUT_Lecturer_{safe}_Weekly_Timetable.pdf"'
    build_lecturer_pdf(response, lecturer, sessions, title='Individual Lecturer Weekly Teaching Timetable',
                       period=period, version=version)
    return response


def lecturer_timetable_excel(request):
    from resources.models import Lecturer
    lid = request.GET.get('lecturer')
    if not lid:
        return HttpResponse('lecturer parameter required', status=400)
    try:
        lecturer = Lecturer.objects.get(pk=lid)
    except Lecturer.DoesNotExist:
        return HttpResponse('Lecturer not found', status=404)
    sessions = list(_lecturer_sessions(lecturer.id, request))
    period = _lecturer_period(request, sessions)
    version = request.GET.get('version', 'DRAFT 1')
    from reports.excel import build_lecturer_excel
    buf = build_lecturer_excel(lecturer, sessions, title='Individual Lecturer Weekly Teaching Timetable',
                               period=period, version=version)
    response = HttpResponse(buf.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    safe = lecturer.full_name.replace(' ', '_')
    response['Content-Disposition'] = f'attachment; filename="MUT_Lecturer_{safe}_Weekly_Timetable.xlsx"'
    return response


def lecturer_timetables_bulk(request):
    from resources.models import Lecturer
    from reports.pdf import build_lecturer_pdf
    lecturers = Lecturer.objects.all().order_by('full_name')
    if request.GET.get('school'):
        lecturers = lecturers.filter(school_id=request.GET['school'])
    if request.GET.get('department'):
        lecturers = lecturers.filter(department_id=request.GET['department'])
    buf = io.BytesIO()
    zf = zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED)
    for lec in lecturers:
        sessions = list(_lecturer_sessions(lec.id, request))
        if not sessions:
            continue
        period = _lecturer_period(request, sessions)
        pdf_buf = io.BytesIO()
        build_lecturer_pdf(pdf_buf, lec, sessions, title='Individual Lecturer Weekly Teaching Timetable',
                           period=period, version=request.GET.get('version', 'DRAFT 1'))
        safe = lec.staff_number or lec.full_name.replace(' ', '_')
        zf.writestr(f"{safe}_Weekly_Timetable.pdf", pdf_buf.getvalue())
    zf.close()
    buf.seek(0)
    response = HttpResponse(buf.getvalue(), content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename="MUT_All_Lecturer_Timetables.zip"'
    return response


def lecturer_timetables(request):
    from resources.models import Lecturer
    from institutions.models import School, Department
    from academics.models import AcademicYear, Semester
    qs = Lecturer.objects.all()
    if request.GET.get('search'):
        q = request.GET['search']
        qs = qs.filter(full_name__icontains=q) | qs.filter(staff_number__icontains=q)
    if request.GET.get('school'):
        qs = qs.filter(school_id=request.GET['school'])
    if request.GET.get('department'):
        qs = qs.filter(department_id=request.GET['department'])
    selected = None
    sessions = []
    workload = None
    preview = False
    if request.GET.get('lecturer'):
        try:
            selected = Lecturer.objects.get(pk=request.GET['lecturer'])
            sessions = list(_lecturer_sessions(selected.id, request))
            workload = _lecturer_workload(sessions)
            preview = True
        except Lecturer.DoesNotExist:
            selected = None
    return render(request, 'reports/lecturer_timetables.html', {
        'lecturers': qs.order_by('full_name'),
        'schools': School.objects.all(),
        'departments': Department.objects.all(),
        'years': AcademicYear.objects.all(),
        'semesters': Semester.objects.all(),
        'selected': selected,
        'sessions': sessions,
        'workload': workload,
        'preview': preview,
    })


def lecturer_timetable_pdf(request):
    from resources.models import Lecturer
    lid = request.GET.get('lecturer')
    if not lid:
        return HttpResponse('lecturer parameter required', status=400)
    try:
        lecturer = Lecturer.objects.get(pk=lid)
    except Lecturer.DoesNotExist:
        return HttpResponse('Lecturer not found', status=404)
    sessions = list(_lecturer_sessions(lecturer.id, request))
    period = _lecturer_period(request, sessions)
    version = request.GET.get('version', 'DRAFT 1')
    from reports.pdf import build_lecturer_pdf
    response = HttpResponse(content_type='application/pdf')
    disp = 'inline' if request.GET.get('preview') else 'attachment'
    safe = lecturer.full_name.replace(' ', '_')
    response['Content-Disposition'] = f'{disp}; filename="MUT_Lecturer_{safe}_Weekly_Timetable.pdf"'
    build_lecturer_pdf(response, lecturer, sessions, title='Individual Lecturer Weekly Teaching Timetable',
                       period=period, version=version)
    return response


def lecturer_timetable_excel(request):
    from resources.models import Lecturer
    lid = request.GET.get('lecturer')
    if not lid:
        return HttpResponse('lecturer parameter required', status=400)
    try:
        lecturer = Lecturer.objects.get(pk=lid)
    except Lecturer.DoesNotExist:
        return HttpResponse('Lecturer not found', status=404)
    sessions = list(_lecturer_sessions(lecturer.id, request))
    period = _lecturer_period(request, sessions)
    version = request.GET.get('version', 'DRAFT 1')
    from reports.excel import build_lecturer_excel
    buf = build_lecturer_excel(lecturer, sessions, title='Individual Lecturer Weekly Teaching Timetable',
                               period=period, version=version)
    response = HttpResponse(buf.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    safe = lecturer.full_name.replace(' ', '_')
    response['Content-Disposition'] = f'attachment; filename="MUT_Lecturer_{safe}_Weekly_Timetable.xlsx"'
    return response


def lecturer_timetables_bulk(request):
    from resources.models import Lecturer
    from reports.pdf import build_lecturer_pdf
    lecturers = Lecturer.objects.all().order_by('full_name')
    if request.GET.get('school'):
        lecturers = lecturers.filter(school_id=request.GET['school'])
    if request.GET.get('department'):
        lecturers = lecturers.filter(department_id=request.GET['department'])
    buf = io.BytesIO()
    zf = zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED)
    for lec in lecturers:
        sessions = list(_lecturer_sessions(lec.id, request))
        if not sessions:
            continue
        period = _lecturer_period(request, sessions)
        pdf_buf = io.BytesIO()
        build_lecturer_pdf(pdf_buf, lec, sessions, title='Individual Lecturer Weekly Teaching Timetable',
                           period=period, version=request.GET.get('version', 'DRAFT 1'))
        safe = lec.staff_number or lec.full_name.replace(' ', '_')
        zf.writestr(f"{safe}_Weekly_Timetable.pdf", pdf_buf.getvalue())
    zf.close()
    buf.seek(0)
    response = HttpResponse(buf.getvalue(), content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename="MUT_All_Lecturer_Timetables.zip"'
    return response


def _lecturer_sessions(lecturer_id, request):
    from teaching.models import TeachingSession
    qs = TeachingSession.objects.filter(lecturer_id=lecturer_id).select_related('unit', 'programme', 'class_group', 'venue', 'academic_year', 'semester')
    if request.GET.get('academic_year'):
        qs = qs.filter(academic_year_id=request.GET['academic_year'])
    if request.GET.get('semester'):
        qs = qs.filter(semester_id=request.GET['semester'])
    if request.GET.get('academic_level'):
        qs = qs.filter(programme__level=request.GET['academic_level'])
    return qs


def _lecturer_matrix(sessions):
    from reports.layout import teaching_slots
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    slots = teaching_slots()
    grid = {}
    for d in days:
        for i in range(len(slots)):
            grid[(d, i)] = []
    for s in sessions:
        if s.day not in days:
            continue
        idx = None
        for i, (st, en) in enumerate(slots):
            if s.start_time == st and s.end_time == en:
                idx = i
                break
        if idx is None:
            continue
        grid[(s.day, idx)].append(s)
    return days, slots, grid


def _lecturer_workload(sessions):
    from datetime import datetime
    total_sessions = len(sessions)
    total_hours = 0.0
    for s in sessions:
        dt1 = datetime.combine(datetime.today(), s.start_time)
        dt2 = datetime.combine(datetime.today(), s.end_time)
        total_hours += (dt2 - dt1).total_seconds() / 3600.0
    units = len(set(s.unit_id for s in sessions))
    programmes = len(set(s.programme_id for s in sessions if s.programme_id))
    departments = len(set(s.department_id for s in sessions if s.department_id))
    groups = len(set(s.class_group_id for s in sessions if s.class_group_id))
    days, slots, grid = _lecturer_matrix(sessions)
    occupied = sum(1 for d in days for i in range(len(slots)) if grid[(d, i)])
    free = len(days) * len(slots) - occupied
    conflicts = 0
    for i, a in enumerate(sessions):
        for b in sessions[i+1:]:
            if a.day == b.day and a.start_time < b.end_time and b.start_time < a.end_time:
                conflicts += 1
    return {
        'total_sessions': total_sessions,
        'total_hours': round(total_hours, 2),
        'units': units,
        'programmes': programmes,
        'departments': departments,
        'groups': groups,
        'free_sessions': free,
        'conflicts': conflicts,
    }


def _lecturer_period(request, sessions):
    from academics.models import AcademicYear, Semester
    from reports.layout import period_string_for_teaching
    sem = None
    ay = None
    if request.GET.get('semester'):
        try:
            sem = Semester.objects.get(pk=request.GET['semester'])
        except Semester.DoesNotExist:
            sem = None
    if request.GET.get('academic_year'):
        try:
            ay = AcademicYear.objects.get(pk=request.GET['academic_year'])
        except AcademicYear.DoesNotExist:
            ay = None
    if sem is None and sessions:
        sem = sessions[0].semester
    if ay is None and sessions:
        ay = sessions[0].academic_year
    return period_string_for_teaching(ay, sem)


def _lecturer_sessions(lecturer_id, request):
    from teaching.models import TeachingSession
    qs = TeachingSession.objects.filter(lecturer_id=lecturer_id).select_related('unit', 'programme', 'class_group', 'venue', 'academic_year', 'semester')
    if request.GET.get('academic_year'):
        qs = qs.filter(academic_year_id=request.GET['academic_year'])
    if request.GET.get('semester'):
        qs = qs.filter(semester_id=request.GET['semester'])
    if request.GET.get('academic_level'):
        qs = qs.filter(programme__level=request.GET['academic_level'])
    return qs


def _lecturer_matrix(sessions):
    from reports.layout import teaching_slots
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    slots = teaching_slots()
    grid = {}
    for d in days:
        for i in range(len(slots)):
            grid[(d, i)] = []
    for s in sessions:
        if s.day not in days:
            continue
        idx = None
        for i, (st, en) in enumerate(slots):
            if s.start_time == st and s.end_time == en:
                idx = i
                break
        if idx is None:
            continue
        grid[(s.day, idx)].append(s)
    return days, slots, grid


def _lecturer_workload(sessions):
    from datetime import datetime
    total_sessions = len(sessions)
    total_hours = 0.0
    for s in sessions:
        dt1 = datetime.combine(datetime.today(), s.start_time)
        dt2 = datetime.combine(datetime.today(), s.end_time)
        total_hours += (dt2 - dt1).total_seconds() / 3600.0
    units = len(set(s.unit_id for s in sessions))
    programmes = len(set(s.programme_id for s in sessions if s.programme_id))
    departments = len(set(s.department_id for s in sessions if s.department_id))
    groups = len(set(s.class_group_id for s in sessions if s.class_group_id))
    days, slots, grid = _lecturer_matrix(sessions)
    occupied = sum(1 for d in days for i in range(len(slots)) if grid[(d, i)])
    free = len(days) * len(slots) - occupied
    conflicts = 0
    for i, a in enumerate(sessions):
        for b in sessions[i+1:]:
            if a.day == b.day and a.start_time < b.end_time and b.start_time < a.end_time:
                conflicts += 1
    return {
        'total_sessions': total_sessions,
        'total_hours': round(total_hours, 2),
        'units': units,
        'programmes': programmes,
        'departments': departments,
        'groups': groups,
        'free_sessions': free,
        'conflicts': conflicts,
    }


def _lecturer_period(request, sessions):
    from academics.models import AcademicYear, Semester
    from reports.layout import period_string_for_teaching
    sem = None
    ay = None
    if request.GET.get('semester'):
        try:
            sem = Semester.objects.get(pk=request.GET['semester'])
        except Semester.DoesNotExist:
            sem = None
    if request.GET.get('academic_year'):
        try:
            ay = AcademicYear.objects.get(pk=request.GET['academic_year'])
        except AcademicYear.DoesNotExist:
            ay = None
    if sem is None and sessions:
        sem = sessions[0].semester
    if ay is None and sessions:
        ay = sessions[0].academic_year
    return period_string_for_teaching(ay, sem)
