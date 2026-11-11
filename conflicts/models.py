from django.db import models
from django.conf import settings
import json


class ConflictRecord(models.Model):
    CONFLICT_TYPE_CHOICES = [
        ('teaching', 'Teaching'),
        ('examination', 'Examination'),
    ]
    SEVERITY_CHOICES = [
        ('error', 'Error'),
        ('warning', 'Warning'),
    ]
    conflict_type = models.CharField(max_length=20, choices=CONFLICT_TYPE_CHOICES)
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default='error')
    message = models.TextField()
    related_model = models.CharField(max_length=100, blank=True)
    related_id = models.CharField(max_length=100, blank=True)
    resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.message[:80]


class ConflictResolutionRun(models.Model):
    STATUS_CHOICES = [
        ('queued', 'Queued'),
        ('processing', 'Processing'),
        ('validating', 'Validating'),
        ('resolving', 'Resolving'),
        ('completed', 'Completed'),
        ('completed_with_warnings', 'Completed With Warnings'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    started_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='queued')
    scope = models.JSONField(default=dict, blank=True)
    total_conflicts = models.PositiveIntegerField(default=0)
    resolved = models.PositiveIntegerField(default=0)
    remaining = models.PositiveIntegerField(default=0)
    applied = models.BooleanField(default=False)
    details = models.JSONField(default=dict, blank=True)
    error = models.TextField(blank=True)

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        return f"Resolution Run {self.id} ({self.status})"


class ConflictResolutionRecord(models.Model):
    STATUS_CHOICES = [
        ('proposed', 'Proposed'),
        ('applied', 'Applied'),
        ('rejected', 'Rejected'),
        ('unresolved', 'Unresolved'),
    ]
    run = models.ForeignKey(ConflictResolutionRun, on_delete=models.CASCADE, related_name='records', null=True, blank=True)
    conflict_type = models.CharField(max_length=20, choices=[('teaching','Teaching'),('examination','Examination')])
    conflict_message = models.TextField(blank=True)
    affected_model = models.CharField(max_length=100, blank=True)
    affected_id = models.CharField(max_length=100, blank=True)
    original = models.JSONField(default=dict, blank=True)
    proposed = models.JSONField(default=dict, blank=True)
    final = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='proposed')
    strategy = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.conflict_type}: {self.conflict_message[:60]}"


# Compatibility aliases
class ConflictResolutionHistory(ConflictResolutionRun):
    class Meta:
        proxy = True

class ConflictHistory(ConflictResolutionRun):
    class Meta:
        proxy = True

class ResolutionHistory(ConflictResolutionRun):
    class Meta:
        proxy = True
