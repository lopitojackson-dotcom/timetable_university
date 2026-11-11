def notification_counts(request):
    if request.user.is_authenticated:
        try:
            return {'unread_notifications': request.user.notifications.filter(is_read=False).count()}
        except Exception:
            return {'unread_notifications': 0}
    return {'unread_notifications': 0}