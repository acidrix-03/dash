import sqlite3

def get_all_data_from_document_tracker():
    db_path = 'document_tracker.db'
    data = {}

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        # Fetch all documents
        cursor.execute("SELECT * FROM documents")
        data['documents'] = cursor.fetchall()

        # Fetch all forwarding history
        cursor.execute("SELECT * FROM forwarding_history")
        data['forwarding_history'] = cursor.fetchall()

        # Fetch all receiving history
        cursor.execute("SELECT * FROM receiving_history")
        data['receiving_history'] = cursor.fetchall()

    return data

# Example usage
if __name__ == "__main__":
    all_data = get_all_data_from_document_tracker()
    print("Documents:", all_data['documents'])
    print("Forwarding History:", all_data['forwarding_history'])
    print("Receiving History:", all_data['receiving_history'])