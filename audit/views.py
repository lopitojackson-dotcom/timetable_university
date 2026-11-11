from django.shortcuts import render
from django.views.generic import ListView
from accounts.mixins import AdminRequiredMixin, SearchableListViewMixin, CrudContextMixin
from .models import AuditLog
from .services import audit_teaching_coverage, audit_exam_coverage, audit_summary


class AuditLogList(AdminRequiredMixin, SearchableListViewMixin, CrudContextMixin, ListView):
    model = AuditLog
    template_name = 'generic_list.html'
    paginate_by = 50


def compliance_dashboard(request):
    teaching = audit_teaching_coverage(
        academic_level=request.GET.get('academic_level') or None,
        school=request.GET.get('school') or None,
        department=request.GET.get('department') or None,
        programme=request.GET.get('programme') or None,
        academic_year=request.GET.get('academic_year') or None,
        semester=request.GET.get('semester') or None,
    )
    exam = audit_exam_coverage(
        academic_level=request.GET.get('academic_level') or None,
        school=request.GET.get('school') or None,
        department=request.GET.get('department') or None,
        programme=request.GET.get('programme') or None,
        academic_year=request.GET.get('academic_year') or None,
        semester=request.GET.get('semester') or None,
    )
    summary = audit_summary(teaching, exam)
    return render(request, 'audit/compliance.html', {
        'teaching': teaching[:200],
        'exam': exam[:200],
        'summary': summary,
        'total_teaching': len(teaching),
        'total_exam': len(exam),
    })
