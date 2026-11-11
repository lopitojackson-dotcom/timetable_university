from accounts.mixins import CrudContextMixin, AdminRequiredMixin, SearchableListViewMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from .models import Institution, School, Department


def make_list(mdl, template='generic_list.html'):
    class V(AdminRequiredMixin, SearchableListViewMixin, CrudContextMixin, ListView):
        model = mdl
        template_name = template
        paginate_by = 50
    return V

def make_create(mdl, flds, surl, template='generic_form.html'):
    class V(AdminRequiredMixin, CrudContextMixin, CreateView):
        model = mdl
        fields = flds
        template_name = template
        success_url = surl
    return V

def make_update(mdl, flds, surl, template='generic_form.html'):
    class V(AdminRequiredMixin, CrudContextMixin, UpdateView):
        model = mdl
        fields = flds
        template_name = template
        success_url = surl
    return V

def make_delete(mdl, surl, template='generic_delete.html'):
    class V(AdminRequiredMixin, CrudContextMixin, DeleteView):
        model = mdl
        template_name = template
        success_url = surl
    return V


InstitutionList = make_list(Institution)
InstitutionCreate = make_create(Institution, ['name','logo','address','email','telephone','website','academic_calendar_settings'], reverse_lazy('institution_list'))
InstitutionUpdate = make_update(Institution, ['name','logo','address','email','telephone','website','academic_calendar_settings'], reverse_lazy('institution_list'))
InstitutionDelete = make_delete(Institution, reverse_lazy('institution_list'))

SchoolList = make_list(School)
SchoolCreate = make_create(School, ['name','code','description','institution'], reverse_lazy('school_list'))
SchoolUpdate = make_update(School, ['name','code','description','institution'], reverse_lazy('school_list'))
SchoolDelete = make_delete(School, reverse_lazy('school_list'))

DepartmentList = make_list(Department)
DepartmentCreate = make_create(Department, ['name','code','school','administrator'], reverse_lazy('department_list'))
DepartmentUpdate = make_update(Department, ['name','code','school','administrator'], reverse_lazy('department_list'))
DepartmentDelete = make_delete(Department, reverse_lazy('department_list'))


@login_required
def institution_settings(request):
    if not request.user.is_superuser:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied
    inst = Institution.objects.first()
    if inst is None:
        inst = Institution.objects.create(name="Murang'a University of Technology")
    if request.method == 'POST':
        inst.name = request.POST.get('name', inst.name)
        inst.short_name = request.POST.get('short_name', inst.short_name)
        inst.acronym = request.POST.get('acronym', inst.acronym)
        inst.address = request.POST.get('address', inst.address)
        inst.postal_address = request.POST.get('postal_address', inst.postal_address)
        inst.email = request.POST.get('email', inst.email)
        inst.telephone = request.POST.get('telephone', inst.telephone)
        inst.website = request.POST.get('website', inst.website)
        inst.motto = request.POST.get('motto', inst.motto)
        inst.primary_color = request.POST.get('primary_color', inst.primary_color)
        inst.secondary_color = request.POST.get('secondary_color', inst.secondary_color)
        if request.FILES.get('logo'):
            inst.logo = request.FILES['logo']
        inst.updated_by = request.user
        inst.save()
        messages.success(request, 'Institution branding updated successfully.')
        return redirect('institution_settings')
    return render(request, 'institutions/settings.html', {'institution': inst})




