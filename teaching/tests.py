from django.test import TestCase
from institutions.models import Institution, School, Department
from academics.models import AcademicYear, Semester, Programme, ClassGroup, AcademicUnit
from resources.models import Lecturer, Venue
from .models import TeachingSession
from conflicts.services import detect_teaching_conflicts

class ConflictTests(TestCase):
    def setUp(self):
        inst = Institution.objects.create(name='MUT')
        sch = School.objects.create(name='S', code='S', institution=inst)
        dep = Department.objects.create(name='D', code='D', school=sch)
        prog = Programme.objects.create(name='P', code='P', department=dep, school=sch)
        ay = AcademicYear.objects.create(name='2026/2027', start_date='2026-09-01', end_date='2027-04-30')
        sem = Semester.objects.create(name='S1', academic_year=ay, start_date='2026-09-01', end_date='2026-12-20')
        cg = ClassGroup.objects.create(programme=prog, academic_year=ay, semester=sem, study_year=1, study_semester=1, group_name='G1', expected_population=10)
        unit = AcademicUnit.objects.create(code='U1', name='Unit1', department=dep, programme=prog)
        lec = Lecturer.objects.create(staff_number='L1', full_name='Lec', department=dep, school=sch)
        ven = Venue.objects.create(name='R1', code='R1', venue_type='lecture_room', capacity=40, active=True)
        self.s1 = TeachingSession.objects.create(academic_year=ay, semester=sem, school=sch, department=dep, programme=prog, study_year=1, study_semester=1, class_group=cg, unit=unit, lecturer=lec, day='Monday', start_time='08:00', end_time='10:00', venue=ven, status='draft')
        self.s2 = TeachingSession.objects.create(academic_year=ay, semester=sem, school=sch, department=dep, programme=prog, study_year=1, study_semester=1, class_group=cg, unit=unit, lecturer=lec, day='Monday', start_time='09:00', end_time='11:00', venue=ven, status='draft')

    def test_conflict_detected(self):
        n = detect_teaching_conflicts()
        self.assertGreater(n, 0)


from django.core.exceptions import ValidationError
from django.test import TestCase
from institutions.models import Institution, School, Department
from academics.models import AcademicYear, Semester, Programme, ClassGroup, AcademicUnit
from resources.models import Lecturer, Venue


class WeekendValidationTests(TestCase):
    def setUp(self):
        inst = Institution.objects.create(name='MUT')
        sch = School.objects.create(name='S', code='S', institution=inst)
        dep = Department.objects.create(name='D', code='D', school=sch)
        prog = Programme.objects.create(name='P', code='P', department=dep, school=sch)
        ay = AcademicYear.objects.create(name='2026/2027', start_date='2026-09-01', end_date='2027-04-30')
        sem = Semester.objects.create(name='S1', academic_year=ay, start_date='2026-09-01', end_date='2026-12-20')
        cg = ClassGroup.objects.create(programme=prog, academic_year=ay, semester=sem, study_year=1, study_semester=1, group_name='G1', expected_population=10)
        unit = AcademicUnit.objects.create(code='U1', name='Unit1', department=dep, programme=prog)
        lec = Lecturer.objects.create(staff_number='L1', full_name='Lec', department=dep, school=sch)
        ven = Venue.objects.create(name='R1', code='R1', venue_type='lecture_room', capacity=40, active=True)

    def test_rejects_saturday(self):
        inst = Institution.objects.first()
        sch = School.objects.first()
        dep = Department.objects.first()
        prog = Programme.objects.first()
        ay = AcademicYear.objects.first()
        sem = Semester.objects.first()
        cg = ClassGroup.objects.first()
        unit = AcademicUnit.objects.first()
        lec = Lecturer.objects.first()
        ven = Venue.objects.first()
        from teaching.models import TeachingSession
        with self.assertRaises(ValidationError):
            TeachingSession.objects.create(academic_year=ay, semester=sem, school=sch, department=dep,
                programme=prog, study_year=1, study_semester=1, class_group=cg, unit=unit, lecturer=lec,
                day='Saturday', start_time='08:00', end_time='10:00', venue=ven, status='draft')

    def test_rejects_sunday(self):
        ay = AcademicYear.objects.first()
        sem = Semester.objects.first()
        cg = ClassGroup.objects.first()
        unit = AcademicUnit.objects.first()
        lec = Lecturer.objects.first()
        ven = Venue.objects.first()
        sch = School.objects.first()
        dep = Department.objects.first()
        prog = Programme.objects.first()
        from teaching.models import TeachingSession
        with self.assertRaises(ValidationError):
            TeachingSession.objects.create(academic_year=ay, semester=sem, school=sch, department=dep,
                programme=prog, study_year=1, study_semester=1, class_group=cg, unit=unit, lecturer=lec,
                day='Sunday', start_time='08:00', end_time='10:00', venue=ven, status='draft')
