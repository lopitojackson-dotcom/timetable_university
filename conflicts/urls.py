from django.urls import path
from django.views.generic import RedirectView
from . import views
urlpatterns = [
    path('', views.ConflictList.as_view(), name='conflict_list'),
    path('run/', views.run_detection, name='conflict_run'),
    path('detect/', views.run_detection, name='conflict_detect'),
    path('detect-all/', views.run_detection, name='detect_all_conflicts'),
    path('resolve/', views.resolve_all, name='conflict_resolve'),
    path('resolve-all/', views.resolve_all, name='resolve_all_conflicts'),
    path('resolve/preview/', views.resolve_all, name='conflict_resolve_preview'),
    path('resolution/<int:run_id>/apply/', views.apply_resolution, name='conflict_apply'),
    path('resolution/<int:run_id>/cancel/', views.cancel_resolution, name='conflict_cancel'),
    path('resolution/<int:run_id>/', views.ConflictResolutionDetail.as_view(), name='conflict_resolution_detail'),
    path('history/', views.ConflictResolutionHistory.as_view(), name='conflict_history'),
    path('resolution-history/', views.ConflictResolutionHistory.as_view(), name='conflict_resolution_history'),
    path('create/', RedirectView.as_view(url='/conflicts/', permanent=False)),
    path('<int:pk>/edit/', RedirectView.as_view(url='/conflicts/', permanent=False)),
    path('<int:pk>/delete/', RedirectView.as_view(url='/conflicts/', permanent=False)),
]