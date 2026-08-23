"""
Automatic Database Seeder for Production Deployments
Seeds Superuser and 100 Student accounts securely without needing public CSV files.
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'examportal.settings')
django.setup()

from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password

STUDENT_CREDENTIALS = {
    'ROLL_01': 'ijefau',
    'ROLL_02': '7q7zsi',
    'ROLL_03': 'npyuap',
    'ROLL_04': 'qmzqp7',
    'ROLL_05': '9s7uzm',
    'ROLL_06': '3c932b',
    'ROLL_07': 'nfv9c9',
    'ROLL_08': '7wdgjp',
    'ROLL_09': 'w32zny',
    'ROLL_10': 'yfc7kt',
    'ROLL_11': 'kjjjui',
    'ROLL_12': 'cs5fkh',
    'ROLL_13': 'hiihx5',
    'ROLL_14': 'dv4gs8',
    'ROLL_15': '9kd8iz',
    'ROLL_16': '9cykv8',
    'ROLL_17': 'vh3d6x',
    'ROLL_18': 'vhqmrc',
    'ROLL_19': 'f76amw',
    'ROLL_20': 'z5sjvx',
    'ROLL_21': 'egykvs',
    'ROLL_22': 'yq82rc',
    'ROLL_23': 'qxe76k',
    'ROLL_24': '6ed4r7',
    'ROLL_25': 'kwkrfu',
    'ROLL_26': 'iei3qm',
    'ROLL_27': 'tk98dq',
    'ROLL_28': 'uer8qn',
    'ROLL_29': 'r6bzkx',
    'ROLL_30': 'twiqhu',
    'ROLL_31': 'cn58f2',
    'ROLL_32': 'fgjkp8',
    'ROLL_33': 'bq3djb',
    'ROLL_34': 'q5bk6j',
    'ROLL_35': 'jmkpuy',
    'ROLL_36': 'fgyvzt',
    'ROLL_37': '38upjy',
    'ROLL_38': '2zbt38',
    'ROLL_39': '2zw6f5',
    'ROLL_40': '9g6ejk',
    'ROLL_41': 'fw3hfw',
    'ROLL_42': 'p6ud5v',
    'ROLL_43': 'tfpebz',
    'ROLL_44': 'fhitrp',
    'ROLL_45': 'aw8qu5',
    'ROLL_46': '6m25cp',
    'ROLL_47': 'f35468',
    'ROLL_48': 'g6cxxe',
    'ROLL_49': 'ctne4v',
    'ROLL_50': 'zcx96j',
    'ROLL_51': 'msdh23',
    'ROLL_52': 'rx49eq',
    'ROLL_53': '7ktime',
    'ROLL_54': 'jb2hpu',
    'ROLL_55': '3memfx',
    'ROLL_56': '2v82n5',
    'ROLL_57': 'na4qgu',
    'ROLL_58': 'm39zdq',
    'ROLL_59': 'nnaife',
    'ROLL_60': 'u479zb',
    'ROLL_61': '659aqn',
    'ROLL_62': 'qhpn39',
    'ROLL_63': 'bg43ac',
    'ROLL_64': '5xdusr',
    'ROLL_65': 'uie2pu',
    'ROLL_66': '74atmg',
    'ROLL_67': 'zjuyua',
    'ROLL_68': 'kgejyq',
    'ROLL_69': 'je497z',
    'ROLL_70': 'b4x2vq',
    'ROLL_71': 'rvihrj',
    'ROLL_72': 'p8jcag',
    'ROLL_73': '9apt78',
    'ROLL_74': 'krzhhz',
    'ROLL_75': 'twvjwu',
    'ROLL_76': 'jqw6zh',
    'ROLL_77': 'sqmi8q',
    'ROLL_78': 'zcvmqk',
    'ROLL_79': 'bm49pr',
    'ROLL_80': '7wac3c',
    'ROLL_81': 'd7qwmp',
    'ROLL_82': 'cxv95s',
    'ROLL_83': 'jhmzcv',
    'ROLL_84': 'ztrhvi',
    'ROLL_85': 'm58eqb',
    'ROLL_86': 'tjwtfm',
    'ROLL_87': 'gykm6v',
    'ROLL_88': 'm4293b',
    'ROLL_89': 'qqrhw5',
    'ROLL_90': '5cpycq',
    'ROLL_91': 'cqvm83',
    'ROLL_92': 'hqtcrt',
    'ROLL_93': 'kvpue3',
    'ROLL_94': 'fzpygz',
    'ROLL_95': 'x9yj63',
    'ROLL_96': 'j92udm',
    'ROLL_97': 'gg9gfn',
    'ROLL_98': 'wjdjn2',
    'ROLL_99': 'y884pq',
    'ROLL_100': 'dpvdgz',
}

def init_db():
    print("=" * 60)
    print("  SEEDING PRODUCTION DATABASE")
    print("=" * 60)

    # 1. Ensure Superuser exists
    admin_user, created = User.objects.get_or_create(
        username='SurajitSahoo',
        defaults={'is_staff': True, 'is_superuser': True}
    )
    admin_user.set_password('admin123')
    admin_user.is_staff = True
    admin_user.is_superuser = True
    admin_user.save()
    print(f"  • Instructor/Admin: SurajitSahoo (Password: admin123) - {'Created' if created else 'Verified'}")

    # 2. Seed 100 Students
    users_to_update = []
    for username, password in STUDENT_CREDENTIALS.items():
        user, _ = User.objects.get_or_create(
            username=username,
            defaults={'is_staff': False, 'is_superuser': False}
        )
        user.password = make_password(password)
        user.is_staff = False
        user.is_superuser = False
        users_to_update.append(user)

    User.objects.bulk_update(users_to_update, ['password', 'is_staff', 'is_superuser'])
    print(f"  • Students Seeded: {len(users_to_update)} accounts verified.")
    print("=" * 60)
    print("  PRODUCTION DATABASE READY!")
    print("=" * 60)

if __name__ == '__main__':
    init_db()
