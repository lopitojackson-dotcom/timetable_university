from django.db import models
from django.conf import settings
from academics.models import AcademicYear, Semester, Programme, ClassGroup, AcademicUnit
from institutions.models import School, Department
from resources.models import Lecturer, Venue, Invigilator


class ExaminationPeriod(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('closed', 'Closed'),
        ('archived', 'Archived'),
    ]
    name = models.CharField(max_length=255)
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='exam_periods')
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return self.name


class ExaminationTimeSlot(models.Model):
    name = models.CharField(max_length=50)
    start_time = models.TimeField()
    end_time = models.TimeField()
    active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'start_time']

    def __str__(self):
        return f"{self.name} ({self.start_time}-{self.end_time})"


class ExaminationSession(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('published', 'Published'),
        ('withdrawn', 'Withdrawn'),
        ('archived', 'Archived'),
    ]
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='exam_sessions')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='exam_sessions')
    examination_period = models.ForeignKey(ExaminationPeriod, on_delete=models.CASCADE, related_name='sessions')
    examination_date = models.DateField()
    day_of_week = models.CharField(max_length=15, blank=True)
    start_time = models.TimeField()
    end_time = models.TimeField()
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='exam_sessions')
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='exam_sessions')
    programme = models.ForeignKey(Programme, on_delete=models.CASCADE, related_name='exam_sessions')
    study_year = models.PositiveIntegerField(default=1)
    study_semester = models.PositiveIntegerField(default=1)
    class_group = models.ForeignKey(ClassGroup, on_delete=models.SET_NULL, null=True, blank=True, related_name='exam_sessions')
    unit = models.ForeignKey(AcademicUnit, on_delete=models.CASCADE, related_name='exam_sessions')
    unit_lecturer = models.ForeignKey(Lecturer, on_delete=models.SET_NULL, null=True, blank=True, related_name='exam_lecturer_sessions')
    expected_candidates = models.PositiveIntegerField(default=0)
    invigilators = models.ManyToManyField(Invigilator, blank=True, related_name='exam_sessions')
    venue = models.ForeignKey(Venue, on_delete=models.SET_NULL, null=True, blank=True, related_name='exam_sessions')
    special_instructions = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    generation_run = models.ForeignKey('ExaminationGenerationRun', on_delete=models.SET_NULL, null=True, blank=True, related_name='sessions')
    alternative = models.ForeignKey('ExaminationAlternative', on_delete=models.SET_NULL, null=True, blank=True, related_name='sessions')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['examination_date', 'start_time']

    def clean(self):
        from django.core.exceptions import ValidationError
        if isinstance(self.examination_date, str):
            from datetime import date
            try:
                self.examination_date = date.fromisoformat(self.examination_date)
            except ValueError:
                pass
        if not self.day_of_week and self.examination_date:
            self.day_of_week = self.examination_date.strftime('%A')
        if self.day_of_week in ('Saturday', 'Sunday'):
            raise ValidationError({'day_of_week': 'Examinations cannot be scheduled on weekends.'})
        if self.examination_date and hasattr(self.examination_date, 'weekday') and self.examination_date.weekday() >= 5:
            raise ValidationError({'examination_date': 'Examinations cannot be scheduled on weekends.'})
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError({'end_time': 'End time must be after start time.'})

    def save(self, *args, **kwargs):
        if not self.day_of_week and self.examination_date:
            self.day_of_week = self.examination_date.strftime('%A')
        self.clean()
        super().save(*args, **kwargs)

    def venue_allocations(self):
        extras = list(self.extra_venues.all())
        if extras:
            extra_total = sum(e.candidate_count or 0 for e in extras)
            primary_count = self.expected_candidates - extra_total
            if primary_count < 0:
                primary_count = 0
            allocs = []
            if self.venue:
                allocs.append((self.venue, primary_count))
            for e in extras:
                allocs.append((e.venue, e.candidate_count or 0))
            return allocs
        if self.venue:
            return [(self.venue, self.expected_candidates)]
        return []

    def __str__(self):
        return f"{self.unit.code} {self.examination_date} {self.start_time}-{self.end_time}"


class ExaminationSessionVenue(models.Model):
    session = models.ForeignKey(ExaminationSession, on_delete=models.CASCADE, related_name='extra_venues')
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name='exam_allocations')
    capacity_override = models.PositiveIntegerField(null=True, blank=True)
    candidate_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.session} @ {self.venue}"


class ExaminationTimetable(models.Model):
    ACADEMIC_LEVEL_CHOICES = [('diploma', 'Diploma'), ('degree', 'Degree')]
    STATUS_CHOICES = ExaminationSession.STATUS_CHOICES
    name = models.CharField(max_length=255)
    academic_level = models.CharField(max_length=20, choices=ACADEMIC_LEVEL_CHOICES, blank=True, null=True, db_index=True)
    examination_period = models.ForeignKey(ExaminationPeriod, on_delete=models.CASCADE, related_name='timetables')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='exam_timetables')
    semester = models.ForeignKey(Semester, on_delete=models.SET_NULL, null=True, blank=True, related_name='exam_timetables')
    school = models.ForeignKey(School, on_delete=models.SET_NULL, null=True, blank=True, related_name='exam_timetables')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    version = models.PositiveIntegerField(default=1)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} (v{self.version})"


class ExaminationTimetableRevision(models.Model):
    timetable = models.ForeignKey(ExaminationTimetable, on_delete=models.CASCADE, related_name='revisions')
    revision_number = models.PositiveIntegerField()
    modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    modified_at = models.DateTimeField(auto_now_add=True)
    previous_values = models.JSONField(default=dict, blank=True)
    new_values = models.JSONField(default=dict, blank=True)
    reason = models.TextField(blank=True)


class ExaminationGenerationRun(models.Model):
    ACADEMIC_LEVEL_CHOICES = [('diploma', 'Diploma'), ('degree', 'Degree')]
    academic_level = models.CharField(max_length=20, choices=ACADEMIC_LEVEL_CHOICES, blank=True, null=True, db_index=True)
    examination_period = models.ForeignKey(ExaminationPeriod, on_delete=models.CASCADE, related_name='runs')
    academic_year = models.ForeignKey('academics.AcademicYear', on_delete=models.CASCADE, related_name='exam_runs')
    semester = models.ForeignKey('academics.Semester', on_delete=models.SET_NULL, null=True, blank=True, related_name='exam_runs')
    school = models.ForeignKey('institutions.School', on_delete=models.SET_NULL, null=True, blank=True, related_name='exam_runs')
    programme = models.ForeignKey('academics.Programme', on_delete=models.SET_NULL, null=True, blank=True, related_name='exam_runs')
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
        return f"Exam Run {self.id}"


class ExaminationAlternative(models.Model):
    run = models.ForeignKey(ExaminationGenerationRun, on_delete=models.CASCADE, related_name='alternatives')
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
        return f"Exam Alternative {self.number} (score {self.score})"
