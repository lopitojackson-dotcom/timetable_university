from django.views.generic import ListView
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from accounts.mixins import CrudContextMixin, AdminRequiredMixin, SearchableListViewMixin
from .models import Notification

class NotificationList(AdminRequiredMixin, SearchableListViewMixin, CrudContextMixin, ListView):
    model = Notification
    template_name = 'notifications/list.html'
    paginate_by = 50

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['notification_types'] = Notification.TYPE_CHOICES
        return ctx

    def get_queryset(self):
        qs = super().get_queryset().filter(user=self.request.user)
        ntype = self.request.GET.get('type')
        if ntype:
            qs = qs.filter(notification_type=ntype)
        read = self.request.GET.get('read')
        if read == 'unread':
            qs = qs.filter(is_read=False)
        elif read == 'read':
            qs = qs.filter(is_read=True)
        return qs

@login_required
def mark_read(request, pk):
    n = Notification.objects.filter(pk=pk, user=request.user).first()
    if n:
        n.is_read = True
        n.save(update_fields=['is_read'])
        if n.link:
            return redirect(n.link)
    return redirect(request.GET.get('next') or '/notifications/')

@login_required
def mark_all_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return redirect(request.GET.get('next') or '/notifications/')

@login_required
def delete_notification(request, pk):
    n = Notification.objects.filter(pk=pk, user=request.user).first()
    if n:
        n.delete()
    return redirect(request.GET.get('next') or '/notifications/')

@login_required
def unread_count(request):
    from django.http import JsonResponse
    return JsonResponse({'unread': request.user.notifications.filter(is_read=False).count()})