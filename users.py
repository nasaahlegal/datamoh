import os
import psycopg2
import time

DATABASE_URL = os.environ.get("DATABASE_URL")

def get_connection():
    return psycopg2.connect(DATABASE_URL, sslmode="require")

def init_users_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            sub_expiry BIGINT DEFAULT 0,
            free_questions_left INT DEFAULT 3,
            created_at BIGINT
        )
    """)
    conn.commit()
    conn.close()

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
            "free_questions_left": row[4] if row[4] is not None else 3
        }
    return {
        "user_id": user_id,
        "username": "",
        "full_name": "",
        "sub_expiry": 0,
        "free_questions_left": 3
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

def reset_free_questions(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET free_questions_left=3 WHERE user_id=%s", (user_id,))
    conn.commit()
    conn.close()

def set_subscription(user_id, username, full_name, days=30, is_extension=False):
    conn = get_connection()
    cur = conn.cursor()
    
    if is_extension:
        # تمديد الاشتراك: إضافة أيام إلى تاريخ الانتهاء الحالي
        cur.execute("SELECT sub_expiry FROM users WHERE user_id = %s", (user_id,))
        current_expiry = cur.fetchone()[0] or int(time.time())
        expiry = current_expiry + days * 24 * 60 * 60
    else:
        # اشتراك جديد: بدء من الوقت الحالي
        expiry = int(time.time()) + days * 24 * 60 * 60
    
    cur.execute(
        "UPDATE users SET sub_expiry = %s WHERE user_id = %s",
        (expiry, user_id)
    )
    conn.commit()
    conn.close()

def is_subscribed(user_id):
    user = get_user(user_id)
    if user and user["sub_expiry"] and user["sub_expiry"] > int(time.time()):
        return True
    return False

def get_subscription_expiry(user_id):
    user = get_user(user_id)
    return user["sub_expiry"] if user else None