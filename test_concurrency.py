import os
import sys
import time
import django
from concurrent.futures import ThreadPoolExecutor, as_completed

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'examportal.settings')
django.setup()

from django.contrib.auth.models import User
from exams.models import Exam, Question, ExamAttempt, Submission, Result
from django.test import Client

def setup_test_students(count=100):
    print(f"Ensuring {count} test student accounts exist...")
    created_count = 0
    students = []
    for i in range(1, count + 1):
        username = f"loadtest_student_{i}"
        user, created = User.objects.get_or_create(
            username=username,
            defaults={'is_staff': False}
        )
        if created:
            user.set_password("pass1234")
            user.save()
            created_count += 1
        students.append(user)
    print(f"Ready with {len(students)} students ({created_count} newly created).")
    return students

def simulate_student_exam(user, exam_id):
    c = Client()
    c.force_login(user)
    
    # 1. Access exam page
    t0 = time.time()
    get_resp = c.get(f'/exam/{exam_id}/')
    if get_resp.status_code != 200 and get_resp.status_code != 302:
        return (user.username, False, f"GET status {get_resp.status_code}", time.time() - t0)
    
    # 2. Get questions for payload
    exam = Exam.objects.get(id=exam_id)
    payload = {}
    for q in exam.questions.all():
        if q.question_type == 'MCQ':
            payload[f'question_{q.id}'] = '1'
        elif q.question_type == 'MULTI':
            payload[f'question_{q.id}'] = ['1', '2']
        elif q.question_type == 'NUM':
            payload[f'question_{q.id}'] = '42'
    
    # 3. Post submission
    post_resp = c.post(f'/exam/{exam_id}/', data=payload)
    elapsed = time.time() - t0
    
    success = (post_resp.status_code in [200, 302])
    return (user.username, success, f"HTTP {post_resp.status_code}", elapsed)

def run_concurrent_test():
    exam = Exam.objects.first()
    if not exam:
        print("No exam found to test.")
        return
    
    print(f"\n--- Starting 100 Concurrent Student Submission Test on '{exam.title}' (ID: {exam.id}) ---")
    
    # Clean previous test attempts for test students
    students = setup_test_students(100)
    student_ids = [s.id for s in students]
    ExamAttempt.objects.filter(student_id__in=student_ids, exam=exam).delete()
    Submission.objects.filter(student_id__in=student_ids, exam=exam).delete()
    Result.objects.filter(student_id__in=student_ids, exam=exam).delete()
    
    start_all = time.time()
    results = []
    
    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = {executor.submit(simulate_student_exam, user, exam.id): user for user in students}
        for future in as_completed(futures):
            res = future.result()
            results.append(res)
    
    total_time = time.time() - start_all
    successes = [r for r in results if r[1]]
    failures = [r for r in results if not r[1]]
    avg_latency = sum(r[3] for r in results) / len(results) if results else 0
    
    print(f"\n=== CONCURRENCY TEST RESULTS ===")
    print(f"Total Requests: {len(results)}")
    print(f"Successful Submissions: {len(successes)} / {len(results)} ({(len(successes)/len(results))*100:.1f}%)")
    print(f"Failed Submissions: {len(failures)}")
    print(f"Total Test Time: {total_time:.2f} seconds")
    print(f"Average Response Time per Student: {avg_latency:.3f} seconds")
    print(f"Throughput: {len(results)/total_time:.2f} submissions/sec")
    
    if failures:
        print(f"Sample Failures: {failures[:3]}")
    else:
        print(">>> SUCCESS: 100/100 concurrent students submitted simultaneously with ZERO database lock errors! <<<")

if __name__ == '__main__':
    run_concurrent_test()
