import psycopg2
from core.config import DB_CONFIG


conn = psycopg2.connect(**DB_CONFIG)
cursor = conn.cursor()


cursor.execute("""
CREATE TABLE IF NOT EXISTS dialog_history (
id SERIAL PRIMARY KEY,
role TEXT,
content TEXT
);
""")
conn.commit()