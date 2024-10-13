import sqlite3

def add_column_to_table():
    try:
        with sqlite3.connect('documents.db') as conn:
            # Add 'recommending_approval' column to recommended_applications
            conn.execute('ALTER TABLE recommended_applications ADD COLUMN recommending_approval TEXT')
        print("Column 'recommending_approval' added successfully!")
    except sqlite3.OperationalError as e:
        print(f"Error: {e}")

def add_columns_to_leave_application():
    with sqlite3.connect('documents.db') as conn:
        # Add 'office' column to leave_application
        try:
            conn.execute('ALTER TABLE leave_application ADD COLUMN office TEXT')
            print("Column 'office' added successfully.")
        except sqlite3.OperationalError:
            print("Column 'office' already exists.")

        # Add 'salary' column to leave_application
        try:
            conn.execute('ALTER TABLE leave_application ADD COLUMN salary INTEGER')
            print("Column 'salary' added successfully.")
        except sqlite3.OperationalError:
            print("Column 'salary' already exists.")

def add_column_to_travel_authority():
    with sqlite3.connect('documents.db') as conn:
        # Add 'recommender_position' column to travel_authority
        try:
            conn.execute('ALTER TABLE travel_authority ADD COLUMN recommender_position TEXT')
            print("Column 'recommender_position' added successfully.")
        except sqlite3.OperationalError:
            print("Column 'recommender_position' already exists.")

if __name__ == '__main__':
    add_columns_to_leave_application()  # Call to alter leave_application table
    add_column_to_table()               # Call to alter recommended_applications table
    add_column_to_travel_authority()     # Call to alter travel_authority table
