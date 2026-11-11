# University Teaching and Examination Timetable Management System

## Setup (Windows)

1. Create virtual environment:
```
python -m venv venv
venv\Scripts\activate
```

2. Install dependencies:
```
pip install -r requirements.txt
```

3. Run migrations:
```
python manage.py migrate
```

4. Create superuser:
```
python manage.py createsuperuser
```
Then set role to super_admin via shell if needed.

5. Start server:
```
python manage.py runserver
```

6. Access:
- Dashboard: http://127.0.0.1:8000/
- Admin: http://127.0.0.1:8000/admin/
- Public portal: http://127.0.0.1:8000/dashboard/public/teaching/ (or via links)

## Backup SQLite
Copy db.sqlite3 to a safe location.

## Production
Set DJANGO_DEBUG=False, DJANGO_SECRET_KEY, DJANGO_ALLOWED_HOSTS. Use PostgreSQL by changing DATABASES.
```