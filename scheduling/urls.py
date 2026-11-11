from django.urls import path
from . import views

urlpatterns = [
    path('teaching/', views.generate_teaching_view, name='generate_teaching'),
    path('teaching/alternatives/', views.generate_teaching_alternatives_view, name='generate_teaching_alternatives'),
    path('teaching/alternatives/<int:run_id>/', views.teaching_alternatives_view, name='teaching_alternatives'),
    path('teaching/alternatives/select/<int:alt_id>/', views.select_teaching_alternative, name='select_teaching_alternative'),
    path('exams/', views.generate_exam_view, name='generate_exam'),
    path('exams/alternatives/', views.generate_exam_alternatives_view, name='generate_exam_alternatives'),
    path('exams/alternatives/<int:run_id>/', views.exam_alternatives_view, name='exam_alternatives'),
    path('exams/alternatives/select/<int:alt_id>/', views.select_exam_alternative, name='select_exam_alternative'),
]
