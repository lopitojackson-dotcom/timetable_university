from reportlab.lib.pagesizes import landscape, A4, A3
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
import os

from reports.layout import (DAYS, teaching_slots, exam_slots, build_teaching_section,
                           build_exam_section, chunks, period_string_for_teaching,
                           period_string_for_exam, classgroup_column_label)

GREEN = colors.HexColor('#2e7d32')


def build_lecturer_pdf(response, lecturer, sessions, title='Individual Lecturer Weekly Teaching Timetable',
                       period='', version='DRAFT 1', pagesize=None):
    from reports.layout import teaching_slots
    from reports.views import _lecturer_matrix, _lecturer_workload
    days, slots, grid = _lecturer_matrix(sessions)
    # build rows
    rows = []
    for i, (st, en) in enumerate(slots):
        time_label = f"{st.strftime('%I:%M %p')} - {en.strftime('%I:%M %p')}"
        row = [time_label]
        for d in days:
            cell_sessions = grid[(d, i)]
            if not cell_sessions:
                row.append('Free')
            else:
                parts = []
                for s in cell_sessions:
                    lines = [s.unit.code]
                    if s.unit.name:
                        lines.append(s.unit.name)
                    if s.programme:
                        lines.append(f"{s.programme.code} - Y{s.study_year}S{s.study_semester}")
                    if s.class_group:
                        lines.append(str(s.class_group.group_name))
                    venue = s.venue.code if s.venue else ('Online' if s.is_online else '')
                    if venue:
                        lines.append(venue)
                    parts.append('\n'.join(lines))
                row.append('\n---\n'.join(parts))
        rows.append(row)
    header = ['TIME'] + [d.upper() for d in days]
    t = Table([header] + rows, repeatRows=1)
    # workload
    wl = _lecturer_workload(sessions)
    wl_rows = [
        ['Workload indicator', 'Total'],
        ['Weekly teaching sessions', wl['total_sessions']],
        ['Weekly teaching hours', wl['total_hours']],
        ['Academic units', wl['units']],
        ['Programmes', wl['programmes']],
        ['Departments', wl['departments']],
        ['Class groups', wl['groups']],
        ['Free sessions', wl['free_sessions']],
        ['Scheduling conflicts', wl['conflicts']],
    ]
    wlt = Table(wl_rows, colWidths=[60 * mm, 30 * mm])
    if pagesize is None:
        for base in (A4, A3, A2, A1, A0):
            cand = landscape(base)
            avail_w = cand[0] - 16 * mm
            avail_h = cand[1] - (60 + 12) * mm
            try:
                w1, h1 = t.wrap(avail_w, 10 ** 6)
                w2, h2 = wlt.wrap(avail_w, 10 ** 6)
                h = h1 + h2 + 20 * mm
            except Exception:
                h = 10 ** 6
            if h <= avail_h:
                pagesize = cand
                break
        if pagesize is None:
            pagesize = landscape(A0)
    doc = SimpleDocTemplate(response, pagesize=pagesize, leftMargin=8 * mm,
                            rightMargin=8 * mm, topMargin=60 * mm, bottomMargin=12 * mm)
    story = []
    drawer = lambda c, d: _draw_lecturer_page(c, d, title, period, version, pagesize, lecturer)
    # table
    style_cmds = [
        ('BACKGROUND', (0, 0), (-1, 0), GREEN),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 7),
        ('GRID', (0, 0), (-1, -1), 0.4, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 1), (0, -1), LIGHT),
    ]
    t.setStyle(TableStyle(style_cmds))
    story.append(t)
    story.append(Spacer(1, 4 * mm))
    wlt.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), GREEN),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.4, colors.black),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
    ]))
    story.append(wlt)
    doc.build(story, onFirstPage=drawer, onLaterPages=drawer)


def _draw_lecturer_page(canvas, doc, title, period, version, pagesize, lecturer):
    width, height = pagesize
    canvas.saveState()
    canvas.setFont('Helvetica-Bold', 10)
    canvas.drawRightString(width - 10 * mm, height - 10 * mm, version)
    logo = _logo_path()
    if logo and os.path.exists(logo):
        canvas.drawImage(logo, (width - 22 * mm) / 2, height - 30 * mm,
                        width=22 * mm, height=22 * mm, preserveAspectRatio=True, mask='auto')
    canvas.setFont('Helvetica-Bold', 13)
    canvas.drawCentredString(width / 2, height - 34 * mm, "Murang'a University of Technology")
    canvas.setFont('Helvetica-Bold', 10)
    canvas.drawCentredString(width / 2, height - 40 * mm, title)
    canvas.setFont('Helvetica', 9)
    canvas.drawCentredString(width / 2, height - 45 * mm, f"Lecturer: {lecturer.full_name}  |  Staff No: {lecturer.staff_number}")
    canvas.drawCentredString(width / 2, height - 50 * mm, f"Department: {lecturer.department}  |  School: {lecturer.school}")
    if period:
        canvas.drawCentredString(width / 2, height - 55 * mm, period)
    canvas.setFont('Helvetica', 8)
    canvas.drawString(10 * mm, 6 * mm, _institution_name() + ' - Lecturer Timetable')
    canvas.drawRightString(width - 10 * mm, 6 * mm, f'Page {doc.page}')
    canvas.restoreState()
LIGHT = colors.HexColor('#f1f5f9')

from reportlab.lib.pagesizes import A4, A3, A2, A1, A0


def _choose_pagesize(estimated_rows, preferred=None):
    if preferred is not None:
        return preferred
    # estimated_rows includes header row
    needed = estimated_rows * 14 + 40
    margins = 55 * 1 + 12  # top+bottom approximated in points? use 67
    margins = 67
    candidates = [A4, A3, A2, A1, A0]
    for base in candidates:
        if (base[0] - margins) >= needed:
            return landscape(base)
    return landscape(A0)


def _institution():
    from institutions.models import Institution
    return Institution.objects.first()


def _logo_path():
    inst = _institution()
    if inst and inst.logo:
        try:
            p = inst.logo.path
            if os.path.exists(p):
                return p
        except Exception:
            pass
    from django.conf import settings
    base = getattr(settings, 'BASE_DIR', None)
    candidates = []
    if base:
        candidates += [os.path.join(base, 'static', 'images', 'logo.png'),
                      os.path.join(base, 'static', 'logo.png'),
                      os.path.join(base, 'media', 'institution', 'logo.png')]
    candidates += [os.path.join('static', 'images', 'logo.png'),
                  os.path.join('static', 'logo.png')]
    for c in candidates:
        if os.path.exists(c):
            return c
    return None


def _institution_name():
    inst = _institution()
    if inst and inst.name:
        return inst.name
    return "Murang'a University of Technology"


def _footer(canvas, doc):
    canvas.saveState()
    canvas.setFont('Helvetica', 8)
    canvas.drawString(10 * mm, 6 * mm, _institution_name() + ' - Timetable')
    canvas.drawRightString(doc.pagesize[0] - 10 * mm, 6 * mm, f'Page {doc.page}')
    canvas.restoreState()


def _header_story(story, title, period, version, pagesize):
    styles = getSampleStyleSheet()
    from reportlab.lib.styles import ParagraphStyle
    vstyle = ParagraphStyle('vright', parent=styles['Normal'], alignment=2, fontName='Helvetica-Bold', fontSize=10)
    story.append(Paragraph(version, vstyle))
    logo = _logo_path()
    if logo and os.path.exists(logo):
        story.append(Image(logo, width=22 * mm, height=22 * mm, hAlign='CENTER'))
    p = Paragraph('Murang\'a University of Technology', styles['Title'])
    story.append(p)
    story.append(Paragraph(title, styles['Heading2']))
    if period:
        story.append(Paragraph(period, styles['Normal']))
    story.append(Spacer(1, 4 * mm))


def _draw_page(canvas, doc, title, period, version, pagesize):
    width, height = pagesize
    canvas.saveState()
    # version top-right
    canvas.setFont('Helvetica-Bold', 10)
    canvas.drawRightString(width - 10 * mm, height - 10 * mm, version)
    # logo
    logo = _logo_path()
    if logo and os.path.exists(logo):
        canvas.drawImage(logo, (width - 22 * mm) / 2, height - 34 * mm,
                        width=22 * mm, height=22 * mm, preserveAspectRatio=True, mask='auto')
    canvas.setFont('Helvetica-Bold', 14)
    canvas.drawCentredString(width / 2, height - 38 * mm, _institution_name())
    canvas.setFont('Helvetica-Bold', 11)
    canvas.drawCentredString(width / 2, height - 44 * mm, title)
    if period:
        canvas.setFont('Helvetica', 10)
        canvas.drawCentredString(width / 2, height - 50 * mm, period)
    # footer
    canvas.setFont('Helvetica', 8)
    canvas.drawString(10 * mm, 6 * mm, _institution_name() + ' - Timetable')
    canvas.drawRightString(width - 10 * mm, 6 * mm, f'Page {doc.page}')
    canvas.restoreState()


PAPER_SIZES = {
    'A4': (595.27, 841.89),
    'A3': (841.89, 1190.55),
    'A2': (1190.55, 1683.78),
    'A1': (1683.78, 2383.94),
    'A0': (2383.94, 3370.39),
}


def _paper_pagesize(name):
    base = PAPER_SIZES.get((name or '').upper())
    if not base:
        return None
    return landscape(base)



LIGHT = colors.HexColor('#f1f5f9')


def _text_width(text, font='Helvetica', size=8):
    try:
        return pdfmetrics.stringWidth(str(text), font, size)
    except Exception:
        return len(str(text)) * size * 0.5


def _col_widths_for_teaching(columns, font_size=8.5):
    day_w = max(18 * mm, _text_width('WEDNESDAY', 'Helvetica-Bold', font_size) + 6 * mm)
    time_w = max(30 * mm, _text_width('07:00 AM - 10:00 AM', 'Helvetica', font_size) + 6 * mm)
    details_w = max(18 * mm, _text_width('Lecturer', 'Helvetica-Bold', font_size) + 6 * mm)
    prog_ws = []
    for c in columns:
        label = c.get('label', '')
        w = _text_width(label, 'Helvetica-Bold', font_size) + 8 * mm
        # content sample: unit code + name
        w = max(w, 24 * mm)
        w = min(max(w, 24 * mm), 40 * mm)
        prog_ws.append(w)
    return [day_w, time_w, details_w] + prog_ws


def _col_widths_for_exam(columns, font_size=8.5):
    return _col_widths_for_teaching(columns, font_size)


def _choose_pagesize(sections_tables, avail_height_factor=1.0):
    # sections_tables: list of (rows, merges, col_widths)
    candidates = [A4, A3, A2, A1, A0]
    best = None
    for base in candidates:
        cand = landscape(base)
        avail_w = cand[0] - 16 * mm
        avail_h = cand[1] - (42 + 10 + 8) * mm
        ok = True
        for (rows, merges, cws) in sections_tables:
            try:
                t = Table(rows, colWidths=cws)
                w, h = t.wrap(avail_w, 10 ** 6)
            except Exception:
                w, h = 10 ** 6, 10 ** 6
            if not (w <= avail_w + 2 and h <= avail_h):
                ok = False
                break
        if ok:
            best = cand
            break
    if best is None:
        best = landscape(A0)
    return best


def _distribute_row_heights(table, avail_h, natural_h, num_rows):
    # returns rowHeights list or None
    if num_rows <= 0:
        return None
    usable = avail_h - 12 * mm
    extra = usable - natural_h
    if natural_h > usable and num_rows > 0:
        # shrink rows to fit instead of overflowing
        return [usable / num_rows for _ in range(num_rows)]
    if extra <= 2 * mm:
        if num_rows > 0 and natural_h > 0:
            return [natural_h / num_rows for _ in range(num_rows)]
        return None
    per = extra / num_rows
    base = natural_h / num_rows
    # cap growth so rows do not become oversized
    if per > 3 * mm:
        per = 3 * mm
    # never exceed available height
    if base + per > usable / num_rows + 3 * mm:
        per = max(0, usable / num_rows - base)
    return [base + per for _ in range(num_rows)]


def build_teaching_pdf(response, sessions, columns, title='Undergraduate Teaching Timetable',
                       period='', version='DRAFT 1', pagesize=None, columns_per_page=20,
                       paper_size=None):
    from reports.layout import teaching_slots, build_teaching_section, chunks
    slot_list = teaching_slots()
    sections_cols = chunks(columns, size=columns_per_page) if columns else [[]]
    if not sections_cols:
        sections_cols = [[]]
    # build rows/merges per section
    section_data = []
    for sec_cols in sections_cols:
        rows, merges = build_teaching_section(sessions, sec_cols, slot_list)
        cws = _col_widths_for_teaching(sec_cols)
        section_data.append((rows, merges, cws, sec_cols))

    if pagesize is None and paper_size:
        pagesize = _paper_pagesize(paper_size)
    if pagesize is None:
        pagesize = _choose_pagesize([(r, m, c) for (r, m, c, _) in section_data])

    avail_w = pagesize[0] - 16 * mm
    avail_h = pagesize[1] - (42 + 10) * mm
    doc = SimpleDocTemplate(response, pagesize=pagesize, leftMargin=8 * mm,
                            rightMargin=8 * mm, topMargin=42 * mm, bottomMargin=10 * mm)
    story = []
    drawer = lambda c, d: _draw_page(c, d, title, period, version, pagesize)
    font_size = 8.5 if pagesize[0] < 900 else 9.5

    for si, (rows, merges, cws, sec_cols) in enumerate(section_data, start=1):
        if si > 1:
            story.append(PageBreak())
        if len(section_data) > 1:
            story.append(Paragraph(f'Section {si} of {len(section_data)}', getSampleStyleSheet()['Heading3']))
        header = ['DAY', 'TIME', 'DETAILS'] + [c['label'] for c in sec_cols]
        full_rows = [header] + rows
        t = Table(full_rows, colWidths=cws, repeatRows=1, splitByRow=0, splitInRow=0)
        # natural height
        try:
            w, h = t.wrap(avail_w, 10 ** 6)
        except Exception:
            h = avail_h
        # distribute
        rh = _distribute_row_heights(t, avail_h, h, len(full_rows))
        if rh is not None:
            t = Table(full_rows, colWidths=cws, rowHeights=rh, repeatRows=1, splitByRow=0, splitInRow=0)
        style_cmds = [
            ('BACKGROUND', (0, 0), (-1, 0), GREEN),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), font_size),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.4, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (2, -1), 'CENTER'),
            ('FONTNAME', (2, 1), (2, -1), 'Helvetica-Bold'),
            ('BACKGROUND', (2, 1), (2, -1), LIGHT),
        ]
        for (sr, sc, er, ec) in merges:
            style_cmds.append(('SPAN', (sc, sr + 1), (ec, er + 1)))
        t.setStyle(TableStyle(style_cmds))
        story.append(t)
    doc.build(story, onFirstPage=drawer, onLaterPages=drawer)


def build_exam_pdf(response, sessions, columns, title='Undergraduate Examination Timetable',
                   period='', version='DRAFT 1', pagesize=None, columns_per_page=20,
                   paper_size=None):
    from reports.layout import exam_slots, build_exam_section, chunks
    slot_list = exam_slots()
    sections_cols = chunks(columns, size=columns_per_page) if columns else [[]]
    if not sections_cols:
        sections_cols = [[]]
    section_data = []
    for sec_cols in sections_cols:
        rows, merges = build_exam_section(sessions, sec_cols, slot_list)
        cws = _col_widths_for_exam(sec_cols)
        section_data.append((rows, merges, cws, sec_cols))

    if pagesize is None and paper_size:
        pagesize = _paper_pagesize(paper_size)
    if pagesize is None:
        pagesize = _choose_pagesize([(r, m, c) for (r, m, c, _) in section_data])

    avail_w = pagesize[0] - 16 * mm
    avail_h = pagesize[1] - (42 + 10) * mm
    doc = SimpleDocTemplate(response, pagesize=pagesize, leftMargin=8 * mm,
                            rightMargin=8 * mm, topMargin=42 * mm, bottomMargin=10 * mm)
    story = []
    drawer = lambda c, d: _draw_page(c, d, title, period, version, pagesize)
    font_size = 8.5 if pagesize[0] < 900 else 9.5

    for si, (rows, merges, cws, sec_cols) in enumerate(section_data, start=1):
        if si > 1:
            story.append(PageBreak())
        if len(section_data) > 1:
            story.append(Paragraph(f'Section {si} of {len(section_data)}', getSampleStyleSheet()['Heading3']))
        header = ['DAY/DATE', 'TIME', 'DETAILS'] + [c['label'] for c in sec_cols]
        full_rows = [header] + rows
        t = Table(full_rows, colWidths=cws, repeatRows=1, splitByRow=0, splitInRow=0)
        try:
            w, h = t.wrap(avail_w, 10 ** 6)
        except Exception:
            h = avail_h
        rh = _distribute_row_heights(t, avail_h, h, len(full_rows))
        if rh is not None:
            t = Table(full_rows, colWidths=cws, rowHeights=rh, repeatRows=1)
        style_cmds = [
            ('BACKGROUND', (0, 0), (-1, 0), GREEN),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), font_size),
            ('GRID', (0, 0), (-1, -1), 0.4, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (2, -1), 'CENTER'),
            ('FONTNAME', (2, 1), (2, -1), 'Helvetica-Bold'),
            ('BACKGROUND', (2, 1), (2, -1), LIGHT),
        ]
        for (sr, sc, er, ec) in merges:
            style_cmds.append(('SPAN', (sc, sr + 1), (ec, er + 1)))
        t.setStyle(TableStyle(style_cmds))
        story.append(t)
    doc.build(story, onFirstPage=drawer, onLaterPages=drawer)


def build_lecturer_pdf(response, lecturer, sessions, title='Individual Lecturer Weekly Teaching Timetable',
                       period='', version='DRAFT 1', pagesize=None):
    from reports.views import _lecturer_matrix, _lecturer_workload
    from reports.layout import teaching_slots
    days, slots, grid = _lecturer_matrix(sessions)
    rows = []
    for i, (st, en) in enumerate(slots):
        time_label = f"{st.strftime('%I:%M %p')} - {en.strftime('%I:%M %p')}"
        row = [time_label]
        for d in days:
            cell_sessions = grid[(d, i)]
            if not cell_sessions:
                row.append('Free')
            else:
                parts = []
                for s in cell_sessions:
                    lines = [s.unit.code]
                    if s.unit.name:
                        lines.append(s.unit.name)
                    if s.programme:
                        lines.append(f"{s.programme.code} - Y{s.study_year}S{s.study_semester}")
                    if s.class_group:
                        lines.append(str(s.class_group.group_name))
                    venue = s.venue.code if s.venue else ('Online' if s.is_online else '')
                    if venue:
                        lines.append(venue)
                    parts.append('\n'.join(lines))
                row.append('\n---\n'.join(parts))
        rows.append(row)
    header = ['TIME'] + [d.upper() for d in days]
    # col widths
    time_w = max(32 * mm, _text_width('07:00 AM - 10:00 AM', 'Helvetica', 8.5) + 6 * mm)
    day_w = max(30 * mm, 28 * mm)
    cws = [time_w] + [day_w for _ in days]
    wl = _lecturer_workload(sessions)
    wl_rows = [
        ['Workload indicator', 'Total'],
        ['Weekly teaching sessions', wl['total_sessions']],
        ['Weekly teaching hours', wl['total_hours']],
        ['Academic units', wl['units']],
        ['Programmes', wl['programmes']],
        ['Departments', wl['departments']],
        ['Class groups', wl['groups']],
        ['Free sessions', wl['free_sessions']],
        ['Scheduling conflicts', wl['conflicts']],
    ]
    wlt = Table(wl_rows, colWidths=[60 * mm, 30 * mm])
    t = Table([header] + rows, colWidths=cws, repeatRows=1)
    if pagesize is None:
        for base in (A4, A3, A2):
            cand = landscape(base)
            avail_w = cand[0] - 16 * mm
            avail_h = cand[1] - (40 + 10) * mm
            try:
                w1, h1 = t.wrap(avail_w, 10 ** 6)
                w2, h2 = wlt.wrap(avail_w, 10 ** 6)
                h = h1 + h2 + 8 * mm
            except Exception:
                h = 10 ** 6
            if h <= avail_h and w1 <= avail_w + 2:
                pagesize = cand
                break
        if pagesize is None:
            pagesize = landscape(A2)
    doc = SimpleDocTemplate(response, pagesize=pagesize, leftMargin=8 * mm,
                            rightMargin=8 * mm, topMargin=40 * mm, bottomMargin=10 * mm)
    story = []
    drawer = lambda c, d: _draw_lecturer_page(c, d, title, period, version, pagesize, lecturer)
    style_cmds = [
        ('BACKGROUND', (0, 0), (-1, 0), GREEN),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8.5),
        ('GRID', (0, 0), (-1, -1), 0.4, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 1), (0, -1), LIGHT),
    ]
    t.setStyle(TableStyle(style_cmds))
    story.append(t)
    story.append(Spacer(1, 4 * mm))
    wlt.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), GREEN),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.4, colors.black),
        ('FONTSIZE', (0, 0), (-1, -1), 8.5),
    ]))
    story.append(wlt)
    doc.build(story, onFirstPage=drawer, onLaterPages=drawer)


def _draw_lecturer_page(canvas, doc, title, period, version, pagesize, lecturer):
    width, height = pagesize
    canvas.saveState()
    canvas.setFont('Helvetica-Bold', 10)
    canvas.drawRightString(width - 10 * mm, height - 10 * mm, version)
    logo = _logo_path()
    if logo and os.path.exists(logo):
        canvas.drawImage(logo, (width - 20 * mm) / 2, height - 30 * mm,
                        width=20 * mm, height=20 * mm, preserveAspectRatio=True, mask='auto')
    canvas.setFont('Helvetica-Bold', 13)
    canvas.drawCentredString(width / 2, height - 33 * mm, _institution_name())
    canvas.setFont('Helvetica-Bold', 10)
    canvas.drawCentredString(width / 2, height - 38 * mm, title)
    canvas.setFont('Helvetica', 9)
    canvas.drawCentredString(width / 2, height - 43 * mm, f"Lecturer: {lecturer.full_name}  |  Staff No: {lecturer.staff_number}")
    canvas.drawCentredString(width / 2, height - 48 * mm, f"Department: {lecturer.department}  |  School: {lecturer.school}")
    if period:
        canvas.drawCentredString(width / 2, height - 53 * mm, period)
    canvas.setFont('Helvetica', 8)
    canvas.drawString(10 * mm, 6 * mm, _institution_name() + ' - Lecturer Timetable')
    canvas.drawRightString(width - 10 * mm, 6 * mm, f'Page {doc.page}')
    canvas.restoreState()


def _draw_page(canvas, doc, title, period, version, pagesize):
    width, height = pagesize
    canvas.saveState()
    canvas.setFont('Helvetica-Bold', 10)
    canvas.drawRightString(width - 10 * mm, height - 10 * mm, version)
    logo = _logo_path()
    if logo and os.path.exists(logo):
        canvas.drawImage(logo, (width - 20 * mm) / 2, height - 28 * mm,
                        width=20 * mm, height=20 * mm, preserveAspectRatio=True, mask='auto')
    canvas.setFont('Helvetica-Bold', 13)
    canvas.drawCentredString(width / 2, height - 31 * mm, _institution_name())
    canvas.setFont('Helvetica-Bold', 10)
    canvas.drawCentredString(width / 2, height - 36 * mm, title)
    if period:
        canvas.setFont('Helvetica', 9)
        canvas.drawCentredString(width / 2, height - 41 * mm, period)
    canvas.setFont('Helvetica', 8)
    canvas.drawString(10 * mm, 6 * mm, _institution_name() + ' - Timetable')
    canvas.drawRightString(width - 10 * mm, 6 * mm, f'Page {doc.page}')
    canvas.restoreState()


def _paper_pagesize(name):
    base = PAPER_SIZES.get((name or '').upper()) if 'PAPER_SIZES' in globals() else None
    if not base:
        # fallback
        PAPER_SIZES_LOCAL = {
            'A4': (595.27, 841.89), 'A3': (841.89, 1190.55),
            'A2': (1190.55, 1683.78), 'A1': (1683.78, 2383.94), 'A0': (2383.94, 3370.39),
        }
        base = PAPER_SIZES_LOCAL.get((name or '').upper())
    if not base:
        return None
    return landscape(base)


PAPER_SIZES = {
    'A4': (595.27, 841.89),
    'A3': (841.89, 1190.55),
    'A2': (1190.55, 1683.78),
    'A1': (1683.78, 2383.94),
    'A0': (2383.94, 3370.39),
}
