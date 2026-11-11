from django.db import models
from django.conf import settings


class AcademicYear(models.Model):
    name = models.CharField(max_length=50, unique=True)  # e.g. 2026/2027
    start_date = models.DateField()
    end_date = models.DateField()

    class Meta:
        ordering = ['-name']

    def __str__(self):
        return self.name


class Semester(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('archived', 'Archived'),
    ]
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='semesters')
    name = models.CharField(max_length=50)  # e.g. Semester 1
    start_date = models.DateField()
    end_date = models.DateField()
    teaching_start_date = models.DateField(null=True, blank=True)
    teaching_end_date = models.DateField(null=True, blank=True)
    examination_start_date = models.DateField(null=True, blank=True)
    examination_end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')

    class Meta:
        unique_together = ('academic_year', 'name')
        ordering = ['academic_year', 'name']

    def __str__(self):
        return f"{self.academic_year} - {self.name}"


class Programme(models.Model):
    LEVEL_CHOICES = [
        ('certificate', 'Certificate'),
        ('diploma', 'Diploma'),
        ('degree', 'Degree'),
        ('masters', 'Masters'),
        ('phd', 'PhD'),
    ]
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True)
    department = models.ForeignKey('institutions.Department', on_delete=models.CASCADE, related_name='programmes')
    school = models.ForeignKey('institutions.School', on_delete=models.CASCADE, related_name='programmes')
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='degree')
    duration_years = models.PositiveIntegerField(default=4)
    semesters_per_year = models.PositiveIntegerField(default=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')

    class Meta:
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.name}"


class ClassGroup(models.Model):
    STUDY_MODE_CHOICES = [
        ('regular', 'Regular'),
        ('odel', 'ODEL'),
        ('evening', 'Evening'),
        ('weekend', 'Weekend'),
    ]
    programme = models.ForeignKey(Programme, on_delete=models.CASCADE, related_name='class_groups')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='class_groups')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='class_groups')
    study_year = models.PositiveIntegerField()
    study_semester = models.PositiveIntegerField()
    group_name = models.CharField(max_length=50, default='Group 1')
    expected_population = models.PositiveIntegerField(default=0)
    study_mode = models.CharField(max_length=20, choices=STUDY_MODE_CHOICES, default='regular')

    class Meta:
        unique_together = ('programme', 'academic_year', 'semester', 'study_year', 'study_semester', 'group_name')
        ordering = ['programme', 'study_year', 'study_semester', 'group_name']

    def label(self):
        return f"Y{self.study_year}S{self.study_semester}"

    def __str__(self):
        return f"{self.programme.code} {self.label()} {self.group_name}"


class AcademicUnit(models.Model):
    CLASSIFICATION_CHOICES = [
        ('theory', 'Theory'),
        ('practical', 'Practical'),
        ('both', 'Theory & Practical'),
    ]
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=255)
    department = models.ForeignKey('institutions.Department', on_delete=models.CASCADE, related_name='units')
    programme = models.ForeignKey(Programme, on_delete=models.SET_NULL, null=True, blank=True, related_name='units')
    programmes = models.ManyToManyField(Programme, blank=True, related_name='shared_units')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.SET_NULL, null=True, blank=True, related_name='units')
    semester = models.ForeignKey(Semester, on_delete=models.SET_NULL, null=True, blank=True, related_name='units')
    credit_hours = models.PositiveIntegerField(default=3)
    lecturers = models.ManyToManyField('resources.Lecturer', blank=True, related_name='units')
    classification = models.CharField(max_length=20, choices=CLASSIFICATION_CHOICES, default='theory')
    required_sessions_per_week = models.PositiveIntegerField(default=1)
    required_hours_per_week = models.PositiveIntegerField(default=3)
    preferred_session_duration = models.PositiveIntegerField(default=3)
    min_session_duration = models.PositiveIntegerField(default=3)
    max_session_duration = models.PositiveIntegerField(default=3)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.name}"


class StudentPopulation(models.Model):
    class_group = models.ForeignKey(ClassGroup, on_delete=models.CASCADE, related_name='populations')
    expected_enrolment = models.PositiveIntegerField(default=0)
    actual_enrolment = models.PositiveIntegerField(default=0)
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='populations')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='populations')

    def __str__(self):
        return f"{self.class_group} - {self.actual_enrolment or self.expected_enrolment}"
