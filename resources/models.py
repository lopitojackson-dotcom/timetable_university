from django.db import models
from django.conf import settings


class Lecturer(models.Model):
    EMPLOYMENT_CHOICES = [
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('contract', 'Contract'),
        ('adjunct', 'Adjunct'),
    ]
    staff_number = models.CharField(max_length=50, unique=True)
    full_name = models.CharField(max_length=255)
    email = models.EmailField(blank=True)
    telephone = models.CharField(max_length=50, blank=True)
    department = models.ForeignKey('institutions.Department', on_delete=models.CASCADE, related_name='lecturers')
    school = models.ForeignKey('institutions.School', on_delete=models.CASCADE, related_name='lecturers')
    employment_status = models.CharField(max_length=20, choices=EMPLOYMENT_CHOICES, default='full_time')
    max_teaching_hours_week = models.PositiveIntegerField(default=18)
    availability = models.TextField(blank=True, help_text='Free-text availability notes')
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='lecturer_profile')

    class Meta:
        ordering = ['full_name']

    def __str__(self):
        return f"{self.staff_number} - {self.full_name}"


class Invigilator(models.Model):
    EMPLOYMENT_CHOICES = [
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('contract', 'Contract'),
    ]
    staff_number = models.CharField(max_length=50, unique=True)
    full_name = models.CharField(max_length=255)
    email = models.EmailField(blank=True)
    department = models.ForeignKey('institutions.Department', on_delete=models.SET_NULL, null=True, blank=True, related_name='invigilators')
    availability = models.TextField(blank=True)
    max_invigilations_per_day = models.PositiveIntegerField(default=2)
    employment_status = models.CharField(max_length=20, choices=EMPLOYMENT_CHOICES, default='full_time')
    lecturer = models.OneToOneField(Lecturer, on_delete=models.SET_NULL, null=True, blank=True, related_name='invigilator_profile')
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='invigilator_profile')

    class Meta:
        ordering = ['full_name']

    def __str__(self):
        return f"{self.staff_number} - {self.full_name}"


class Venue(models.Model):
    VENUE_TYPE_CHOICES = [
        ('lecture_room', 'Lecture Room'),
        ('computer_lab', 'Computer Laboratory'),
        ('science_lab', 'Science Laboratory'),
        ('nursing_lab', 'Nursing Laboratory'),
        ('chemistry_lab', 'Chemistry Laboratory'),
        ('botany_lab', 'Botany Laboratory'),
        ('assembly_hall', 'Assembly Hall'),
        ('online', 'Online Classroom'),
        ('kitchen', 'Kitchen'),
        ('restaurant', 'Restaurant'),
        ('other', 'Other'),
    ]
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True)
    venue_type = models.CharField(max_length=30, choices=VENUE_TYPE_CHOICES, default='lecture_room')
    building = models.CharField(max_length=255, blank=True)
    floor = models.CharField(max_length=50, blank=True)
    capacity = models.PositiveIntegerField(default=0)
    availability = models.TextField(blank=True)
    active = models.BooleanField(default=True)
    teaching_enabled = models.BooleanField(default=True)
    examination_enabled = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.code} - {self.name}"


class AvailabilitySlot(models.Model):
    """Generic availability for lecturer or venue."""
    lecturer = models.ForeignKey(Lecturer, on_delete=models.CASCADE, null=True, blank=True, related_name='availability_slots')
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, null=True, blank=True, related_name='availability_slots')
    day = models.CharField(max_length=15)
    start_time = models.TimeField()
    end_time = models.TimeField()
    available = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.day} {self.start_time}-{self.end_time}"
