from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_SUPER_ADMIN = 'super_admin'
    ROLE_TIMETABLE_ADMIN = 'timetable_admin'
    ROLE_SCHOOL_ADMIN = 'school_admin'
    ROLE_LECTURER = 'lecturer'
    ROLE_STUDENT = 'student'

    ROLE_CHOICES = [
        (ROLE_SUPER_ADMIN, 'Super Administrator'),
        (ROLE_TIMETABLE_ADMIN, 'Timetable Administrator'),
        (ROLE_SCHOOL_ADMIN, 'School/Faculty Administrator'),
        (ROLE_LECTURER, 'Lecturer'),
        (ROLE_STUDENT, 'Student'),
    ]

    role = models.CharField(max_length=30, choices=ROLE_CHOICES, default=ROLE_STUDENT)
    phone = models.CharField(max_length=30, blank=True)
    department = models.ForeignKey('institutions.Department', on_delete=models.SET_NULL, null=True, blank=True, related_name='users')
    school = models.ForeignKey('institutions.School', on_delete=models.SET_NULL, null=True, blank=True, related_name='users')

    def is_super_admin(self):
        return self.role == self.ROLE_SUPER_ADMIN or self.is_superuser

    def is_timetable_admin(self):
        return self.role in (self.ROLE_SUPER_ADMIN, self.ROLE_TIMETABLE_ADMIN) or self.is_superuser

    def is_school_admin(self):
        return self.role in (self.ROLE_SUPER_ADMIN, self.ROLE_TIMETABLE_ADMIN, self.ROLE_SCHOOL_ADMIN) or self.is_superuser

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
