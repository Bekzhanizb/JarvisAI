from storage.db import cursor, conn


def save_message(role, content):
    cursor.execute(
        "INSERT INTO dialog_history (role, content) VALUES (%s, %s)",
    (role, content))
    conn.commit()