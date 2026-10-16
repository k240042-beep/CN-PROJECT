import sqlite3

DB_NAME = "chat.db"

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    # Users table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    """)
    # New: Messages table for chat history (F4)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            message TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def add_user(username, password_hash):
    conn = get_connection()
    try:
        conn.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, password_hash))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_user(username):
    conn = get_connection()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    return user

# New: Functions to save and load chat history
def save_message(username, message):
    conn = get_connection()
    conn.execute("INSERT INTO messages (username, message) VALUES (?, ?)", (username, message))
    conn.commit()
    conn.close()

def get_recent_messages(limit=50):
    conn = get_connection()
    # Get the latest messages in chronological order
    messages = conn.execute("SELECT username, message, timestamp FROM messages ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return list(reversed(messages))

def save_message(username, message):
    # Stores one chat message in the database
    conn = get_connection()
    conn.execute(
        "INSERT INTO messages (username, message) VALUES (?, ?)",
        (username, message)
    )
    conn.commit()
    conn.close()

def get_recent_messages(limit=50):
    # Returns the last 50 messages, oldest first
    conn = get_connection()
    rows = conn.execute(
        """SELECT username, message, timestamp FROM
           (SELECT * FROM messages ORDER BY id DESC LIMIT ?)
           ORDER BY id ASC""",
        (limit,)
    ).fetchall()
    conn.close()
    return rows
