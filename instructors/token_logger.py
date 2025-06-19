from utils.db import db
from datetime import datetime

def log_token_history(student_username, instructor_username, action, tokens_changed, module="general"):
    db["token_logs"].insert_one({
        "student": student_username,
        "instructor": instructor_username,
        "action": action,
        "module": module,
        "tokens_changed": tokens_changed,
        "timestamp": datetime.utcnow()
    })
