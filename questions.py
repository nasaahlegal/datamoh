import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

QUESTIONS_FILE = Path(__file__).parent / "questions_db.json"

def load_questions():
    if not QUESTIONS_FILE.exists():
        return {
            "أحوال شخصية": [],
            "عقارات": [],
            "عمل": [],
            "جنائي": [],
            "مرور": [],
            "أخرى": []
        }
    with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_questions(data):
    with open(QUESTIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

LEGAL_QUESTIONS = load_questions()

def add_question(category, question, answer):
    if category not in LEGAL_QUESTIONS:
        LEGAL_QUESTIONS[category] = []
    LEGAL_QUESTIONS[category].append([question, answer])
    save_questions(LEGAL_QUESTIONS)
    logger.info(f"Added question to {category}: {question}")

def edit_question(category, idx, question, answer):
    if category in LEGAL_QUESTIONS and 0 <= idx < len(LEGAL_QUESTIONS[category]):
        LEGAL_QUESTIONS[category][idx] = [question, answer]
        save_questions(LEGAL_QUESTIONS)
        logger.info(f"Edited question in {category} idx {idx}")

def delete_question(category, idx):
    if category in LEGAL_QUESTIONS and 0 <= idx < len(LEGAL_QUESTIONS[category]):
        del LEGAL_QUESTIONS[category][idx]
        save_questions(LEGAL_QUESTIONS)
        logger.info(f"Deleted question in {category} idx {idx}")