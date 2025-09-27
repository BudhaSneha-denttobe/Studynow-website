from flask import Flask, render_template, Response, request, redirect, url_for, session, jsonify
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash
import json
from datetime import datetime, timedelta
app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'

# ---------------- Database functions ----------------
def init_db():
    if not os.path.exists('studynow.db'):
        conn = sqlite3.connect('studynow.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
        print("Database created")
    else:
        print("Database already exists")

def create_user(username, email, password):
    conn = sqlite3.connect('studynow.db')
    cursor = conn.cursor()
    hashed_password = generate_password_hash(password)
    try:
        cursor.execute('INSERT INTO users (username, email, password) VALUES (?, ?, ?)',
                      (username, email, hashed_password))
        conn.commit()
        return True, "User created successfully!"
    except sqlite3.IntegrityError as e:
        error_msg = str(e)
        if 'username' in error_msg.lower():
            return False, "Username already exists"
        elif 'email' in error_msg.lower():
            return False, "Email already exists"
        else:
            return False, "Username or email already exists"
    except Exception as e:
        return False, f"Database error: {str(e)}"
    finally:
        conn.close()

def verify_user(email, password):
    conn = sqlite3.connect('studynow.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, password FROM users WHERE email = ?', (email,))
    user = cursor.fetchone()
    conn.close()
    if user and check_password_hash(user[2], password):
        return {'id': user[0], 'username': user[1], 'email': email}
    return None

# Initialize database once
init_db()

# ---------------- Camera functions ----------------
import cv2
import numpy as np

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

def generate_frames():
    cap = cv2.VideoCapture(0)  # Initialize camera
    if not cap.isOpened():
        print("Warning: Camera not available, using placeholder")

    while True:
        success, frame = cap.read()
        if not success:
            # Placeholder image
            placeholder = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(placeholder, "Camera Not Available", (150, 220),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            ret, buffer = cv2.imencode('.jpg', placeholder)
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' +
                   buffer.tobytes() + b'\r\n')
            break
        else:
            frame = cv2.flip(frame, 1)  # Mirror effect
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            faces = face_cascade.detectMultiScale(gray, 1.1, 4)

            if len(faces) == 0:
                # No face
                cv2.putText(frame, "Stay Focused Dont Distract", (50, 60),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
            else:
                for (x, y, w, h) in faces:
                    face_center_x = x + w // 2
                    frame_center_x = frame.shape[1] // 2
                    offset = face_center_x - frame_center_x

                    if abs(offset) < 60:
                        cv2.putText(frame, "Keep on going 👏", (50, 60),
                                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 3)
                    else:
                        cv2.putText(frame, "Stay focused Don't Distract 👀", (50, 60),
                                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 3)

            # Label at top-right
            cv2.putText(frame, "StudyNow Live Feed", (400, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

            ret, buffer = cv2.imencode('.jpg', frame)
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' +
                   buffer.tobytes() + b'\r\n')

    cap.release()

# ---------------- Routes ----------------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/study_timer')
def study_timer():
    return render_template('study_timer.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/todo')
def todo():
    return render_template('todo.html')

@app.route('/timetable')
def timetable():
    return render_template('timetable.html')

@app.route('/chatbot')
def chatbot():
    return render_template('chatbot.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/login2', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            email = request.form.get('email')
            password = request.form.get('password')
            if not email or not password:
                return jsonify({'success': False, 'message': 'Please fill in all fields'})
            user = verify_user(email, password)
            if user:
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['email'] = user['email']
                return jsonify({'success': True, 'message': 'Login successful!'})
            else:
                return jsonify({'success': False, 'message': 'Invalid email or password'})
        except Exception as e:
            return jsonify({'success': False, 'message': f'Login failed: {str(e)}'})
    return render_template('login2.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        try:
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            if not username or not email or not password:
                return jsonify({'success': False, 'message': 'Please fill in all fields'})
            if '@' not in email or '.' not in email:
                return jsonify({'success': False, 'message': 'Please enter a valid email address'})
            if len(password) < 6:
                return jsonify({'success': False, 'message': 'Password must be at least 6 characters'})
            success, message = create_user(username, email, password)
            if success:
                return jsonify({'success': True, 'message': message})
            else:
                return jsonify({'success': False, 'message': message})
        except Exception as e:
            return jsonify({'success': False, 'message': f'Signup failed: {str(e)}'})
    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/admin')
def admin_dashboard():
    conn = sqlite3.connect('studynow.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM users')
    total_users = cursor.fetchone()[0]
    cursor.execute('SELECT id, username, email, created_at FROM users ORDER BY created_at DESC')
    users = cursor.fetchall()
    cursor.execute('SELECT COUNT(*) FROM users WHERE DATE(created_at) = DATE("now")')
    today_signups = cursor.fetchone()[0]
    conn.close()
    return render_template('admin.html',
                           total_users=total_users,
                           today_signups=today_signups,
                           users=users)

@app.route('/admin/export')
def export_users():
    conn = sqlite3.connect('studynow.db')
    cursor = conn.cursor()
    cursor.execute('SELECT username, email, created_at FROM users ORDER BY created_at')
    users = cursor.fetchall()
    conn.close()
    csv_content = "Username,Email,Signup Date\n"
    for user in users:
        csv_content += f'"{user[0]}","{user[1]}","{user[2]}"\n'
    return Response(
        csv_content,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=studynow_users.csv"}
    )
@app.route('/api/save-study-session', methods=['POST'])
def save_study_session():
    try:
        user_id = session.get('user_id', 1)  # Default to demo user
        data = request.json
        
        # Get today's date
        today = datetime.now().strftime('%Y-%m-%d')
        
        conn = get_db_connection()
        
        # Check if session already exists for today
        existing_session = conn.execute(
            'SELECT * FROM study_sessions WHERE user_id = ? AND date = ?',
            (user_id, today)
        ).fetchone()
        
        if existing_session:
            # Update existing session
            conn.execute('''
                UPDATE study_sessions 
                SET minutes = minutes + ?, 
                    pomodoro_sessions = pomodoro_sessions + ?
                WHERE user_id = ? AND date = ?
            ''', (
                data.get('minutes', 0),
                data.get('pomodoro_sessions', 1),
                user_id,
                today
            ))
        else:
            # Insert new session
            conn.execute('''
                INSERT INTO study_sessions (user_id, date, minutes, tasks_completed, pomodoro_sessions)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                user_id,
                today,
                data.get('minutes', 0),
                data.get('tasks_completed', 0),
                data.get('pomodoro_sessions', 1)
            ))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Study session saved!'})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/get-today-stats')
def get_today_stats():
    user_id = session.get('user_id', 1)
    today = datetime.now().strftime('%Y-%m-%d')
    
    conn = get_db_connection()
    
    today_data = conn.execute('''
        SELECT COALESCE(SUM(minutes), 0) as minutes,
               COALESCE(SUM(tasks_completed), 0) as tasks,
               COALESCE(SUM(pomodoro_sessions), 0) as pomodoros
        FROM study_sessions 
        WHERE user_id = ? AND date = ?
    ''', (user_id, today)).fetchone()
    
    conn.close()
    
    return jsonify({
        'today_minutes': today_data['minutes'],
        'completed_tasks': today_data['tasks'],
        'pomodoro_sessions': today_data['pomodoros']
    })

@app.route('/api/get-study-data')
def get_study_data():
    user_id = session.get('user_id', 1)
    
    conn = get_db_connection()
    
    # Get studied days for this month
    current_month = datetime.now().strftime('%Y-%m')
    studied_days = conn.execute('''
        SELECT DISTINCT strftime('%d', date) as day 
        FROM study_sessions 
        WHERE user_id = ? AND strftime('%Y-%m', date) = ? AND minutes > 0
    ''', (user_id, current_month)).fetchall()
    
    # Get weekly data
    weekly_data = []
    for i in range(6, -1, -1):
        date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        day_data = conn.execute('''
            SELECT COALESCE(SUM(minutes), 0) as minutes
            FROM study_sessions 
            WHERE user_id = ? AND date = ?
        ''', (user_id, date)).fetchone()
        weekly_data.append(day_data['minutes'])
    
    conn.close()
    
    return jsonify({
        'studied_days': [int(day['day']) for day in studied_days],
        'weekly_data': weekly_data
    })


if __name__ == '__main__':
    print("Starting StudyNow...")
    app.run(debug=True, host='127.0.0.1', port=5000)
