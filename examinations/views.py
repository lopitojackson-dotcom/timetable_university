from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from accounts.mixins import CrudContextMixin, AdminRequiredMixin, SearchableListViewMixin
from .models import ExaminationPeriod, ExaminationTimeSlot, ExaminationSession, ExaminationTimetable

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

ExaminationPeriodList=make_list(ExaminationPeriod)
ExaminationPeriodCreate=make_create(ExaminationPeriod,['name','academic_year','start_date','end_date','status'],reverse_lazy('exam_period_list'))
ExaminationPeriodUpdate=make_update(ExaminationPeriod,['name','academic_year','start_date','end_date','status'],reverse_lazy('exam_period_list'))
ExaminationPeriodDelete=make_delete(ExaminationPeriod,reverse_lazy('exam_period_list'))

ExaminationTimeSlotList=make_list(ExaminationTimeSlot)
ExaminationTimeSlotCreate=make_create(ExaminationTimeSlot,['name','start_time','end_time','active','order'],reverse_lazy('exam_timeslot_list'))
ExaminationTimeSlotUpdate=make_update(ExaminationTimeSlot,['name','start_time','end_time','active','order'],reverse_lazy('exam_timeslot_list'))
ExaminationTimeSlotDelete=make_delete(ExaminationTimeSlot,reverse_lazy('exam_timeslot_list'))

ExaminationSessionList=make_list(ExaminationSession)
ExaminationSessionCreate=make_create(ExaminationSession,['academic_year','semester','examination_period','examination_date','day_of_week','start_time','end_time','school','department','programme','study_year','study_semester','class_group','unit','unit_lecturer','expected_candidates','invigilators','venue','special_instructions','status'],reverse_lazy('exam_session_list'))
ExaminationSessionUpdate=make_update(ExaminationSession,['academic_year','semester','examination_period','examination_date','day_of_week','start_time','end_time','school','department','programme','study_year','study_semester','class_group','unit','unit_lecturer','expected_candidates','invigilators','venue','special_instructions','status'],reverse_lazy('exam_session_list'))
ExaminationSessionDelete=make_delete(ExaminationSession,reverse_lazy('exam_session_list'))

ExaminationTimetableList=make_list(ExaminationTimetable)
ExaminationTimetableCreate=make_create(ExaminationTimetable,['name','examination_period','academic_year','semester','school','status','version'],reverse_lazy('exam_timetable_list'))
ExaminationTimetableUpdate=make_update(ExaminationTimetable,['name','examination_period','academic_year','semester','school','status','version'],reverse_lazy('exam_timetable_list'))
ExaminationTimetableDelete=make_delete(ExaminationTimetable,reverse_lazy('exam_timetable_list'))

@login_required
def publish_exam(request):
    if not (request.user.is_superuser or request.user.is_timetable_admin()):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied
    ExaminationSession.objects.all().update(status='published')
    from audit.models import AuditLog
    AuditLog.objects.create(user=request.user, action='publish', model_name='ExaminationSession', details='Published examination timetable')
    messages.success(request, 'Examination timetable published.')
    return redirect('exam_session_list')

@login_required
def withdraw_exam(request):
    if not (request.user.is_superuser or request.user.is_timetable_admin()):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied
    ExaminationSession.objects.all().update(status='withdrawn')
    messages.success(request, 'Examination timetable withdrawn.')
    return redirect('exam_session_list')




