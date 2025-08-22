# E-Library Django Project

E-Library is a Django-based digital library application.  
This project allows users to upload, read, and analyze PDF books interactively.

---

## Features
- **User Authentication** – Login & user registration
- **Book Management** – Upload, edit, and delete books
- **Catalog** – Search & filter by genre or favorites
- **Favorite System** – Mark/unmark books as favorites
- **Book Preview** – Read PDFs directly in the app (without opening a new tab)
- **Keyword Analysis** – Analyze book content using **TF-IDF** (powered by scikit-learn)
- **Responsive UI** – Built with TailwindCSS for a modern interface

---

## Tech Stack
- **Backend**: Django 4.x
- **Database**: SQLite (default, can be replaced with PostgreSQL/MySQL)
- **Frontend**: Django Templates + TailwindCSS
- **PDF Processing**: PyMuPDF
- **Text Analysis**: scikit-learn (TF-IDF)
- **Authentication**: Django Auth System

---

## Project Structure
elibproject/
```bash
│── books/ # Main app for book management
│── users/ # User management & authentication
│── media/ # Uploaded files (covers, PDFs, page images)
│── static/ # Static files (css, js)
│── templates/ # HTML templates
│── elib/ # Project configuration
│── db.sqlite3 # Database (optional, don’t upload in production)
│── manage.py # Django management script
```
---

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/username/elibproject.git
   cd elibproject
   ```

2. Create a virtual environment & install dependencies:
    ```bash
    python -m venv venv
    source venv/bin/activate   # Mac/Linux
    venv\Scripts\activate      # Windows

    pip install -r requirements.txt
    ```

3. Run database migrations:
    ```bash
    python manage.py migrate
    ```

4. Create a superuser:
    ```bash
    python manage.py createsuperuser
    ```

5. Start the development server:
    ```bash
    python manage.py runserver
    ```

6. Open in browser:
    ```bash
    http://127.0.0.1:8000/
    ```