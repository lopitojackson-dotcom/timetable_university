from conflicts.services import detect_teaching_conflicts, detect_exam_conflicts
from teaching.models import TeachingSession
from examinations.models import ExaminationSession
from resources.models import Venue
from datetime import time


def validate_teaching_session(session):
    errors = []
    if session.day in ('Saturday', 'Sunday'):
        errors.append('Invalid teaching day.')
    if not (session.start_time and session.end_time and session.start_time < session.end_time):
        errors.append('Invalid session duration.')
    if session.lecturer_id:
        qs = TeachingSession.objects.filter(day=session.day, lecturer=session.lecturer).exclude(pk=session.pk)
        for o in qs:
            if not (o.end_time <= session.start_time or session.end_time <= o.start_time):
                errors.append(f"Lecturer {session.lecturer} already allocated on {session.day} {o.start_time}-{o.end_time}.")
    if session.venue_id:
        qs = TeachingSession.objects.filter(day=session.day, venue=session.venue).exclude(pk=session.pk)
        for o in qs:
            if not (o.end_time <= session.start_time or session.end_time <= o.start_time):
                errors.append(f"Room {session.venue} already booked on {session.day} {o.start_time}-{o.end_time}.")
    if session.class_group_id:
        qs = TeachingSession.objects.filter(day=session.day, class_group=session.class_group).exclude(pk=session.pk)
        for o in qs:
            if not (o.end_time <= session.start_time or session.end_time <= o.start_time):
                errors.append(f"Class group already has a session on {session.day} {o.start_time}-{o.end_time}.")
    if session.venue and session.student_population and session.venue.capacity and session.student_population > session.venue.capacity:
        errors.append(f"Room capacity exceeded: {session.student_population} > {session.venue.capacity}.")
    return errors


def validate_exam_session(session):
    errors = []
    if session.examination_date and session.examination_date.weekday() >= 5:
        errors.append('Examination scheduled on weekend.')
    if session.examination_period_id:
        sp = session.examination_period.start_date
        ep = session.examination_period.end_date
        if isinstance(sp, str):
            from datetime import date
            sp = date.fromisoformat(sp)
            ep = date.fromisoformat(ep)
        if session.examination_date < sp or session.examination_date > ep:
            errors.append('Examination outside approved period.')
    if not (session.start_time and session.end_time and session.start_time < session.end_time):
        errors.append('Invalid examination duration.')
    total_cap = 0
    for v, c in session.venue_allocations() if hasattr(session, 'venue_allocations') else []:
        if v:
            total_cap += v.capacity or 0
    if total_cap == 0 and session.venue:
        total_cap = session.venue.capacity or 0
    if session.venue and session.expected_candidates and total_cap and session.expected_candidates > total_cap:
        errors.append(f"Room capacity exceeded: {session.expected_candidates} > {total_cap}.")
    pass
    # overlaps
    qs = ExaminationSession.objects.filter(examination_date=session.examination_date).exclude(pk=session.pk)
    for o in qs:
        if not (o.end_time <= session.start_time or session.end_time <= o.start_time):
            if o.venue_id == session.venue_id:
                errors.append(f"Venue {session.venue} double-booked.")
            if o.class_group_id == session.class_group_id:
                errors.append('Class group clash.')
            shared = set(o.invigilators.values_list('id', flat=True)) & set(session.invigilators.values_list('id', flat=True))
            if shared:
                errors.append('Invigilator clash.')
            if o.unit_lecturer_id and o.unit_lecturer_id == session.unit_lecturer_id:
                errors.append('Lecturer clash.')
            # shared multi-venue rooms
            o_venues = set(v.id for v, _ in o.venue_allocations() if v)
            s_venues = set(v.id for v, _ in session.venue_allocations() if v)
            if o_venues & s_venues:
                errors.append('Shared examination room.')
    return errors


def suggest_alternative_teaching(session):
    from teaching.models import TeachingTimeSlot
    slots = list(TeachingTimeSlot.objects.filter(active=True))
    if not slots:
        slots = None
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    venues = Venue.objects.filter(active=True, teaching_enabled=True)
    for day in days:
        for v in venues:
            if v.capacity and session.student_population and v.capacity < session.student_population and v.venue_type != 'online':
                continue
            # check conflicts
            qs = TeachingSession.objects.filter(day=day, venue=v).exclude(pk=session.pk)
            conflict = False
            for o in qs:
                # assume default slot? We need time; use session's current times
                if not (o.end_time <= session.start_time or session.end_time <= o.start_time):
                    conflict = True
                    break
            if not conflict:
                return {'day': day, 'venue': v.code, 'start_time': str(session.start_time), 'end_time': str(session.end_time)}
    return None


def suggest_alternative_exam(session):
    from examinations.models import ExaminationTimeSlot, ExaminationSession
    from academics.models import AcademicYear
    slots = list(ExaminationTimeSlot.objects.filter(active=True))
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    venues = Venue.objects.filter(active=True, examination_enabled=True)
    # candidate dates within period
    dates = []
    if session.examination_period_id:
        d = session.examination_period.start_date
        end = session.examination_period.end_date
        from datetime import timedelta
        while d <= end:
            if d.weekday() < 5:
                dates.append(d)
            d = d + timedelta(days=1)
    if not dates:
        dates = [session.examination_date]
    for dt in dates:
        for v in venues:
            if v.capacity and session.expected_candidates and v.capacity < session.expected_candidates and v.venue_type != 'online':
                continue
            qs = ExaminationSession.objects.filter(examination_date=dt, venue=v).exclude(pk=session.pk)
            conflict = False
            for o in qs:
                if not (o.end_time <= session.start_time or session.end_time <= o.start_time):
                    conflict = True
                    break
            if not conflict:
                return {'date': str(dt), 'venue': v.code, 'start_time': str(session.start_time), 'end_time': str(session.end_time)}
    return None


# aliases
validate_session = validate_teaching_session
suggest_alternative = suggest_alternative_teaching
find_alternative_slot = suggest_alternative_teaching
find_alternative_room = suggest_alternative_teaching
find_alternative = suggest_alternative_teaching
suggest_alternative_session = suggest_alternative_teaching