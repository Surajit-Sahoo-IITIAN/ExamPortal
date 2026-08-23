"""
PDF Question Extractor & Importer

Extracts multiple-choice questions (MCQs) from a PDF file and:
1. Exports them directly to a CSV (`extracted_questions.csv`) for quick review/edit.
2. OR directly imports them into a Django Exam if answers and options are found!

Usage:
    # Option 1: Extract from PDF and convert to editable CSV
    python import_from_pdf.py --pdf my_exam.pdf --to-csv my_questions.csv

    # Option 2: Directly extract and import into Exam ID (e.g. Exam 1)
    python import_from_pdf.py --pdf my_exam.pdf --exam-id 1
"""

import os
import sys
import re
import csv
import argparse
from pypdf import PdfReader


def parse_pdf_text(pdf_path):
    if not os.path.exists(pdf_path):
        print(f"\n❌ Error: File '{pdf_path}' not found!")
        sys.exit(1)

    reader = PdfReader(pdf_path)
    full_text = ""
    for page_idx, page in enumerate(reader.pages):
        text = page.extract_text()
        if text:
            full_text += text + "\n"
    return full_text


def extract_questions_from_text(text, default_marks=1.0):
    """
    Regex parser designed to match common question patterns in question papers.
    Matches:
    1. Question text...
       (A) Opt1  (B) Opt2
       (C) Opt3  (D) Opt4
       Answer: B or Ans: (B) or Ans: 2
    """
    # Normalize newlines and spaces
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    full_str = "\n".join(lines)

    # Split by Question markers: e.g. "1.", "1)", "Q1.", "Q.1", "Question 1"
    q_split_pattern = r'(?:^|\n)(?:Q(?:uestion)?\.?\s*)?(\d+)[\.\)\:\-]\s*'
    chunks = re.split(q_split_pattern, "\n" + full_str)

    questions = []
    if len(chunks) > 1:
        # chunks will be [prefix, q_num1, content1, q_num2, content2, ...]
        for i in range(1, len(chunks), 2):
            q_num = chunks[i]
            q_body = chunks[i+1].strip()

            q_data = parse_question_chunk(q_body, q_num, default_marks)
            if q_data:
                questions.append(q_data)
    else:
        # Fallback: line-by-line heuristic
        print("  Notice: Numbered questions format not directly segmented, attempting line scan...")
        # fallback parsing
        pass

    return questions


def parse_question_chunk(chunk, q_num, default_marks=1.0):
    # Search for Answer line if available
    ans_match = re.search(r'(?:Ans(?:wer)?|Correct\s*(?:Option|Ans)?)\s*[:\-\=]?\s*\(?([A-Da-d1-4])\)?', chunk, re.IGNORECASE)
    correct_ans = "1"
    if ans_match:
        val = ans_match.group(1).upper()
        mapping = {'A': '1', 'B': '2', 'C': '3', 'D': '4', '1': '1', '2': '2', '3': '3', '4': '4'}
        correct_ans = mapping.get(val, '1')
        # Remove answer line from chunk
        chunk = chunk[:ans_match.start()].strip()

    # Search for options A, B, C, D
    # Matches (A) / A. / A) / [A]
    opt_pattern = r'(?:\(([A-Da-d])\)|(?:\b|^)([A-Da-d])[\.\)\:\-])\s*'
    opt_splits = re.split(opt_pattern, chunk)

    if len(opt_splits) >= 9:
        # Structure: [q_text, opt_letter1, opt_letter2_alt, opt1_text, ...]
        # Let's extract carefully
        q_text = opt_splits[0].strip()
        opts = []
        i = 1
        while i < len(opt_splits):
            letter = opt_splits[i] or opt_splits[i+1]
            opt_text = opt_splits[i+2].strip() if i+2 < len(opt_splits) else ""
            opts.append(opt_text)
            i += 3

        opt1 = opts[0] if len(opts) > 0 else ""
        opt2 = opts[1] if len(opts) > 1 else ""
        opt3 = opts[2] if len(opts) > 2 else ""
        opt4 = opts[3] if len(opts) > 3 else ""

        return {
            'q_num': q_num,
            'question_text': q_text,
            'option1': opt1,
            'option2': opt2,
            'option3': opt3,
            'option4': opt4,
            'correct_answer': correct_ans,
            'marks': default_marks
        }
    else:
        # Fallback: Put entire chunk as question text
        return {
            'q_num': q_num,
            'question_text': chunk,
            'option1': '',
            'option2': '',
            'option3': '',
            'option4': '',
            'correct_answer': correct_ans,
            'marks': default_marks
        }


def save_to_csv(questions, output_csv):
    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Question Text', 'Option A', 'Option B', 'Option C', 'Option D', 'Correct Answer', 'Marks'])
        for q in questions:
            writer.writerow([
                q['question_text'],
                q['option1'],
                q['option2'],
                q['option3'],
                q['option4'],
                q['correct_answer'],
                q['marks']
            ])
    print(f"\n✅ Extracted {len(questions)} questions into '{output_csv}'!")
    print(f"👉 You can open '{output_csv}' in Excel, review/verify answers, then run:")
    print(f"   python import_questions.py <exam_id> {output_csv}\n")


def import_directly_to_exam(questions, exam_id):
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'examportal.settings')
    import django
    django.setup()
    from exams.models import Exam, Question

    try:
        exam = Exam.objects.get(id=exam_id)
    except Exam.DoesNotExist:
        print(f"\n❌ Error: Exam with ID {exam_id} does not exist!")
        return

    added = 0
    for q in questions:
        Question.objects.create(
            exam=exam,
            question_type='MCQ',
            question_text=q['question_text'],
            option1=q['option1'],
            option2=q['option2'],
            option3=q['option3'],
            option4=q['option4'],
            correct_answer=q['correct_answer'],
            marks=q['marks']
        )
        added += 1

    total = sum(exam.questions.values_list('marks', flat=True))
    exam.total_marks = total
    exam.save()

    print(f"\n✅ Successfully imported {added} questions directly into '{exam.title}' (ID {exam.id})!")
    print(f"📊 Exam Total Marks: {total}")
    print(f"🌐 Review at: http://127.0.0.1:8000/admin/exams/exam/{exam.id}/change/\n")


def main():
    parser = argparse.ArgumentParser(description="Extract MCQ Questions from PDF")
    parser.add_argument('--pdf', required=True, help="Path to the PDF file")
    parser.add_argument('--to-csv', help="Export extracted questions to a CSV file (recommended)")
    parser.add_argument('--exam-id', type=int, help="Directly import into a Django Exam by ID")
    parser.add_argument('--marks', type=float, default=1.0, help="Default marks per question (default: 1.0)")

    args = parser.parse_args()

    print(f"📄 Reading PDF: {args.pdf} ...")
    raw_text = parse_pdf_text(args.pdf)
    print(f"🔍 Extracting questions and options...")
    questions = extract_questions_from_text(raw_text, default_marks=args.marks)

    if not questions:
        print("⚠️ No structured questions could be automatically identified from this PDF layout.")
        print("Tip: Use the CSV template `questions_template.csv` or check PDF text formatting.")
        return

    print(f"🎯 Found {len(questions)} questions in PDF!")

    if args.to_csv:
        save_to_csv(questions, args.to_csv)
    elif args.exam_id:
        import_directly_to_exam(questions, args.exam_id)
    else:
        # Default action: save to extracted_questions.csv
        out_csv = "extracted_questions.csv"
        save_to_csv(questions, out_csv)


if __name__ == '__main__':
    main()
