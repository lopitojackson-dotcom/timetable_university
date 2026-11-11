from django.test import TestCase
from django.core.exceptions import ValidationError
from datetime import date

from institutions.models import Institution, School, Department
from academics.models import AcademicYear, Semester, Programme, ClassGroup, AcademicUnit
from resources.models import Venue, Invigilator, Lecturer
from examinations.models import ExaminationPeriod, ExaminationSession
from datetime import timedelta


class ExamWeekendValidationTests(TestCase):
    def setUp(self):
        inst = Institution.objects.create(name='MUT')
        sch = School.objects.create(name='S', code='S', institution=inst)
        dep = Department.objects.create(name='D', code='D', school=sch)
        prog = Programme.objects.create(name='P', code='P', department=dep, school=sch)
        ay = AcademicYear.objects.create(name='2026/2027', start_date='2026-09-01', end_date='2027-04-30')
        sem = Semester.objects.create(name='S1', academic_year=ay, start_date='2026-09-01', end_date='2026-12-20')
        cg = ClassGroup.objects.create(programme=prog, academic_year=ay, semester=sem, study_year=1, study_semester=1, group_name='G1', expected_population=10)
        unit = AcademicUnit.objects.create(code='U1', name='Unit1', department=dep, programme=prog)
        ven = Venue.objects.create(name='R1', code='R1', venue_type='lecture_room', capacity=40, active=True, examination_enabled=True)
        period = ExaminationPeriod.objects.create(name='P1', academic_year=ay, start_date=date(2026,12,5), end_date=date(2026,12,6), status='draft')
        self.ctx = (inst, sch, dep, prog, ay, sem, cg, unit, ven, period)

    def test_rejects_saturday(self):
        inst, sch, dep, prog, ay, sem, cg, unit, ven, period = self.ctx
        # Saturday Dec 5 2026? Let's find a Saturday
        sat = date(2026, 12, 5)
        while sat.weekday() != 5:
            sat = sat + timedelta(days=1)
        with self.assertRaises(ValidationError):
            ExaminationSession.objects.create(academic_year=ay, semester=sem, examination_period=period,
                examination_date=sat, start_time='08:00', end_time='11:00', school=sch, department=dep,
                programme=prog, study_year=1, study_semester=1, class_group=cg, unit=unit,
                expected_candidates=10, venue=ven, status='draft')

    def test_rejects_sunday(self):
        inst, sch, dep, prog, ay, sem, cg, unit, ven, period = self.ctx
        sun = date(2026, 12, 6)
        while sun.weekday() != 6:
            sun = sun + timedelta(days=1)
        with self.assertRaises(ValidationError):
            ExaminationSession.objects.create(academic_year=ay, semester=sem, examination_period=period,
                examination_date=sun, start_time='08:00', end_time='11:00', school=sch, department=dep,
                programme=prog, study_year=1, study_semester=1, class_group=cg, unit=unit,
                expected_candidates=10, venue=ven, status='draft')
