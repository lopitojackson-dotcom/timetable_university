from django.db import models
from django.conf import settings
from academics.models import AcademicYear, Semester, Programme, ClassGroup, AcademicUnit
from institutions.models import School, Department
from resources.models import Lecturer, Venue


class TeachingTimeSlot(models.Model):
    name = models.CharField(max_length=50)
    start_time = models.TimeField()
    end_time = models.TimeField()
    active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'start_time']

    def __str__(self):
        return f"{self.name} ({self.start_time}-{self.end_time})"


class TeachingSession(models.Model):
    DAY_CHOICES = [
        ('Monday', 'Monday'), ('Tuesday', 'Tuesday'), ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'), ('Friday', 'Friday'),
    ]
    SESSION_TYPE_CHOICES = [
        ('lecture', 'Lecture'),
        ('tutorial', 'Tutorial'),
        ('practical', 'Practical'),
        ('laboratory', 'Laboratory'),
        ('seminar', 'Seminar'),
        ('online', 'Online Class'),
        ('workshop', 'Workshop'),
    ]
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('published', 'Published'),
        ('withdrawn', 'Withdrawn'),
        ('archived', 'Archived'),
    ]

    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='teaching_sessions')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='teaching_sessions')
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='teaching_sessions')
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='teaching_sessions')
    programme = models.ForeignKey(Programme, on_delete=models.CASCADE, related_name='teaching_sessions')
    study_year = models.PositiveIntegerField(default=1)
    study_semester = models.PositiveIntegerField(default=1)
    class_group = models.ForeignKey(ClassGroup, on_delete=models.SET_NULL, null=True, blank=True, related_name='teaching_sessions')
    unit = models.ForeignKey(AcademicUnit, on_delete=models.CASCADE, related_name='teaching_sessions')
    lecturer = models.ForeignKey(Lecturer, on_delete=models.SET_NULL, null=True, blank=True, related_name='teaching_sessions')
    day = models.CharField(max_length=15, choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    venue = models.ForeignKey(Venue, on_delete=models.SET_NULL, null=True, blank=True, related_name='teaching_sessions')
    session_type = models.CharField(max_length=20, choices=SESSION_TYPE_CHOICES, default='lecture')
    group_label = models.CharField(max_length=50, blank=True, help_text='Teaching group label e.g. Group 1')
    student_population = models.PositiveIntegerField(default=0)
    remarks = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    is_online = models.BooleanField(default=False)
    generation_run = models.ForeignKey('TeachingGenerationRun', on_delete=models.SET_NULL, null=True, blank=True, related_name='sessions')
    alternative = models.ForeignKey('TeachingAlternative', on_delete=models.SET_NULL, null=True, blank=True, related_name='sessions')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['day', 'start_time']

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.day in ('Saturday', 'Sunday'):
            raise ValidationError({'day': 'Teaching sessions cannot be scheduled on weekends.'})
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError({'end_time': 'End time must be after start time.'})

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.unit.code} {self.day} {self.start_time}-{self.end_time}"


class TeachingSessionVenue(models.Model):
    session = models.ForeignKey(TeachingSession, on_delete=models.CASCADE, related_name='extra_venues')
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name='teaching_allocations')
    capacity_override = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.session} @ {self.venue}"


class TeachingTimetable(models.Model):
    ACADEMIC_LEVEL_CHOICES = [('diploma', 'Diploma'), ('degree', 'Degree')]
    STATUS_CHOICES = TeachingSession.STATUS_CHOICES
    name = models.CharField(max_length=255)
    academic_level = models.CharField(max_length=20, choices=ACADEMIC_LEVEL_CHOICES, blank=True, null=True, db_index=True)
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='teaching_timetables')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='teaching_timetables')
    school = models.ForeignKey(School, on_delete=models.SET_NULL, null=True, blank=True, related_name='teaching_timetables')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='teaching_timetables')
    programme = models.ForeignKey(Programme, on_delete=models.SET_NULL, null=True, blank=True, related_name='teaching_timetables')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    version = models.PositiveIntegerField(default=1)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} (v{self.version})"


class TeachingTimetableRevision(models.Model):
    timetable = models.ForeignKey(TeachingTimetable, on_delete=models.CASCADE, related_name='revisions')
    revision_number = models.PositiveIntegerField()
    modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    modified_at = models.DateTimeField(auto_now_add=True)
    previous_values = models.JSONField(default=dict, blank=True)
    new_values = models.JSONField(default=dict, blank=True)
    reason = models.TextField(blank=True)


class TeachingGenerationRun(models.Model):
    ACADEMIC_LEVEL_CHOICES = [('diploma', 'Diploma'), ('degree', 'Degree')]
    academic_level = models.CharField(max_length=20, choices=ACADEMIC_LEVEL_CHOICES, blank=True, null=True, db_index=True)
    academic_year = models.ForeignKey('academics.AcademicYear', on_delete=models.CASCADE, related_name='teaching_runs')
    semester = models.ForeignKey('academics.Semester', on_delete=models.CASCADE, related_name='teaching_runs')
    school = models.ForeignKey('institutions.School', on_delete=models.SET_NULL, null=True, blank=True, related_name='teaching_runs')
    department = models.ForeignKey('institutions.Department', on_delete=models.SET_NULL, null=True, blank=True, related_name='teaching_runs')
    programme = models.ForeignKey('academics.Programme', on_delete=models.SET_NULL, null=True, blank=True, related_name='teaching_runs')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    preferences = models.JSONField(default=dict, blank=True)
    idempotency_key = models.CharField(max_length=128, null=True, blank=True, unique=True, db_index=True)
    status = models.CharField(max_length=30, default='completed')
    progress = models.PositiveIntegerField(default=100)
    message = models.TextField(blank=True)
    error = models.TextField(blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Teaching Run {self.id} - {self.academic_year} {self.semester}"


class TeachingAlternative(models.Model):
    run = models.ForeignKey(TeachingGenerationRun, on_delete=models.CASCADE, related_name='alternatives')
    number = models.PositiveIntegerField()
    score = models.FloatField(default=0)
    conflicts = models.PositiveIntegerField(default=0)
    unscheduled = models.PositiveIntegerField(default=0)
    valid = models.BooleanField(default=False)
    selected = models.BooleanField(default=False)
    seed = models.IntegerField(default=0)
    details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['number']
        unique_together = ('run', 'number')

    def __str__(self):
        return f"Alternative {self.number} (score {self.score})"

