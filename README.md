# Al-Shiraa Solar Energy Flask App

This is a dynamic Flask application for Al-Shiraa Solar Energy, featuring a product dashboard, user authentication, and Postgres database integration.

## Setup

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Environment Variables**:
    By default, the app uses a local SQLite database (`site.db`).
    To use a production database (like Neon Postgres), set the `NETLIFY_DATABASE_URL` environment variable.
    ```bash
    export NETLIFY_DATABASE_URL="postgresql://user:password@host/dbname"
    ```

3.  **Initialize Database & Admin User**:
    Run the following command to create the database tables and an initial admin user (`admin` / `admin123`).
    ```bash
    flask create_admin
    ```

4.  **Run the Application**:
    ```bash
    python app.py
    ```
    The app will be available at `http://127.0.0.1:5000`.

## Features
-   **Authentication**: Login for Admin and Staff.
-   **Dashboard**: Manage products (Add, Edit, Delete).
-   **Calculators**: Solar and battery calculators.
-   **Responsive Design**: Mobile-friendly interface.

## Project Structure
-   `app.py`: Main application file.
-   `models.py`: Database models (User, Product).
-   `forms.py`: WTForms for handling input.
-   `templates/`: HTML templates (Jinja2).
-   `static/`: CSS, JS, Images, and Uploads.
