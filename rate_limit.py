import time

user_last_message = {}
MIN_SECONDS = 3

def is_spam(user_id: int):
    now = time.time()
    last = user_last_message.get(user_id, 0)
    if now - last < MIN_SECONDS:
        return True
    user_last_message[user_id] = now
    return False