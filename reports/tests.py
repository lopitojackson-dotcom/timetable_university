from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from institutions.models import Institution, School, Department
from academics.models import AcademicYear, Semester, Programme, ClassGroup, AcademicUnit
from resources.models import Lecturer, Venue
from teaching.models import TeachingSession

User = get_user_model()

class PdfLayoutTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='pdf', password='p', role='super_admin', is_superuser=True)
        inst = Institution.objects.create(name='Inst')
        school = School.objects.create(name='School', code='SCH', institution=inst)
        dept = Department.objects.create(name='Dept', code='DEP', school=school)
        prog = Programme.objects.create(name='Prog', code='PRG', department=dept, school=school, level='degree')
        ay = AcademicYear.objects.create(name='2026/2027', start_date='2026-01-01', end_date='2026-12-31')
        sem = Semester.objects.create(academic_year=ay, name='Sem1', start_date='2026-01-01', end_date='2026-06-30')
        cg = ClassGroup.objects.create(programme=prog, academic_year=ay, semester=sem, study_year=1, study_semester=1, expected_population=50)
        unit = AcademicUnit.objects.create(code='U1', name='Unit One', department=dept, programme=prog)
        lect = Lecturer.objects.create(staff_number='L1', full_name='Lecturer One', department=dept, school=school)
        unit.lecturers.add(lect)
        venue = Venue.objects.create(name='Room', code='R1', capacity=100, teaching_enabled=True, examination_enabled=True)
        TeachingSession.objects.create(academic_year=ay, semester=sem, school=school, department=dept, programme=prog, class_group=cg, unit=unit, lecturer=lect, day='Friday', start_time='07:00', end_time='10:00', venue=venue, student_population=50, status='draft')
        self.client = Client()
        self.client.force_login(self.user)

    def test_teaching_pdf_one_page_with_friday(self):
        from pypdf import PdfReader
        import io
        r = self.client.get('/reports/teaching/layout/?preview=1')
        self.assertEqual(r.status_code, 200)
        rd = PdfReader(io.BytesIO(r.content))
        self.assertEqual(len(rd.pages), 1)
        text = "\n".join((p.extract_text() or '') for p in rd.pages)
        self.assertIn('FRIDAY', text.upper())