from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Q

class CrudContextMixin:
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if getattr(self, 'model', None):
            ctx.setdefault('title', self.model._meta.verbose_name_plural.replace('_', ' ').title())
        path = self.request.path
        if path.endswith('create/') or path.endswith('edit/'):
            parts = [p for p in path.split('/') if p]
            if len(parts) >= 2:
                ctx.setdefault('back_url', '/' + '/'.join(parts[:-1]) + '/')
            else:
                ctx.setdefault('back_url', '/')
        else:
            ctx.setdefault('back_url', path)
        return ctx

class SearchableListViewMixin:
    search_fields = []
    def get_search_fields(self):
        if self.search_fields:
            return self.search_fields
        model = self.model
        candidates = ['name','code','title','full_name','staff_number','unit_code','group_name','email']
        return [f for f in candidates if hasattr(model, f) or f in [fd.name for fd in model._meta.fields]]
    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.GET.get('q')
        fields = self.get_search_fields()
        if q and fields:
            cond = Q()
            for f in fields:
                cond |= Q(**{f+'__icontains': q})
            try:
                qs = qs.filter(cond)
            except Exception:
                pass
        return qs

class AdminRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_superuser or request.user.is_timetable_admin() or request.user.is_school_admin()):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

class SuperAdminRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_superuser or request.user.is_super_admin()):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)
