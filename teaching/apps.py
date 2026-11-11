from django.apps import AppConfig

class TeachingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'teaching'

    def ready(self):
        from django.db.utils import OperationalError, ProgrammingError
        try:
            from .models import TeachingTimeSlot
            if not TeachingTimeSlot.objects.exists():
                defaults = [
                    ('Morning 1', '07:00:00', '10:00:00', 1),
                    ('Morning 2', '10:00:00', '13:00:00', 2),
                    ('Afternoon', '13:00:00', '16:00:00', 3),
                    ('Evening', '16:00:00', '19:00:00', 4),
                ]
                for name, st, en, order in defaults:
                    TeachingTimeSlot.objects.create(name=name, start_time=st, end_time=en, order=order)
        except (OperationalError, ProgrammingError):
            pass
