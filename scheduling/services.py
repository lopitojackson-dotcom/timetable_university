from datetime import date, timedelta, time
from teaching.models import TeachingSession, TeachingTimeSlot, TeachingGenerationRun, TeachingAlternative
from examinations.models import ExaminationSession, ExaminationSessionVenue, ExaminationTimeSlot, ExaminationPeriod, ExaminationGenerationRun, ExaminationAlternative
from examinations.models import ExaminationSession, ExaminationTimeSlot, ExaminationPeriod
from academics.models import ClassGroup, AcademicUnit, AcademicYear, Semester
from resources.models import Venue, Lecturer, Invigilator
from institutions.models import School, Department
from academics.models import Programme

DEFAULT_TEACHING_SLOTS = [
    ('Morning 1', time(7,0), time(10,0)),
    ('Morning 2', time(10,0), time(13,0)),
    ('Afternoon', time(13,0), time(16,0)),
    ('Evening', time(16,0), time(19,0)),
]
DEFAULT_DAYS = ['Monday','Tuesday','Wednesday','Thursday','Friday']

def _teaching_slots():
    qs = list(TeachingTimeSlot.objects.filter(active=True).order_by('order','start_time'))
    if qs:
        return [(s.name, s.start_time, s.end_time) for s in qs]
    return DEFAULT_TEACHING_SLOTS

def _exam_slots():
    qs = list(ExaminationTimeSlot.objects.filter(active=True).order_by('order','start_time'))
    if qs:
        return [(s.name, s.start_time, s.end_time) for s in qs]
    return [('Session 1', time(8,0), time(10,0)),('Session 2', time(11,0), time(13,0)),('Session 3', time(14,0), time(16,0)),('Session 4', time(16,30), time(18,30))]

LAB_TYPES = {'practical','laboratory'}

def _allocate_exam_venues(pop):
    from resources.models import Venue
    venues = sorted([v for v in Venue.objects.filter(active=True, examination_enabled=True) if v.capacity and v.capacity > 0], key=lambda v: v.capacity)
    if not venues:
        venues = list(Venue.objects.filter(active=True, examination_enabled=True))
    chosen = []
    remaining = pop
    if not venues:
        return []
    # greedy largest? Use venues sorted by capacity desc for fewer rooms
    for v in sorted(venues, key=lambda x: x.capacity, reverse=True):
        if remaining <= 0:
            break
        take = min(v.capacity, remaining)
        if take <= 0:
            take = remaining
        chosen.append((v, take))
        remaining -= take
    if remaining > 0 and chosen:
        v, c = chosen[-1]
        chosen[-1] = (v, c + remaining)
        remaining = 0
    if not chosen:
        v = venues[0]
        chosen.append((v, pop))
    return chosen

def _max_capacity(exam=False):
    from resources.models import Venue
    qs = Venue.objects.filter(active=True)
    if exam:
        qs = qs.filter(examination_enabled=True)
    else:
        qs = qs.filter(teaching_enabled=True)
    caps = [v.capacity for v in qs if v.capacity and v.capacity > 0]
    return max(caps) if caps else 100

def _split_class_groups(cgs, exam=False):
    max_cap = _max_capacity(exam=exam)
    result = []
    for cg in cgs:
        pop = cg.expected_population or 0
        if pop <= 0 or pop <= max_cap:
            result.append(cg)
            continue
        # split into groups of max_cap
        sizes = []
        remaining = pop
        while remaining > 0:
            take = min(max_cap, remaining)
            sizes.append(take)
            remaining -= take
        for i, size in enumerate(sizes, start=1):
            gname = f"Group {i}"
            new_cg, _ = ClassGroup.objects.get_or_create(
                programme=cg.programme, academic_year=cg.academic_year, semester=cg.semester,
                study_year=cg.study_year, study_semester=cg.study_semester, group_name=gname,
                defaults={'expected_population': size, 'study_mode': cg.study_mode})
            if new_cg.expected_population != size:
                new_cg.expected_population = size
                new_cg.save()
            result.append(new_cg)
    return result

def generate_teaching_timetable(academic_year, semester, school=None, department=None, programme=None, created_by=None, academic_level=None):
    days = DEFAULT_DAYS
    slots = _teaching_slots()
    # class groups
    cgs = ClassGroup.objects.filter(academic_year=academic_year, semester=semester)
    if programme:
        cgs = cgs.filter(programme=programme)
    if school:
        cgs = cgs.filter(programme__school=school)
    if department:
        cgs = cgs.filter(programme__department=department)
    if academic_level:
        cgs = cgs.filter(programme__level=academic_level)
    cgs = _split_class_groups(list(cgs), exam=False)
    cgs.sort(key=lambda x: x.expected_population, reverse=True)

    # units
    units = AcademicUnit.objects.filter(active=True)
    if programme:
        units = units.filter(programme=programme) | AcademicUnit.objects.filter(programmes=programme, active=True)
    if department:
        units = units.filter(department=department)
    if school:
        units = units.filter(department__school=school)
    if academic_level:
        from django.db.models import Q
        units = units.filter(Q(programme__level=academic_level) | Q(programmes__level=academic_level))

    # existing sessions for conflict check
    existing = list(TeachingSession.objects.filter(academic_year=academic_year, semester=semester))
    created_sessions = []
    unscheduled = []

    def conflicts(day, start, end, lecturer, venue, cg):
        for s in existing + created_sessions:
            if s.day != day:
                continue
            if not (s.end_time <= start or end <= s.start_time):
                if s.lecturer_id and lecturer and s.lecturer_id == lecturer.id:
                    return True
                if s.venue_id and venue and s.venue_id == venue.id:
                    return True
                if s.class_group_id and cg and s.class_group_id == cg.id:
                    return True
        return False

    for cg in cgs:
        # units for this programme
        prog_units = [u for u in units if u.programme_id == cg.programme_id or cg.programme in list(u.programmes.all())]
        if not prog_units:
            prog_units = list(units.filter(programme__isnull=True)) if False else []
        for unit in prog_units:
            lects = list(unit.lecturers.all()) or [None]
            pop = cg.expected_population
            needs_lab = unit.classification in LAB_TYPES or unit.classification == 'both'
            venues_qs = Venue.objects.filter(active=True, teaching_enabled=True)
            if needs_lab:
                venues_qs = venues_qs.filter(venue_type__in=['computer_lab','science_lab','nursing_lab','chemistry_lab','botany_lab'])
            else:
                venues_qs = venues_qs.filter(venue_type__in=['lecture_room','assembly_hall','online'])
            venues_list = list(venues_qs.order_by('capacity'))
            cap_venues = [v for v in venues_list if v.capacity >= pop or v.venue_type == 'online']
            if not cap_venues:
                cap_venues = venues_list
            allocated = False
            for day in days:
                for slot_name, st, en in slots:
                    for lecturer in lects:
                        for v in cap_venues:
                            if conflicts(day, st, en, lecturer, v, cg):
                                continue
                            sess = TeachingSession.objects.create(
                                academic_year=academic_year, semester=semester,
                                school=cg.programme.school, department=cg.programme.department,
                                programme=cg.programme, study_year=cg.study_year, study_semester=cg.study_semester,
                                class_group=cg, unit=unit, lecturer=lecturer, day=day,
                                start_time=st, end_time=en, venue=v, session_type='practical' if needs_lab else 'lecture',
                                group_label=cg.group_name, student_population=pop, status='draft',
                                is_online=(v.venue_type=='online'), created_by=created_by)
                            created_sessions.append(sess)
                            allocated = True
                            break
                        if allocated:
                            break
                    if allocated:
                        break
                if allocated:
                    break
            if not allocated:
                unscheduled.append(f"{unit.code} for {cg}")
    return created_sessions, unscheduled

def generate_exam_timetable(examination_period, academic_year, semester=None, school=None, programme=None, created_by=None, academic_level=None):
    days_dates = []
    d = examination_period.start_date
    while d <= examination_period.end_date:
        if d.weekday() < 5:
            days_dates.append(d)
        d = d + timedelta(days=1)
    slots = _exam_slots()
    cgs = ClassGroup.objects.filter(academic_year=academic_year)
    if semester:
        cgs = cgs.filter(semester=semester)
    if programme:
        cgs = cgs.filter(programme=programme)
    if school:
        cgs = cgs.filter(programme__school=school)
    if academic_level:
        cgs = cgs.filter(programme__level=academic_level)
    cgs = _split_class_groups(list(cgs), exam=True)
    cgs.sort(key=lambda x: x.expected_population, reverse=True)

    units = AcademicUnit.objects.filter(active=True)
    if programme:
        units = units.filter(programme=programme) | AcademicUnit.objects.filter(programmes=programme, active=True)
    if school:
        units = units.filter(department__school=school)
    if academic_level:
        from django.db.models import Q
        units = units.filter(Q(programme__level=academic_level) | Q(programmes__level=academic_level))

    existing = list(ExaminationSession.objects.filter(examination_period=examination_period))
    existing_inv = [set(s.invigilators.values_list('id', flat=True)) for s in existing]
    created = []
    created_inv = []
    unscheduled = []

    def conflicts(dt, start, end, venue, cg, invs, lecturer):
        inv_ids = set(i.id for i in invs)
        all_sessions = list(enumerate(existing + created))
        for idx, s in all_sessions:
            if s.examination_date != dt:
                continue
            if not (s.end_time <= start or end <= s.start_time):
                if s.venue_id and venue and s.venue_id == venue.id:
                    return True
                if s.class_group_id and cg and s.class_group_id == cg.id:
                    return True
                inv_set = existing_inv[idx] if idx < len(existing_inv) else created_inv[idx - len(existing_inv)]
                if inv_set & inv_ids:
                    return True
                if s.unit_lecturer_id and lecturer and s.unit_lecturer_id == lecturer.id:
                    return True
        return False

    invigilators = list(Invigilator.objects.all())
    for cg in cgs:
        prog_units = [u for u in units if u.programme_id == cg.programme_id or cg.programme in list(u.programmes.all())]
        for unit in prog_units:
            lecturer = unit.lecturers.first() if unit.lecturers.exists() else None
            pop = cg.expected_population
            sufficient = [v for v in Venue.objects.filter(active=True, examination_enabled=True) if (v.capacity or 0) >= pop]
            venue_options = [[(v, pop)] for v in sufficient]
            multi = _allocate_exam_venues(pop)
            if multi:
                venue_options.append(multi)
            if not venue_options:
                venue_options = [[(Venue.objects.filter(active=True, examination_enabled=True).first(), pop)]]
            inv_candidates = []
            if invigilators:
                ninv = len(invigilators)
                for i in range(min(20, ninv)):
                    inv_candidates.append([invigilators[i], invigilators[(i + 1) % ninv]])
            else:
                inv_candidates = [[]]
            allocated = False
            for dt in days_dates:
                for slot_name, st, en in slots:
                    for venue_alloc in venue_options:
                        for invs in inv_candidates:
                            conflict_found = False
                            for v, _ in venue_alloc:
                                if conflicts(dt, st, en, v, cg, invs, lecturer):
                                    conflict_found = True
                                    break
                            if conflict_found:
                                continue
                            primary_v, primary_count = venue_alloc[0]
                            sess = ExaminationSession.objects.create(
                                academic_year=academic_year, semester=cg.semester,
                                examination_period=examination_period, examination_date=dt,
                                day_of_week=dt.strftime('%A'), start_time=st, end_time=en,
                                school=cg.programme.school, department=cg.programme.department,
                                programme=cg.programme, study_year=cg.study_year, study_semester=cg.study_semester,
                                class_group=cg, unit=unit, unit_lecturer=lecturer,
                                expected_candidates=pop, venue=primary_v, status='draft', created_by=created_by)
                            sess.invigilators.set(invs)
                            for v, cnt in venue_alloc[1:]:
                                ExaminationSessionVenue.objects.create(session=sess, venue=v, candidate_count=cnt)
                            created_inv.append(set(i.id for i in invs))
                            created.append(sess)
                            allocated = True
                            break
                        if allocated:
                            break
                    if allocated:
                        break
                if allocated:
                    break
            if not allocated:
                unscheduled.append(f"{unit.code} for {cg}")
    return created, unscheduled


def generate_teaching_alternatives(academic_year, semester, school=None, department=None, programme=None, created_by=None, count=10, academic_level=None, idempotency_key=None):
    import random, hashlib
    if idempotency_key is None:
        idempotency_key = hashlib.sha256(f"teaching|{academic_year.id}|{semester.id}|{getattr(school,'id',school)}|{getattr(department,'id',department)}|{getattr(programme,'id',programme)}|{academic_level}|{count}".encode()).hexdigest()
    existing_run = TeachingGenerationRun.objects.filter(idempotency_key=idempotency_key).first()
    if existing_run is not None:
        return existing_run, list(existing_run.alternatives.all())
    cgs = ClassGroup.objects.filter(academic_year=academic_year, semester=semester)
    if programme:
        cgs = cgs.filter(programme=programme)
    if school:
        cgs = cgs.filter(programme__school=school)
    if department:
        cgs = cgs.filter(programme__department=department)
    if academic_level:
        cgs = cgs.filter(programme__level=academic_level)
    cgs = _split_class_groups(list(cgs), exam=False)
    cgs.sort(key=lambda x: x.expected_population, reverse=True)

    units = AcademicUnit.objects.filter(active=True)
    if programme:
        units = (units.filter(programme=programme) | AcademicUnit.objects.filter(programmes=programme, active=True)).distinct()
    if department:
        units = units.filter(department=department)
    if school:
        units = units.filter(department__school=school)
    if academic_level:
        from django.db.models import Q
        units = units.filter(Q(programme__level=academic_level) | Q(programmes__level=academic_level))
    units = list(units)

    existing_sessions = list(TeachingSession.objects.filter(academic_year=academic_year, semester=semester))

    run = TeachingGenerationRun.objects.create(
        academic_level=academic_level, academic_year=academic_year, semester=semester, school=school, department=department,
        programme=programme, created_by=created_by, preferences={'count': count}, idempotency_key=idempotency_key)

    days = DEFAULT_DAYS[:]
    slots = _teaching_slots()
    venues_all = list(Venue.objects.filter(active=True, teaching_enabled=True))
    alternatives = []

    for alt_no in range(1, count + 1):
        rng = random.Random(alt_no * 9973 + run.id)
        alt_days = days[:]
        rng.shuffle(alt_days)
        alt_slots = slots[:]
        rng.shuffle(alt_slots)
        alt_venues = venues_all[:]
        rng.shuffle(alt_venues)

        alt = TeachingAlternative.objects.create(run=run, number=alt_no, seed=alt_no * 9973 + run.id)
        created_sessions = []
        unscheduled = []

        def conflicts(day, start, end, lecturer, venue, cg):
            for s in existing_sessions + created_sessions:
                if s.day != day:
                    continue
                if not (s.end_time <= start or end <= s.start_time):
                    if s.lecturer_id and lecturer and s.lecturer_id == lecturer.id:
                        return True
                    if s.venue_id and venue and s.venue_id == venue.id:
                        return True
                    if s.class_group_id and cg and s.class_group_id == cg.id:
                        return True
            return False

        for cg in cgs:
            prog_units = [u for u in units if u.programme_id == cg.programme_id or cg.programme in list(u.programmes.all())]
            for unit in prog_units:
                lects = list(unit.lecturers.all()) or [None]
                needs_lab = unit.classification in LAB_TYPES or unit.classification == 'both'
                if needs_lab:
                    vpool = [v for v in alt_venues if v.venue_type in ('computer_lab','science_lab','nursing_lab','chemistry_lab','botany_lab')]
                else:
                    vpool = [v for v in alt_venues if v.venue_type in ('lecture_room','assembly_hall','online')]
                if not vpool:
                    vpool = alt_venues
                cap_venues = [v for v in vpool if v.capacity >= cg.expected_population or v.venue_type == 'online']
                if not cap_venues:
                    cap_venues = vpool

                allocated = False
                for day in alt_days:
                    for slot_name, st, en in alt_slots:
                        for lecturer in lects:
                            for v in cap_venues:
                                if conflicts(day, st, en, lecturer, v, cg):
                                    continue
                                sess = TeachingSession.objects.create(
                                    academic_year=academic_year, semester=semester,
                                    school=cg.programme.school, department=cg.programme.department,
                                    programme=cg.programme, study_year=cg.study_year, study_semester=cg.study_semester,
                                    class_group=cg, unit=unit, lecturer=lecturer, day=day,
                                    start_time=st, end_time=en, venue=v,
                                    session_type='practical' if needs_lab else 'lecture',
                                    group_label=cg.group_name, student_population=cg.expected_population,
                                    status='draft', is_online=(v.venue_type == 'online'),
                                    created_by=created_by, generation_run=run, alternative=alt)
                                created_sessions.append(sess)
                                allocated = True
                                break
                            if allocated:
                                break
                        if allocated:
                            break
                    if allocated:
                        break
                if not allocated:
                    unscheduled.append(f"{unit.code} for {cg}")

        # conflict recount (should be 0 by construction)
        conflict_count = 0
        # score: coverage
        total = len(cgs) * max(1, len(units) // max(1, len(cgs))) if cgs else 1
        coverage = len(created_sessions)
        score = round(100.0 * coverage / max(1, coverage + len(unscheduled)), 2)
        valid = (len(unscheduled) == 0)
        alt.conflicts = conflict_count
        alt.unscheduled = len(unscheduled)
        alt.score = score
        alt.valid = valid
        alt.details = {'created': len(created_sessions), 'unscheduled': unscheduled}
        alt.save()
        alternatives.append(alt)

    return run, alternatives


def generate_exam_alternatives(examination_period, academic_year, semester=None, school=None, programme=None, created_by=None, count=10, academic_level=None, idempotency_key=None):
    import random, hashlib
    from datetime import timedelta
    if idempotency_key is None:
        idempotency_key = hashlib.sha256(f"exam|{examination_period.id}|{academic_year.id}|{getattr(semester,'id',semester)}|{getattr(school,'id',school)}|{getattr(programme,'id',programme)}|{academic_level}|{count}".encode()).hexdigest()
    existing_run = ExaminationGenerationRun.objects.filter(idempotency_key=idempotency_key).first()
    if existing_run is not None:
        return existing_run, list(existing_run.alternatives.all())
    days_dates = []
    d = examination_period.start_date
    while d <= examination_period.end_date:
        if d.weekday() < 5:
            days_dates.append(d)
        d = d + timedelta(days=1)

    cgs = ClassGroup.objects.filter(academic_year=academic_year)
    if semester:
        cgs = cgs.filter(semester=semester)
    if programme:
        cgs = cgs.filter(programme=programme)
    if school:
        cgs = cgs.filter(programme__school=school)
    if academic_level:
        cgs = cgs.filter(programme__level=academic_level)
    cgs = _split_class_groups(list(cgs), exam=True)
    cgs.sort(key=lambda x: x.expected_population, reverse=True)

    units = AcademicUnit.objects.filter(active=True)
    if programme:
        units = (units.filter(programme=programme) | AcademicUnit.objects.filter(programmes=programme, active=True)).distinct()
    if school:
        units = units.filter(department__school=school)
    if academic_level:
        from django.db.models import Q
        units = units.filter(Q(programme__level=academic_level) | Q(programmes__level=academic_level))
    units = list(units)

    existing_exams = list(ExaminationSession.objects.filter(examination_period=examination_period))

    run = ExaminationGenerationRun.objects.create(
        academic_level=academic_level, examination_period=examination_period, academic_year=academic_year, semester=semester,
        school=school, programme=programme, created_by=created_by, preferences={'count': count}, idempotency_key=idempotency_key)

    slots = _exam_slots()
    invigilators = list(Invigilator.objects.all())
    venues_all = list(Venue.objects.filter(active=True, examination_enabled=True))
    alternatives = []

    for alt_no in range(1, count + 1):
        rng = random.Random(alt_no * 7919 + run.id)
        alt_dates = days_dates[:]
        rng.shuffle(alt_dates)
        alt_slots = slots[:]
        rng.shuffle(alt_slots)
        alt_venues = venues_all[:]
        rng.shuffle(alt_venues)

        alt = ExaminationAlternative.objects.create(run=run, number=alt_no, seed=alt_no * 7919 + run.id)
        created = []
        created_inv = []
        unscheduled = []

        def conflicts(dt, start, end, venue, cg, invs, lecturer):
            inv_ids = set(i.id for i in invs)
            alls = list(existing_exams) + list(created)
            for idx, s in enumerate(alls):
                if s.examination_date != dt:
                    continue
                if not (s.end_time <= start or end <= s.start_time):
                    if s.venue_id and venue and s.venue_id == venue.id:
                        return True
                    if s.class_group_id and cg and s.class_group_id == cg.id:
                        return True
                    if idx < len(existing_exams):
                        inv_set = set(s.invigilators.values_list('id', flat=True))
                    else:
                        inv_set = created_inv[idx - len(existing_exams)]
                    if inv_set & inv_ids:
                        return True
                    if s.unit_lecturer_id and lecturer and s.unit_lecturer_id == lecturer.id:
                        return True
            return False

        for cg in cgs:
            prog_units = [u for u in units if u.programme_id == cg.programme_id or cg.programme in list(u.programmes.all())]
            for unit in prog_units:
                lecturer = unit.lecturers.first() if unit.lecturers.exists() else None
                pop = cg.expected_population
                sufficient = [v for v in alt_venues if (v.capacity or 0) >= pop and v.examination_enabled]
                venue_options = [[(v, pop)] for v in sufficient]
                multi = _allocate_exam_venues(pop)
                if multi:
                    venue_options.append(multi)
                if not venue_options:
                    venue_options = [[(alt_venues[0], pop)]] if alt_venues else []
                allocated = False
                if not venue_options:
                    unscheduled.append(f"{unit.code} for {cg}")
                    continue
                inv_candidates = []
                if invigilators:
                    ninv = len(invigilators)
                    for i in range(min(20, ninv)):
                        inv_candidates.append([invigilators[i], invigilators[(i + 1) % ninv]])
                else:
                    inv_candidates = [[]]
                for dt in alt_dates:
                    for slot_name, st, en in alt_slots:
                        for venue_alloc in venue_options:
                            for invs in inv_candidates:
                                conflict_found = False
                                for v, _ in venue_alloc:
                                    if conflicts(dt, st, en, v, cg, invs, lecturer):
                                        conflict_found = True
                                        break
                                if conflict_found:
                                    continue
                                primary_v, primary_count = venue_alloc[0]
                                sess = ExaminationSession.objects.create(
                                    academic_year=academic_year, semester=cg.semester,
                                    examination_period=examination_period, examination_date=dt,
                                    day_of_week=dt.strftime('%A'), start_time=st, end_time=en,
                                    school=cg.programme.school, department=cg.programme.department,
                                    programme=cg.programme, study_year=cg.study_year, study_semester=cg.study_semester,
                                    class_group=cg, unit=unit, unit_lecturer=lecturer,
                                    expected_candidates=pop, venue=primary_v, status='draft',
                                    created_by=created_by, generation_run=run, alternative=alt)
                                sess.invigilators.set(invs)
                                for v, cnt in venue_alloc[1:]:
                                    ExaminationSessionVenue.objects.create(session=sess, venue=v, candidate_count=cnt)
                                created_inv.append(set(i.id for i in invs))
                                created.append(sess)
                                allocated = True
                                break
                            if allocated:
                                break
                        if allocated:
                            break
                    if allocated:
                        break
                if not allocated:
                    unscheduled.append(f"{unit.code} for {cg}")

        score = round(100.0 * len(created) / max(1, len(created) + len(unscheduled)), 2)
        valid = (len(unscheduled) == 0)
        alt.conflicts = 0
        alt.unscheduled = len(unscheduled)
        alt.score = score
        alt.valid = valid
        alt.details = {'created': len(created), 'unscheduled': unscheduled}
        alt.save()
        alternatives.append(alt)

    return run, alternatives
