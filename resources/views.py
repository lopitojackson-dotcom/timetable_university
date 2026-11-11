from accounts.mixins import CrudContextMixin, AdminRequiredMixin, SearchableListViewMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from .models import Lecturer, Invigilator, Venue, AvailabilitySlot

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

LecturerList=make_list(Lecturer)
LecturerCreate=make_create(Lecturer,['staff_number','full_name','email','telephone','department','school','employment_status','max_teaching_hours_week','availability','user'],reverse_lazy('lecturer_list'))
LecturerUpdate=make_update(Lecturer,['staff_number','full_name','email','telephone','department','school','employment_status','max_teaching_hours_week','availability','user'],reverse_lazy('lecturer_list'))
LecturerDelete=make_delete(Lecturer,reverse_lazy('lecturer_list'))

InvigilatorList=make_list(Invigilator)
InvigilatorCreate=make_create(Invigilator,['staff_number','full_name','email','department','availability','max_invigilations_per_day','employment_status','lecturer','user'],reverse_lazy('invigilator_list'))
InvigilatorUpdate=make_update(Invigilator,['staff_number','full_name','email','department','availability','max_invigilations_per_day','employment_status','lecturer','user'],reverse_lazy('invigilator_list'))
InvigilatorDelete=make_delete(Invigilator,reverse_lazy('invigilator_list'))

VenueList=make_list(Venue)
VenueCreate=make_create(Venue,['name','code','venue_type','building','floor','capacity','availability','active'],reverse_lazy('venue_list'))
VenueUpdate=make_update(Venue,['name','code','venue_type','building','floor','capacity','availability','active'],reverse_lazy('venue_list'))
VenueDelete=make_delete(Venue,reverse_lazy('venue_list'))

AvailabilitySlotList=make_list(AvailabilitySlot)
AvailabilitySlotCreate=make_create(AvailabilitySlot,['lecturer','venue','day','start_time','end_time','available'],reverse_lazy('availabilityslot_list'))
AvailabilitySlotUpdate=make_update(AvailabilitySlot,['lecturer','venue','day','start_time','end_time','available'],reverse_lazy('availabilityslot_list'))
AvailabilitySlotDelete=make_delete(AvailabilitySlot,reverse_lazy('availabilityslot_list'))

@login_required
def room_utilization(request):
    from teaching.models import TeachingSession
    from examinations.models import ExaminationSession
    from .models import Venue
    venues = Venue.objects.all()
    data = []
    for v in venues:
        ts = TeachingSession.objects.filter(venue=v).count()
        es = ExaminationSession.objects.filter(venue=v).count()
        data.append({'venue': v, 'teaching': ts, 'exam': es})
    return render(request, 'resources/room_utilization.html', {'data': data})




