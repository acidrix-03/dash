import sqlite3

def add_column_to_table():
    try:
        with sqlite3.connect('documents.db') as conn:
            conn.execute('ALTER TABLE recommended_applications ADD COLUMN recommending_approval TEXT')
        print("Column 'recommending_approval' added successfully!")
    except sqlite3.OperationalError as e:
        print(f"Error: {e}")

import sqlite3

def add_columns_to_leave_application():
    with sqlite3.connect('documents.db') as conn:
        # Add 'office' column
        try:
            conn.execute('ALTER TABLE leave_application ADD COLUMN office TEXT')
            print("Column 'office' added successfully.")
        except sqlite3.OperationalError:
            print("Column 'office' already exists.")

        # Add 'salary' column
        try:
            conn.execute('ALTER TABLE leave_application ADD COLUMN salary INTEGER')
            print("Column 'salary' added successfully.")
        except sqlite3.OperationalError:
            print("Column 'salary' already exists.")

if __name__ == '__main__':
    add_columns_to_leave_application()  # Call the function to alter the database


if __name__ == '__main__':
    add_column_to_table()
