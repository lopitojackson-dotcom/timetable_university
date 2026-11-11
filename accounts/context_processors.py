def institution_branding(request):
    from institutions.models import Institution
    try:
        inst = Institution.objects.first()
    except Exception:
        inst = None
    return {'institution': inst}
