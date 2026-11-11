from django.urls import path
from . import views

urlpatterns = [
    path('periods/', views.ExaminationPeriodList.as_view(), name='exam_period_list'),
    path('periods/create/', views.ExaminationPeriodCreate.as_view(), name='exam_period_create'),
    path('periods/<int:pk>/edit/', views.ExaminationPeriodUpdate.as_view(), name='exam_period_update'),
    path('periods/<int:pk>/delete/', views.ExaminationPeriodDelete.as_view(), name='exam_period_delete'),

    path('timeslots/', views.ExaminationTimeSlotList.as_view(), name='exam_timeslot_list'),
    path('timeslots/create/', views.ExaminationTimeSlotCreate.as_view(), name='exam_timeslot_create'),
    path('timeslots/<int:pk>/edit/', views.ExaminationTimeSlotUpdate.as_view(), name='exam_timeslot_update'),
    path('timeslots/<int:pk>/delete/', views.ExaminationTimeSlotDelete.as_view(), name='exam_timeslot_delete'),

    path('sessions/', views.ExaminationSessionList.as_view(), name='exam_session_list'),
    path('sessions/create/', views.ExaminationSessionCreate.as_view(), name='exam_session_create'),
    path('sessions/<int:pk>/edit/', views.ExaminationSessionUpdate.as_view(), name='exam_session_update'),
    path('sessions/<int:pk>/delete/', views.ExaminationSessionDelete.as_view(), name='exam_session_delete'),

    path('timetables/', views.ExaminationTimetableList.as_view(), name='exam_timetable_list'),
    path('timetables/create/', views.ExaminationTimetableCreate.as_view(), name='exam_timetable_create'),
    path('timetables/<int:pk>/edit/', views.ExaminationTimetableUpdate.as_view(), name='exam_timetable_update'),
    path('timetables/<int:pk>/delete/', views.ExaminationTimetableDelete.as_view(), name='exam_timetable_delete'),
    path('publish/', views.publish_exam, name='exam_publish'),
    path('withdraw/', views.withdraw_exam, name='exam_withdraw'),
]
