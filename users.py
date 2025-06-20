import os
import psycopg2
import time
from config import DATABASE_URL, FREE_QUESTIONS_LIMIT

def get_connection():
    return psycopg2.connect(DATABASE_URL, sslmode="require")

def init_paid_questions_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS paid_questions (
            user_id BIGINT PRIMARY KEY,
            question TEXT,
            created_at BIGINT
        )
    """)
    conn.commit()
    conn.close()

def init_users_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            sub_expiry BIGINT DEFAULT 0,
            free_questions_left INT DEFAULT {FREE_QUESTIONS_LIMIT},
            created_at BIGINT
        )
    """)
    conn.commit()
    conn.close()
    # تهيئة جدول الأسئلة المدفوعة
    init_paid_questions_db()

def get_user(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT user_id, username, full_name, sub_expiry, free_questions_left FROM users WHERE user_id=%s", (user_id,))
    row = cur.fetchone()
    conn.close()
    if row:
        return {
            "user_id": row[0],
            "username": row[1],
            "full_name": row[2],
            "sub_expiry": row[3] or 0,
            "free_questions_left": row[4] if row[4] is not None else FREE_QUESTIONS_LIMIT
        }
    return {
        "user_id": user_id,
        "username": "",
        "full_name": "",
        "sub_expiry": 0,
        "free_questions_left": FREE_QUESTIONS_LIMIT
    }

def create_or_get_user(user_id, username, full_name):
    user = get_user(user_id)
    if user and user["free_questions_left"] is not None:
        return user
    now = int(time.time())
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO users (user_id, username, full_name, created_at) VALUES (%s, %s, %s, %s) "
        "ON CONFLICT (user_id) DO NOTHING",
        (user_id, username, full_name, now)
    )
    conn.commit()
    conn.close()
    return get_user(user_id)

def decrement_free_questions(user_id):
    user = get_user(user_id)
    if user and user["free_questions_left"] > 0:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("UPDATE users SET free_questions_left=free_questions_left-1 WHERE user_id=%s", (user_id,))
        conn.commit()
        conn.close()
        return True
    return False

def set_subscription(user_id, username, full_name, days=30):
    now = int(time.time())
    expiry = now + days*24*60*60
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO users (user_id, username, full_name, sub_expiry, free_questions_left, created_at) VALUES (%s, %s, %s, %s, %s, %s) "
        "ON CONFLICT (user_id) DO UPDATE SET sub_expiry=%s, username=%s, full_name=%s, free_questions_left=%s",
        (user_id, username, full_name, expiry, FREE_QUESTIONS_LIMIT, now, expiry, username, full_name, FREE_QUESTIONS_LIMIT)
    )
    conn.commit()
    conn.close()

def is_subscribed(user_id):
    user = get_user(user_id)
    return user and user["sub_expiry"] and user["sub_expiry"] > int(time.time())

def get_active_subscriptions():
    conn = get_connection()
    cur = conn.cursor()
    now = int(time.time())
    cur.execute("""
        SELECT user_id, username, full_name, sub_expiry
        FROM users
        WHERE sub_expiry > %s
        ORDER BY sub_expiry ASC
    """, (now,))
    rows = cur.fetchall()
    conn.close()
    result = []
    for user_id, username, full_name, sub_expiry in rows:
        days_left = int((sub_expiry - now) // (24*60*60))
        result.append({
            "user_id": user_id,
            "username": username,
            "full_name": full_name,
            "days_left": days_left,
        })
    return result

def remove_subscription(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET sub_expiry=0 WHERE user_id=%s", (user_id,))
    conn.commit()
    conn.close()

# --- إدارة الأسئلة المدفوعة ---
def save_paid_question(user_id, question):
    now = int(time.time())
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO paid_questions (user_id, question, created_at) VALUES (%s, %s, %s) "
        "ON CONFLICT (user_id) DO UPDATE SET question=%s, created_at=%s",
        (user_id, question, now, question, now)
    )
    conn.commit()
    conn.close()

def get_paid_question(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT question FROM paid_questions WHERE user_id=%s", (user_id,))
    row = cur.fetchone()
    conn.close()
    if row:
        return row[0]
    return None

def delete_paid_question(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM paid_questions WHERE user_id=%s", (user_id,))
    conn.commit()
    conn.close()