import os
import time
import psycopg2

DATABASE_URL = os.environ["DATABASE_URL"]
FREE_LIMIT = int(os.environ.get("FREE_QUESTIONS_LIMIT", "3"))

def get_connection():
    try:
        return psycopg2.connect(DATABASE_URL, sslmode="require")
    except Exception as e:
        # هنا يمكن تسجيل الخطأ أو إرسال تنبيه للأدمن
        raise

def init_users_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            sub_expiry BIGINT DEFAULT 0,
            free_questions_left INT DEFAULT %s,
            created_at BIGINT
        )
    """, (FREE_LIMIT,))
    conn.commit()
    conn.close()

def get_user(user_id):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT user_id, username, full_name, sub_expiry, free_questions_left FROM users WHERE user_id=%s",
            (user_id,)
        )
        row = cur.fetchone()
        conn.close()
        if row:
            return {
                "user_id": row[0],
                "username": row[1] or "",
                "full_name": row[2] or "",
                "sub_expiry": row[3] or 0,
                "free_questions_left": row[4] if row[4] is not None else FREE_LIMIT
            }
    except:
        pass
    return {
        "user_id": user_id,
        "username": "",
        "full_name": "",
        "sub_expiry": 0,
        "free_questions_left": FREE_LIMIT
    }

def create_or_get_user(user_id, username, full_name):
    user = get_user(user_id)
    if user and user.get("created_at"):
        return user
    now = int(time.time())
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO users (user_id, username, full_name, created_at) VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING",
        (user_id, username, full_name, now)
    )
    conn.commit()
    conn.close()
    return get_user(user_id)

def decrement_free_questions(user_id):
    user = get_user(user_id)
    if user["free_questions_left"] > 0:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "UPDATE users SET free_questions_left=free_questions_left-1 WHERE user_id=%s",
            (user_id,)
        )
        conn.commit()
        conn.close()
        return True
    return False

def set_subscription(user_id, username, full_name, days=30):
    now = int(time.time())
    expiry = now + days * 86400
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO users (user_id, username, full_name, sub_expiry, free_questions_left, created_at)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (user_id) DO UPDATE
          SET sub_expiry=%s, username=%s, full_name=%s, free_questions_left=%s
    """, (
        user_id, username, full_name, expiry, FREE_LIMIT, now,
        expiry, username, full_name, FREE_LIMIT
    ))
    conn.commit()
    conn.close()

def is_subscribed(user_id):
    user = get_user(user_id)
    return user["sub_expiry"] > int(time.time())

def get_active_subscriptions():
    conn = get_connection()
    cur = conn.cursor()
    now = int(time.time())
    cur.execute(
        "SELECT user_id, username, full_name, sub_expiry FROM users WHERE sub_expiry > %s ORDER BY sub_expiry",
        (now,)
    )
    rows = cur.fetchall()
    conn.close()
    result = []
    for uid, uname, fname, expiry in rows:
        result.append({
            "user_id": uid,
            "username": uname or "",
            "full_name": fname or "",
            "days_left": (expiry - now) // 86400
        })
    return result

def remove_subscription(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET sub_expiry=0 WHERE user_id=%s", (user_id,))
    conn.commit()
    conn.close()
