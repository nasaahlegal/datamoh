import json
import os
from datetime import datetime, timedelta
from functools import wraps

LOG_FILE = "admin_actions.log"
RETENTION_DAYS = 45

def log_admin_action(action):
    """
    Decorator to log admin actions automatically to a file.
    Keeps only records from the last RETENTION_DAYS days.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(update, context, *args, **kwargs):
            # ---- اجمع بيانات الإجراء الإداري
            admin_id = getattr(update.effective_user, "id", None)
            # حاول من context أو من user_id في الدالة أو من user_id في user_data
            user_id = None
            details = ""
            # محاولة معرفة user_id المناسب
            if hasattr(update, "callback_query") and update.callback_query:
                data = update.callback_query.data
                if data:
                    for prefix in ["accept_sub_", "reject_sub_", "accept_question_", "reject_question_", "extend_", "delete_"]:
                        if data.startswith(prefix):
                            try:
                                user_id = int(data.split("_")[-1])
                            except:
                                pass
            if not user_id:
                # حاول من user_data (عند التمديد والحذف مثلاً)
                sub = context.user_data.get("selected_sub")
                if sub and isinstance(sub, dict):
                    user_id = sub.get("user_id")
            if not user_id:
                # حاول من args (غير شائع هنا)
                if args:
                    try:
                        user_id = args[0]
                    except Exception:
                        pass
            # إعداد التفاصيل (يمكن تعديلها حسب الحاجة)
            if hasattr(update, "callback_query") and update.callback_query:
                details = f"callback_data: {update.callback_query.data}"
            elif hasattr(update, "message") and update.message:
                details = update.message.text
            # ---- نفذ الدالة الأصلية
            result = await func(update, context, *args, **kwargs)
            # ---- سجّل الإجراء
            now = datetime.utcnow()
            log_entry = {
                "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
                "action": action,
                "admin_id": admin_id,
                "user_id": user_id,
                "details": details
            }
            # تحميل السجلات القديمة وحذف ما مر عليه أكثر من 45 يومًا
            logs = []
            if os.path.exists(LOG_FILE):
                with open(LOG_FILE, "r", encoding="utf-8") as f:
                    for line in f:
                        try:
                            entry = json.loads(line)
                            entry_time = datetime.strptime(entry["timestamp"], "%Y-%m-%d %H:%M:%S")
                            if now - entry_time <= timedelta(days=RETENTION_DAYS):
                                logs.append(entry)
                        except Exception:
                            continue
            logs.append(log_entry)
            with open(LOG_FILE, "w", encoding="utf-8") as f:
                for entry in logs:
                    f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            return result
        return wrapper
    return decorator

def get_admin_logs():
    """
    Return all current logs (not older than RETENTION_DAYS) as a list of dicts.
    """
    now = datetime.utcnow()
    logs = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    entry_time = datetime.strptime(entry["timestamp"], "%Y-%m-%d %H:%M:%S")
                    if now - entry_time <= timedelta(days=RETENTION_DAYS):
                        logs.append(entry)
                except Exception:
                    continue
    return logs