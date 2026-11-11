from django.urls import path
from . import views

urlpatterns = [
    path('settings/', views.institution_settings, name='institution_settings'),
    path('institutions/', views.InstitutionList.as_view(), name='institution_list'),
    path('institutions/create/', views.InstitutionCreate.as_view(), name='institution_create'),
    path('institutions/<int:pk>/edit/', views.InstitutionUpdate.as_view(), name='institution_update'),
    path('institutions/<int:pk>/delete/', views.InstitutionDelete.as_view(), name='institution_delete'),

    path('schools/', views.SchoolList.as_view(), name='school_list'),
    path('schools/create/', views.SchoolCreate.as_view(), name='school_create'),
    path('schools/<int:pk>/edit/', views.SchoolUpdate.as_view(), name='school_update'),
    path('schools/<int:pk>/delete/', views.SchoolDelete.as_view(), name='school_delete'),

    path('departments/', views.DepartmentList.as_view(), name='department_list'),
    path('departments/create/', views.DepartmentCreate.as_view(), name='department_create'),
    path('departments/<int:pk>/edit/', views.DepartmentUpdate.as_view(), name='department_update'),
    path('departments/<int:pk>/delete/', views.DepartmentDelete.as_view(), name='department_delete'),
]
