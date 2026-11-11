from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.home, name='dashboard'),
    path('public/teaching/', views.public_teaching, name='public_teaching'),
    path('public/exam/', views.public_exam, name='public_exam'),
]
