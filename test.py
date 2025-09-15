from app import db  # Replace `app` with your Flask app module
conn = db.connect()
cursor = conn.cursor()

cursor.execute('''
    SELECT id, name, position, division, office, document_type, submitted_by, details, received, comments
    FROM documents
    WHERE is_archived = 0;
''')
print(cursor.fetchall())

conn.close()
