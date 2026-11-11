from django.db import models
from django.conf import settings


class Institution(models.Model):
    name = models.CharField(max_length=255)
    short_name = models.CharField(max_length=100, blank=True)
    acronym = models.CharField(max_length=50, blank=True)
    logo = models.ImageField(upload_to='institution/', blank=True, null=True)
    address = models.TextField(blank=True)
    postal_address = models.TextField(blank=True)
    email = models.EmailField(blank=True)
    telephone = models.CharField(max_length=50, blank=True)
    website = models.URLField(blank=True)
    motto = models.CharField(max_length=255, blank=True)
    primary_color = models.CharField(max_length=20, blank=True, default='#2e7d32')
    secondary_color = models.CharField(max_length=20, blank=True, default='#1b5e20')
    academic_calendar_settings = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='institution_updates')

    def __str__(self):
        return self.name


class School(models.Model):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='schools')

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.code} - {self.name}"


class Department(models.Model):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True)
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='departments')
    administrator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='administered_departments')

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.code} - {self.name}"
