from django.apps import AppConfig

class ExaminationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'examinations'

    def ready(self):
        from django.db.utils import OperationalError, ProgrammingError
        try:
            from .models import ExaminationTimeSlot
            from datetime import time
            if not ExaminationTimeSlot.objects.exists():
                defaults = [
                    ('Session 1', '08:00:00', '10:00:00', 1),
                    ('Session 2', '11:00:00', '13:00:00', 2),
                    ('Session 3', '14:00:00', '16:00:00', 3),
                    ('Session 4', '16:30:00', '18:30:00', 4),
                ]
                for name, st, en, order in defaults:
                    ExaminationTimeSlot.objects.create(name=name, start_time=st, end_time=en, order=order)
        except (OperationalError, ProgrammingError):
            pass
