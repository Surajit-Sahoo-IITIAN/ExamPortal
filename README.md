# 🎓 Modern Online Examination & Assessment Portal

An enterprise-grade, anti-cheat protected **Online Examination & Assessment Portal** built with Django, SQLite WAL Mode (tested for 100+ concurrent students), WhiteNoise, and Waitress/Gunicorn.

---

## 🌟 Key Features

### 🛡️ 1. Multi-Layered Anti-Cheat & Security
- **Tab Switch Detection**: Automatically monitors student tab/window activity via the Page Visibility API.
  - **1st Violation**: Instant warning modal popup (`Violation 1 of 2`).
  - **2nd Violation**: Auto-saves student's answered questions and terminates the exam.
- **Shortcut & DevTools Blocking**: Disables `F12`, `Ctrl+Shift+I`, `Ctrl+Shift+J`, `Ctrl+U`, and Right-Click Context Menu.
- **Accidental Tab Close Protection**: `beforeunload` warning prompts prevent accidental browser closure during live exams.

### 📥 2. PDF & CSV Question Paper Importer (Admin Integrated)
- **PDF Extraction**: Upload a PDF question paper directly in Django Admin (`📥 Import Questions (PDF / CSV)`) — automatically extracts Question Numbers, Options (A, B, C, D), and Answer Keys.
- **CSV Bulk Import**: Upload spreadsheet files (`.csv`) with instant validation and total score computation.
- **Inline Question Editor**: Add and edit all 20+ questions on a single page directly inside the Exam Admin.

### 👥 3. 100-Student Management & Case-Insensitive Auth
- **Bulk Accounts**: Pre-generated student accounts (`ROLL_01` to `ROLL_100`) with unique, private 6-character passwords.
- **Flexible Login**: Case-insensitive authentication (`roll_01`, `ROLL_01`, `Roll_01` all work seamlessly).
- **Credentials Export**: Auto-generated `students_credentials.csv` for easy classroom distribution.

### 📊 4. Real-Time Instructor & Student Dashboards
- **Instructor Analytics**: Live classroom leaderboard, average scores, score distributions, and real-time anti-cheat violation counts.
- **Student Dashboard**: Clean card layout showing exam schedules, duration, status (Available, Submitted, Terminated), and instant result breakdowns.

### ⚡ 5. High-Concurrency Backend (100+ Simultaneous Submissions)
- Configured with **SQLite WAL (Write-Ahead Logging)**, `synchronous=NORMAL`, and a 60-second busy timeout.
- Stress-tested with 100 simultaneous automated submissions with zero database locks.

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.10+
- Git

### 2. Installation
```bash
# Clone the repository
git clone https://github.com/binodbishwakarama-max/examportal.git
cd examportal

# Create and activate virtual environment
python -m venv .venv

# On Windows:
.\.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Database Setup & Static Collection
```bash
python manage.py migrate
python manage.py collectstatic --no-input
```

### 4. Run Development Server
```bash
python manage.py runserver 0.0.0.0:8000
```
Open **http://127.0.0.1:8000/** in your browser.

---

## 🔑 Default Credentials

| Role | Username | Password | Access URL |
| :--- | :--- | :--- | :--- |
| **Instructor / Admin** | `SurajitSahoo` | `admin123` | `/admin/` and `/instructor/dashboard/` |
| **100 Students** | `ROLL_01` to `ROLL_100` | *(See `students_credentials.csv`)* | `/login/` (Student Dashboard) |

---

## ☁️ Deployment on Render.com (100% Free)

1. Fork or push this repository to your GitHub account.
2. Log in to [Render.com](https://render.com) and click **New + ➔ Web Service**.
3. Select your repository `examportal`.
4. Configure:
   - **Environment**: `Python 3`
   - **Build Command**: `./build.sh`
   - **Start Command**: `gunicorn examportal.wsgi:application`
5. Click **Create Web Service**. Your live HTTPS link will be generated automatically!

---

## 🖥️ Local Classroom Hosting (Waitress + ngrok)

For hosting directly from your laptop during a classroom session:

```powershell
# Terminal 1: Launch multi-threaded production WSGI server (16 threads)
python run_production.py

# Terminal 2: Expose to internet via ngrok
ngrok http 8000
```

---

## 🛠️ Tech Stack
- **Backend**: Python, Django 5.x / 6.x
- **WSGI / Production**: Waitress (Windows), Gunicorn (Linux)
- **Static Assets**: WhiteNoise
- **PDF Extraction**: PyPDF
- **Styling**: Modern Vanilla CSS, Google Fonts (Inter & Outfit), Glassmorphism & Responsive Design

---

## 📄 License
This project is open-source under the MIT License.
