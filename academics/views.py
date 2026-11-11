from accounts.mixins import CrudContextMixin, AdminRequiredMixin, SearchableListViewMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import AcademicYear, Semester, Programme, ClassGroup, AcademicUnit, StudentPopulation


def make_list(mdl):
    class V(AdminRequiredMixin, SearchableListViewMixin, CrudContextMixin, ListView):
        model = mdl
        template_name = 'generic_list.html'
        paginate_by = 50
    return V

def make_create(mdl, flds, surl):
    class V(AdminRequiredMixin, CrudContextMixin, CreateView):
        model = mdl
        fields = flds
        template_name = 'generic_form.html'
        success_url = surl
    return V

def make_update(mdl, flds, surl):
    class V(AdminRequiredMixin, CrudContextMixin, UpdateView):
        model = mdl
        fields = flds
        template_name = 'generic_form.html'
        success_url = surl
    return V

def make_delete(mdl, surl):
    class V(AdminRequiredMixin, CrudContextMixin, DeleteView):
        model = mdl
        template_name = 'generic_delete.html'
        success_url = surl
    return V

# AcademicYear
AcademicYearList = make_list(AcademicYear)
AcademicYearCreate = make_create(AcademicYear, ['name','start_date','end_date'], reverse_lazy('academic_year_list'))
AcademicYearUpdate = make_update(AcademicYear, ['name','start_date','end_date'], reverse_lazy('academic_year_list'))
AcademicYearDelete = make_delete(AcademicYear, reverse_lazy('academic_year_list'))

# Semester
SemesterList = make_list(Semester)
SemesterCreate = make_create(Semester, ['academic_year','name','start_date','end_date','teaching_start_date','teaching_end_date','examination_start_date','examination_end_date','status'], reverse_lazy('semester_list'))
SemesterUpdate = make_update(Semester, ['academic_year','name','start_date','end_date','teaching_start_date','teaching_end_date','examination_start_date','examination_end_date','status'], reverse_lazy('semester_list'))
SemesterDelete = make_delete(Semester, reverse_lazy('semester_list'))

# Programme
ProgrammeList = make_list(Programme)
ProgrammeCreate = make_create(Programme, ['name','code','department','school','level','status'], reverse_lazy('programme_list'))
ProgrammeUpdate = make_update(Programme, ['name','code','department','school','level','status'], reverse_lazy('programme_list'))
ProgrammeDelete = make_delete(Programme, reverse_lazy('programme_list'))

# ClassGroup
ClassGroupList = make_list(ClassGroup)
ClassGroupCreate = make_create(ClassGroup, ['programme','academic_year','semester','study_year','study_semester','group_name','expected_population','study_mode'], reverse_lazy('classgroup_list'))
ClassGroupUpdate = make_update(ClassGroup, ['programme','academic_year','semester','study_year','study_semester','group_name','expected_population','study_mode'], reverse_lazy('classgroup_list'))
ClassGroupDelete = make_delete(ClassGroup, reverse_lazy('classgroup_list'))

# AcademicUnit
AcademicUnitList = make_list(AcademicUnit)
AcademicUnitCreate = make_create(AcademicUnit, ['code','name','department','programme','programmes','academic_year','semester','credit_hours','lecturers','classification','active'], reverse_lazy('academicunit_list'))
AcademicUnitUpdate = make_update(AcademicUnit, ['code','name','department','programme','programmes','academic_year','semester','credit_hours','lecturers','classification','active'], reverse_lazy('academicunit_list'))
AcademicUnitDelete = make_delete(AcademicUnit, reverse_lazy('academicunit_list'))

# StudentPopulation
StudentPopulationList = make_list(StudentPopulation)
StudentPopulationCreate = make_create(StudentPopulation, ['class_group','expected_enrolment','actual_enrolment','academic_year','semester'], reverse_lazy('studentpopulation_list'))
StudentPopulationUpdate = make_update(StudentPopulation, ['class_group','expected_enrolment','actual_enrolment','academic_year','semester'], reverse_lazy('studentpopulation_list'))
StudentPopulationDelete = make_delete(StudentPopulation, reverse_lazy('studentpopulation_list'))




