from django.db import models
from django.contrib.auth.models import User


# ============================================================
# Exam model
# ============================================================

class Exam(models.Model):

    title = models.CharField(max_length=200)

    description = models.TextField(
        blank=True,
        null=True
    )

    total_marks = models.IntegerField()

    duration = models.IntegerField(
        help_text="Duration in minutes"
    )

    start_time = models.DateTimeField(
        blank=True,
        null=True
    )

    end_time = models.DateTimeField(
        blank=True,
        null=True
    )

    # Instructor's suggestions / feedback
    # displayed to the student on the result page
    instructor_feedback = models.TextField(
        blank=True,
        null=True,
        help_text="Instructor's suggestions displayed on the result page"
    )

    def __str__(self):
        return self.title


# ============================================================
# Question model
# ============================================================

class Question(models.Model):

    QUESTION_TYPES = [
        ('MCQ', 'Single Correct MCQ'),
        ('MULTI', 'Multiple Correct'),
        ('NUM', 'Numerical'),
        ('SHORT', 'Short Answer'),
        ('LONG', 'Long Answer'),
        ('UPLOAD', 'Upload Answer'),
    ]

    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name="questions"
    )

    question_type = models.CharField(
        max_length=10,
        choices=QUESTION_TYPES,
        default='MCQ'
    )

    question_text = models.TextField(
        help_text="Supports LaTeX"
    )

    question_image = models.ImageField(
        upload_to='question_images/',
        blank=True,
        null=True
    )

    marks = models.IntegerField(
        default=1
    )

    # --------------------------------------------------------
    # Text / LaTeX options
    # --------------------------------------------------------

    option1 = models.TextField(
        blank=True,
        null=True
    )

    option2 = models.TextField(
        blank=True,
        null=True
    )

    option3 = models.TextField(
        blank=True,
        null=True
    )

    option4 = models.TextField(
        blank=True,
        null=True
    )

    # --------------------------------------------------------
    # Image options
    # --------------------------------------------------------

    option1_image = models.ImageField(
        upload_to='option_images/',
        blank=True,
        null=True
    )

    option2_image = models.ImageField(
        upload_to='option_images/',
        blank=True,
        null=True
    )

    option3_image = models.ImageField(
        upload_to='option_images/',
        blank=True,
        null=True
    )

    option4_image = models.ImageField(
        upload_to='option_images/',
        blank=True,
        null=True
    )

    # --------------------------------------------------------
    # Correct answer
    #
    # MCQ   -> one answer
    # MULTI -> comma separated answers
    # NUM   -> numerical answer
    # SHORT/LONG -> optional model answer
    # --------------------------------------------------------

    correct_answer = models.TextField(
        blank=True,
        null=True
    )

    # --------------------------------------------------------
    # Explanation shown after submission
    # --------------------------------------------------------

    explanation = models.TextField(
        blank=True,
        null=True,
        help_text="Explanation shown to the student after submission"
    )

    # --------------------------------------------------------
    # Numerical tolerance
    # --------------------------------------------------------

    tolerance = models.FloatField(
        blank=True,
        null=True,
        help_text="For numerical answer"
    )

    def __str__(self):
        return f"{self.exam.title} - Q{self.id}"


# ============================================================
# Student submissions
# ============================================================

class Submission(models.Model):

    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE
    )

    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE
    )

    # --------------------------------------------------------
    # Text / selected answer
    # --------------------------------------------------------

    answer_text = models.TextField(
        blank=True,
        null=True
    )

    # --------------------------------------------------------
    # File upload answer
    # --------------------------------------------------------

    answer_file = models.FileField(
        upload_to='student_submissions/',
        blank=True,
        null=True
    )

    submitted_at = models.DateTimeField(
        auto_now_add=True
    )

    is_evaluated = models.BooleanField(
        default=False
    )

    marks_obtained = models.FloatField(
        default=0
    )

    def __str__(self):
        return f"{self.student.username} - Q{self.question.id}"


# ============================================================
# Final result
# ============================================================

class Result(models.Model):

    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE
    )

    total_score = models.FloatField(
        default=0
    )

    submitted_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.student.username} - {self.exam.title}"


# ============================================================
# Student exam attempt
# ============================================================

class ExamAttempt(models.Model):

    STATUS_CHOICES = [
        ('IN_PROGRESS', 'In Progress'),
        ('SUBMITTED', 'Submitted'),
        ('AUTO_SUBMITTED', 'Auto Submitted'),
        ('TERMINATED', 'Terminated'),
    ]

    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE
    )

    started_at = models.DateTimeField(
        auto_now_add=True
    )

    submitted_at = models.DateTimeField(
        blank=True,
        null=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='IN_PROGRESS'
    )

    # --------------------------------------------------------
    # Number of times the student leaves the exam window
    # --------------------------------------------------------

    violation_count = models.PositiveIntegerField(
        default=0
    )

    first_violation_at = models.DateTimeField(
        blank=True,
        null=True
    )

    second_violation_at = models.DateTimeField(
        blank=True,
        null=True
    )

    terminated_at = models.DateTimeField(
        blank=True,
        null=True
    )

    def __str__(self):
        return (
            f"{self.student.username} - "
            f"{self.exam.title} - "
            f"{self.status}"
        )