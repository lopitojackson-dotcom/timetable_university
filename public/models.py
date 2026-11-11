from django.db import models
from django.utils import timezone

class Announcement(models.Model):
    CATEGORY_CHOICES = [
        ('teaching', 'Teaching Timetable Updates'),
        ('examination', 'Examination Timetable Updates'),
        ('academic', 'Academic Calendar Notices'),
        ('system', 'System Announcements'),
        ('general', 'General Academic Information'),
    ]
    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='general')
    publication_date = models.DateField(default=timezone.now)
    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-publication_date', '-created_at']

    def __str__(self):
        return self.title