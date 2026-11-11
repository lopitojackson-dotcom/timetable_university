from accounts.mixins import CrudContextMixin, AdminRequiredMixin, SearchableListViewMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse_lazy
from .models import TeachingTimeSlot, TeachingSession, TeachingTimetable, TeachingTimetableRevision

def make_list(mdl):
    class V(AdminRequiredMixin, SearchableListViewMixin, CrudContextMixin, ListView):
        model = mdl; template_name='generic_list.html'; paginate_by=50
    return V
def make_create(mdl, flds, url):
    class V(AdminRequiredMixin, CrudContextMixin, CreateView):
        model=mdl; fields=flds; template_name='generic_form.html'; success_url=url
    return V
def make_update(mdl, flds, url):
    class V(AdminRequiredMixin, CrudContextMixin, UpdateView):
        model=mdl; fields=flds; template_name='generic_form.html'; success_url=url
    return V
def make_delete(mdl, url):
    class V(AdminRequiredMixin, CrudContextMixin, DeleteView):
        model=mdl; template_name='generic_delete.html'; success_url=url
    return V

# TimeSlot
TeachingTimeSlotList=make_list(TeachingTimeSlot)
TeachingTimeSlotCreate=make_create(TeachingTimeSlot,['name','start_time','end_time','active','order'],reverse_lazy('teaching_timeslot_list'))
TeachingTimeSlotUpdate=make_update(TeachingTimeSlot,['name','start_time','end_time','active','order'],reverse_lazy('teaching_timeslot_list'))
TeachingTimeSlotDelete=make_delete(TeachingTimeSlot,reverse_lazy('teaching_timeslot_list'))

# Session
TeachingSessionList=make_list(TeachingSession)
TeachingSessionCreate=make_create(TeachingSession,['academic_year','semester','school','department','programme','study_year','study_semester','class_group','unit','lecturer','day','start_time','end_time','venue','session_type','group_label','student_population','remarks','status','is_online'],reverse_lazy('teaching_session_list'))
TeachingSessionUpdate=make_update(TeachingSession,['academic_year','semester','school','department','programme','study_year','study_semester','class_group','unit','lecturer','day','start_time','end_time','venue','session_type','group_label','student_population','remarks','status','is_online'],reverse_lazy('teaching_session_list'))
TeachingSessionDelete=make_delete(TeachingSession,reverse_lazy('teaching_session_list'))

# Timetable
TeachingTimetableList=make_list(TeachingTimetable)
TeachingTimetableCreate=make_create(TeachingTimetable,['name','academic_year','semester','school','department','programme','status','version'],reverse_lazy('teaching_timetable_list'))
TeachingTimetableUpdate=make_update(TeachingTimetable,['name','academic_year','semester','school','department','programme','status','version'],reverse_lazy('teaching_timetable_list'))
TeachingTimetableDelete=make_delete(TeachingTimetable,reverse_lazy('teaching_timetable_list'))

@login_required
def publish_teaching(request):
    if not (request.user.is_superuser or request.user.is_timetable_admin()):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied
    from .models import TeachingSession
    TeachingSession.objects.all().update(status='published')
    from audit.models import AuditLog
    AuditLog.objects.create(user=request.user, action='publish', model_name='TeachingSession', details='Published teaching timetable')
    messages.success(request, 'Teaching timetable published.')
    return redirect('teaching_session_list')

@login_required
def withdraw_teaching(request):
    if not (request.user.is_superuser or request.user.is_timetable_admin()):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied
    from .models import TeachingSession
    TeachingSession.objects.all().update(status='withdrawn')
    messages.success(request, 'Teaching timetable withdrawn.')
    return redirect('teaching_session_list')


@login_required
def teaching_grid(request):
    from .models import TeachingSession, TeachingTimeSlot
    from academics.models import AcademicYear, Semester, Programme
    sessions = TeachingSession.objects.all()
    if request.GET.get('academic_year'):
        sessions = sessions.filter(academic_year_id=request.GET['academic_year'])
    if request.GET.get('semester'):
        sessions = sessions.filter(semester_id=request.GET['semester'])
    if request.GET.get('programme'):
        sessions = sessions.filter(programme_id=request.GET['programme'])
    days = ['Monday','Tuesday','Wednesday','Thursday','Friday']
    slots = list(TeachingTimeSlot.objects.filter(active=True).order_by('order','start_time'))
    grid = {d: {s.id: [] for s in slots} for d in days}
    for s in sessions:
        for sl in slots:
            if sl.start_time == s.start_time and sl.end_time == s.end_time:
                grid[s.day][sl.id].append(s)
                break
    rows = []
    for d in days:
        cells = [grid[d][sl.id] for sl in slots]
        rows.append({'day': d, 'cells': cells})
    return render(request, 'teaching/grid.html', {
        'rows': rows, 'slots': slots,
        'years': AcademicYear.objects.all(),
        'semesters': Semester.objects.all(),
        'programmes': Programme.objects.all(),
    })




