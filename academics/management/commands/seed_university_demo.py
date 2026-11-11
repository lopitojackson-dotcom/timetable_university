from django.core.management.base import BaseCommand
from django.db import transaction
from institutions.models import Institution, School, Department
from academics.models import AcademicYear, Semester, Programme, ClassGroup, AcademicUnit, StudentPopulation
from resources.models import Lecturer, Venue, Invigilator
from accounts.models import User
import random

SCHOOLS = [
    ("School of Computing and Information Technology", "SCIT", [
        ("Department of Computer Science", "DCS"),
        ("Department of Information Technology", "DIT"),
        ("Department of Software Engineering", "DSE"),
    ]),
    ("School of Business and Economics", "SBE", [
        ("Department of Business Administration", "DBA"),
        ("Department of Accounting and Finance", "DAF"),
        ("Department of Economics", "DEC"),
    ]),
    ("School of Engineering and Technology", "SET", [
        ("Department of Electrical Engineering", "DEE"),
        ("Department of Mechanical Engineering", "DME"),
        ("Department of Civil Engineering", "DCE"),
    ]),
    ("School of Education", "SED", [
        ("Department of Educational Foundations", "DEF"),
        ("Department of Curriculum Studies", "DCS2"),
        ("Department of Educational Technology", "DET"),
    ]),
    ("School of Pure and Applied Sciences", "SPAS", [
        ("Department of Mathematics", "DMATH"),
        ("Department of Physics", "DPHY"),
        ("Department of Chemistry", "DCHEM"),
    ]),
    ("School of Agriculture and Environmental Sciences", "SAES", [
        ("Department of Agricultural Sciences", "DAG"),
        ("Department of Environmental Sciences", "DENV"),
        ("Department of Food Science", "DFS"),
    ]),
    ("School of Social Sciences and Humanities", "SSSH", [
        ("Department of Social Sciences", "DSS"),
        ("Department of Communication Studies", "DCOM"),
        ("Department of Humanities", "DHUM"),
    ]),
]

FIRST_NAMES = ["James","Mary","John","Patricia","Robert","Jennifer","Michael","Linda","William","Elizabeth","David","Barbara","Richard","Susan","Joseph","Jessica","Thomas","Sarah","Charles","Karen","Daniel","Nancy","Matthew","Lisa","Anthony","Betty","Mark","Margaret","Donald","Sandra"]
LAST_NAMES = ["Smith","Johnson","Williams","Brown","Jones","Garcia","Miller","Davis","Rodriguez","Martinez","Hernandez","Lopez","Gonzalez","Wilson","Anderson","Thomas","Taylor","Moore","Jackson","Martin","Lee","Perez","Thompson","White","Harris","Sanchez","Clark","Ramirez","Lewis","Robinson"]

class Command(BaseCommand):
    help = "Seed realistic university demo data"

    def add_arguments(self, parser):
        parser.add_argument('--students', type=int, default=21000)
        parser.add_argument('--reset', action='store_true')

    @transaction.atomic
    def handle(self, *args, **options):
        n_students = options['students']
        if options['reset']:
            # delete demo data only (students, class groups, units, lecturers, venues, programmes, departments, schools) but keep institution
            StudentPopulation.objects.all().delete()
            ClassGroup.objects.all().delete()
            AcademicUnit.objects.all().delete()
            Lecturer.objects.all().delete()
            Invigilator.objects.all().delete()
            Venue.objects.all().delete()
            Programme.objects.all().delete()
            Department.objects.all().delete()
            School.objects.all().delete()
            self.stdout.write("Reset demo data.")

        inst, _ = Institution.objects.get_or_create(name="Murang'a University of Technology", defaults={'address':'Murang\'a, Kenya','email':'info@mut.ac.ke'})

        # Schools & departments
        schools = []
        depts = []
        for sname, scode, dlist in SCHOOLS:
            sch, _ = School.objects.get_or_create(code=scode, defaults={'name': sname, 'institution': inst})
            schools.append(sch)
            for dname, dcode in dlist:
                dep, _ = Department.objects.get_or_create(code=dcode, defaults={'name': dname, 'school': sch})
                depts.append(dep)

        # Academic year & semester
        ay, _ = AcademicYear.objects.get_or_create(name='2026/2027', defaults={'start_date':'2026-09-01','end_date':'2027-04-30'})
        sem, _ = Semester.objects.get_or_create(academic_year=ay, name='Semester 1', defaults={'start_date':'2026-09-01','end_date':'2026-12-20','teaching_start_date':'2026-09-01','teaching_end_date':'2026-12-01','examination_start_date':'2026-12-02','examination_end_date':'2026-12-20','status':'active'})

        # Programmes: 70 total (30 diploma, 40 degree)
        prog_types = [('Diploma', 30), ('Degree', 40)]
        programmes = []
        # distribute across departments
        dept_cycle = depts[:]
        idx = 0
        prog_counter = 1
        for level, qty in prog_types:
            for i in range(qty):
                dep = dept_cycle[idx % len(dept_cycle)]
                idx += 1
                code = f"{'DIP' if level=='Diploma' else 'BSC'}-{prog_counter:03d}"
                name = f"{'Diploma' if level=='Diploma' else 'Bachelor of Science'} in {dep.name.split('of')[-1].strip() if 'of' in dep.name else dep.name} {i+1}"
                lvl = 'diploma' if level == 'Diploma' else 'degree'
                prog, _ = Programme.objects.get_or_create(code=code, defaults={'name': name, 'department': dep, 'school': dep.school, 'level': lvl, 'status': 'active'})
                programmes.append(prog)
                prog_counter += 1

        # Lecturers: 200
        lecturers = []
        for i in range(1, 201):
            dep = depts[i % len(depts)]
            lec, _ = Lecturer.objects.get_or_create(staff_number=f"MUT/STAFF/{i:03d}", defaults={
                'full_name': f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
                'email': f"staff{i}@mut.ac.ke",
                'telephone': f"07{random.randint(10000000,99999999)}",
                'department': dep,
                'school': dep.school,
                'employment_status': random.choice(['full_time','full_time','full_time','part_time','contract']),
                'max_teaching_hours_week': random.choice([12,15,18,21]),
                'availability': 'Available Mon-Fri',
            })
            lecturers.append(lec)

        # Invigilators: create from lecturers
        for lec in lecturers[:100]:
            Invigilator.objects.get_or_create(staff_number=lec.staff_number, defaults={
                'full_name': lec.full_name, 'email': lec.email, 'department': lec.department,
                'availability': lec.availability, 'max_invigilations_per_day': 2,
                'employment_status': lec.employment_status, 'lecturer': lec,
            })

        # Venues: 200
        venues = []
        types = ['lecture_room','lecture_room','lecture_room','computer_lab','science_lab']
        for i in range(1, 201):
            vtype = random.choice(types)
            cap = random.choice([40,60,80,100,120,150,200,250,300,400,600])
            is_teaching = i <= 170
            venue, _ = Venue.objects.get_or_create(code=f"R{i:03d}", defaults={
                'name': f"Room {i:03d}",
                'venue_type': vtype,
                'building': f"Building {random.randint(1,8)}",
                'floor': str(random.randint(0,4)),
                'capacity': cap,
                'availability': 'Available',
                'active': True,
                'teaching_enabled': is_teaching,
                'examination_enabled': True,
            })
            venues.append(venue)

        # Academic units: 5 per programme
        units = []
        for prog in programmes:
            for j in range(1, 6):
                dep = prog.department
                unit, _ = AcademicUnit.objects.get_or_create(code=f"{prog.code}-U{j}", defaults={
                    'name': f"{prog.code} Unit {j}",
                    'department': dep,
                    'programme': prog,
                    'academic_year': ay,
                    'semester': sem,
                    'credit_hours': random.choice([2,3,3,4]),
                    'classification': random.choice(['theory','theory','practical','both']),
                    'active': True,
                })
                # assign 1-2 lecturers
                lecs = random.sample(lecturers, k=random.randint(1,2))
                unit.lecturers.set(lecs)
                # associate programme via programmes m2m
                unit.programmes.add(prog)
                units.append(unit)

        # Distribute 21000 students across programmes
        total = n_students
        # weights: random
        weights = [random.randint(100, 600) for _ in programmes]
        s = sum(weights)
        alloc = [int(total * w / s) for w in weights]
        # adjust remainder
        diff = total - sum(alloc)
        alloc[0] += diff

        student_counter = 1
        class_groups = []
        for prog, count in zip(programmes, alloc):
            # one class group per programme (could split but keep simple)
            cg, _ = ClassGroup.objects.get_or_create(programme=prog, academic_year=ay, semester=sem, study_year=1, study_semester=1, group_name='Group 1', defaults={
                'expected_population': count,
                'study_mode': random.choice(['regular','regular','odel']),
            })
            class_groups.append(cg)
            StudentPopulation.objects.get_or_create(class_group=cg, academic_year=ay, semester=sem, defaults={
                'expected_enrolment': count, 'actual_enrolment': count,
            })
            # create student users? Skip creating 21k users to save time; counts tracked via class groups
            student_counter += count

        self.stdout.write(self.style.SUCCESS(f"Seeded: {len(schools)} schools, {len(depts)} depts, {len(programmes)} programmes, {len(lecturers)} lecturers, {len(venues)} venues, {sum(alloc)} students (target {n_students})"))
