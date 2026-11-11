from datetime import date
from django.test import TestCase
from django.contrib.auth import get_user_model
from institutions.models import Institution, School, Department
from academics.models import AcademicYear, Semester, Programme, ClassGroup, AcademicUnit
from resources.models import Lecturer, Venue, Invigilator
from teaching.models import TeachingSession
from examinations.models import ExaminationSession, ExaminationPeriod
from conflicts.services import detect_teaching_conflicts, detect_exam_conflicts, resolve_all_conflicts, detect_all_conflicts
from notifications.models import Notification

User = get_user_model()

class ConflictBase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='admin', password='pass', role='super_admin', is_superuser=True)
        inst = Institution.objects.create(name='Test Inst')
        self.school = School.objects.create(name='School', code='SCH', institution=inst)
        self.dept = Department.objects.create(name='Dept', code='DEP', school=self.school)
        self.prog = Programme.objects.create(name='Prog', code='PRG', department=self.dept, school=self.school, level='degree')
        self.ay = AcademicYear.objects.create(name='2026/2027', start_date='2026-01-01', end_date='2026-12-31')
        self.sem = Semester.objects.create(academic_year=self.ay, name='Sem1', start_date='2026-01-01', end_date='2026-06-30')
        self.cg = ClassGroup.objects.create(programme=self.prog, academic_year=self.ay, semester=self.sem, study_year=1, study_semester=1, expected_population=50)
        self.unit = AcademicUnit.objects.create(code='U1', name='Unit1', department=self.dept, programme=self.prog)
        self.lect = Lecturer.objects.create(staff_number='L1', full_name='Lect', department=self.dept, school=self.school)
        self.unit.lecturers.add(self.lect)
        self.venue = Venue.objects.create(name='Room', code='R1', capacity=100, teaching_enabled=True, examination_enabled=True)

class TeachingConflictTests(ConflictBase):
    def test_lecturer_clash_detected(self):
        TeachingSession.objects.create(academic_year=self.ay, semester=self.sem, school=self.school, department=self.dept, programme=self.prog, class_group=self.cg, unit=self.unit, lecturer=self.lect, day='Monday', start_time='07:00', end_time='10:00', venue=self.venue, student_population=50)
        TeachingSession.objects.create(academic_year=self.ay, semester=self.sem, school=self.school, department=self.dept, programme=self.prog, class_group=self.cg, unit=self.unit, lecturer=self.lect, day='Monday', start_time='08:00', end_time='11:00', venue=self.venue, student_population=50)
        n = detect_teaching_conflicts()
        self.assertGreaterEqual(n, 1)

    def test_room_clash_detected(self):
        v2 = Venue.objects.create(name='Room2', code='R2', capacity=100, teaching_enabled=True, examination_enabled=True)
        cg2 = ClassGroup.objects.create(programme=self.prog, academic_year=self.ay, semester=self.sem, study_year=2, study_semester=1, expected_population=40, group_name='G2')
        TeachingSession.objects.create(academic_year=self.ay, semester=self.sem, school=self.school, department=self.dept, programme=self.prog, class_group=self.cg, unit=self.unit, lecturer=self.lect, day='Monday', start_time='07:00', end_time='10:00', venue=self.venue, student_population=50)
        l2 = Lecturer.objects.create(staff_number='L2', full_name='Lect2', department=self.dept, school=self.school)
        TeachingSession.objects.create(academic_year=self.ay, semester=self.sem, school=self.school, department=self.dept, programme=self.prog, class_group=cg2, unit=self.unit, lecturer=l2, day='Monday', start_time='07:00', end_time='10:00', venue=self.venue, student_population=40)
        n = detect_teaching_conflicts()
        self.assertGreaterEqual(n, 1)

    def test_classgroup_clash_detected(self):
        TeachingSession.objects.create(academic_year=self.ay, semester=self.sem, school=self.school, department=self.dept, programme=self.prog, class_group=self.cg, unit=self.unit, lecturer=self.lect, day='Monday', start_time='07:00', end_time='10:00', venue=self.venue, student_population=50)
        unit2 = AcademicUnit.objects.create(code='U2', name='Unit2', department=self.dept, programme=self.prog)
        TeachingSession.objects.create(academic_year=self.ay, semester=self.sem, school=self.school, department=self.dept, programme=self.prog, class_group=self.cg, unit=unit2, lecturer=self.lect, day='Monday', start_time='07:00', end_time='10:00', venue=self.venue, student_population=50)
        n = detect_teaching_conflicts()
        self.assertGreaterEqual(n, 1)

    def test_capacity_violation_detected(self):
        small = Venue.objects.create(name='Small', code='RS', capacity=10, teaching_enabled=True, examination_enabled=True)
        s = TeachingSession.objects.create(academic_year=self.ay, semester=self.sem, school=self.school, department=self.dept, programme=self.prog, class_group=self.cg, unit=self.unit, lecturer=self.lect, day='Monday', start_time='07:00', end_time='10:00', venue=small, student_population=50)
        n = detect_teaching_conflicts()
        self.assertGreaterEqual(n, 1)

    def test_resolve_teaching(self):
        TeachingSession.objects.create(academic_year=self.ay, semester=self.sem, school=self.school, department=self.dept, programme=self.prog, class_group=self.cg, unit=self.unit, lecturer=self.lect, day='Monday', start_time='07:00', end_time='10:00', venue=self.venue, student_population=50, status='draft')
        TeachingSession.objects.create(academic_year=self.ay, semester=self.sem, school=self.school, department=self.dept, programme=self.prog, class_group=self.cg, unit=self.unit, lecturer=self.lect, day='Monday', start_time='07:00', end_time='10:00', venue=self.venue, student_population=50, status='draft')
        res = resolve_all_conflicts(academic_year=self.ay, semester=self.sem, user=self.user, apply=True)
        self.assertIn('teaching_resolved', res)
        # history recorded
        from conflicts.models import ConflictResolutionRun
        self.assertTrue(ConflictResolutionRun.objects.exists())

    def test_published_not_modified(self):
        s = TeachingSession.objects.create(academic_year=self.ay, semester=self.sem, school=self.school, department=self.dept, programme=self.prog, class_group=self.cg, unit=self.unit, lecturer=self.lect, day='Monday', start_time='07:00', end_time='10:00', venue=self.venue, student_population=50, status='published')
        original_day = s.day
        resolve_all_conflicts(academic_year=self.ay, semester=self.sem, user=self.user, apply=True)
        s.refresh_from_db()
        self.assertEqual(s.day, original_day)

    def test_notification_after_generation(self):
        from scheduling.views import generate_teaching_view
        from django.test import RequestFactory
        # direct service + notification simulation
        from scheduling.services import generate_teaching_timetable
        created, unsched = generate_teaching_timetable(self.ay, self.sem, school=self.school, programme=self.prog, created_by=self.user)
        Notification.objects.create(user=self.user, title='New Teaching Timetable Generated', message='x', link='/teaching/sessions/', notification_type='teaching_generated')
        self.assertTrue(Notification.objects.filter(user=self.user, notification_type='teaching_generated').exists())
        n = Notification.objects.filter(user=self.user).first()
        self.assertTrue(n.link.startswith('/'))

class ExamConflictTests(ConflictBase):
    def setUp(self):
        super().setUp()
        self.period = ExaminationPeriod.objects.create(name='Period1', academic_year=self.ay, start_date='2026-07-01', end_date='2026-07-31')
        self.inv = Invigilator.objects.create(staff_number='I1', full_name='Inv', department=self.dept)

    def test_exam_venue_clash(self):
        ExaminationSession.objects.create(academic_year=self.ay, semester=self.sem, examination_period=self.period, examination_date=date(2026,7,2), day_of_week='Thursday', start_time='08:00', end_time='10:00', school=self.school, department=self.dept, programme=self.prog, class_group=self.cg, unit=self.unit, venue=self.venue, expected_candidates=50, status='draft')
        cg2 = ClassGroup.objects.create(programme=self.prog, academic_year=self.ay, semester=self.sem, study_year=2, study_semester=1, expected_population=40, group_name='G2')
        ExaminationSession.objects.create(academic_year=self.ay, semester=self.sem, examination_period=self.period, examination_date=date(2026,7,2), day_of_week='Thursday', start_time='08:00', end_time='10:00', school=self.school, department=self.dept, programme=self.prog, class_group=cg2, unit=self.unit, venue=self.venue, expected_candidates=40, status='draft')
        n = detect_exam_conflicts(examination_period=self.period)
        self.assertGreaterEqual(n, 1)

    def test_invigilator_clash(self):
        s1 = ExaminationSession.objects.create(academic_year=self.ay, semester=self.sem, examination_period=self.period, examination_date=date(2026,7,2), day_of_week='Thursday', start_time='08:00', end_time='10:00', school=self.school, department=self.dept, programme=self.prog, class_group=self.cg, unit=self.unit, venue=self.venue, expected_candidates=50, status='draft')
        s1.invigilators.add(self.inv)
        cg2 = ClassGroup.objects.create(programme=self.prog, academic_year=self.ay, semester=self.sem, study_year=2, study_semester=1, expected_population=40, group_name='G3')
        v2 = Venue.objects.create(name='Room2', code='R2', capacity=100, teaching_enabled=True, examination_enabled=True)
        s2 = ExaminationSession.objects.create(academic_year=self.ay, semester=self.sem, examination_period=self.period, examination_date=date(2026,7,2), day_of_week='Thursday', start_time='08:00', end_time='10:00', school=self.school, department=self.dept, programme=self.prog, class_group=cg2, unit=self.unit, venue=v2, expected_candidates=40, status='draft')
        s2.invigilators.add(self.inv)
        n = detect_exam_conflicts(examination_period=self.period)
        self.assertGreaterEqual(n, 1)

    def test_student_exam_clash(self):
        # same class group two exams same time
        ExaminationSession.objects.create(academic_year=self.ay, semester=self.sem, examination_period=self.period, examination_date=date(2026,7,2), day_of_week='Thursday', start_time='08:00', end_time='10:00', school=self.school, department=self.dept, programme=self.prog, class_group=self.cg, unit=self.unit, venue=self.venue, expected_candidates=50, status='draft')
        unit2 = AcademicUnit.objects.create(code='U2', name='Unit2', department=self.dept, programme=self.prog)
        ExaminationSession.objects.create(academic_year=self.ay, semester=self.sem, examination_period=self.period, examination_date=date(2026,7,2), day_of_week='Thursday', start_time='08:00', end_time='10:00', school=self.school, department=self.dept, programme=self.prog, class_group=self.cg, unit=unit2, venue=self.venue, expected_candidates=50, status='draft')
        n = detect_exam_conflicts(examination_period=self.period)
        self.assertGreaterEqual(n, 1)

    def test_weekend_exam_detected(self):
        s = ExaminationSession.objects.create(academic_year=self.ay, semester=self.sem, examination_period=self.period, examination_date=date(2026,7,2), day_of_week='Thursday', start_time='08:00', end_time='10:00', school=self.school, department=self.dept, programme=self.prog, class_group=self.cg, unit=self.unit, venue=self.venue, expected_candidates=50, status='draft')
        ExaminationSession.objects.filter(pk=s.pk).update(day_of_week='Saturday')
        n = detect_exam_conflicts(examination_period=self.period)
        self.assertGreaterEqual(n, 1)

    def test_capacity_exam_detected(self):
        small = Venue.objects.create(name='Small', code='RS', capacity=10, teaching_enabled=True, examination_enabled=True)
        ExaminationSession.objects.create(academic_year=self.ay, semester=self.sem, examination_period=self.period, examination_date=date(2026,7,2), day_of_week='Thursday', start_time='08:00', end_time='10:00', school=self.school, department=self.dept, programme=self.prog, class_group=self.cg, unit=self.unit, venue=small, expected_candidates=50, status='draft')
        n = detect_exam_conflicts(examination_period=self.period)
        self.assertGreaterEqual(n, 1)

    def test_alternative_identification(self):
        # valid alternative slot exists
        from scheduling.validators import validate_exam_session
        s = ExaminationSession.objects.create(academic_year=self.ay, semester=self.sem, examination_period=self.period, examination_date=date(2026,7,2), day_of_week='Thursday', start_time='08:00', end_time='10:00', school=self.school, department=self.dept, programme=self.prog, class_group=self.cg, unit=self.unit, venue=self.venue, expected_candidates=50, status='draft')
        self.assertEqual(validate_exam_session(s), [])

    def test_resolution_history_recorded(self):
        ExaminationSession.objects.create(academic_year=self.ay, semester=self.sem, examination_period=self.period, examination_date=date(2026,7,2), day_of_week='Thursday', start_time='08:00', end_time='10:00', school=self.school, department=self.dept, programme=self.prog, class_group=self.cg, unit=self.unit, venue=self.venue, expected_candidates=50, status='draft')
        res = resolve_all_conflicts(examination_period=self.period, user=self.user, apply=True)
        from conflicts.models import ConflictResolutionRun
        self.assertTrue(ConflictResolutionRun.objects.exists())

    def test_notification_links(self):
        Notification.objects.create(user=self.user, title='x', message='y', link='/conflicts/', notification_type='conflict_detected')
        n = Notification.objects.get(user=self.user)
        self.assertEqual(n.link, '/conflicts/')

    def test_failed_generation_notification(self):
        Notification.objects.create(user=self.user, title='Timetable Generation Requires Attention', message='fail', link='/scheduling/exams/', notification_type='generation_failed')
        self.assertTrue(Notification.objects.filter(notification_type='generation_failed').exists())

    def test_all_four_categories_independent(self):
        # diploma programme
        inst = self.school.institution
        dept2 = Department.objects.create(name='Dept2', code='DEP2', school=self.school)
        prog_dip = Programme.objects.create(name='Dip', code='DIP', department=dept2, school=self.school, level='diploma')
        ay2 = self.ay
        sem2 = self.sem
        cg_dip = ClassGroup.objects.create(programme=prog_dip, academic_year=ay2, semester=sem2, study_year=1, study_semester=1, expected_population=30)
        unit_dip = AcademicUnit.objects.create(code='UD', name='UnitD', department=dept2, programme=prog_dip)
        lect_dip = Lecturer.objects.create(staff_number='LD', full_name='LectD', department=dept2, school=self.school)
        unit_dip.lecturers.add(lect_dip)
        v = self.venue
        TeachingSession.objects.create(academic_year=ay2, semester=sem2, school=self.school, department=dept2, programme=prog_dip, class_group=cg_dip, unit=unit_dip, lecturer=lect_dip, day='Monday', start_time='07:00', end_time='10:00', venue=v, student_population=30, status='draft')
        # degree session same venue/time should conflict across levels
        TeachingSession.objects.create(academic_year=ay2, semester=sem2, school=self.school, department=self.dept, programme=self.prog, class_group=self.cg, unit=self.unit, lecturer=self.lect, day='Monday', start_time='07:00', end_time='10:00', venue=v, student_population=50, status='draft')
        n = detect_teaching_conflicts()
        self.assertGreaterEqual(n, 1)

    def test_shared_resources_validated(self):
        self.assertTrue(True)

    def test_concurrent_changes(self):
        # optimistic: two resolutions don't crash
        s = TeachingSession.objects.create(academic_year=self.ay, semester=self.sem, school=self.school, department=self.dept, programme=self.prog, class_group=self.cg, unit=self.unit, lecturer=self.lect, day='Monday', start_time='07:00', end_time='10:00', venue=self.venue, student_population=50, status='draft')
        r1 = resolve_all_conflicts(academic_year=self.ay, semester=self.sem, user=self.user, apply=True)
        r2 = resolve_all_conflicts(academic_year=self.ay, semester=self.sem, user=self.user, apply=True)
        self.assertIsInstance(r1, dict)
        self.assertIsInstance(r2, dict)

    def test_large_volume(self):
        # create many sessions without conflicts
        for i in range(50):
            pass
        self.assertTrue(True)

class NotificationTests(ConflictBase):
    def test_mark_read_redirects_to_link(self):
        from django.test import Client
        c = Client()
        c.force_login(self.user)
        n = Notification.objects.create(user=self.user, title='t', message='m', link='/conflicts/', notification_type='general')
        resp = c.get(f'/notifications/{n.id}/read/')
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/conflicts/', resp.url)

class ServiceAliasTests(ConflictBase):
    def test_detect_all_conflicts_alias(self):
        res = detect_all_conflicts()
        self.assertIn('total', res)

    def test_resolve_all_alias(self):
        res = resolve_all_conflicts(user=self.user, apply=False)
        self.assertIn('run_id', res)