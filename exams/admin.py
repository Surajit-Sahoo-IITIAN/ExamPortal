from django.contrib import admin

from .models import (
    Exam,
    Question,
    Submission,
    Result,
    ExamAttempt
)


# ============================================================
# Inline Questions inside Exam Admin
# ============================================================

class QuestionInline(admin.StackedInline):
    model = Question
    extra = 1
    classes = ('collapse',)

    fieldsets = (
        ('Question', {
            'fields': (
                'question_type',
                'question_text',
                'question_image',
                'marks',
            )
        }),
        ('Options (A, B, C, D)', {
            'fields': (
                ('option1', 'option1_image'),
                ('option2', 'option2_image'),
                ('option3', 'option3_image'),
                ('option4', 'option4_image'),
            )
        }),
        ('Answer & Explanation', {
            'fields': (
                'correct_answer',
                'tolerance',
                'explanation',
            )
        }),
    )


# ============================================================
# Exam Admin
# ============================================================

from django.urls import path
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
import csv
import io
import re
from pypdf import PdfReader


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

    inlines = [QuestionInline]

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:exam_id>/import-questions/',
                self.admin_site.admin_view(self.import_questions_view),
                name='exam-import-questions',
            ),
            path(
                'import-questions/',
                self.admin_site.admin_view(self.import_questions_view),
                name='exam-import-questions-global',
            ),
        ]
        return custom_urls + urls

    def import_questions_view(self, request, exam_id=None):
        exam = get_object_or_404(Exam, id=exam_id) if exam_id else None
        all_exams = Exam.objects.all().order_by('-id')

        if request.method == 'POST':
            target_exam_id = request.POST.get('exam_id') or exam_id
            target_exam = get_object_or_404(Exam, id=target_exam_id)
            uploaded_file = request.FILES.get('file')
            default_marks = float(request.POST.get('default_marks', 1.0) or 1.0)

            if not uploaded_file:
                messages.error(request, "Please select a file to upload (.pdf or .csv).")
                return redirect(request.path)

            filename = uploaded_file.name.lower()

            try:
                if filename.endswith('.csv'):
                    added, skipped = self._process_csv(target_exam, uploaded_file)
                    messages.success(request, f"Successfully imported {added} questions from CSV into '{target_exam.title}'! ({skipped} skipped)")
                elif filename.endswith('.pdf'):
                    added = self._process_pdf(target_exam, uploaded_file, default_marks)
                    if added > 0:
                        messages.success(request, f"Successfully extracted and imported {added} questions from PDF into '{target_exam.title}'!")
                    else:
                        messages.warning(request, "No structured MCQ questions could be identified from this PDF layout.")
                else:
                    messages.error(request, "Unsupported file format. Please upload a .pdf or .csv file.")
                    return redirect(request.path)

                # Update total marks
                total = sum(target_exam.questions.values_list('marks', flat=True))
                target_exam.total_marks = total
                target_exam.save()

                return redirect('admin:exams_exam_change', target_exam.id)

            except Exception as e:
                messages.error(request, f"Error processing file: {str(e)}")
                return redirect(request.path)

        return render(
            request,
            'admin/exams/import_questions.html',
            {
                'exam': exam,
                'all_exams': all_exams,
                'title': 'Import Questions (PDF/CSV)',
                'opts': self.model._meta,
            }
        )

    def _process_csv(self, exam, uploaded_file):
        decoded_file = uploaded_file.read().decode('utf-8-sig')
        reader = csv.reader(io.StringIO(decoded_file))
        header = next(reader, None)

        added = 0
        skipped = 0

        for row in reader:
            if not row or all(c.strip() == '' for c in row):
                continue
            if len(row) < 7:
                skipped += 1
                continue

            q_text = row[0].strip()
            opt1 = row[1].strip()
            opt2 = row[2].strip()
            opt3 = row[3].strip()
            opt4 = row[4].strip()
            try:
                corr = str(int(row[5].strip()))
                marks = float(row[6].strip())
            except (ValueError, TypeError):
                skipped += 1
                continue

            if not q_text or corr not in ['1', '2', '3', '4']:
                skipped += 1
                continue

            Question.objects.create(
                exam=exam,
                question_type='MCQ',
                question_text=q_text,
                option1=opt1,
                option2=opt2,
                option3=opt3,
                option4=opt4,
                correct_answer=corr,
                marks=marks,
            )
            added += 1

        return added, skipped

    def _process_pdf(self, exam, uploaded_file, default_marks=1.0):
        reader = PdfReader(uploaded_file)
        full_text = ""
        for page in reader.pages:
            t = page.extract_text()
            if t:
                full_text += t + "\n"

        lines = [l.strip() for l in full_text.split('\n') if l.strip()]
        full_str = "\n".join(lines)

        q_split_pattern = r'(?:^|\n)(?:Q(?:uestion)?\.?\s*)?(\d+)[\.\)\:\-]\s*'
        chunks = re.split(q_split_pattern, "\n" + full_str)

        added = 0
        if len(chunks) > 1:
            for i in range(1, len(chunks), 2):
                q_body = chunks[i+1].strip()
                ans_match = re.search(r'(?:Ans(?:wer)?|Correct\s*(?:Option|Ans)?)\s*[:\-\=]?\s*\(?([A-Da-d1-4])\)?', q_body, re.IGNORECASE)
                correct_ans = "1"
                if ans_match:
                    val = ans_match.group(1).upper()
                    mapping = {'A': '1', 'B': '2', 'C': '3', 'D': '4', '1': '1', '2': '2', '3': '3', '4': '4'}
                    correct_ans = mapping.get(val, '1')
                    q_body = q_body[:ans_match.start()].strip()

                opt_pattern = r'(?:\(([A-Da-d])\)|(?:\b|^)([A-Da-d])[\.\)\:\-])\s*'
                opt_splits = re.split(opt_pattern, q_body)

                if len(opt_splits) >= 9:
                    q_text = opt_splits[0].strip()
                    opts = []
                    idx = 1
                    while idx < len(opt_splits):
                        opt_text = opt_splits[idx+2].strip() if idx+2 < len(opt_splits) else ""
                        opts.append(opt_text)
                        idx += 3

                    opt1 = opts[0] if len(opts) > 0 else ""
                    opt2 = opts[1] if len(opts) > 1 else ""
                    opt3 = opts[2] if len(opts) > 2 else ""
                    opt4 = opts[3] if len(opts) > 3 else ""

                    Question.objects.create(
                        exam=exam,
                        question_type='MCQ',
                        question_text=q_text,
                        option1=opt1,
                        option2=opt2,
                        option3=opt3,
                        option4=opt4,
                        correct_answer=correct_ans,
                        marks=default_marks
                    )
                    added += 1
                elif q_body:
                    Question.objects.create(
                        exam=exam,
                        question_type='MCQ',
                        question_text=q_body,
                        correct_answer=correct_ans,
                        marks=default_marks
                    )
                    added += 1

        return added


# ============================================================
# Question Admin (standalone access still available)
# ============================================================

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'exam',
        'question_type',
        'question_text_short',
        'marks',
        'correct_answer',
    )

    list_filter = (
        'exam',
        'question_type',
    )

    search_fields = (
        'question_text',
    )

    def question_text_short(self, obj):
        text = obj.question_text or ''
        return text[:80] + '...' if len(text) > 80 else text
    question_text_short.short_description = 'Question'


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