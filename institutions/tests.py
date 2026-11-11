from django.test import TestCase
from .models import Institution, School

class InstitutionTests(TestCase):
    def test_school_creation(self):
        inst = Institution.objects.create(name='MUT')
        sch = School.objects.create(name='SOICT', code='SOICT', institution=inst)
        self.assertEqual(str(sch), 'SOICT - SOICT')
        self.assertEqual(inst.schools.count(), 1)
