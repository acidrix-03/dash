import sqlite3

def add_is_archived_column():
    try:
        conn = sqlite3.connect('document_tracker.db')
        cursor = conn.cursor()
        
        # Add the is_archived column
        cursor.execute("ALTER TABLE documents ADD COLUMN is_archived INTEGER DEFAULT 0;")
        
        conn.commit()
        conn.close()
        print("is_archived column added successfully.")
        
    except sqlite3.OperationalError as e:
        print("Error:", e)

add_is_archived_column()
