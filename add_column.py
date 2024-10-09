import sqlite3

def add_column_to_table():
    try:
        with sqlite3.connect('documents.db') as conn:
            conn.execute('ALTER TABLE recommended_applications ADD COLUMN recommending_approval TEXT')
        print("Column 'recommending_approval' added successfully!")
    except sqlite3.OperationalError as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    add_column_to_table()
