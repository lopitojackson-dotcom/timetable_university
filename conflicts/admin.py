from django.contrib import admin
from .models import *
for m in [o for o in globals().values() if isinstance(o, type) and issubclass(o, __import__('django.db.models', fromlist=['Model']).Model)]:
    try: admin.site.register(m)
    except Exception: pass

