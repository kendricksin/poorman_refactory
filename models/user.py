def create_user(conn, username):
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (username) VALUES (?)", 
        (username,)
    )
    conn.commit()
    return cursor.lastrowid

def get_user_by_username(conn, username):
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM users WHERE username = ?", 
        (username,)
    )
    return cursor.fetchone()