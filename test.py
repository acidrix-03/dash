import sqlite3
with sqlite3.connect('users.db') as conn:
    user_data = conn.execute('SELECT id, username, position, office, salary FROM users WHERE id = ?', 
                              (user_id,)).fetchone()
    print(f"User Data After Update: {user_data}")  # Check if the data reflects the update
