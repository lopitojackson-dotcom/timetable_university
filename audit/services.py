from datetime import datetime, timedelta
from academics.models import AcademicUnit, ClassGroup, Programme
from teaching.models import TeachingSession
from examinations.models import ExaminationSession
from institutions.models import School, Department


def _unit_duration_hours(s):
    dt1 = datetime.combine(datetime.today(), s.start_time)
    dt2 = datetime.combine(datetime.today(), s.end_time)
    return (dt2 - dt1).total_seconds() / 3600.0


def audit_teaching_coverage(academic_level=None, school=None, department=None, programme=None,
                           academic_year=None, semester=None):
    results = []
    cgs = ClassGroup.objects.all()
    if academic_level:
        cgs = cgs.filter(programme__level=academic_level)
    if school:
        cgs = cgs.filter(programme__school_id=school)
    if department:
        cgs = cgs.filter(programme__department_id=department)
    if programme:
        cgs = cgs.filter(programme_id=programme)
    if academic_year:
        cgs = cgs.filter(academic_year_id=academic_year)
    if semester:
        cgs = cgs.filter(semester_id=semester)

    for cg in cgs.select_related('programme', 'academic_year', 'semester'):
        prog = cg.programme
        units = AcademicUnit.objects.filter(active=True)
        if prog:
            units = units.filter(programme=prog) | AcademicUnit.objects.filter(programmes=prog, active=True)
        if department:
            units = units.filter(department_id=department)
        if school:
            units = units.filter(department__school_id=school)
        units = units.distinct()
        for unit in units:
            required_hours = unit.required_hours_per_week or 3
            sessions = TeachingSession.objects.filter(class_group=cg, unit=unit)
            if academic_year:
                sessions = sessions.filter(academic_year_id=academic_year)
            if semester:
                sessions = sessions.filter(semester_id=semester)
            sessions = list(sessions)
            scheduled_hours = sum(_unit_duration_hours(s) for s in sessions)
            issues = []
            conflicts = False
            # capacity
            for s in sessions:
                if s.venue and s.student_population and s.venue.capacity and s.student_population > s.venue.capacity:
                    issues.append('Room capacity exceeded')
                if s.day in ('Saturday', 'Sunday'):
                    issues.append('Weekend allocation')
                if not s.lecturer:
                    issues.append('Missing lecturer')
                if not s.venue:
                    issues.append('Missing venue')
            # overlaps
            for i, a in enumerate(sessions):
                for b in sessions[i+1:]:
                    if a.day == b.day and a.start_time < b.end_time and b.start_time < a.end_time:
                        conflicts = True
                        issues.append('Overlapping sessions')
            if not sessions:
                status = 'MISSING'
            elif conflicts or issues:
                status = 'FAIL'
            elif scheduled_hours < required_hours:
                status = 'FAIL'
                issues.append('Insufficient hours')
            elif scheduled_hours > required_hours:
                status = 'EXCESS'
            elif scheduled_hours == required_hours:
                status = 'PASS'
            else:
                status = 'PARTIAL'
            results.append({
                'academic_level': prog.level if prog else '',
                'programme': str(prog),
                'programme_id': prog.id if prog else None,
                'year': cg.study_year,
                'semester': cg.study_semester,
                'unit_code': unit.code,
                'unit_name': unit.name,
                'group': cg.group_name,
                'required_hours': required_hours,
                'scheduled_hours': round(scheduled_hours, 2),
                'sessions': len(sessions),
                'status': status,
                'issues': '; '.join(sorted(set(issues))) if issues else '',
            })
    return results


def audit_exam_coverage(academic_level=None, school=None, department=None, programme=None,
                        academic_year=None, semester=None, examination_period=None):
    results = []
    cgs = ClassGroup.objects.all()
    if academic_level:
        cgs = cgs.filter(programme__level=academic_level)
    if school:
        cgs = cgs.filter(programme__school_id=school)
    if department:
        cgs = cgs.filter(programme__department_id=department)
    if programme:
        cgs = cgs.filter(programme_id=programme)
    if academic_year:
        cgs = cgs.filter(academic_year_id=academic_year)
    if semester:
        cgs = cgs.filter(semester_id=semester)

    for cg in cgs.select_related('programme', 'academic_year', 'semester'):
        prog = cg.programme
        units = AcademicUnit.objects.filter(active=True)
        if prog:
            units = units.filter(programme=prog) | AcademicUnit.objects.filter(programmes=prog, active=True)
        if department:
            units = units.filter(department_id=department)
        if school:
            units = units.filter(department__school_id=school)
        units = units.distinct()
        for unit in units:
            sessions = ExaminationSession.objects.filter(class_group=cg, unit=unit)
            if academic_year:
                sessions = sessions.filter(academic_year_id=academic_year)
            if semester:
                sessions = sessions.filter(semester_id=semester)
            if examination_period:
                sessions = sessions.filter(examination_period_id=examination_period)
            sessions = list(sessions)
            issues = []
            for s in sessions:
                if s.examination_date and s.examination_date.weekday() >= 5:
                    issues.append('Weekend exam')
                if s.venue and s.expected_candidates and s.venue.capacity and s.expected_candidates > s.venue.capacity:
                    issues.append('Room capacity exceeded')
                if not s.venue:
                    issues.append('Missing room')
            if not sessions:
                status = 'MISSING'
            elif issues:
                status = 'FAIL'
            else:
                status = 'PASS'
            results.append({
                'academic_level': prog.level if prog else '',
                'programme': str(prog),
                'programme_id': prog.id if prog else None,
                'year': cg.study_year,
                'semester': cg.study_semester,
                'unit_code': unit.code,
                'unit_name': unit.name,
                'group': cg.group_name,
                'required_exams': 1,
                'scheduled_exams': len(sessions),
                'status': status,
                'issues': '; '.join(sorted(set(issues))) if issues else '',
            })
    return results


def audit_summary(teaching_results, exam_results):
    def counts(res):
        from collections import Counter
        c = Counter(r['status'] for r in res)
        total = len(res)
        passed = c.get('PASS', 0)
        pct = round(100.0 * passed / total, 2) if total else 100.0
        return {'total': total, 'pass': passed, 'missing': c.get('MISSING', 0),
                'fail': c.get('FAIL', 0), 'partial': c.get('PARTIAL', 0),
                'excess': c.get('EXCESS', 0), 'percentage': pct}
    return {'teaching': counts(teaching_results), 'examination': counts(exam_results)}