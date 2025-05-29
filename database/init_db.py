import sqlite3
import os

def init_db():
    if not os.path.exists("invoice.db"):
        conn = sqlite3.connect("invoice.db")
        with open("database/schema.sql", "r") as f:
            conn.executescript(f.read())
        print("Database initialized successfully")
    else:
        print("Database already exists")

if __name__ == "__main__":
    init_db()