from datetime import time, date, timedelta
from django.db import transaction
from django.utils import timezone

from teaching.models import TeachingSession, TeachingTimeSlot, TeachingGenerationRun, TeachingAlternative
from examinations.models import ExaminationSession, ExaminationSessionVenue, ExaminationTimeSlot, ExaminationPeriod, ExaminationGenerationRun, ExaminationAlternative
from academics.models import ClassGroup, AcademicUnit, AcademicYear, Semester
from resources.models import Venue, Lecturer, Invigilator, AvailabilitySlot
from institutions.models import School, Department
from academics.models import Programme
from conflicts.models import ConflictRecord, ConflictResolutionRun, ConflictResolutionRecord
from notifications.models import Notification


DEFAULT_TEACHING_SLOTS = [
    (time(7, 0), time(10, 0)),
    (time(10, 0), time(13, 0)),
    (time(13, 0), time(16, 0)),
    (time(16, 0), time(19, 0)),
]
DEFAULT_DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']


def _teaching_slots():
    qs = list(TeachingTimeSlot.objects.filter(active=True).order_by('order', 'start_time'))
    if qs:
        return [(s.start_time, s.end_time) for s in qs]
    return DEFAULT_TEACHING_SLOTS


def _exam_slots():
    qs = list(ExaminationTimeSlot.objects.filter(active=True).order_by('order', 'start_time'))
    if qs:
        return [(s.start_time, s.end_time) for s in qs]
    return [(time(8, 0), time(10, 0)), (time(11, 0), time(13, 0)), (time(14, 0), time(16, 0)), (time(16, 30), time(18, 30))]


def _overlap(a_start, a_end, b_start, b_end):
    return not (a_end <= b_start or b_end <= a_start)


def _lecturer_available(lecturer, day, start, end):
    if lecturer is None:
        return True
    slots = AvailabilitySlot.objects.filter(lecturer=lecturer, day=day)
    if not slots.exists():
        return True
    for sl in slots:
        if sl.available and sl.start_time <= start and end <= sl.end_time:
            return True
    return False


def _venue_available(venue, day, start, end):
    if venue is None:
        return True
    slots = AvailabilitySlot.objects.filter(venue=venue, day=day)
    if not slots.exists():
        return True
    for sl in slots:
        if sl.available and sl.start_time <= start and end <= sl.end_time:
            return True
    return False


def _create_conflict(conflict_type, message, related_model='', related_id='', severity='error'):
    return ConflictRecord.objects.create(
        conflict_type=conflict_type, severity=severity, message=message,
        related_model=related_model, related_id=str(related_id) if related_id is not None else ''
    )


# ---------------- Teaching detection ----------------
def detect_teaching_conflicts(academic_level=None, school=None, department=None, programme=None,
                              academic_year=None, semester=None):
    ConflictRecord.objects.filter(conflict_type='teaching', resolved=False).delete()
    qs = TeachingSession.objects.all()
    if academic_year:
        qs = qs.filter(academic_year=academic_year)
    if semester:
        qs = qs.filter(semester=semester)
    if school:
        qs = qs.filter(school=school)
    if department:
        qs = qs.filter(department=department)
    if programme:
        qs = qs.filter(programme=programme)
    if academic_level:
        qs = qs.filter(programme__level=academic_level)
    sessions = list(qs)
    count = 0

    # per-session checks
    seen_pairs = set()
    for s in sessions:
        # missing lecturer/venue
        if not s.lecturer_id:
            _create_conflict('teaching', f"Missing lecturer for {s.unit.code} on {s.day} {s.start_time}-{s.end_time}", 'TeachingSession', s.id)
            count += 1
        if not s.venue_id:
            _create_conflict('teaching', f"Missing venue for {s.unit.code} on {s.day} {s.start_time}-{s.end_time}", 'TeachingSession', s.id)
            count += 1
        # invalid day
        if s.day in ('Saturday', 'Sunday'):
            _create_conflict('teaching', f"Invalid teaching day (weekend) for {s.unit.code}", 'TeachingSession', s.id)
            count += 1
        # invalid time
        if not (s.start_time and s.end_time and s.start_time < s.end_time):
            _create_conflict('teaching', f"Invalid session duration for {s.unit.code}", 'TeachingSession', s.id)
            count += 1
        # capacity (primary + extra venues)
        if s.venue and s.student_population:
            total_cap = s.venue.capacity or 0
            for ev in s.extra_venues.all():
                total_cap += (ev.capacity_override or (ev.venue.capacity if ev.venue else 0) or 0)
            if total_cap and s.student_population > total_cap:
                _create_conflict('teaching', f"Room capacity exceeded for {s.unit.code}: {s.student_population} > {total_cap}", 'TeachingSession', s.id)
                count += 1
        # academic year/semester correctness of unit
        try:
            unit = s.unit
            if unit.academic_year_id and unit.academic_year_id != s.academic_year_id:
                _create_conflict('teaching', f"Unit {unit.code} assigned to incorrect academic year for {s.programme}", 'TeachingSession', s.id)
                count += 1
            if unit.semester_id and unit.semester_id != s.semester_id:
                _create_conflict('teaching', f"Unit {unit.code} assigned to incorrect semester for {s.programme}", 'TeachingSession', s.id)
                count += 1
        except Exception:
            pass
        # availability
        if s.lecturer and not _lecturer_available(s.lecturer, s.day, s.start_time, s.end_time):
            _create_conflict('teaching', f"Lecturer {s.lecturer.full_name} unavailable for {s.unit.code} on {s.day} {s.start_time}-{s.end_time}", 'TeachingSession', s.id)
            count += 1
        if s.venue and not _venue_available(s.venue, s.day, s.start_time, s.end_time):
            _create_conflict('teaching', f"Venue {s.venue.code} unavailable for {s.unit.code} on {s.day} {s.start_time}-{s.end_time}", 'TeachingSession', s.id)
            count += 1
        # academic year/semester correctness (unit belongs)
        try:
            unit = s.unit
            if unit.programme_id and unit.programme_id != s.programme_id and s.programme not in list(unit.programmes.all()):
                _create_conflict('teaching', f"Unit {unit.code} assigned to incorrect programme/year/semester for {s.programme}", 'TeachingSession', s.id)
                count += 1
        except Exception:
            pass
        # duplicate pair
        pair = (s.unit_id, s.class_group_id)
        if pair in seen_pairs:
            _create_conflict('teaching', f"Duplicate unit scheduling: {s.unit.code} for {s.class_group}", 'TeachingSession', s.id)
            count += 1
        seen_pairs.add(pair)

    # pairwise
    for i, a in enumerate(sessions):
        for b in sessions[i + 1:]:
            if a.day != b.day:
                continue
            if not _overlap(a.start_time, a.end_time, b.start_time, b.end_time):
                continue
            if a.lecturer_id and a.lecturer_id == b.lecturer_id:
                _create_conflict('teaching', f"Lecturer {a.lecturer} double-booked: {a.unit.code} and {b.unit.code} on {a.day} {a.start_time}-{a.end_time}", 'TeachingSession', a.id)
                count += 1
            if a.venue_id and a.venue_id == b.venue_id:
                _create_conflict('teaching', f"Venue {a.venue} double-booked: {a.unit.code} and {b.unit.code} on {a.day} {a.start_time}-{a.end_time}", 'TeachingSession', a.id)
                count += 1
            if a.class_group_id and a.class_group_id == b.class_group_id:
                _create_conflict('teaching', f"Class group {a.class_group} clash: {a.unit.code} and {b.unit.code} on {a.day} {a.start_time}-{a.end_time}", 'TeachingSession', a.id)
                count += 1
            # student group population overlap handled by class group
    return count


# ---------------- Exam detection ----------------
def detect_exam_conflicts(academic_level=None, school=None, department=None, programme=None,
                         academic_year=None, semester=None, examination_period=None):
    ConflictRecord.objects.filter(conflict_type='examination', resolved=False).delete()
    qs = ExaminationSession.objects.all()
    if academic_year:
        qs = qs.filter(academic_year=academic_year)
    if semester:
        qs = qs.filter(semester=semester)
    if school:
        qs = qs.filter(school=school)
    if department:
        qs = qs.filter(department=department)
    if programme:
        qs = qs.filter(programme=programme)
    if academic_level:
        qs = qs.filter(programme__level=academic_level)
    if examination_period:
        qs = qs.filter(examination_period=examination_period)
    sessions = list(qs)
    count = 0

    for s in sessions:
        if not s.venue_id:
            _create_conflict('examination', f"Missing examination venue for {s.unit.code} on {s.examination_date}", 'ExaminationSession', s.id)
            count += 1
        if not s.invigilators.exists():
            _create_conflict('examination', f"Missing invigilator for {s.unit.code} on {s.examination_date}", 'ExaminationSession', s.id)
            count += 1
        if s.examination_date and s.examination_date.weekday() >= 5:
            _create_conflict('examination', f"Examination scheduled on weekend for {s.unit.code}", 'ExaminationSession', s.id)
            count += 1
        if s.examination_period_id:
            if s.examination_date < s.examination_period.start_date or s.examination_date > s.examination_period.end_date:
                _create_conflict('examination', f"Examination outside approved period for {s.unit.code}", 'ExaminationSession', s.id)
                count += 1
        if not (s.start_time and s.end_time and s.start_time < s.end_time):
            _create_conflict('examination', f"Invalid examination duration for {s.unit.code}", 'ExaminationSession', s.id)
            count += 1
        if s.expected_candidates:
            total_cap = 0
            for v, c in s.venue_allocations():
                if v:
                    total_cap += v.capacity or 0
            if total_cap and s.expected_candidates > total_cap:
                _create_conflict('examination', f"Insufficient exam venue capacity for {s.unit.code}: {s.expected_candidates} > {total_cap}", 'ExaminationSession', s.id)
                count += 1
        # invigilator max per day
        if s.invigilators.exists():
            for inv in s.invigilators.all():
                day_sessions = [x for x in sessions if x.examination_date == s.examination_date and x.invigilators.filter(pk=inv.pk).exists()]
                if len(day_sessions) > getattr(inv, 'max_invigilations_per_day', 2):
                    _create_conflict('examination', f"Invigilator {inv.full_name} exceeds daily limit on {s.examination_date}", 'ExaminationSession', s.id)
                    count += 1
                    break
        # lecturer availability
        if s.unit_lecturer_id:
            # basic availability slots
            from resources.models import AvailabilitySlot
            slots = AvailabilitySlot.objects.filter(lecturer=s.unit_lecturer, day=s.day_of_week)
            if slots.exists():
                ok = any(sl.available and sl.start_time <= s.start_time and s.end_time <= sl.end_time for sl in slots)
                if not ok:
                    _create_conflict('examination', f"Lecturer {s.unit_lecturer.full_name} unavailable for {s.unit.code}", 'ExaminationSession', s.id)
                    count += 1
        # candidate allocated to more than one room for same exam: check venue allocations total
        allocs = s.venue_allocations()
        venues = [v for v, _ in allocs]
        if len(venues) != len(set(v.id for v in venues if v)):
            _create_conflict('examination', f"Candidate allocated to duplicate room for {s.unit.code}", 'ExaminationSession', s.id)
            count += 1
        total_alloc = sum(c for _, c in allocs)
        if total_alloc and total_alloc != s.expected_candidates:
            _create_conflict('examination', f"Candidate allocation mismatch for {s.unit.code}: {total_alloc} vs {s.expected_candidates}", 'ExaminationSession', s.id, severity='warning')
            count += 1
        # invigilator availability? basic: max per day could be checked but skip

    for i, a in enumerate(sessions):
        for b in sessions[i + 1:]:
            if a.examination_date != b.examination_date:
                continue
            if not _overlap(a.start_time, a.end_time, b.start_time, b.end_time):
                continue
            if a.venue_id and a.venue_id == b.venue_id:
                _create_conflict('examination', f"Venue {a.venue} double-booked exams: {a.unit.code} and {b.unit.code}", 'ExaminationSession', a.id)
                count += 1
            if a.class_group_id and a.class_group_id == b.class_group_id:
                _create_conflict('examination', f"Class group clash exams: {a.unit.code} and {b.unit.code}", 'ExaminationSession', a.id)
                count += 1
            shared_inv = set(a.invigilators.values_list('id', flat=True)) & set(b.invigilators.values_list('id', flat=True))
            if shared_inv:
                _create_conflict('examination', f"Invigilator double-booked: {a.unit.code} and {b.unit.code}", 'ExaminationSession', a.id)
                count += 1
            if a.unit_lecturer_id and a.unit_lecturer_id == b.unit_lecturer_id:
                _create_conflict('examination', f"Lecturer clash: {a.unit.code} and {b.unit.code}", 'ExaminationSession', a.id)
                count += 1
            # shared venue across multi-venue allocations
            a_venues = set(v.id for v, _ in a.venue_allocations() if v)
            b_venues = set(v.id for v, _ in b.venue_allocations() if v)
            if a_venues & b_venues:
                # only if not already primary venue equality? already counted; count as room clash if any shared
                if not (a.venue_id and a.venue_id == b.venue_id):
                    _create_conflict('examination', f"Shared examination room between {a.unit.code} and {b.unit.code}", 'ExaminationSession', a.id)
                    count += 1
    # capacity per venue across overlapping? primary check done
    return count


def detect_all_conflicts(**scope):
    t = detect_teaching_conflicts(**{k: v for k, v in scope.items() if k in ('academic_level','school','department','programme','academic_year','semester')})
    e = detect_exam_conflicts(**{k: v for k, v in scope.items() if k in ('academic_level','school','department','programme','academic_year','semester','examination_period')})
    return {'teaching': t, 'examination': e, 'total': t + e}


# ---------------- Resolution ----------------
def _session_to_dict(s):
    return {'id': s.id, 'day': s.day, 'start': str(s.start_time), 'end': str(s.end_time), 'venue': s.venue_id, 'lecturer': s.lecturer_id}


def resolve_teaching_conflicts(academic_level=None, school=None, department=None, programme=None,
                               academic_year=None, semester=None, user=None, apply=True,
                               run=None):
    from teaching.models import TeachingSession
    qs = TeachingSession.objects.all()
    if academic_year:
        qs = qs.filter(academic_year=academic_year)
    if semester:
        qs = qs.filter(semester=semester)
    if school:
        qs = qs.filter(school=school)
    if department:
        qs = qs.filter(department=department)
    if programme:
        qs = qs.filter(programme=programme)
    if academic_level:
        qs = qs.filter(programme__level=academic_level)
    sessions = list(qs.order_by('id'))
    days = DEFAULT_DAYS
    slots = _teaching_slots()
    venues = list(Venue.objects.filter(active=True, teaching_enabled=True))
    fixed = []
    resolved = 0
    records = []
    for s in sessions:
        # skip published/approved? protect published
        if s.status in ('approved', 'published'):
            fixed.append(s)
            continue
        def conflict_with_fixed(sess):
            for f in fixed:
                if f.day != sess.day:
                    continue
                if not _overlap(f.start_time, f.end_time, sess.start_time, sess.end_time):
                    continue
                if f.lecturer_id and sess.lecturer_id and f.lecturer_id == sess.lecturer_id:
                    return True
                if f.venue_id and sess.venue_id and f.venue_id == sess.venue_id:
                    return True
                if f.class_group_id and sess.class_group_id and f.class_group_id == sess.class_group_id:
                    return True
            return False

        if not conflict_with_fixed(s):
            fixed.append(s)
            continue
        original = _session_to_dict(s)
        moved = False
        proposed = None
        for day in days:
            for st, en in slots:
                for v in venues:
                    if v.capacity and s.student_population and v.capacity < s.student_population and v.venue_type != 'online':
                        continue
                    if not _lecturer_available(s.lecturer, day, st, en):
                        continue
                    if not _venue_available(v, day, st, en):
                        continue
                    old = (s.day, s.start_time, s.end_time, s.venue_id)
                    s.day = day
                    s.start_time = st
                    s.end_time = en
                    s.venue = v
                    if conflict_with_fixed(s):
                        s.day, s.start_time, s.end_time = old[0], old[1], old[2]
                        s.venue_id = old[3]
                        continue
                    proposed = _session_to_dict(s)
                    if apply:
                        try:
                            s.save()
                            moved = True
                        except Exception:
                            s.day, s.start_time, s.end_time = old[0], old[1], old[2]
                            s.venue_id = old[3]
                            continue
                    else:
                        moved = True
                    break
                if moved:
                    break
            if moved:
                break
        if moved:
            resolved += 1
            final = _session_to_dict(s) if apply else proposed
            if not apply:
                # revert in-memory
                s.day, s.start_time, s.end_time = original['day'], original['start'], original['end']
                s.venue_id = original['venue']
            rec = ConflictResolutionRecord.objects.create(
                run=run, conflict_type='teaching', conflict_message=f"Teaching conflict for session {original['id']}",
                affected_model='TeachingSession', affected_id=str(original['id']),
                original=original, proposed=proposed or {}, final=final or {},
                status='applied' if apply else 'proposed', strategy='move_slot_or_room')
            records.append(rec)
        else:
            # revert
            s.day, s.start_time, s.end_time = original['day'], original['start'], original['end']
            s.venue_id = original['venue']
            ConflictResolutionRecord.objects.create(
                run=run, conflict_type='teaching', conflict_message=f"Unresolved teaching conflict for session {original['id']}",
                affected_model='TeachingSession', affected_id=str(original['id']),
                original=original, proposed={}, final={}, status='unresolved', strategy='none')
        fixed.append(s)
    return {'resolved': resolved, 'records': records}


def resolve_exam_conflicts(academic_level=None, school=None, department=None, programme=None,
                           academic_year=None, semester=None, examination_period=None, user=None,
                           apply=True, run=None):
    from examinations.models import ExaminationSession
    qs = ExaminationSession.objects.all()
    if examination_period:
        qs = qs.filter(examination_period=examination_period)
    if academic_year:
        qs = qs.filter(academic_year=academic_year)
    if semester:
        qs = qs.filter(semester=semester)
    if school:
        qs = qs.filter(school=school)
    if department:
        qs = qs.filter(department=department)
    if programme:
        qs = qs.filter(programme=programme)
    if academic_level:
        qs = qs.filter(programme__level=academic_level)
    sessions = list(qs.order_by('id'))
    dates = sorted(set(s.examination_date for s in sessions))
    slots = _exam_slots()
    venues = list(Venue.objects.filter(active=True, examination_enabled=True))
    fixed = []
    resolved = 0
    records = []
    for s in sessions:
        if s.status in ('approved', 'published'):
            fixed.append(s)
            continue
        def conflict_with_fixed(sess):
            for f in fixed:
                if f.examination_date != sess.examination_date:
                    continue
                if not _overlap(f.start_time, f.end_time, sess.start_time, sess.end_time):
                    continue
                if f.venue_id and sess.venue_id and f.venue_id == sess.venue_id:
                    return True
                if f.class_group_id and sess.class_group_id and f.class_group_id == sess.class_group_id:
                    return True
                shared = set(f.invigilators.values_list('id', flat=True)) & set(sess.invigilators.values_list('id', flat=True))
                if shared:
                    return True
                if f.unit_lecturer_id and sess.unit_lecturer_id and f.unit_lecturer_id == sess.unit_lecturer_id:
                    return True
            return False

        if not conflict_with_fixed(s):
            fixed.append(s)
            continue
        original = {'id': s.id, 'date': str(s.examination_date), 'start': str(s.start_time), 'end': str(s.end_time), 'venue': s.venue_id}
        moved = False
        proposed = None
        for dt in dates:
            for st, en in slots:
                for v in venues:
                    if v.capacity and s.expected_candidates and v.capacity < s.expected_candidates and v.venue_type != 'online':
                        continue
                    old = (s.examination_date, s.start_time, s.end_time, s.venue_id, s.day_of_week)
                    s.examination_date = dt
                    s.day_of_week = dt.strftime('%A')
                    s.start_time = st
                    s.end_time = en
                    s.venue = v
                    if conflict_with_fixed(s):
                        s.examination_date, s.start_time, s.end_time = old[0], old[1], old[2]
                        s.venue_id = old[3]
                        s.day_of_week = old[4]
                        continue
                    proposed = {'id': s.id, 'date': str(s.examination_date), 'start': str(s.start_time), 'end': str(s.end_time), 'venue': s.venue_id}
                    if apply:
                        try:
                            s.save()
                            moved = True
                        except Exception:
                            s.examination_date, s.start_time, s.end_time = old[0], old[1], old[2]
                            s.venue_id = old[3]
                            s.day_of_week = old[4]
                            continue
                    else:
                        moved = True
                    break
                if moved:
                    break
            if moved:
                break
        if moved:
            resolved += 1
            final = {'id': s.id, 'date': str(s.examination_date), 'start': str(s.start_time), 'end': str(s.end_time), 'venue': s.venue_id}
            if not apply:
                s.examination_date = original['date']
                s.start_time = original['start']
                s.end_time = original['end']
                s.venue_id = original['venue']
                s.day_of_week = date.fromisoformat(original['date']).strftime('%A') if False else s.day_of_week
            ConflictResolutionRecord.objects.create(
                run=run, conflict_type='examination', conflict_message=f"Exam conflict for session {original['id']}",
                affected_model='ExaminationSession', affected_id=str(original['id']),
                original=original, proposed=proposed or {}, final=final or {},
                status='applied' if apply else 'proposed', strategy='move_slot_or_room')
        else:
            s.examination_date = date.fromisoformat(original['date'])
            s.start_time = time.fromisoformat(original['start'])
            s.end_time = time.fromisoformat(original['end'])
            s.venue_id = original['venue']
            ConflictResolutionRecord.objects.create(
                run=run, conflict_type='examination', conflict_message=f"Unresolved exam conflict for session {original['id']}",
                affected_model='ExaminationSession', affected_id=str(original['id']),
                original=original, proposed={}, final={}, status='unresolved', strategy='none')
        fixed.append(s)
    return {'resolved': resolved, 'records': records}


@transaction.atomic
def resolve_all_conflicts(academic_level=None, school=None, department=None, programme=None,
                          academic_year=None, semester=None, examination_period=None,
                          user=None, apply=True, preview=False):
    # Default apply=False for safety? Prompt one-click should apply. We'll apply for drafts.
    # Determine apply based on published existence
    from teaching.models import TeachingSession
    from examinations.models import ExaminationSession
    ts_qs = TeachingSession.objects.filter(status='published')
    es_qs = ExaminationSession.objects.filter(status='published')
    if academic_year:
        ts_qs = ts_qs.filter(academic_year=academic_year)
        es_qs = es_qs.filter(academic_year=academic_year)
    if semester:
        ts_qs = ts_qs.filter(semester=semester)
        es_qs = es_qs.filter(semester=semester)
    if school:
        ts_qs = ts_qs.filter(school=school)
        es_qs = es_qs.filter(school=school)
    if department:
        ts_qs = ts_qs.filter(department=department)
        es_qs = es_qs.filter(department=department)
    if programme:
        ts_qs = ts_qs.filter(programme=programme)
        es_qs = es_qs.filter(programme=programme)
    if academic_level:
        ts_qs = ts_qs.filter(programme__level=academic_level)
        es_qs = es_qs.filter(programme__level=academic_level)
    if examination_period:
        es_qs = es_qs.filter(examination_period=examination_period)
    has_published = ts_qs.exists() or es_qs.exists()
    do_apply = (not has_published) and bool(apply) and not bool(preview)
    # But if published, never auto-apply; require confirmation (preview)
    if has_published:
        do_apply = False

    run = ConflictResolutionRun.objects.create(started_by=user, status='processing', scope={
        'academic_level': academic_level, 'school': getattr(school, 'id', school),
        'department': getattr(department, 'id', department), 'programme': getattr(programme, 'id', programme),
        'academic_year': getattr(academic_year, 'id', academic_year), 'semester': getattr(semester, 'id', semester),
        'examination_period': getattr(examination_period, 'id', examination_period),
    }, applied=do_apply)

    run.status = 'validating'
    run.save(update_fields=['status'])
    before_t = detect_teaching_conflicts(academic_level=academic_level, school=school, department=department, programme=programme, academic_year=academic_year, semester=semester)
    before_e = detect_exam_conflicts(academic_level=academic_level, school=school, department=department, programme=programme, academic_year=academic_year, semester=semester, examination_period=examination_period)
    total_before = before_t + before_e
    run.total_conflicts = total_before
    run.status = 'resolving'
    run.save(update_fields=['status', 'total_conflicts'])

    tr = resolve_teaching_conflicts(academic_level=academic_level, school=school, department=department, programme=programme, academic_year=academic_year, semester=semester, user=user, apply=do_apply, run=run)
    er = resolve_exam_conflicts(academic_level=academic_level, school=school, department=department, programme=programme, academic_year=academic_year, semester=semester, examination_period=examination_period, user=user, apply=do_apply, run=run)

    after_t = detect_teaching_conflicts(academic_level=academic_level, school=school, department=department, programme=programme, academic_year=academic_year, semester=semester)
    after_e = detect_exam_conflicts(academic_level=academic_level, school=school, department=department, programme=programme, academic_year=academic_year, semester=semester, examination_period=examination_period)

    run.resolved = (before_t - after_t) + (before_e - after_e)
    run.remaining = after_t + after_e
    run.status = 'completed_with_warnings' if run.remaining > 0 else 'completed'
    run.completed_at = timezone.now()
    run.details = {
        'teaching_before': before_t, 'exam_before': before_e,
        'teaching_after': after_t, 'exam_after': after_e,
        'teaching_resolved': tr['resolved'], 'exam_resolved': er['resolved'],
        'applied': do_apply,
    }
    run.save()

    # notifications
    try:
        if user is not None:
            Notification.objects.create(
                user=user,
                title='Timetable Conflicts Resolved',
                message=f"Detected {total_before} conflicts and resolved {run.resolved}. {run.remaining} require attention.",
                link=f'/conflicts/resolution/{run.id}/',
                notification_type='conflict_resolution',
                metadata={'run_id': run.id}
            )
            if run.remaining > 0:
                Notification.objects.create(
                    user=user, title='Conflicts Remaining',
                    message=f"{run.remaining} conflicts remain unresolved.",
                    link=f'/conflicts/resolution/{run.id}/', notification_type='conflicts_remaining',
                    metadata={'run_id': run.id})
    except Exception:
        pass

    result = {
        'teaching_resolved': tr['resolved'],
        'exam_resolved': er['resolved'],
        'resolved': run.resolved,
        'resolved_conflicts': run.resolved,
        'conflicts_resolved': run.resolved,
        'remaining': run.remaining,
        'remaining_conflicts': run.remaining,
        'conflicts_detected': total_before,
        'conflicts_remaining': run.remaining,
        'applied': do_apply,
        'run_id': run.id,
        'teaching_before': before_t, 'exam_before': before_e,
        'teaching_after': after_t, 'exam_after': after_e,
    }
    return result


# Backwards aliases
def detect_conflicts(*a, **k):
    return detect_all_conflicts(**k)


def validate_teaching_session(session):
    from scheduling.validators import validate_teaching_session as v
    return v(session)


def validate_exam_session(session):
    from scheduling.validators import validate_exam_session as v
    return v(session)


def suggest_alternative_teaching(session):
    from scheduling.validators import suggest_alternative_teaching as s
    return s(session)


def suggest_alternative_exam(session):
    from scheduling.validators import suggest_alternative_exam as s
    return s(session)


def resolve_conflicts(*a, **k):
    return resolve_all_conflicts(*a, **k)

def detect_all(*a, **k):
    return detect_all_conflicts(**k)

def run_conflict_detection(*a, **k):
    return detect_all_conflicts(**k)

def resolve_all(*a, **k):
    return resolve_all_conflicts(*a, **k)

def resolve(*a, **k):
    return resolve_all_conflicts(*a, **k)


def run_detection(*a, **k):
    return detect_all_conflicts(**k)