from django.views.generic import ListView, DetailView
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from accounts.mixins import CrudContextMixin, AdminRequiredMixin, SearchableListViewMixin, SuperAdminRequiredMixin
from .models import ConflictRecord, ConflictResolutionRun, ConflictResolutionRecord
from .services import detect_teaching_conflicts, detect_exam_conflicts, detect_all_conflicts, resolve_all_conflicts
from notifications.models import Notification


class ConflictList(AdminRequiredMixin, SearchableListViewMixin, CrudContextMixin, ListView):
    model = ConflictRecord
    template_name = 'conflicts/list.html'
    paginate_by = 50


class ConflictResolutionHistory(AdminRequiredMixin, SearchableListViewMixin, CrudContextMixin, ListView):
    model = ConflictResolutionRun
    template_name = 'conflicts/history.html'
    paginate_by = 50


class ConflictResolutionDetail(AdminRequiredMixin, CrudContextMixin, DetailView):
    model = ConflictResolutionRun
    template_name = 'conflicts/resolution_detail.html'
    context_object_name = 'run'
    pk_url_kwarg = 'run_id'


def _scope_from_request(request):
    scope = {}
    for key in ('academic_level', 'school', 'department', 'programme', 'academic_year', 'semester', 'examination_period'):
        val = request.POST.get(key) or request.GET.get(key)
        if val:
            scope[key] = val
    # resolve FKs lazily in services? services expects objects/ids; ids okay for filters? detect functions filter by id if passed? They compare FK fields to value; Django allows id. Fine.
    return scope


@login_required
def run_detection(request):
    if not (request.user.is_superuser or request.user.is_timetable_admin() or request.user.is_school_admin()):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied
    scope = _scope_from_request(request)
    result = detect_all_conflicts(**scope)
    messages.success(request, f"Detected {result['teaching']} teaching and {result['examination']} examination conflicts.")
    return redirect('conflict_list')


@login_required
def resolve_all(request):
    if not (request.user.is_superuser or request.user.is_timetable_admin() or request.user.is_school_admin()):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied
    scope = _scope_from_request(request)
    # Convert id strings to objects where needed for services filters? services filters use qs.filter(field=val) works with id.
    preview_flag = request.POST.get('preview') == '1' or request.GET.get('preview') == '1'
    apply_flag = request.POST.get('apply') == '1' or request.GET.get('apply') == '1'
    if 'apply' not in request.POST and 'apply' not in request.GET:
        apply_flag = not preview_flag
    # published protection: if any published, force preview (no auto apply) unless superadmin explicitly apply=force
    force = request.POST.get('force') == '1' or request.GET.get('force') == '1'
    if force:
        apply_flag = True
    result = resolve_all_conflicts(user=request.user, apply=apply_flag and not preview_flag, preview=preview_flag, **scope)
    if result.get('applied'):
        messages.success(request, f"Resolved {result['resolved']} conflicts. {result['remaining']} remain.")
        return redirect('conflict_list')
    # preview mode
    run = ConflictResolutionRun.objects.get(pk=result['run_id'])
    return render(request, 'conflicts/resolution_preview.html', {'run': run, 'result': result})


@login_required
def apply_resolution(request, run_id):
    if not (request.user.is_superuser or request.user.is_timetable_admin() or request.user.is_school_admin()):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied
    run = get_object_or_404(ConflictResolutionRun, pk=run_id)
    if request.method == 'POST':
        # Re-run with apply=True using stored scope
        scope = run.scope or {}
        result = resolve_all_conflicts(user=request.user, apply=True, preview=False, **scope)
        messages.success(request, f"Applied resolution. {result['resolved']} resolved, {result['remaining']} remain.")
        return redirect('conflict_resolution_detail', run_id=result['run_id'])
    return render(request, 'conflicts/apply_confirm.html', {'run': run})


@login_required
def cancel_resolution(request, run_id):
    run = get_object_or_404(ConflictResolutionRun, pk=run_id)
    run.status = 'cancelled'
    run.save(update_fields=['status'])
    messages.info(request, 'Resolution cancelled.')
    return redirect('conflict_list')