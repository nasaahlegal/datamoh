import psycopg2
import os

DATABASE_URL = os.environ.get("DATABASE_URL")

def get_connection():
    return psycopg2.connect(DATABASE_URL, sslmode="require")

def init_questions_db():
    conn = get_connection()
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

def add_question(category, question, answer):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO legal_questions (category, question, answer) VALUES (%s, %s, %s)", (category, question, answer))
    conn.commit()
    conn.close()

def update_question(question_id, question, answer):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE legal_questions SET question=%s, answer=%s WHERE id=%s", (question, answer, question_id))
    conn.commit()
    conn.close()

def delete_question(question_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM legal_questions WHERE id=%s", (question_id,))
    conn.commit()
    conn.close()

def get_questions_by_category(category):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, question, answer FROM legal_questions WHERE category=%s", (category,))
    rows = cur.fetchall()
    conn.close()
    return rows

def get_all_questions():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, category, question, answer FROM legal_questions ORDER BY category")
    rows = cur.fetchall()
    conn.close()
    return rows

def get_question_by_id(question_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, category, question, answer FROM legal_questions WHERE id=%s", (question_id,))
    row = cur.fetchone()
    conn.close()
    return row