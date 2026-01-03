session_history = []


def add(role, content):
    session_history.append({"role": role, "content": content})


def get():
    return session_history


def clear():
    session_history.clear()