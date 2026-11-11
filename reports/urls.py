from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='reports_index'),
    path('downloads/', views.download_center, name='download_center'),
    path('downloads/all/', views.download_all_years, name='download_all_years'),
    path('lecturers/', views.lecturer_timetables, name='lecturer_timetables'),
    path('lecturers/pdf/', views.lecturer_timetable_pdf, name='lecturer_timetable_pdf'),
    path('lecturers/excel/', views.lecturer_timetable_excel, name='lecturer_timetable_excel'),
    path('lecturers/bulk/', views.lecturer_timetables_bulk, name='lecturer_timetables_bulk'),
    path('teaching/pdf/', views.teaching_pdf, name='teaching_pdf'),
    path('exam/pdf/', views.exam_pdf, name='exam_pdf'),
    path('teaching/excel/', views.teaching_excel, name='teaching_excel'),
    path('exam/excel/', views.exam_excel, name='exam_excel'),
    path('teaching/layout/', views.teaching_layout_pdf, name='teaching_layout_pdf'),
    path('exam/layout/', views.exam_layout_pdf, name='exam_layout_pdf'),
]
