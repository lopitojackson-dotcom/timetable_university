from django.db import models
from django.conf import settings


class Notification(models.Model):
    TYPE_CHOICES = [
        ('teaching_generated', 'Teaching Generated'),
        ('exam_generated', 'Exam Generated'),
        ('alternatives_ready', 'Alternatives Ready'),
        ('regenerated', 'Regenerated'),
        ('auto_corrected', 'Auto Corrected'),
        ('conflict_detected', 'Conflict Detected'),
        ('conflict_resolution', 'Conflict Resolution'),
        ('conflicts_remaining', 'Conflicts Remaining'),
        ('approval_required', 'Approval Required'),
        ('published', 'Published'),
        ('generation_failed', 'Generation Failed'),
        ('general', 'General'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255)
    message = models.TextField()
    link = models.CharField(max_length=255, blank=True)
    notification_type = models.CharField(max_length=40, choices=TYPE_CHOICES, default='general', db_index=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def mark_read(self):
        self.is_read = True
        self.save(update_fields=['is_read'])

    def mark_as_read(self):
        return self.mark_read()
