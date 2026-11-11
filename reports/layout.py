from datetime import time

DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']

def teaching_slots():
    from teaching.models import TeachingTimeSlot
    slots = list(TeachingTimeSlot.objects.filter(active=True).order_by('order', 'start_time'))
    if slots:
        return [(s.start_time, s.end_time) for s in slots]
    return [(time(7, 0), time(10, 0)), (time(10, 0), time(13, 0)),
            (time(13, 0), time(16, 0)), (time(16, 0), time(19, 0))]

def exam_slots():
    from examinations.models import ExaminationTimeSlot
    slots = list(ExaminationTimeSlot.objects.filter(active=True).order_by('order', 'start_time'))
    if slots:
        return [(s.start_time, s.end_time) for s in slots]
    return [(time(8, 0), time(11, 0))]

def classgroup_column_label(cg, multiple=False):
    code = cg.programme.code
    if cg.study_mode and cg.study_mode != 'regular':
        code = f"{code} {cg.study_mode.upper()}"
    label = f"Y{cg.study_year}S{cg.study_semester}"
    if multiple:
        gn = (cg.group_name or '').strip()
        if gn.lower().startswith('group '):
            gn = 'G' + gn.split()[-1]
        if gn:
            label = f"{label} {gn}"
    pop = cg.expected_population
    return f"{code} - {label} ({pop})"

def period_string_for_teaching(academic_year=None, semester=None):
    if semester is not None:
        start = getattr(semester, 'teaching_start_date', None) or semester.start_date
        end = getattr(semester, 'teaching_end_date', None) or semester.end_date
    elif academic_year is not None:
        start = academic_year.start_date
        end = academic_year.end_date
    else:
        return ''
    return _format_period(start, end)

def period_string_for_exam(academic_year=None, semester=None, period=None):
    if period is not None:
        start = period.start_date
        end = period.end_date
    elif semester is not None:
        start = getattr(semester, 'examination_start_date', None) or semester.start_date
        end = getattr(semester, 'examination_end_date', None) or semester.end_date
    elif academic_year is not None:
        start = academic_year.start_date
        end = academic_year.end_date
    else:
        return ''
    return _format_period(start, end)

def _format_period(start, end):
    if not start or not end:
        return ''
    if start.year == end.year:
        return f"{start.strftime('%B')} - {end.strftime('%B %Y')}"
    return f"{start.strftime('%B %Y')} - {end.strftime('%B %Y')}"

def build_teaching_section(sessions, columns, slot_list):
    """Return (rows, merges) for a section. rows is list of lists, first col DAY, second TIME, third DETAILS, then programme cols."""
    rows = []
    merges = []
    day_start_idx = {}
    for day in DAYS:
        day_start_idx[day] = len(rows)
        for (st, en) in slot_list:
            time_label = f"{st.strftime('%I:%M %p')} - {en.strftime('%I:%M %p')}"
            # normalize leading zero in hour? keep standard
            slot_first = len(rows)
            for info in ['Unit', 'Lecturer', 'Venue']:
                rows.append(['', '', info] + ['' for _ in columns])
            merges.append((slot_first, 1, slot_first + 2, 1))
            rows[slot_first][1] = time_label
        day_end = len(rows) - 1
        ds = day_start_idx[day]
        if day_end >= ds:
            merges.append((ds, 0, day_end, 0))
        if ds < len(rows):
            rows[ds][0] = day.upper()

    # offsets
    offsets = {}
    r = 0
    for day in DAYS:
        offsets[day] = r
        r += 3 * len(slot_list)

    for ci, c in enumerate(columns):
        for s in sessions:
            if getattr(s.class_group, 'id', None) != c['id']:
                continue
            if s.day not in DAYS:
                continue
            si = None
            for i, (st, en) in enumerate(slot_list):
                if s.start_time == st and s.end_time == en:
                    si = i
                    break
            if si is None:
                continue
            base = offsets[s.day] + si * 3
            unit_cell = s.unit.code
            if s.unit.name:
                unit_cell = f"{s.unit.code}\n{s.unit.name}"
            rows[base][3 + ci] = unit_cell
            rows[base + 1][3 + ci] = s.lecturer.full_name if s.lecturer else ''
            venue = s.venue
            if venue is None:
                venue_str = 'Online' if s.is_online else ''
            else:
                venue_str = venue.code
                if s.is_online:
                    venue_str = 'Online'
            rows[base + 2][3 + ci] = venue_str
    return rows, merges

def build_exam_section(sessions, columns, slot_list):
    rows = []
    merges = []
    # distinct dates sorted
    dates = sorted(set(s.examination_date for s in sessions if s.examination_date.weekday() < 5))
    date_start_idx = {}
    for d in dates:
        date_start_idx[d] = len(rows)
        for (st, en) in slot_list:
            time_label = f"{st.strftime('%I:%M %p')} - {en.strftime('%I:%M %p')}"
            slot_first = len(rows)
            for info in ['Unit/Exam', 'Invigilator', 'Venue/Candidates']:
                rows.append(['', '', info] + ['' for _ in columns])
            merges.append((slot_first, 1, slot_first + 2, 1))
            rows[slot_first][1] = time_label
        day_end = len(rows) - 1
        ds = date_start_idx[d]
        if day_end >= ds:
            merges.append((ds, 0, day_end, 0))
        if ds < len(rows):
            rows[ds][0] = d.strftime('%A\n%d/%m/%Y')

    offsets = {}
    r = 0
    for d in dates:
        offsets[d] = r
        r += 3 * len(slot_list)

    for ci, c in enumerate(columns):
        for s in sessions:
            if getattr(s.class_group, 'id', None) != c['id']:
                continue
            if s.examination_date not in offsets:
                continue
            si = None
            for i, (st, en) in enumerate(slot_list):
                if s.start_time == st and s.end_time == en:
                    si = i
                    break
            if si is None:
                continue
            base = offsets[s.examination_date] + si * 3
            unit_cell = s.unit.code
            if s.unit.name:
                unit_cell = f"{s.unit.code}\n{s.unit.name}"
            rows[base][3 + ci] = unit_cell
            invs = ', '.join(i.full_name for i in s.invigilators.all())
            if not invs and s.unit_lecturer:
                invs = str(s.unit_lecturer)
            rows[base + 1][3 + ci] = invs
            allocs = s.venue_allocations()
            venue_lines = []
            for v, cnt in allocs:
                code = v.code if v else ''
                venue_lines.append(f"{code} ({cnt})")
            rows[base + 2][3 + ci] = "\n".join(venue_lines)
    return rows, merges

def chunks(columns, size=8):
    if len(columns) <= size:
        return [columns]
    return [columns[i:i + size] for i in range(0, len(columns), size)]
