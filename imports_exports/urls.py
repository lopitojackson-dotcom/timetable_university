from django.urls import path
from . import views

from django.views.generic import RedirectView
urlpatterns = [
    path('', views.ImportJobList.as_view(), name='importjob_list'),
    path('upload/', views.import_view, name='import_upload'),
    path('create/', RedirectView.as_view(url='/imports/upload/', permanent=False), name='import_create'),
    path('export/', views.export_view, name='export_page'),
]
