"""
Question Importer — Import questions from CSV into an Exam.

Usage:
    python import_questions.py <exam_id> <csv_file>

Example:
    python import_questions.py 1 questions.csv

CSV Format:
    Question Text, Option A, Option B, Option C, Option D, Correct Answer (1-4), Marks
"""

import os
import sys
import csv
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'examportal.settings')
django.setup()

from exams.models import Exam, Question


def import_questions(exam_id, csv_path):
    # Validate exam exists
    try:
        exam = Exam.objects.get(id=exam_id)
    except Exam.DoesNotExist:
        print(f"\n  ERROR: Exam with ID {exam_id} not found!")
        print(f"\n  Available exams:")
        for e in Exam.objects.all():
            print(f"    ID={e.id}  Title=\"{e.title}\"")
        sys.exit(1)

    # Validate CSV exists
    if not os.path.exists(csv_path):
        print(f"\n  ERROR: File '{csv_path}' not found!")
        sys.exit(1)

    print(f"\n{'='*60}")
    print(f"  Question Importer")
    print(f"{'='*60}")
    print(f"  Exam:  {exam.title} (ID={exam.id})")
    print(f"  File:  {csv_path}")
    print(f"{'='*60}\n")

    # Read CSV
    questions_added = 0
    questions_skipped = 0
    errors = []

    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        header = next(reader, None)  # Skip header row

        if header is None:
            print("  ERROR: CSV file is empty!")
            sys.exit(1)

        for row_num, row in enumerate(reader, start=2):
            # Skip empty rows
            if not row or all(cell.strip() == '' for cell in row):
                continue

            # Validate column count
            if len(row) < 7:
                errors.append(f"  Row {row_num}: Expected 7 columns, got {len(row)} — SKIPPED")
                questions_skipped += 1
                continue

            question_text = row[0].strip()
            option1 = row[1].strip()
            option2 = row[2].strip()
            option3 = row[3].strip()
            option4 = row[4].strip()

            try:
                correct_answer = int(row[5].strip())
            except ValueError:
                errors.append(f"  Row {row_num}: Correct Answer '{row[5]}' is not a number (1-4) — SKIPPED")
                questions_skipped += 1
                continue

            if correct_answer not in [1, 2, 3, 4]:
                errors.append(f"  Row {row_num}: Correct Answer must be 1-4, got {correct_answer} — SKIPPED")
                questions_skipped += 1
                continue

            try:
                marks = float(row[6].strip())
            except ValueError:
                errors.append(f"  Row {row_num}: Marks '{row[6]}' is not a number — SKIPPED")
                questions_skipped += 1
                continue

            if not question_text:
                errors.append(f"  Row {row_num}: Question text is empty — SKIPPED")
                questions_skipped += 1
                continue

            # Create question
            Question.objects.create(
                exam=exam,
                question_type='MCQ',
                question_text=question_text,
                option1=option1,
                option2=option2,
                option3=option3,
                option4=option4,
                correct_answer=str(correct_answer),
                marks=marks,
            )
            questions_added += 1
            print(f"  ✓ Q{questions_added}: {question_text[:60]}...")

    print(f"\n{'='*60}")
    print(f"  RESULTS")
    print(f"{'='*60}")
    print(f"  ✅ Questions added:   {questions_added}")
    print(f"  ⚠  Questions skipped: {questions_skipped}")
    print(f"  📝 Total in exam:     {exam.questions.count()}")
    print(f"{'='*60}")

    if errors:
        print(f"\n  Errors:")
        for err in errors:
            print(err)

    if questions_added > 0:
        # Update total marks
        total = sum(exam.questions.values_list('marks', flat=True))
        exam.total_marks = total
        exam.save()
        print(f"\n  📊 Exam total marks auto-updated to: {total}")

    print(f"\n  Done! Go to http://127.0.0.1:8000/admin/exams/exam/{exam.id}/change/ to review.\n")


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print(__doc__)
        print("  Available exams:")
        for e in Exam.objects.all():
            print(f"    ID={e.id}  Title=\"{e.title}\"")
        sys.exit(0)

    import_questions(
        exam_id=int(sys.argv[1]),
        csv_path=sys.argv[2]
    )
