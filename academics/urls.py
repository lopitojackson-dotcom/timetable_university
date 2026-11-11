from django.urls import path
from . import views

urlpatterns = [
    path('years/', views.AcademicYearList.as_view(), name='academic_year_list'),
    path('years/create/', views.AcademicYearCreate.as_view(), name='academic_year_create'),
    path('years/<int:pk>/edit/', views.AcademicYearUpdate.as_view(), name='academic_year_update'),
    path('years/<int:pk>/delete/', views.AcademicYearDelete.as_view(), name='academic_year_delete'),

    path('semesters/', views.SemesterList.as_view(), name='semester_list'),
    path('semesters/create/', views.SemesterCreate.as_view(), name='semester_create'),
    path('semesters/<int:pk>/edit/', views.SemesterUpdate.as_view(), name='semester_update'),
    path('semesters/<int:pk>/delete/', views.SemesterDelete.as_view(), name='semester_delete'),

    path('programmes/', views.ProgrammeList.as_view(), name='programme_list'),
    path('programmes/create/', views.ProgrammeCreate.as_view(), name='programme_create'),
    path('programmes/<int:pk>/edit/', views.ProgrammeUpdate.as_view(), name='programme_update'),
    path('programmes/<int:pk>/delete/', views.ProgrammeDelete.as_view(), name='programme_delete'),

    path('classgroups/', views.ClassGroupList.as_view(), name='classgroup_list'),
    path('classgroups/create/', views.ClassGroupCreate.as_view(), name='classgroup_create'),
    path('classgroups/<int:pk>/edit/', views.ClassGroupUpdate.as_view(), name='classgroup_update'),
    path('classgroups/<int:pk>/delete/', views.ClassGroupDelete.as_view(), name='classgroup_delete'),

    path('units/', views.AcademicUnitList.as_view(), name='academicunit_list'),
    path('units/create/', views.AcademicUnitCreate.as_view(), name='academicunit_create'),
    path('units/<int:pk>/edit/', views.AcademicUnitUpdate.as_view(), name='academicunit_update'),
    path('units/<int:pk>/delete/', views.AcademicUnitDelete.as_view(), name='academicunit_delete'),

    path('populations/', views.StudentPopulationList.as_view(), name='studentpopulation_list'),
    path('populations/create/', views.StudentPopulationCreate.as_view(), name='studentpopulation_create'),
    path('populations/<int:pk>/edit/', views.StudentPopulationUpdate.as_view(), name='studentpopulation_update'),
    path('populations/<int:pk>/delete/', views.StudentPopulationDelete.as_view(), name='studentpopulation_delete'),
]
