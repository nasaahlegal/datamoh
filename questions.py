import psycopg2
import os

DATABASE_URL = os.environ.get("DATABASE_URL")

def get_conn():
    return psycopg2.connect(DATABASE_URL, sslmode="require")

def init_questions_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS legal_questions (
            id SERIAL PRIMARY KEY,
            category TEXT,
            question TEXT,
            answer TEXT
        )
    """)
    conn.commit()
    conn.close()

def add_legal_question(category, question, answer):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO legal_questions (category, question, answer) VALUES (%s, %s, %s)",
        (category, question, answer)
    )
    conn.commit()
    conn.close()

def delete_legal_question(question_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM legal_questions WHERE id=%s", (question_id,))
    conn.commit()
    conn.close()

def fetch_questions_by_category(category):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, question FROM legal_questions WHERE category=%s", (category,))
    rows = cur.fetchall()
    conn.close()
    return rows

def fetch_answer_by_question(question):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT answer FROM legal_questions WHERE question=%s", (question,))
    row = cur.fetchone()
    conn.close()
    if row:
        return row[0]
    return None

def fetch_all_categories():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT category FROM legal_questions")
    cats = [r[0] for r in cur.fetchall()]
    conn.close()
    return cats

def fetch_all_questions():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, category, question, answer FROM legal_questions")
    qas = cur.fetchall()
    conn.close()
    return qas

init_questions_db()