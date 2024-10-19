def add_rejection_comment_column():
    with sqlite3.connect('documents.db') as conn:
        conn.execute('ALTER TABLE cto_application ADD COLUMN rejection_comment TEXT;')
        conn.execute('ALTER TABLE leave_application ADD COLUMN rejection_comment TEXT;')
        conn.execute('ALTER TABLE travel_authority ADD COLUMN rejection_comment TEXT;')
        conn.commit()
    print("Rejection comment column added successfully.")
