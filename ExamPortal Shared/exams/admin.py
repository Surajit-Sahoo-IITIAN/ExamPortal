from django.contrib import admin

from .models import (
    Exam,
    Question,
    Submission,
    Result,
    ExamAttempt
)


# ============================================================
# Exam Admin
# ============================================================

@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):

    list_display = (
        'title',
        'total_marks',
        'duration',
        'start_time',
        'end_time',
    )

    search_fields = (
        'title',
    )

    fieldsets = (
        (
            'Exam Information',
            {
                'fields': (
                    'title',
                    'description',
                    'total_marks',
                    'duration',
                )
            }
        ),

        (
            'Exam Schedule',
            {
                'fields': (
                    'start_time',
                    'end_time',
                )
            }
        ),

        (
            'Instructor Feedback',
            {
                'fields': (
                    'instructor_feedback',
                ),
                'description': (
                    "Enter the suggestions or feedback that "
                    "will be displayed to students on their "
                    "result page."
                ),
            }
        ),
    )


# ============================================================
# Question Admin
# ============================================================

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'exam',
        'question_type',
        'marks',
    )

    list_filter = (
        'exam',
        'question_type',
    )

    search_fields = (
        'question_text',
    )


# ============================================================
# Submission Admin
# ============================================================

@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):

    list_display = (
        'student',
        'exam',
        'question',
        'is_evaluated',
        'marks_obtained',
        'submitted_at',
    )

    list_filter = (
        'exam',
        'is_evaluated',
    )

    search_fields = (
        'student__username',
        'exam__title',
    )


# ============================================================
# Result Admin
# ============================================================

@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):

    list_display = (
        'student',
        'exam',
        'total_score',
        'submitted_at',
    )

    list_filter = (
        'exam',
    )

    search_fields = (
        'student__username',
        'exam__title',
    )


# ============================================================
# Exam Attempt Admin
# ============================================================

@admin.register(ExamAttempt)
class ExamAttemptAdmin(admin.ModelAdmin):

    list_display = (
        'student',
        'exam',
        'status',
        'violation_count',
        'started_at',
        'submitted_at',
    )

    list_filter = (
        'exam',
        'status',
    )

    search_fields = (
        'student__username',
        'exam__title',
    )