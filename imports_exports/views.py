from django.views.generic import ListView
from django.shortcuts import render, redirect
from django.contrib import messages
from accounts.mixins import CrudContextMixin, AdminRequiredMixin, SearchableListViewMixin
from .models import ImportJob

class ImportJobList(AdminRequiredMixin, SearchableListViewMixin, CrudContextMixin, ListView):
    model = ImportJob
    template_name = 'generic_list.html'
    paginate_by = 50

def import_view(request):
    if request.method == 'POST' and request.FILES.get('file'):
        f = request.FILES['file']
        job = ImportJob.objects.create(file=f, model_name=request.POST.get('model_name','School'), created_by=request.user)
        messages.success(request, 'File uploaded. Process via admin or implement parser.')
        return redirect('importjob_list')
    return render(request, 'imports/import_form.html')

def export_view(request):
    return render(request, 'imports/export_form.html')


