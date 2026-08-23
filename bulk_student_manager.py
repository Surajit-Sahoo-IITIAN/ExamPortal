import os
import sys
import csv
import django
import random
import string

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'examportal.settings')
django.setup()

from django.contrib.auth.models import User

def generate_random_password(length=6):
    """Generate a simple, student-friendly alphanumeric password (e.g. math24, pass89)."""
    chars = string.ascii_lowercase + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

def bulk_generate_students(count=70, prefix="ROLL_", password_mode="default", default_pass="student123", output_csv="students_credentials.csv"):
    """
    Generate student accounts in bulk and export credentials to CSV.
    
    password_mode:
        'default': All students get the same password (e.g., student123)
        'random': Each student gets a unique secure password
    """
    print(f"\n=======================================================")
    print(f"  Generating {count} Student Accounts (Prefix: '{prefix}')")
    print(f"=======================================================")
    
    credentials = []
    created_count = 0
    updated_count = 0
    
    for i in range(1, count + 1):
        username = f"{prefix}{i:02d}"  # Format as ROLL_01, ROLL_02 ... ROLL_70
        
        if password_mode == "random":
            password = generate_random_password(6)
        else:
            password = default_pass
            
        user, created = User.objects.get_or_create(
            username=username,
            defaults={'is_staff': False, 'is_superuser': False}
        )
        
        user.set_password(password)
        user.is_staff = False
        user.save()
        
        if created:
            created_count += 1
        else:
            updated_count += 1
            
        credentials.append({
            'Roll Number / Username': username,
            'Password': password,
            'Role': 'Student'
        })
    
    # Export credentials to CSV file
    with open(output_csv, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['Roll Number / Username', 'Password', 'Role'])
        writer.writeheader()
        writer.writerows(credentials)
        
    print(f"\n Successfully processed {count} students:")
    print(f"   - Newly Created: {created_count}")
    print(f"   - Updated/Reset: {updated_count}")
    print(f"\n Credentials exported to: {os.path.abspath(output_csv)}")
    print(f"   (You can open this CSV in Excel, print it, or share credentials with students!)")
    print(f"=======================================================\n")

def import_students_from_csv(csv_filepath):
    """
    Import student accounts from a CSV file.
    Expected CSV columns: username, password (or name, roll_number, password)
    """
    if not os.path.exists(csv_filepath):
        print(f"Error: File not found at '{csv_filepath}'")
        return
        
    print(f"\nImporting students from {csv_filepath}...")
    imported_count = 0
    
    with open(csv_filepath, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Flexible column lookup
            username = row.get('username') or row.get('Username') or row.get('Roll Number') or row.get('roll_number')
            password = row.get('password') or row.get('Password') or 'student123'
            
            if not username:
                continue
                
            username = username.strip()
            password = password.strip()
            
            user, created = User.objects.get_or_create(
                username=username,
                defaults={'is_staff': False}
            )
            user.set_password(password)
            user.is_staff = False
            user.save()
            imported_count += 1
            
    print(f" Successfully imported/updated {imported_count} students from CSV.\n")

if __name__ == '__main__':
    # Default execution: generates 70 students ROLL_01 to ROLL_70 with default password
    count = 70
    if len(sys.argv) > 1:
        try:
            count = int(sys.argv[1])
        except ValueError:
            pass
            
    bulk_generate_students(count=count, prefix="ROLL_", password_mode="default", default_pass="student123")
