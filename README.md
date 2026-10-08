# LibriVerse — Digital Library Portal

> A full-stack Digital Library Portal built with **Django 5**, **Django ORM**, **SQLite (`db.sqlite3`)**, **Bootstrap 5**, **JavaScript (ES6+)**, **WhiteNoise**, and configured for seamless deployment on **Render**.

---

## 1. Project Overview & Features

LibriVerse provides a library management experience for patrons and librarians:
- **Book Catalog & Inventory**: Browse books with covers, genres, ISBNs, descriptions, and dynamic stock badges (*Available: X/Y* or *Checked Out*).
- **JavaScript Instant Search & Filter**: Real-time client-side instant search filtering by Title, Author, Genre, and ISBN without full-page reloads.
- **Circulation & Book Issue Workflow**:
  - Validates inventory before loaning (blocks checkout when available copies = 0).
  - Automatically calculates 14-day default due date (`issue_date + 14 days`).
  - Atomically decrements `available_copies` upon issue.
- **Book Return & Automated Overdue Fine Processing**:
  - Live fine preview as return date is chosen.
  - Calculates overdue charges at **$1.00 per calendar day** past the due date.
  - Automatically increments `available_copies` upon return and marks loans as closed.
- **Member Dashboard & Circulation Log**:
  - Displays currently borrowed books with countdown badges and overdue warnings.
  - Direct 1-click return actions.
  - Complete historical log of returned items and fines paid.
- **Interactive Due-Date & Fine Calculator Tool**:
  - Dedicated interactive simulation utility with loan duration sliders (1–60 days), custom fine rate adjusters, scenario presets (*Exact Due Date*, *3 Days Late*, *10 Days Late*, *3 Weeks Late*), and real-time breakdowns.
- **Django Admin Portal**: Full admin suite at `/admin/` to manage Authors, Books, Members, and Circulation records.

---

## 2. Technology Stack

| Component | Technology |
|---|---|
| **Backend** | Python 3.10 / 3.11+, Django 5.x |
| **Database** | SQLite (`db.sqlite3`) via Django ORM |
| **Frontend** | HTML5, CSS3, JavaScript (ES6+), Bootstrap 5.3, Bootstrap Icons |
| **Static Assets** | WhiteNoise 6.x (`CompressedManifestStaticFilesStorage`) |
| **WSGI Server** | Gunicorn 21+ |
| **Deployment Target** | Render (Web Service / Blueprint) |

---

## 3. Project Directory Structure

```
project-root/
├── manage.py                  # Django administrative script
├── requirements.txt           # Production & local dependencies
├── render.yaml                # Render Blueprint deployment specification
├── create_superuser.py        # Superuser creation & demo data seeding
├── README.md                  # Comprehensive project documentation
├── .gitignore                 # Git ignore rules (venv, bytecode, build artifacts)
├── db.sqlite3                 # SQLite database file (Django ORM)
├── mysite/                    # Django project configuration
│   ├── __init__.py
│   ├── settings.py            # App settings (WhiteNoise, SQLite, templates)
│   ├── urls.py                # Root URL routing
│   ├── wsgi.py                # WSGI entrypoint for Gunicorn
│   └── asgi.py                # ASGI entrypoint
└── library/                   # Library application module
    ├── migrations/            # Database schema migrations
    │   └── 0001_initial.py
    ├── admin.py               # Django Admin configuration & model registration
    ├── apps.py                # App configuration
    ├── forms.py               # ModelForms for Book, Member, Issue, Return
    ├── models.py              # Author, Book, Member, CirculationRecord models
    ├── tests.py               # Unit & integration test suite (7 tests)
    ├── urls.py                # Application URL routes
    ├── views.py               # Workflow views & JSON API endpoints
    ├── templates/             # Bootstrap 5 HTML templates
    │   └── library/
    │       ├── base.html
    │       ├── catalog.html
    │       ├── book_detail.html
    │       ├── issue_book.html
    │       ├── return_book.html
    │       ├── return_selector.html
    │       ├── member_dashboard.html
    │       ├── members_list.html
    │       ├── member_form.html
    │       ├── book_form.html
    │       ├── author_form.html
    │       └── calculator.html
    └── static/                # Static assets (packaged inside app)
        ├── css/
        │   └── style.css      # Custom styling & theme tokens
        └── js/
            └── main.js        # Instant search, calculators & real-time updates
```

---

## 4. Database Schema & Architecture

Managed exclusively through the **Django ORM** using SQLite:

### `Author`
- `name`: Author's full name.
- `biography`: Text biography.

### `Book`
- `title`: Title of the book.
- `author`: `ForeignKey` &rarr; `Author`
- `isbn`: Unique ISBN code.
- `genre`: Categorized genre choice.
- `total_copies`: Total inventory owned by the library.
- `available_copies`: Copies currently in the library on shelves.
- `cover_url`: Link to high-resolution book cover image.
- `description`: Synopsis/summary text.

### `Member`
- `name`: Member's full name.
- `member_id`: Unique library card identifier (e.g. `MEM-101`).
- `email`: Contact email address.
- `phone`: Contact phone number.
- `joined_date`: Registration date.

### `CirculationRecord`
- `book`: `ForeignKey` &rarr; `Book`
- `member`: `ForeignKey` &rarr; `Member`
- `issue_date`: Date book was checked out.
- `due_date`: Date book is due (defaults to 14 days after issue).
- `return_date`: Date book was checked in (nullable until returned).
- `fine_amount`: Accrued fine in USD (`DecimalField`, default `$0.00`).
- `returned`: Boolean status flag (`False` = active loan, `True` = archived return).

---

## 4. Business Logic Implementation

1. **Zero-Copy Issue Protection**:
   - `available_copies > 0` validation. If copies are 0, issuing is blocked with an alert.
2. **Inventory Stock Tracking**:
   - On issue: `book.available_copies = book.available_copies - 1`
   - On return: `book.available_copies = book.available_copies + 1`
3. **14-Day Due Date Rule**:
   - By default, `due_date = issue_date + timedelta(days=14)`.
4. **Overdue Fine Computation**:
   - If `return_date > due_date`:
     $$\text{Fine} = (\text{return\_date} - \text{due\_date}).\text{days} \times \$1.00$$
   - If returned on or before due date: $\text{Fine} = \$0.00$.

---

## 5. Local Setup & Execution Guide

### Prerequisites
- Python 3.10+ or Python 3.11+
- Virtual environment tool (`venv`)

### Step 1: Clone or Navigate to the Project Root
```bash
cd "c:\Users\Admin\Desktop\New folder"
```

### Step 2: Activate Virtual Environment
- **Windows (PowerShell)**:
  ```powershell
  .\venv\Scripts\Activate.ps1
  ```
- **Windows (CMD)**:
  ```cmd
  venv\Scripts\activate.bat
  ```
- **Linux / macOS**:
  ```bash
  source venv/bin/activate
  ```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Run Migrations
```bash
python manage.py makemigrations library
python manage.py migrate
```

### Step 5: Seed Sample Demonstration Data & Admin
```bash
python create_superuser.py
```
> This script automatically sets up:
> - Superuser account: `username: admin`, `password: admin123`
> - Sample Authors: *George Orwell, F. Scott Fitzgerald, Jane Austen, Robert C. Martin, Isaac Asimov, etc.*
> - Sample Books across multiple genres with realistic cover artwork.
> - Sample Members with active loans, overdue loans (for testing fines), and past returned history.

### Step 6: Start the Development Server
```bash
python manage.py runserver
```
Visit **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)** in your browser.

---

## 6. Render Deployment Guide (Mandatory)

The repository is pre-configured with `render.yaml`, `requirements.txt`, and WhiteNoise static asset serving for Render.

### Render Blueprint Configuration (`render.yaml`)
```yaml
services:
  - type: web
    name: digital-library-demo
    runtime: python
    rootDir: .
    buildCommand: "pip install -r requirements.txt && python manage.py collectstatic --no-input && python manage.py migrate && python create_superuser.py"
    startCommand: "python manage.py migrate && python create_superuser.py && gunicorn mysite.wsgi:application"
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.0
      - key: WEB_CONCURRENCY
        value: 2
```

### Deployment Steps:
1. **Initialize Git & Push to GitHub**:
   ```bash
   git init
   git add .
   git commit -m "LibriVerse Digital Library Portal initial commit"
   git branch -M main
   git remote add origin https://github.com/<your-username>/<your-repo-name>.git
   git push -u origin main
   ```
2. **Create Web Service on Render**:
   - Log into [Render Dashboard](https://dashboard.render.com/).
   - Click **New +** &rarr; **Blueprint** (or **Web Service**).
   - Connect your GitHub repository.
   - If using Blueprint, Render will read `render.yaml` automatically.
   - If setting up manually:
     - **Runtime**: `Python`
     - **Build Command**:
       ```bash
       pip install -r requirements.txt && python manage.py collectstatic --no-input && python manage.py migrate && python create_superuser.py
       ```
     - **Start Command**:
       ```bash
       python manage.py migrate && python create_superuser.py && gunicorn mysite.wsgi:application
       ```
3. **Environment Variables**:
   - Add `SECRET_KEY`: Set to any long random string (e.g. `django-insecure-prod-key-xyz...`).
   - `RENDER`: Set to `True` (automatically disables `DEBUG` in production).
4. **Deploy & Verify**:
   - Render will build dependencies, collect static files, apply migrations, seed the database, and start Gunicorn.
   - Access your live app at `https://<your-service-name>.onrender.com`.
   - Access the Django Admin at `https://<your-service-name>.onrender.com/admin/`.

> **Note on SQLite on Render**:
> SQLite (`db.sqlite3`) is used as instructed. The free web service tier on Render has an ephemeral filesystem, meaning data may reset when the server spins down or redeploys. The `create_superuser.py` script automatically re-populates the admin and sample catalog on restart.

---

## 7. Automated Test Suite

Run the built-in test suite covering inventory models, issue workflows, zero-copy checks, return calculations, and API endpoints:
```bash
python manage.py test library
```

---

## 8. Credentials & Default Access

- **Admin Portal**: `/admin/`
- **Username**: `admin`
- **Password**: `admin123`
- **Sample Patrons**:
  - `Alice Walker` (`MEM-101`)
  - `David Miller` (`MEM-102`)
  - `Elena Rostova` (`MEM-103`)
  - `Marcus Chen` (`MEM-104`)
