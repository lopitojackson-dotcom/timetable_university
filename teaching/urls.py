from django.urls import path
from . import views

urlpatterns = [
    path('timeslots/', views.TeachingTimeSlotList.as_view(), name='teaching_timeslot_list'),
    path('timeslots/create/', views.TeachingTimeSlotCreate.as_view(), name='teaching_timeslot_create'),
    path('timeslots/<int:pk>/edit/', views.TeachingTimeSlotUpdate.as_view(), name='teaching_timeslot_update'),
    path('timeslots/<int:pk>/delete/', views.TeachingTimeSlotDelete.as_view(), name='teaching_timeslot_delete'),

    path('sessions/', views.TeachingSessionList.as_view(), name='teaching_session_list'),
    path('sessions/create/', views.TeachingSessionCreate.as_view(), name='teaching_session_create'),
    path('sessions/<int:pk>/edit/', views.TeachingSessionUpdate.as_view(), name='teaching_session_update'),
    path('sessions/<int:pk>/delete/', views.TeachingSessionDelete.as_view(), name='teaching_session_delete'),

    path('timetables/', views.TeachingTimetableList.as_view(), name='teaching_timetable_list'),
    path('timetables/create/', views.TeachingTimetableCreate.as_view(), name='teaching_timetable_create'),
    path('timetables/<int:pk>/edit/', views.TeachingTimetableUpdate.as_view(), name='teaching_timetable_update'),
    path('timetables/<int:pk>/delete/', views.TeachingTimetableDelete.as_view(), name='teaching_timetable_delete'),
    path('grid/', views.teaching_grid, name='teaching_grid'),
    path('publish/', views.publish_teaching, name='teaching_publish'),
    path('withdraw/', views.withdraw_teaching, name='teaching_withdraw'),
]
