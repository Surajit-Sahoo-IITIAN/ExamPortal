import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'examportal.settings')
django.setup()

from django.contrib.auth import authenticate

test_cases = [
    'roll_01',
    'ROLL_01',
    'Roll_01',
    'rOlL_01',
    '  roll_01  ',
    'roll_15',
    'ROLL_15',
    'roll_70',
    'ROLL_70',
    '  Roll_70  '
]

print("=" * 60)
print("  CASE-INSENSITIVE AUTHENTICATION VERIFICATION")
print("=" * 60)

for case in test_cases:
    user = authenticate(username=case, password='student123')
    status = f"PASS -> Matched '{user.username}'" if user else "FAIL"
    print(f"  Input: {repr(case):<20} => {status}")
    assert user is not None, f"Failed for {case}"

print("=" * 60)
print("  ALL 9 CASE-INSENSITIVE LOGIN TESTS PASSED!")
print("=" * 60)
