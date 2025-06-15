import psycopg2
import os
import time

from app_logging import log_event, log_error

DATABASE_URL = os.environ.get("DATABASE_URL")
FREE_QUESTIONS_LIMIT = 3

def get_connection():
    return psycopg2.connect(DATABASE_URL, sslmode="require")

def init_users_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id BIGINT PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            free_questions_left INTEGER DEFAULT %s,
            sub_expiry BIGINT DEFAULT 0
        )
    """, (FREE_QUESTIONS_LIMIT,))
    conn.commit()
    conn.close()

def create_or_get_user(user_id, username, full_name):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE id=%s", (user_id,))
    if cur.fetchone() is None:
        cur.execute("INSERT INTO users (id, username, full_name, free_questions_left, sub_expiry) VALUES (%s, %s, %s, %s, %s)",
                    (user_id, username, full_name, FREE_QUESTIONS_LIMIT, 0))
        log_event(f"Created new user: {user_id} - {username} - {full_name}")
        conn.commit()
    conn.close()

def get_user(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, username, full_name, free_questions_left, sub_expiry FROM users WHERE id=%s", (user_id,))
    row = cur.fetchone()
    conn.close()
    if row:
        return {
            "id": row[0],
            "username": row[1],
            "full_name": row[2],
            "free_questions_left": row[3],
            "sub_expiry": row[4]
        }
    else:
        return None

def decrement_free_questions(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET free_questions_left = free_questions_left - 1 WHERE id=%s AND free_questions_left > 0", (user_id,))
    log_event(f"Decremented free questions for user: {user_id}")
    conn.commit()
    conn.close()

def set_subscription(user_id, days=30):
    now = int(time.time())
    expiry = now + days*24*60*60
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET sub_expiry=%s WHERE id=%s", (expiry, user_id))
    log_event(f"Set subscription for user: {user_id} until {expiry}")
    conn.commit()
    conn.close()

def extend_subscription(user_id, days=30):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT sub_expiry FROM users WHERE id=%s", (user_id,))
    row = cur.fetchone()
    now = int(time.time())
    if row and row[0] > now:
        new_expiry = row[0] + days*24*60*60
    else:
        new_expiry = now + days*24*60*60
    cur.execute("UPDATE users SET sub_expiry=%s WHERE id=%s", (new_expiry, user_id))
    log_event(f"Extended subscription for user: {user_id} until {new_expiry}")
    conn.commit()
    conn.close()

def remove_subscription(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET sub_expiry=0 WHERE id=%s", (user_id,))
    log_event(f"Removed subscription for user: {user_id}")
    conn.commit()
    conn.close()

def is_subscribed(user_id):
    user = get_user(user_id)
    if user is None:
        return False
    now = int(time.time())
    return user["sub_expiry"] > now

def get_active_subscriptions():
    now = int(time.time())
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, username, full_name, sub_expiry FROM users WHERE sub_expiry > %s", (now,))
    rows = cur.fetchall()
    conn.close()
    return rows