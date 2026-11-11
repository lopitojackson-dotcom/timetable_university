from django.urls import path
from . import views

urlpatterns = [
    path('lecturers/', views.LecturerList.as_view(), name='lecturer_list'),
    path('lecturers/create/', views.LecturerCreate.as_view(), name='lecturer_create'),
    path('lecturers/<int:pk>/edit/', views.LecturerUpdate.as_view(), name='lecturer_update'),
    path('lecturers/<int:pk>/delete/', views.LecturerDelete.as_view(), name='lecturer_delete'),

    path('invigilators/', views.InvigilatorList.as_view(), name='invigilator_list'),
    path('invigilators/create/', views.InvigilatorCreate.as_view(), name='invigilator_create'),
    path('invigilators/<int:pk>/edit/', views.InvigilatorUpdate.as_view(), name='invigilator_update'),
    path('invigilators/<int:pk>/delete/', views.InvigilatorDelete.as_view(), name='invigilator_delete'),

    path('venues/', views.VenueList.as_view(), name='venue_list'),
    path('venues/create/', views.VenueCreate.as_view(), name='venue_create'),
    path('venues/<int:pk>/edit/', views.VenueUpdate.as_view(), name='venue_update'),
    path('venues/<int:pk>/delete/', views.VenueDelete.as_view(), name='venue_delete'),

    path('availability/', views.AvailabilitySlotList.as_view(), name='availabilityslot_list'),
    path('availability/create/', views.AvailabilitySlotCreate.as_view(), name='availabilityslot_create'),
    path('availability/<int:pk>/edit/', views.AvailabilitySlotUpdate.as_view(), name='availabilityslot_update'),
    path('availability/<int:pk>/delete/', views.AvailabilitySlotDelete.as_view(), name='availabilityslot_delete'),
    path('room-utilization/', views.room_utilization, name='room_utilization'),
]
