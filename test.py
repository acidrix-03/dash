import sqlite3

with sqlite3.connect('documents.db') as conn:
    result = conn.execute("SELECT id, name, date_submitted FROM cto_application").fetchall()
    for row in result:
        print(row)
