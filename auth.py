import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

def init_db():
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

def create_user(username, email, password):
    conn = sqlite3.connect('studynow.db')
    cursor = conn.cursor()
    
    hashed_password = generate_password_hash(password)
    
    try:
        cursor.execute('INSERT INTO users (username, email, password) VALUES (?, ?, ?)', 
                      (username, email, hashed_password))
        conn.commit()
        return True, "User created successfully!"
    except sqlite3.IntegrityError:
        return False, "Username or email already exists"
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