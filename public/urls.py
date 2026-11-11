from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='public_home'),
    path('about/', views.about, name='public_about'),
    path('timetables/teaching/', views.teaching_timetables, name='public_teaching_timetables'),
    path('timetables/examination/', views.examination_timetables, name='public_exam_timetables'),
    path('schools/', views.schools_departments, name='public_schools'),
    path('academic-calendar/', views.academic_calendar, name='public_academic_calendar'),
    path('announcements/', views.announcements, name='public_announcements'),
    path('faq/', views.faq, name='public_faq'),
    path('contact/', views.contact, name='public_contact'),
]