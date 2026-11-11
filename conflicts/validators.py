from scheduling.validators import (
    validate_teaching_session, validate_exam_session, validate_session,
    suggest_alternative_teaching, suggest_alternative_exam, suggest_alternative,
)

# re-export for convenience
def validate_session_conflict(session):
    if hasattr(session, 'examination_date'):
        return validate_exam_session(session)
    return validate_teaching_session(session)