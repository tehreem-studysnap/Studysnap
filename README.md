# StudySnap - Student Task Organizer

StudySnap is a simple web application where students can register, log in and manage their study tasks (add, view, complete and delete).

## Technologies Used
- Python 3
- Flask (web framework and REST API)
- SQLite (database)
- HTML and CSS (user interface)

## Features
- User registration and login (passwords stored as hashes)
- Forgot password / reset password
- Add, view, complete and delete tasks
- Each user can only see and change their own tasks
- Input validation and error messages
- REST API endpoints

## How to Run
1. Install Python 3 from python.org
2. Install Flask: `pip install flask`
3. Run the app: `python app.py`
4. Open a browser and go to `http://127.0.0.1:5000`

## REST API Endpoints
(Login is required for all endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/tasks | Get all tasks of the logged-in user |
| POST | /api/tasks | Add a new task (JSON: title, subject, due_date) |
| PUT | /api/tasks/<id>/complete | Mark a task as completed |
| DELETE | /api/tasks/<id> | Delete a task |

## Database Tables
- **users**: user_id, name, email, password
- **tasks**: task_id, title, subject, due_date, status, user_id

## Future Scope
- Email-based password reset link
- Task reminders
- Search and filter tasks
