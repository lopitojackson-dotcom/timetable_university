from django.urls import path
from . import views
urlpatterns = [
    path('', views.NotificationList.as_view(), name='notification_list'),
    path('<int:pk>/read/', views.mark_read, name='notification_read'),
    path('read-all/', views.mark_all_read, name='notification_read_all'),
    path('<int:pk>/delete/', views.delete_notification, name='notification_delete'),
    path('unread-count/', views.unread_count, name='notification_unread_count'),
]