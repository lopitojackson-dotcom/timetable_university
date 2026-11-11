import io
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.page import PageMargins

GREEN_FILL = PatternFill('solid', fgColor='2E7D32')


def build_lecturer_excel(lecturer, sessions, title='Individual Lecturer Weekly Teaching Timetable',
                         period='', version='DRAFT 1'):
    from reports.views import _lecturer_matrix, _lecturer_workload
    from reports.layout import teaching_slots
    days, slots, grid = _lecturer_matrix(sessions)
    wb = Workbook()
    wb.remove(wb.active)
    ws = wb.create_sheet(title='Lecturer')
    ws['A1'] = "Murang'a University of Technology"
    ws['A1'].font = Font(bold=True, size=14)
    ws['A2'] = title
    ws['A2'].font = Font(bold=True, size=12)
    ws['A3'] = f"Lecturer: {lecturer.full_name} ({lecturer.staff_number})"
    ws['A4'] = f"Department: {lecturer.department} | School: {lecturer.school}"
    ws['A5'] = period
    ws['A6'] = version
    ws['A6'].font = Font(bold=True)
    header_row = 8
    header = ['TIME'] + [d.upper() for d in days]
    for c, val in enumerate(header, start=1):
        cell = ws.cell(row=header_row, column=c, value=val)
        cell.fill = GREEN_FILL
        cell.font = Font(bold=True, color='FFFFFF', size=9)
        cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        cell.border = BORDER
    r = header_row + 1
    for i, (st, en) in enumerate(slots):
        time_label = f"{st.strftime('%I:%M %p')} - {en.strftime('%I:%M %p')}"
        ws.cell(row=r, column=1, value=time_label).border = BORDER
        ws.cell(row=r, column=1).font = Font(size=9, bold=True)
        for j, d in enumerate(days):
            cell_sessions = grid[(d, i)]
            if not cell_sessions:
                val = 'Free'
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
                val = '\n---\n'.join(parts)
            c = ws.cell(row=r, column=2 + j, value=val)
            c.border = BORDER
            c.font = Font(size=9)
            c.alignment = Alignment(vertical='center', wrap_text=True)
        r += 1
    # workload
    r += 1
    wl = _lecturer_workload(sessions)
    ws.cell(row=r, column=1, value='Workload indicator').font = Font(bold=True)
    ws.cell(row=r, column=2, value='Total').font = Font(bold=True)
    r += 1
    for k, v in [
        ('Weekly teaching sessions', wl['total_sessions']),
        ('Weekly teaching hours', wl['total_hours']),
        ('Academic units', wl['units']),
        ('Programmes', wl['programmes']),
        ('Departments', wl['departments']),
        ('Class groups', wl['groups']),
        ('Free sessions', wl['free_sessions']),
        ('Scheduling conflicts', wl['conflicts']),
    ]:
        ws.cell(row=r, column=1, value=k).border = BORDER
        ws.cell(row=r, column=2, value=v).border = BORDER
        r += 1
    ws.column_dimensions['A'].width = 18
    for i in range(len(days)):
        ws.column_dimensions[chr(ord('B') + i)].width = 24
    ws.freeze_panes = ws.cell(row=header_row + 1, column=2)
    ws.page_setup.orientation = 'landscape'
    ws.page_setup.fitToWidth = 1
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.print_title_rows = f'{header_row}:{header_row}'
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf
LIGHT_FILL = PatternFill('solid', fgColor='F1F5F9')
thin = Side(style='thin', color='000000')
BORDER = Border(left=thin, right=thin, top=thin, bottom=thin)

def _style_header(ws, header, row=1):
    for c, val in enumerate(header, start=1):
        cell = ws.cell(row=row, column=c, value=val)
        cell.fill = GREEN_FILL
        cell.font = Font(bold=True, color='FFFFFF', size=9)
        cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        cell.border = BORDER

def _write_section(ws, columns, rows, merges, title_rows):
    # title_rows: list of (text, bold) already written? We'll write titles before table.
    header = ['DAY', 'TIME', 'DETAILS'] + [c['label'] for c in columns]
    # write header at current next row
    hdr_row = ws.max_row + 1 if ws.max_row > 0 else 1
    # Actually handle externally
    return header, hdr_row

def build_teaching_excel(sessions, columns, title='Undergraduate Teaching Timetable',
                         period='', version='DRAFT 1', columns_per_page=20):
    from reports.layout import teaching_slots, build_teaching_section, chunks
    wb = Workbook()
    # remove default
    wb.remove(wb.active)
    slot_list = teaching_slots()
    sections = chunks(columns, size=columns_per_page)
    for si, sec_cols in enumerate(sections, start=1):
        ws = wb.create_sheet(title=f"Section {si}" if len(sections) > 1 else "Teaching")
        # Title block
        ws['A1'] = "Murang'a University of Technology"
        ws['A1'].font = Font(bold=True, size=14)
        ws['A2'] = title
        ws['A2'].font = Font(bold=True, size=12)
        ws['A3'] = period
        ws['A4'] = version
        ws['A4'].font = Font(bold=True)
        header_row = 6
        header = ['DAY', 'TIME', 'DETAILS'] + [c['label'] for c in sec_cols]
        for c, val in enumerate(header, start=1):
            cell = ws.cell(row=header_row, column=c, value=val)
            cell.fill = GREEN_FILL
            cell.font = Font(bold=True, color='FFFFFF', size=9)
            cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
            cell.border = BORDER
        rows, merges = build_teaching_section(sessions, sec_cols, slot_list)
        r = header_row + 1
        for row in rows:
            for c, val in enumerate(row, start=1):
                cell = ws.cell(row=r, column=c, value=val)
                cell.border = BORDER
                cell.font = Font(size=9)
                cell.alignment = Alignment(vertical='center', wrap_text=True, horizontal='center' if c <= 3 else 'left')
            r += 1
        # merges
        for (sr, sc, er, ec) in merges:
            ws.merge_cells(start_row=header_row + 1 + sr, start_column=sc + 1,
                           end_row=header_row + 1 + er, end_column=ec + 1)
        # column widths
        ws.column_dimensions['A'].width = 12
        ws.column_dimensions['B'].width = 16
        ws.column_dimensions['C'].width = 12
        for i in range(len(sec_cols)):
            ws.column_dimensions[get_column_letter(4 + i)].width = 22
        # freeze
        ws.freeze_panes = ws.cell(row=header_row + 1, column=4)
        # print settings
        ws.page_setup.orientation = 'landscape'
        ws.page_setup.fitToWidth = 1
        ws.sheet_properties.pageSetUpPr.fitToPage = True
        ws.print_title_rows = f'{header_row}:{header_row}'
        ws.page_margins = PageMargins(left=0.3, right=0.3, top=0.4, bottom=0.4)
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf

def build_exam_excel(sessions, columns, title='Undergraduate Examination Timetable',
                     period='', version='DRAFT 1', columns_per_page=20):
    from reports.layout import exam_slots, build_exam_section, chunks
    wb = Workbook()
    wb.remove(wb.active)
    slot_list = exam_slots()
    sections = chunks(columns, size=columns_per_page)
    for si, sec_cols in enumerate(sections, start=1):
        ws = wb.create_sheet(title=f"Section {si}" if len(sections) > 1 else "Examinations")
        ws['A1'] = "Murang'a University of Technology"
        ws['A1'].font = Font(bold=True, size=14)
        ws['A2'] = title
        ws['A2'].font = Font(bold=True, size=12)
        ws['A3'] = period
        ws['A4'] = version
        ws['A4'].font = Font(bold=True)
        header_row = 6
        header = ['DAY/DATE', 'TIME', 'DETAILS'] + [c['label'] for c in sec_cols]
        for c, val in enumerate(header, start=1):
            cell = ws.cell(row=header_row, column=c, value=val)
            cell.fill = GREEN_FILL
            cell.font = Font(bold=True, color='FFFFFF', size=9)
            cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
            cell.border = BORDER
        rows, merges = build_exam_section(sessions, sec_cols, slot_list)
        r = header_row + 1
        for row in rows:
            for c, val in enumerate(row, start=1):
                cell = ws.cell(row=r, column=c, value=val)
                cell.border = BORDER
                cell.font = Font(size=9)
                cell.alignment = Alignment(vertical='center', wrap_text=True, horizontal='center' if c <= 3 else 'left')
            r += 1
        for (sr, sc, er, ec) in merges:
            ws.merge_cells(start_row=header_row + 1 + sr, start_column=sc + 1,
                           end_row=header_row + 1 + er, end_column=ec + 1)
        ws.column_dimensions['A'].width = 14
        ws.column_dimensions['B'].width = 16
        ws.column_dimensions['C'].width = 14
        for i in range(len(sec_cols)):
            ws.column_dimensions[get_column_letter(4 + i)].width = 24
        ws.freeze_panes = ws.cell(row=header_row + 1, column=4)
        ws.page_setup.orientation = 'landscape'
        ws.page_setup.fitToWidth = 1
        ws.sheet_properties.pageSetUpPr.fitToPage = True
        ws.print_title_rows = f'{header_row}:{header_row}'
        ws.page_margins = PageMargins(left=0.3, right=0.3, top=0.4, bottom=0.4)
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf
