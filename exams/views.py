import logging

from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.db import transaction
from django.views.decorators.http import require_POST
from django.http import JsonResponse

from .models import (
    Exam,
    Submission,
    Result,
    ExamAttempt,
)

logger = logging.getLogger(__name__)



# ============================================================
# HELPER FUNCTIONS
# ============================================================

def normalize_answer(answer):
    """
    Normalize a single answer value.
    """

    if answer is None:
        return ""

    answer = str(answer).strip()

    answer = answer.replace(r"\(", "")
    answer = answer.replace(r"\)", "")
    answer = answer.replace(r"\[", "")
    answer = answer.replace(r"\]", "")

    answer = " ".join(answer.split())

    return answer.strip()


def normalize_multi_answer(answer):
    """
    Convert a comma-separated answer into a set.

    Example:
        "1,3" -> {"1", "3"}
        "3,1" -> {"1", "3"}
    """

    if not answer:
        return set()

    values = set()

    for value in str(answer).split(","):

        value = normalize_answer(value)

        if value:
            values.add(value)

    return values


def get_option_values(question):
    """
    Return the four option values in order.
    """

    return [
        normalize_answer(question.option1),
        normalize_answer(question.option2),
        normalize_answer(question.option3),
        normalize_answer(question.option4),
    ]


def get_correct_option_numbers(question):
    """
    Determine which option numbers are correct.

    Current convention:
        MCQ  -> "2"
        MULTI -> "1,3"

    For backward compatibility, if a MULTI answer contains
    something outside 1,2,3,4, it is interpreted as actual
    option text.

    Example:

        correct_answer = "1,3"
        -> options 1 and 3

        old format:
        correct_answer = "2,5"
        options = [2,4,5,9]
        -> options 1 and 3
    """

    if not question.correct_answer:

        return set()

    raw = normalize_answer(
        question.correct_answer
    )

    if question.question_type == "MULTI":

        tokens = normalize_multi_answer(raw)

    else:

        tokens = {
            normalize_answer(raw)
        }

    # ========================================================
    # CURRENT FORMAT:
    # ALL TOKENS ARE OPTION NUMBERS
    # ========================================================

    if tokens and all(
        token in {"1", "2", "3", "4"}
        for token in tokens
    ):

        return tokens

    # ========================================================
    # BACKWARD COMPATIBILITY:
    # ANSWER TEXT FORMAT
    # ========================================================

    option_values = get_option_values(
        question
    )

    correct_numbers = set()

    for token in tokens:

        for index, option_value in enumerate(
            option_values,
            start=1
        ):

            if (
                option_value
                and
                token == option_value
            ):

                correct_numbers.add(
                    str(index)
                )

                break

    return correct_numbers


def get_selected_option_numbers(question, answer_text):
    """
    Student answers are submitted by exam.html as option
    numbers.

    Example:
        MCQ  -> "2"
        MULTI -> "1,3"
    """

    if not answer_text:

        return set()

    if question.question_type == "MULTI":

        return normalize_multi_answer(
            answer_text
        )

    return {
        normalize_answer(answer_text)
    }


def prepare_result_option_data(submission):
    """
    Prepare option information for result.html.

    Each option receives:

        option_number
        value
        is_correct
        is_selected
        css_class

    This keeps all answer interpretation in Python and
    removes ambiguous logic from the template.
    """

    question = submission.question

    selected_options = get_selected_option_numbers(
        question,
        submission.answer_text
    )

    correct_options = get_correct_option_numbers(
        question
    )

    option_values = get_option_values(
        question
    )

    option_data = []

    for number, value in enumerate(
        option_values,
        start=1
    ):

        number_string = str(number)

        is_correct = (
            number_string
            in correct_options
        )

        is_selected = (
            number_string
            in selected_options
        )

        # ----------------------------------------------------
        # CORRECT OPTION ALWAYS GREEN
        # ----------------------------------------------------

        if is_correct:

            css_class = "option-correct"

        # ----------------------------------------------------
        # SELECTED BUT WRONG -> RED
        # ----------------------------------------------------

        elif is_selected:

            css_class = "option-incorrect"

        # ----------------------------------------------------
        # NORMAL OPTION
        # ----------------------------------------------------

        else:

            css_class = "option"

        option_data.append(
            {
                "number":
                    number,

                "value":
                    value,

                "is_correct":
                    is_correct,

                "is_selected":
                    is_selected,

                "css_class":
                    css_class,
            }
        )

    return option_data


# ============================================================
# SMART POST-LOGIN REDIRECT
# ============================================================

@login_required
def post_login_redirect(request):
    """Redirect staff to instructor dashboard, students to student dashboard."""
    if request.user.is_staff:
        return redirect('/instructor/dashboard/')
    return redirect('/student/dashboard/')


# ============================================================
# STUDENT DASHBOARD
# ============================================================

@login_required
def student_dashboard_view(request):
    """Show available exams for students."""

    if request.user.is_staff:
        return redirect('/instructor/dashboard/')

    current_time = timezone.localtime()
    exams = Exam.objects.all().order_by('-id')

    exam_data = []

    for exam in exams:
        attempt = ExamAttempt.objects.filter(
            student=request.user,
            exam=exam
        ).first()

        # Determine status
        if attempt and attempt.status in ['SUBMITTED', 'AUTO_SUBMITTED']:
            status = 'SUBMITTED'
            status_label = 'Submitted'
        elif attempt and attempt.status == 'TERMINATED':
            status = 'TERMINATED'
            status_label = 'Terminated'
        elif exam.start_time and current_time < exam.start_time:
            status = 'UPCOMING'
            status_label = 'Not Started Yet'
        elif exam.end_time and current_time > exam.end_time:
            status = 'CLOSED'
            status_label = 'Exam Closed'
        else:
            status = 'AVAILABLE'
            status_label = 'Available'

        # Get result if exists
        result = Result.objects.filter(
            student=request.user,
            exam=exam
        ).first()

        exam_data.append({
            'exam': exam,
            'status': status,
            'status_label': status_label,
            'attempt': attempt,
            'result': result,
        })

    return render(
        request,
        'student_dashboard.html',
        {
            'exam_data': exam_data,
            'student': request.user,
        }
    )


# ============================================================
# LOGOUT
# ============================================================

def logout_view(request):
    logout(request)

    next_url = request.GET.get('next')

    if next_url:
        return redirect(next_url)

    return redirect('/login/')


# ============================================================
# EXAM VIEW
# ============================================================

@login_required
def exam_view(request, exam_id):

    exam = get_object_or_404(
        Exam,
        id=exam_id
    )

    logger.debug(
        "Exam %s: start=%s end=%s",
        exam.title,
        exam.start_time,
        exam.end_time
    )

    # ========================================================
    # ADMIN / INSTRUCTOR PREVIEW
    # ========================================================

    if request.user.is_staff:

        questions = exam.questions.all()

        return render(
            request,
            "exam.html",
            {
                "exam":
                    exam,

                "questions":
                    questions,

                "exam_end_time": (
                    exam.end_time.isoformat()
                    if exam.end_time
                    else ""
                ),

                "is_admin":
                    True,
            }
        )

    # ========================================================
    # STUDENT
    # ========================================================

    current_time = timezone.localtime()

    # ========================================================
    # FIND EXISTING ATTEMPT
    # ========================================================

    attempt = ExamAttempt.objects.filter(
        student=request.user,
        exam=exam
    ).first()

    # ========================================================
    # TERMINATED
    # ========================================================

    if (
        attempt
        and
        attempt.status == "TERMINATED"
    ):

        return render(
            request,
            "message.html",
            {
                "title":
                    "Examination Terminated",

                "message": (
                    "Your examination has been "
                    "terminated due to multiple "
                    "examination-window violations."
                )
            }
        )

    # ========================================================
    # ALREADY SUBMITTED
    # ========================================================

    if (
        attempt
        and
        attempt.status in [
            "SUBMITTED",
            "AUTO_SUBMITTED"
        ]
    ):

        return render(
            request,
            "message.html",
            {
                "title":
                    "Already Submitted",

                "message": (
                    "You have already submitted this "
                    "examination. Multiple attempts "
                    "are not allowed."
                ),
                "exam_id":
                 exam.id,
            }
        )

    # ========================================================
    # EXAM NOT STARTED
    # ========================================================

    if (
        exam.start_time
        and
        current_time < exam.start_time
    ):

        local_start = timezone.localtime(
            exam.start_time
        )

        return render(
            request,
            "message.html",
            {
                "title":
                    "Exam Not Started",

                "message": (
                    f"This exam will start on "
                    f"{local_start.strftime('%d %b %Y')} "
                    f"at "
                    f"{local_start.strftime('%I:%M %p')}."
                )
            }
        )

    # ========================================================
    # EXAM CLOSED
    # ========================================================

    if (
        exam.end_time
        and
        current_time > exam.end_time
    ):

        return render(
            request,
            "message.html",
            {
                "title":
                    "Exam Closed",

                "message": (
                    "The examination window has ended. "
                    "You can no longer access this exam."
                )
            }
        )

    # ========================================================
    # CREATE ATTEMPT
    # ========================================================

    if attempt is None:

        attempt = ExamAttempt.objects.create(
            student=request.user,
            exam=exam,
            status="IN_PROGRESS"
        )

        logger.info(
            "ExamAttempt created: %s - %s",
            attempt.student.username,
            attempt.exam.title
        )

    # ========================================================
    # QUESTIONS
    # ========================================================

    questions = exam.questions.all()

    # ========================================================
    # SUBMIT EXAM
    # ========================================================

    if request.method == "POST":

        student = request.user

        with transaction.atomic():
            for question in questions:

                # =================================================
                # MULTIPLE CORRECT
                # =================================================

                if question.question_type == "MULTI":

                    selected_answers = request.POST.getlist(
                        f"question_{question.id}"
                    )

                    answer_text = ",".join(
                        selected_answers
                    )

                # =================================================
                # MCQ
                # =================================================

                else:

                    answer_text = request.POST.get(
                        f"question_{question.id}",
                        ""
                    )

                # =================================================
                # FILE
                # =================================================

                answer_file = request.FILES.get(
                    f"question_{question.id}"
                )

                # =================================================
                # CREATE SUBMISSION
                # =================================================

                submission = Submission.objects.create(
                    student=student,
                    exam=exam,
                    question=question,
                    answer_text=answer_text,
                    answer_file=answer_file
                )

                # =================================================
                # MCQ
                # =================================================

                if question.question_type == "MCQ":

                    student_answer = normalize_answer(
                        answer_text
                    )

                    correct_options = (
                        get_correct_option_numbers(
                            question
                        )
                    )

                    if (
                        student_answer
                        and
                        student_answer
                        in correct_options
                    ):

                        submission.marks_obtained = (
                            question.marks
                        )

                    else:

                        submission.marks_obtained = 0

                    submission.is_evaluated = True

                    submission.save()

                # =================================================
                # MULTI
                # =================================================

                elif question.question_type == "MULTI":

                    student_answers = (
                        get_selected_option_numbers(
                            question,
                            answer_text
                        )
                    )

                    correct_answers = (
                        get_correct_option_numbers(
                            question
                        )
                    )

                    # All-or-nothing marking

                    if (
                        student_answers
                        and
                        correct_answers
                        and
                        student_answers
                        == correct_answers
                    ):

                        submission.marks_obtained = (
                            question.marks
                        )

                    else:

                        submission.marks_obtained = 0

                    submission.is_evaluated = True

                    submission.save()

                # =================================================
                # NUMERICAL
                # =================================================

                elif question.question_type == "NUM":

                    submission.is_evaluated = False

                    submission.marks_obtained = 0

                    submission.save()

                # =================================================
                # SHORT / LONG / UPLOAD
                # =================================================

                else:

                    submission.is_evaluated = False

                    submission.marks_obtained = 0

                    submission.save()

            # ====================================================
            # TOTAL SCORE
            # ====================================================

            total_score = sum(
                Submission.objects.filter(
                    student=student,
                    exam=exam
                ).values_list(
                    "marks_obtained",
                    flat=True
                )
            )

            logger.info(
                "Total score: %s - %s - %s",
                student.username,
                exam.title,
                total_score
            )

            # ====================================================
            # CREATE / UPDATE RESULT
            # ====================================================

            result, created = Result.objects.update_or_create(
                student=student,
                exam=exam,
                defaults={
                    "total_score":
                        total_score,

                    "submitted_at":
                        timezone.now()
                }
            )

            logger.info(
                "Result %s: %s - %s - %s",
                'created' if created else 'updated',
                student.username,
                exam.title,
                total_score
            )

            # ====================================================
            # UPDATE ATTEMPT
            # ====================================================

            attempt.status = "SUBMITTED"

            attempt.submitted_at = timezone.now()

            attempt.save()

            logger.info(
                "ExamAttempt submitted: %s - %s",
                attempt.student.username,
                attempt.exam.title
            )

        return redirect(
            "result_view",
            exam_id=exam.id
        )


    # ========================================================
    # DISPLAY EXAM
    # ========================================================

    return render(
        request,
        "exam.html",
        {
            "exam":
                exam,

            "questions":
                questions,

            "exam_end_time": (
                exam.end_time.isoformat()
                if exam.end_time
                else ""
            ),

            "is_admin":
                False,

            "attempt":
                attempt,
        }
    )


# ============================================================
# EXAM VIOLATION
# ============================================================

@login_required
@require_POST
def exam_violation(request, exam_id):

    if request.user.is_staff:
        return JsonResponse({'action': 'none'})

    exam = get_object_or_404(
        Exam,
        id=exam_id
    )

    attempt = ExamAttempt.objects.filter(
        student=request.user,
        exam=exam
    ).first()

    if attempt is None:
        return JsonResponse({'action': 'redirect', 'url': f'/exam/{exam_id}/'})

    if attempt.status != 'IN_PROGRESS':
        return JsonResponse({'action': 'redirect', 'url': f'/exam/{exam_id}/'})

    current_time = timezone.now()

    # ========================================================
    # FIRST VIOLATION — WARNING
    # ========================================================

    if attempt.violation_count == 0:

        attempt.violation_count = 1
        attempt.first_violation_at = current_time
        attempt.save()

        logger.warning(
            "Violation 1: %s - %s",
            request.user.username,
            exam.title
        )

        return JsonResponse({
            'action': 'warning',
            'violation_count': 1,
            'message': (
                'You have left the examination window. '
                'This is your FIRST and FINAL warning. '
                'A second violation will auto-submit your exam.'
            )
        })

    # ========================================================
    # SECOND+ VIOLATION — AUTO-SUBMIT & TERMINATE
    # ========================================================

    else:

        attempt.violation_count += 1
        attempt.second_violation_at = current_time
        attempt.terminated_at = current_time
        attempt.status = 'TERMINATED'
        attempt.save()

        logger.warning(
            "Violation %d (TERMINATED): %s - %s",
            attempt.violation_count,
            request.user.username,
            exam.title
        )

        # Auto-submit: save whatever score exists from any
        # already-created submissions (in case the student
        # submitted partial answers via periodic saves later)
        existing_submissions = Submission.objects.filter(
            student=request.user,
            exam=exam
        )

        if existing_submissions.exists():
            total_score = sum(
                existing_submissions.values_list(
                    'marks_obtained', flat=True
                )
            )
        else:
            total_score = 0

        Result.objects.update_or_create(
            student=request.user,
            exam=exam,
            defaults={
                'total_score': total_score,
                'submitted_at': current_time,
            }
        )

        return JsonResponse({
            'action': 'terminated',
            'violation_count': attempt.violation_count,
            'message': (
                'Your examination has been terminated '
                'due to a second window violation. '
                'Your answered questions have been saved.'
            )
        })


# ============================================================
# SUCCESS PAGE
# ============================================================

def success_view(request):

    return render(
        request,
        "success.html"
    )


# ============================================================
# RESULT PAGE
# ============================================================

@login_required
def result_view(request, exam_id):

    exam = get_object_or_404(
        Exam,
        id=exam_id
    )

    result = get_object_or_404(
        Result,
        student=request.user,
        exam=exam
    )

    submissions = Submission.objects.filter(
        student=request.user,
        exam=exam
    ).select_related(
        "question"
    )

    # ========================================================
    # PREPARE OPTION DATA
    # ========================================================

    for submission in submissions:

        if submission.question.question_type in [
            "MCQ",
            "MULTI"
        ]:

            submission.result_options = (
                prepare_result_option_data(
                    submission
                )
            )

        else:

            submission.result_options = []

    # ========================================================
    # SUMMARY
    # ========================================================

    total_questions = submissions.count()

    correct_count = 0

    incorrect_count = 0

    unanswered_count = 0

    pending_count = 0

    for submission in submissions:

        has_answer = bool(
            submission.answer_text
            and submission.answer_text.strip()
        ) or bool(
            submission.answer_file
        )

        if not has_answer:

            unanswered_count += 1

            continue

        if not submission.is_evaluated:

            pending_count += 1

            continue

        if (
            submission.marks_obtained
            == submission.question.marks
        ):

            correct_count += 1

        else:

            incorrect_count += 1

    # ========================================================
    # ATTEMPTED
    # ========================================================

    attempted_count = (
        total_questions
        - unanswered_count
    )

    # ========================================================
    # PERCENTAGE
    # ========================================================

    if exam.total_marks > 0:

        percentage = (
            result.total_score
            / exam.total_marks
        ) * 100

    else:

        percentage = 0

    percentage = round(
        percentage,
        2
    )

    # ========================================================
    # ACCURACY
    # ========================================================

    if attempted_count > 0:

        accuracy = (
            correct_count
            / attempted_count
        ) * 100

    else:

        accuracy = 0

    accuracy = round(
        accuracy,
        2
    )

    # ========================================================
    # PERFORMANCE LEVEL
    # ========================================================

    if percentage >= 90:

        performance_level = "Excellent"

    elif percentage >= 75:

        performance_level = "Very Good"

    elif percentage >= 60:

        performance_level = "Good"

    elif percentage >= 40:

        performance_level = "Needs Improvement"

    else:

        performance_level = (
            "Requires Significant Improvement"
        )

    # ========================================================
    # PERFORMANCE FEEDBACK
    # ========================================================

    if performance_level == "Excellent":

        performance_feedback = (
            "Excellent performance. You have "
            "demonstrated a strong understanding "
            "of the concepts assessed in this "
            "examination. Continue challenging "
            "yourself with application-based and "
            "higher-order problems."
        )

    elif performance_level == "Very Good":

        performance_feedback = (
            "Very good performance. You have "
            "demonstrated a strong grasp of the "
            "major concepts. Review the questions "
            "answered incorrectly and continue "
            "practicing application-based problems."
        )

    elif performance_level == "Good":

        performance_feedback = (
            "Good performance. You have developed "
            "a reasonable understanding of the "
            "concepts. Review the questions answered "
            "incorrectly and reinforce the underlying "
            "concepts through additional practice."
        )

    elif performance_level == "Needs Improvement":

        performance_feedback = (
            "Some improvement is required. Review "
            "the fundamental concepts associated "
            "with the questions you found difficult "
            "and practice additional problems before "
            "attempting more advanced questions."
        )

    else:

        performance_feedback = (
            "Significant improvement is required. "
            "Revisit the fundamental concepts "
            "covered in the examination and work "
            "through basic problems systematically. "
            "After strengthening the fundamentals, "
            "practice progressively more challenging "
            "questions."
        )

    # ========================================================
    # RESULT ID
    # ========================================================

    result_id = (
        f"RESULT-{result.id:05d}"
    )

    # ========================================================
    # INSTRUCTOR FEEDBACK
    # ========================================================

    instructor_feedback = getattr(
        exam,
        "instructor_feedback",
        ""
    )

    # ========================================================
    # RENDER
    # ========================================================

    return render(
        request,
        "result.html",
        {
            "exam":
                exam,

            "result":
                result,

            "submissions":
                submissions,

            "total_questions":
                total_questions,

            "attempted_count":
                attempted_count,

            "correct_count":
                correct_count,

            "incorrect_count":
                incorrect_count,

            "unanswered_count":
                unanswered_count,

            "pending_count":
                pending_count,

            "percentage":
                percentage,

            "accuracy":
                accuracy,

            "performance_level":
                performance_level,

            "performance_feedback":
                performance_feedback,

            "result_id":
                result_id,

            "instructor_feedback":
                instructor_feedback,
        }
    )


# ============================================================
# EXAM ANALYTICS
# MCQ + MULTIPLE CORRECT ONLY
# ============================================================

@login_required
def exam_analytics_view(request, exam_id):

    # ========================================================
    # STAFF ONLY
    # ========================================================

    if not request.user.is_staff:

        return render(
            request,
            "message.html",
            {
                "title":
                    "Access Denied",

                "message": (
                    "You do not have permission to "
                    "view examination analytics."
                )
            }
        )

    exam = get_object_or_404(
        Exam,
        id=exam_id
    )

    results = Result.objects.filter(
        exam=exam
    ).select_related(
        "student"
    ).order_by(
        "-total_score"
    )

    # ========================================================
    # BASIC STATISTICS
    # ========================================================

    total_students = results.count()

    total_marks = exam.total_marks

    total_score = 0

    highest_score = 0

    lowest_score = 0

    for result in results:

        score = result.total_score or 0

        total_score += score

        if score > highest_score:

            highest_score = score

        if lowest_score is None:

            lowest_score = score

        elif score < lowest_score:

            lowest_score = score

    # ========================================================
    # AVERAGE
    # ========================================================

    if total_students > 0:

        average_score = (
            total_score
            / total_students
        )

    else:

        average_score = 0

    average_score = round(
        average_score,
        2
    )

    # ========================================================
    # AVERAGE PERCENTAGE
    # ========================================================

    if total_marks > 0:

        average_percentage = (
            average_score
            / total_marks
        ) * 100

    else:

        average_percentage = 0

    average_percentage = round(
        average_percentage,
        2
    )

    # ========================================================
    # HIGHEST / LOWEST PERCENTAGE
    # ========================================================

    if total_marks > 0:

        highest_percentage = (
            highest_score
            / total_marks
        ) * 100

        if lowest_score is not None:

            lowest_percentage = (
                lowest_score
                / total_marks
            ) * 100

        else:

            lowest_percentage = 0

    else:

        highest_percentage = 0

        lowest_percentage = 0

    highest_percentage = round(
        highest_percentage,
        2
    )

    lowest_percentage = round(
        lowest_percentage,
        2
    )

    # ========================================================
    # QUESTION ANALYTICS
    # ========================================================

    question_analytics = []

    questions = exam.questions.filter(
        question_type__in=[
            "MCQ",
            "MULTI"
        ]
    ).order_by(
        "id"
    )

    for question in questions:

        submissions = Submission.objects.filter(
            exam=exam,
            question=question
        )

        correct_count = 0

        incorrect_count = 0

        unanswered_count = 0

        option1_count = 0

        option2_count = 0

        option3_count = 0

        option4_count = 0

        # ====================================================
        # CORRECT OPTIONS
        # ====================================================

        correct_options = (
            get_correct_option_numbers(
                question
            )
        )

        option1_correct = (
            "1" in correct_options
        )

        option2_correct = (
            "2" in correct_options
        )

        option3_correct = (
            "3" in correct_options
        )

        option4_correct = (
            "4" in correct_options
        )

        # ====================================================
        # PROCESS SUBMISSIONS
        # ====================================================

        for submission in submissions:

            raw_answer = (
                submission.answer_text
                if submission.answer_text
                else ""
            )

            raw_answer = raw_answer.strip()

            if not raw_answer:

                unanswered_count += 1

                continue

            if (
                submission.is_evaluated
                and
                submission.marks_obtained
                == question.marks
            ):

                correct_count += 1

            else:

                incorrect_count += 1

            # ----------------------------------------------
            # SELECTED OPTIONS
            # ----------------------------------------------

            selected_options = (
                get_selected_option_numbers(
                    question,
                    raw_answer
                )
            )

            if "1" in selected_options:

                option1_count += 1

            if "2" in selected_options:

                option2_count += 1

            if "3" in selected_options:

                option3_count += 1

            if "4" in selected_options:

                option4_count += 1

        # ====================================================
        # COUNTS
        # ====================================================

        total_submissions = submissions.count()

        attempted_count = (
            total_submissions
            - unanswered_count
        )

        # ====================================================
        # SUCCESS RATE
        # ====================================================

        if attempted_count > 0:

            success_rate = (
                correct_count
                / attempted_count
            ) * 100

        else:

            success_rate = 0

        success_rate = round(
            success_rate,
            2
        )

        # ====================================================
        # STORE
        # ====================================================

        question_analytics.append(
            {
                "question":
                    question,

                "total_submissions":
                    total_submissions,

                "correct_count":
                    correct_count,

                "incorrect_count":
                    incorrect_count,

                "unanswered_count":
                    unanswered_count,

                "attempted_count":
                    attempted_count,

                "success_rate":
                    success_rate,

                "option1_count":
                    option1_count,

                "option2_count":
                    option2_count,

                "option3_count":
                    option3_count,

                "option4_count":
                    option4_count,

                "option1_correct":
                    option1_correct,

                "option2_correct":
                    option2_correct,

                "option3_correct":
                    option3_correct,

                "option4_correct":
                    option4_correct,
            }
        )

    # ========================================================
    # RENDER
    # ========================================================

    return render(
        request,
        "exam_analytics.html",
        {
            "exam":
                exam,

            "total_students":
                total_students,

            "average_score":
                average_score,

            "average_percentage":
                average_percentage,

            "highest_score":
                highest_score,

            "highest_percentage":
                highest_percentage,

            "lowest_score":
                lowest_score,

            "lowest_percentage":
                lowest_percentage,

            "total_marks":
                total_marks,

            "question_analytics":
                question_analytics,

            "results":
                results,
        }
    )
# ============================================================
# INSTRUCTOR DASHBOARD
# ============================================================

@login_required
def instructor_dashboard_view(request):

    # --------------------------------------------------------
    # STAFF / INSTRUCTOR ONLY
    # --------------------------------------------------------

    if not request.user.is_staff:

        return render(
            request,
            "message.html",
            {
                "title": "Access Denied",

                "message": (
                    "You do not have permission to "
                    "access the instructor dashboard."
                )
            }
        )

    # --------------------------------------------------------
    # CURRENT TIME
    # --------------------------------------------------------

    current_time = timezone.localtime()

    # --------------------------------------------------------
    # ALL EXAMS
    # --------------------------------------------------------

    exams = Exam.objects.all().order_by("-id")

    # --------------------------------------------------------
    # DASHBOARD COUNTERS
    # --------------------------------------------------------

    total_exams = exams.count()

    active_count = 0
    upcoming_count = 0
    completed_count = 0

    # --------------------------------------------------------
    # EXAM DATA
    # --------------------------------------------------------

    dashboard_exams = []

    # --------------------------------------------------------
    # PROCESS EACH EXAM
    # --------------------------------------------------------

    for exam in exams:

        # ====================================================
        # RESULT / SCORE INFORMATION
        # ====================================================

        results = Result.objects.filter(
            exam=exam
        )

        student_count = results.count()

        scores = list(
            results.values_list(
                "total_score",
                flat=True
            )
        )

        if scores:

            average_score = (
                sum(scores) / len(scores)
            )

            highest_score = max(scores)

        else:

            average_score = 0
            highest_score = 0

        average_score = round(
            average_score,
            2
        )

        highest_score = round(
            highest_score,
            2
        )

        # ====================================================
        # PERCENTAGE
        # ====================================================

        if exam.total_marks > 0:

            average_percentage = (
                average_score
                / exam.total_marks
            ) * 100

            highest_percentage = (
                highest_score
                / exam.total_marks
            ) * 100

        else:

            average_percentage = 0
            highest_percentage = 0

        average_percentage = round(
            average_percentage,
            2
        )

        highest_percentage = round(
            highest_percentage,
            2
        )

        # ====================================================
        # EXAM STATUS
        # ====================================================

        if (
            exam.start_time
            and
            current_time < exam.start_time
        ):

            status = "UPCOMING"
            status_label = "Upcoming"

            upcoming_count += 1

        elif (
            exam.end_time
            and
            current_time > exam.end_time
        ):

            status = "COMPLETED"
            status_label = "Completed"

            completed_count += 1

        else:

            status = "ACTIVE"
            status_label = "Active"

            active_count += 1

        # ====================================================
        # SECURITY & MONITORING
        # ====================================================

        attempts = ExamAttempt.objects.filter(
            exam=exam
        )

        # ----------------------------------------------------
        # TOTAL ATTEMPTS
        # ----------------------------------------------------

        total_attempts = attempts.count()

        # ----------------------------------------------------
        # NORMAL SUBMISSIONS
        # ----------------------------------------------------

        normal_submissions = attempts.filter(
            status="SUBMITTED"
        ).count()

        # ----------------------------------------------------
        # AUTO SUBMISSIONS
        # ----------------------------------------------------

        auto_submissions = attempts.filter(
            status="AUTO_SUBMITTED"
        ).count()

        # ----------------------------------------------------
        # TERMINATED ATTEMPTS
        # ----------------------------------------------------

        terminated_attempts = attempts.filter(
            status="TERMINATED"
        ).count()

        # ----------------------------------------------------
        # TOTAL VIOLATIONS
        # ----------------------------------------------------

        total_violations = sum(
            attempts.values_list(
                "violation_count",
                flat=True
            )
        )

        # ====================================================
        # STORE EXAM DATA
        # ====================================================

        dashboard_exams.append(
            {
                # --------------------------------------------
                # EXISTING DATA
                # --------------------------------------------

                "exam":
                    exam,

                "student_count":
                    student_count,

                "average_score":
                    average_score,

                "average_percentage":
                    average_percentage,

                "highest_score":
                    highest_score,

                "highest_percentage":
                    highest_percentage,

                "status":
                    status,

                "status_label":
                    status_label,

                # --------------------------------------------
                # SECURITY DATA
                # --------------------------------------------

                "total_attempts":
                    total_attempts,

                "normal_submissions":
                    normal_submissions,

                "auto_submissions":
                    auto_submissions,

                "terminated_attempts":
                    terminated_attempts,

                "total_violations":
                    total_violations,
            }
        )

    # --------------------------------------------------------
    # RENDER
    # --------------------------------------------------------

    return render(
        request,
        "instructor_dashboard.html",
        {
            "dashboard_exams":
                dashboard_exams,

            "total_exams":
                total_exams,

            "active_count":
                active_count,

            "upcoming_count":
                upcoming_count,

            "completed_count":
                completed_count,
        }
    )
